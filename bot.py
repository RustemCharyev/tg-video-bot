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
    temp_file = f"video_{chat_id}.mp4"
    
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][filesize<45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<45M]/best',
            'outtmpl': temp_file,
            'quiet': True,
            'merge_output_format': 'mp4',
            'cookiefile': COOKIES_FILE,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Видео')
        
        file_size = os.path.getsize(temp_file)
        if file_size > 50 * 1024 * 1024:
            await status_message.edit_text("❌ Видео слишком большое (>50 МБ).")
            os.remove(temp_file)
            return
        
        await status_message.edit_text("📤 Отправляю видео...")
        with open(temp_file, 'rb') as video:
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
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_and_send_video))
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
