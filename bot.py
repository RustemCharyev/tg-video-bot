import os
import glob
import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
import yt_dlp

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8734624148:AAF3x5Z3pbPNYp-ZECK0zU2DkGCYVXqnFb0")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

@dp.message()
async def download_and_send_video(message: types.Message):
    url = message.text
    if not url or not url.startswith(("http://", "https://")):
        await message.answer("Отправь ссылку на видео (YouTube, TikTok, Instagram, VK...)")
        return

    status = await message.answer("⏳ Скачиваю...")
    os.makedirs("downloads", exist_ok=True)
    output_template = f"downloads/{message.from_user.id}_%(id)s.%(ext)s"

    cookie_files = glob.glob("*cookies*.txt")
    cookie_arg = {"cookiefile": cookie_files[0]} if cookie_files else {}

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        **cookie_arg,
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filepath = await loop.run_in_executor(None, download)

        if not os.path.exists(filepath):
            base, _ = os.path.splitext(filepath)
            filepath = base + ".mp4"

        await status.edit_text("🚀 Отправляю...")
        await message.reply_video(video=FSInputFile(filepath), caption="Готово! 🎬")
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ Ошибка: `{str(e)[:300]}`", parse_mode="Markdown")

    finally:
        for f in glob.glob(f"downloads/{message.from_user.id}_*"):
            try:
                os.remove(f)
            except:
                pass

async def main():
    threading.Thread(target=run_server, daemon=True).start()
    print("✅ Бот запущен!")
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
