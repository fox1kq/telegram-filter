from flask import Flask, request
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
from ban_words import ban_words

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например, https://yourbot.onrender.com

BANNED_WORDS = ban_words

app_flask = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# 🚫 Фильтрация
def contains_banned_word(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in BANNED_WORDS)

# 📩 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text or ""
    user = update.message.from_user
    chat = update.message.chat

    if contains_banned_word(text):
        try:
            await update.message.delete()
            await context.bot.restrict_chat_member(
                chat.id, user.id,
                permissions=ChatPermissions()
            )
            log_msg = (
                f"🚨 *Удалено сообщение с запрещёнными словами!*\n"
                f"👤 Пользователь: @{user.username or '—'}\n"
                f"💬 Сообщение: `{text}`\n"
                f"👥 Группа: {chat.title or chat.id}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=log_msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Ошибка: {e}")

# 📬 Входящий webhook от Telegram
@app_flask.post("/")
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

# 🟢 Запуск (main)
if __name__ == "__main__":
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Устанавливаем webhook
    async def main():
        await application.bot.set_webhook(WEBHOOK_URL)
        print("Webhook установлен!")

    import asyncio
    asyncio.run(main())

    # Запуск Flask-сервера на порту от Render
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
