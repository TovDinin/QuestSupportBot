import telebot
import os
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

logger.info(f"BOT_TOKEN: {'установлен' if BOT_TOKEN else 'НЕ УСТАНОВЛЕН'}")
logger.info(f"ADMIN_ID: {'установлен' if ADMIN_ID else 'НЕ УСТАНОВЛЕН'}")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не задан!")

try:
    ADMIN_ID = int(ADMIN_ID)
    logger.info(f"ADMIN_ID: {ADMIN_ID}")
except ValueError:
    raise ValueError(f"ADMIN_ID должен быть числом, получено: {ADMIN_ID}")

# Создаём бота
bot = telebot.TeleBot(BOT_TOKEN)

# Обработчик сообщений от пользователей
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_message(message):
    try:
        user_id = message.chat.id
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        forward_text = f"📩 Новое сообщение от {user_name} (ID: {user_id}):\n\n{message.text}"
        bot.send_message(ADMIN_ID, forward_text)
        bot.reply_to(message, "✅ Ваше сообщение отправлено. Ожидайте ответа.")
        logger.info(f"Сообщение от {user_id} переслано администратору")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")

# Обработчик ответов администратора
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
                logger.info(f"Ответ отправлен пользователю {user_id}")
                return
        bot.send_message(ADMIN_ID, "❌ Не удалось найти ID пользователя в пересланном сообщении.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")
        bot.send_message(ADMIN_ID, f"❌ Ошибка при отправке ответа: {e}")

# Старт бота
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Бот запущен и готов к работе!")
    logger.info("=" * 50)
    logger.info(f"Бот: @{bot.get_me().username}")
    logger.info(f"Администратор: {ADMIN_ID}")
    logger.info("Ожидание сообщений...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        time.sleep(5)
