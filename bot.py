from videocr import save_subtitles_to_file
from videocr.plugin_manager import PLUGIN_REGISTRY, PluginDownloadTask, check_plugin_status, get_missing_plugins
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

Bot = Client(
    "videocrBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)


START_TXT = """
Hi {}, I'm videocr Bot.

Send a video with hard-coded subtitle to get an external srt file.
"""

START_BTN = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton('Source Code', url='https://github.com/soebb'),
    ]]
)


OCR_ENGINE = "google_lens"  # or "paddleocr"
LANGUAGE = "fa"


def ensure_paddleocr_v5_models() -> None:
    """Install the PP-OCRv5 model bundle expected by this VideOCR code.

    VideOCR's resolve_model_dirs() is pinned to PP-OCRv5, while the plugin
    manager's latest-release registry currently points to PP-OCRv6.
    Keep this compatibility fix in bot.py; do not modify the VideOCR library.
    """
    base_dir = Path(__file__).resolve().parent
    model_dir = base_dir / "PaddleOCR.PP-OCRv5.support.files"

    required_files = [
        model_dir / "det" / "PP-OCRv5_mobile_det" / "inference.yml",
        model_dir / "rec" / "arabic_PP-OCRv5_mobile_rec" / "inference.yml",
        model_dir / "cls" / "PP-LCNet_x1_0_textline_ori" / "inference.yml",
    ]

    if all(path.is_file() for path in required_files):
        print(f"[ready] PaddleOCR PP-OCRv5 models: {model_dir}", flush=True)
        return

    # The latest standalone release ships PP-OCRv6 models. VideOCR in this
    # repository explicitly requests PP-OCRv5, so use the last release that
    # provides the matching PP-OCRv5 support bundle.
    archive_url = (
        "https://github.com/timminator/PaddleOCR-Standalone/releases/download/"
        "v1.4.0/PaddleOCR.PP-OCRv5.support.files.VideOCR.tar.xz"
    )
    cache_dir = base_dir / ".plugin_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / "PaddleOCR.PP-OCRv5.support.files.VideOCR.tar.xz"
    partial_path = cache_dir / (archive_path.name + ".part")

    print("[download] Downloading the PP-OCRv5 model bundle required by VideOCR...", flush=True)

    # Do not reuse a partial or invalid model directory.
    if model_dir.exists():
        shutil.rmtree(model_dir)
    if partial_path.exists():
        partial_path.unlink()

    request = urllib.request.Request(
        archive_url,
        headers={"User-Agent": "VideOCR-Telegram-bot"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, open(partial_path, "wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)

    partial_path.replace(archive_path)

    print("[extract] Extracting PP-OCRv5 model files...", flush=True)
    with tarfile.open(archive_path, mode="r:xz") as archive:
        # The archive is a trusted release asset from the VideOCR dependency
        # publisher. Validate member paths before extraction.
        for member in archive.getmembers():
            target = (base_dir / member.name).resolve()
            if target != base_dir and base_dir not in target.parents:
                raise RuntimeError(f"Unsafe path in PP-OCRv5 archive: {member.name}")
        archive.extractall(base_dir)

    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        raise RuntimeError(
            "The downloaded PP-OCRv5 archive is incomplete; missing: "
            + ", ".join(missing)
        )

    print(f"[ready] PP-OCRv5 models installed: {model_dir}", flush=True)


def download_required_binaries() -> None:
    """Download and verify every binary/model required by the configured OCR engine.

    This runs once before the Telegram client starts, never in response to a video.
    """
    # VideOCR's bundled resolver is pinned to PP-OCRv5. Install that exact
    # model version separately instead of the plugin manager's newer PP-OCRv6.
    ensure_paddleocr_v5_models()

    required_plugins = [
        key for key, info in PLUGIN_REGISTRY.items()
        if OCR_ENGINE in info["required_for"] and key != "paddleocr_models"
    ]

    print(f"Preparing OCR dependencies for '{OCR_ENGINE}'...", flush=True)

    for plugin_key in required_plugins:
        status = check_plugin_status(plugin_key)
        if status["installed"]:
            print(f"[ready] {plugin_key}: {status['path']}", flush=True)
            continue

        print(f"[download] {plugin_key}...", flush=True)
        task = PluginDownloadTask(plugin_key, use_proxy=False)
        task.run()

        status = check_plugin_status(plugin_key)
        if task.status != "done" or not status["installed"]:
            details = task.error_message or "Download/extraction did not produce the expected files."
            raise RuntimeError(
                f"Could not prepare required OCR dependency '{plugin_key}': {details}"
            )

        print(f"[ready] {plugin_key}: {status['path']}", flush=True)

    # Final verification catches missing files before the bot accepts messages.
    missing = [
        key for key in required_plugins
        if not check_plugin_status(key)["installed"]
    ]
    if missing:
        raise RuntimeError(f"Required OCR dependencies are still missing: {', '.join(missing)}")

    print("All OCR dependencies are ready. Starting Telegram bot...", flush=True)


@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    text = START_TXT.format(update.from_user.mention)
    await update.reply_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=START_BTN
    )


def get_paddleocr_log_path() -> str:
    """Return the log path used by VideOCR's log_error() on Linux."""
    state_home = os.environ.get("XDG_STATE_HOME")
    if not state_home:
        state_home = os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(state_home, "VideOCR", "paddleocr_error.log")


@Bot.on_message(filters.private & (filters.video | filters.document))
async def from_tg_files(_, m):
    if m.document and not (m.document.mime_type or "").startswith("video/"):
        return

    msg = await m.reply("Downloading..")
    vid = await m.download()
    await msg.edit_text("Processing..")
    output_name = "out.srt"

    try:
        save_subtitles_to_file(vid, output_name, OCR_ENGINE, LANGUAGE)
        await m.reply_document(output_name)
    except (Exception, SystemExit) as exc:
        await m.reply_text(
            f"Video processing failed: {type(exc).__name__}: {exc}\n"
            "I'll send the PaddleOCR error log if it exists."
        )
        log_path = get_paddleocr_log_path()
        if os.path.isfile(log_path):
            try:
                await m.reply_document(
                    log_path,
                    caption="PaddleOCR error log (paddleocr_error.log)"
                )
            except Exception as send_error:
                await m.reply_text(f"Could not send the log file: {send_error}")
        else:
            await m.reply_text(
                f"Log file was not found at: {log_path}\n"
                "Please check the Railway service logs for the full error."
            )
    finally:
        if os.path.exists(output_name):
            os.remove(output_name)
        if vid and os.path.exists(vid):
            os.remove(vid)
        await msg.delete()


if __name__ == "__main__":
    download_required_binaries()
    Bot.run()
