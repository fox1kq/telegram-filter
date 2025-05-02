from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
from ban_words import ban_words

# 🚫 Запрещённые слова
BANNED_WORDS = ban_words

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# 🔎 Проверка на запрещённые слова
def contains_banned_word(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in BANNED_WORDS)


# 📩 Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text or ""
    user = update.message.from_user
    chat = update.message.chat

    if contains_banned_word(text):
        try:
            # Удаляем сообщение
            await update.message.delete()

            # Перманентный мут (все разрешения отключены)
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_audios=False,
                    can_send_documents=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_video_notes=False,
                    can_send_voice_notes=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_manage_topics=False
                )
            )

            # Выделение запрещённых слов в сообщении
            highlighted_text = text
            for word in BANNED_WORDS:
                if word in highlighted_text:
                    highlighted_text = highlighted_text.replace(word, f"*{word}*")

            # Лог админу (в ЛС)
            log_msg = (
                f"🚨 *Удалено сообщение с запрещёнными словами!*\n"
                f"👤 Пользователь: @{user.username or '—'}\n"
                f"💬 Сообщение: {highlighted_text}\n"
                f"👥 Группа: {chat.title or chat.id}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=log_msg, parse_mode='Markdown')

        except Exception as e:
            print(f"Ошибка: {e}")


# 🚀 Запуск
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Бот запущен!")
    app.run_polling()