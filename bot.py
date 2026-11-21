from videocr import save_subtitles_to_file
from videocr.plugin_manager import PLUGIN_REGISTRY, PluginDownloadTask, check_plugin_status, get_missing_plugins
import os
import traceback
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


def download_required_binaries() -> None:
    """Download and verify every binary/model required by the configured OCR engine.

    This runs once before the Telegram client starts, never in response to a video.
    """
    required_plugins = [
        key for key, info in PLUGIN_REGISTRY.items()
        if OCR_ENGINE in info["required_for"]
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
        # Always preserve the Python traceback, including failures outside the
        # PaddleOCR subprocess (for example JSON parsing or post-processing).
        state_home = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
        log_dir = os.path.join(state_home, "VideOCR")
        os.makedirs(log_dir, exist_ok=True)
        diagnostic_path = os.path.join(log_dir, "processing_error.log")
        with open(diagnostic_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"Exception: {type(exc).__name__}: {exc}\\n\\n")
            log_file.write(traceback.format_exc())

        await m.reply_text(
            f"Video processing failed: {type(exc).__name__}: {exc}\\n"
            "I'll send the Python traceback and any OCR subprocess log."
        )

        # This traceback log is always created by the bot's exception handler.
        try:
            await m.reply_document(
                diagnostic_path,
                caption="Processing traceback (processing_error.log)"
            )
        except Exception as send_error:
            await m.reply_text(f"Could not send the processing traceback: {send_error}")

        # PaddleOCR and Google Lens keep their own stderr/stdout logs.
        for engine_log_name in ("paddleocr_error.log", "google_lens_error.log"):
            engine_log_path = os.path.join(log_dir, engine_log_name)
            if os.path.isfile(engine_log_path):
                try:
                    await m.reply_document(
                        engine_log_path,
                        caption=f"OCR subprocess log ({engine_log_name})"
                    )
                except Exception as send_error:
                    await m.reply_text(f"Could not send {engine_log_name}: {send_error}")
    finally:
        if os.path.exists(output_name):
            os.remove(output_name)
        if vid and os.path.exists(vid):
            os.remove(vid)
        await msg.delete()


if __name__ == "__main__":
    download_required_binaries()
    Bot.run()
