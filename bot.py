from videocr import save_subtitles_to_file
from videocr.plugin_manager import PLUGIN_REGISTRY, PluginDownloadTask, check_plugin_status, get_missing_plugins
import os
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
    missing = get_missing_plugins(OCR_ENGINE)
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
                "Please check the Render service logs for the full error."
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
