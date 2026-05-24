from videocr import save_subtitles_to_file
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

Bot = Client(
    "videocrBot",
    bot_token = BOT_TOKEN,
    api_id = API_ID,
    api_hash = API_HASH
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


OCR_ENGINE = "google_lens" # or "paddleocr"
LANGUAGE = "fa"

@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    text = START_TXT.format(update.from_user.mention)
    reply_markup = START_BTN
    await update.reply_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )


@Bot.on_message(filters.private & (filters.video | filters.document))
async def from_tg_files(_, m):
    if m.document and not m.document.mime_type.startswith("video/"):
        return
    msg = await m.reply("Downloading..")
    vid = await m.download()
    await msg.edit_text("Processing..")
    output_name = "out.srt"
    save_subtitles_to_file(vid, output_name, OCR_ENGINE, LANGUAGE)
    await m.reply_document(output_name)
    await msg.delete()
    os.remove(output_name)
    os.remove(vid)


Bot.run()
