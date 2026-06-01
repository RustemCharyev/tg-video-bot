import os
import logging
import glob
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(SCRIPT_DIR, "cookies.txt")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь ссылку для скачивания видео")

async def download_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    status_message = await update.message.reply_text("⏳ Скачиваю видео, подожди...")
    temp_base = os.path.join(SCRIPT_DIR, f"video_{chat_id}")
    
    # Чистим старые файлы
    for old in glob.glob(f"{temp_base}*"):
        try:
            os.remove(old)
        except Exception:
            pass
    
    # Проверяем cookies
    has_cookies = os.path.exists(COOKIES_PATH)
    logger.info(f"Cookies файл: {COOKIES_PATH} | Найден: {has_cookies}")
    
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'outtmpl': temp_base + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
        }
        
        # ВАЖНО: в Python API yt-dlp параметр называется cookiefile (не cookies!)
        if has_cookies:
            ydl_opts['cookiefile'] = COOKIES_PATH
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Видео') if info else 'Видео'
        
        # Ищем скачанный файл
        actual_file = None
        for ext in ['mp4', 'webm', 'mkv', 'mov', 'avi']:
            candidate = f"{temp_base}.{ext}"
            if os.path.exists(candidate):
                actual_file = candidate
                break
        
        if not actual_file:
            await status_message.edit_text("❌ Не удалось найти скачанный файл.")
            return
        
        file_size = os.path.getsize(actual_file)
        if file_size > 50 * 1024 * 1024:
            await status_message.edit_text("❌ Видео слишком большое (>50 МБ).")
            os.remove(actual_file)
            return
        
        await status_message.edit_text("📤 Отправляю видео...")
        
        with open(actual_file, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=f"🎬 {title}",
                supports_streaming=True
            )
        
        try:
            await status_message.delete()
        except Exception:
            pass
        
    except Exception as e:
        error_text = str(e)
        logger.error(f"Ошибка: {error_text}")
        
        if "Sign in to confirm" in error_text or "not a bot" in error_text:
            await status_message.edit_text(
                "❌ Google заблокировал IP сервера Railway.\n\n"
                "Cookies на облачных серверах больше не работают — Google проверяет IP.\n\n"
                "🔧 Решение: перейди на VPS с «домашним» IP (не облако):\n"
                "• Timeweb.cloud — от 200₽/мес\n"
                "• Beget — от 200₽/мес\n"
                "• Или любой другой хостинг\n\n"
                "Там всё заработает с тем же кодом и cookies.txt.\n"
                "TikTok, VK, Rutube, Instagram — работают и на Railway."
            )
        else:
            await status_message.edit_text(f"❌ Ошибка: {error_text}")
    
    finally:
        for pattern in [f"{temp_base}.*", f"{temp_base}*.part", f"{temp_base}*.ytdl"]:
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except Exception:
                    pass

def main():
    if not TOKEN:
        logger.error("TOKEN не найден!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_and_send_video))
    
    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
