import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
COOKIES_FILE = "cookies.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь ссылку для скачивания видео")

async def download_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id
    
    status_message = await update.message.reply_text("⏳ Скачиваю видео, подожди...")
    temp_file = f"video_{chat_id}"
    
    try:
        ydl_opts = {
            'format': 'best/bestvideo+bestaudio',
            'outtmpl': temp_file + '.%(ext)s',
            'quiet': True,
            'merge_output_format': 'mp4',
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            'socket_timeout': 30,
            'retries': 3,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Видео')
            ext = info.get('ext', 'mp4')
        
        actual_file = temp_file + '.' + ext
        if not os.path.exists(actual_file):
            for e in ['mp4', 'webm', 'mkv', 'mov']:
                if os.path.exists(temp_file + '.' + e):
                    actual_file = temp_file + '.' + e
                    break
        
        file_size = os.path.getsize(actual_file)
        if file_size > 50 * 1024 * 1024:
            await status_message.edit_text("❌ Видео слишком большое (>50 МБ).")
            os.remove(actual_file)
            return
        
        await status_message.edit_text("📤 Отправляю видео...")
        with open(actual_file, 'rb') as video:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video,
                caption=f"🎬 {title}",
                supports_streaming=True
            )
        await status_message.delete()
        
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка: {str(e)}")
    finally:
        for e in ['mp4', 'webm', 'mkv', 'mov']:
            f = temp_file + '.' + e
            if os.path.exists(f):
                os.remove(f)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_and_send_video))
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
