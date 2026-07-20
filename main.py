import telebot
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы!")

ADMIN_ID = int(ADMIN_ID)

# Указываем явный таймаут и параметры для polling
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "✅ Бот работает! Отправьте любое сообщение.")
    logger.info(f"Команда /start от {message.chat.id}")

@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_message(message):
    try:
        user_id = message.chat.id
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        forward_text = f"📩 Новое сообщение от {user_name} (ID: {user_id}):\n\n{message.text}"
        bot.send_message(ADMIN_ID, forward_text)
        bot.reply_to(message, "✅ Ваше сообщение отправлено.")
        logger.info(f"Сообщение от {user_id} переслано администратору")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def handle_admin_reply(message):
    try:
        original_message = message.reply_to_message
        if original_message and original_message.text:
            parts = original_message.text.split('\n')
            user_id_part = next((p for p in parts if p.startswith('ID пользователя:')), None)
            if user_id_part:
                user_id = int(user_id_part.split(':')[1].strip())
                bot.send_message(user_id, message.text)
                bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю.")
                return
        bot.send_message(ADMIN_ID, "❌ Не удалось найти ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")

if __name__ == "__main__":
    logger.info("🚀 Бот запущен!")
    logger.info(f"Бот: @{bot.get_me().username}")
    logger.info(f"Администратор: {ADMIN_ID}")
    
    while True:
        try:
            # Используем явные параметры для polling
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка polling: {e}")
            time.sleep(5)
