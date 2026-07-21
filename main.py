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
bot = telebot.TeleBot(BOT_TOKEN)

# ========== КОМАНДА ДЛЯ ДИАГНОСТИКИ ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "👋 Привет! Бот работает. Напишите любое сообщение, и оно будет переслано администратору.")
    logger.info(f"✅ /start от {message.chat.id}")

@bot.message_handler(commands=['admin'])
def handle_admin_check(message):
    """Проверяет, доходит ли сообщение до администратора"""
    try:
        bot.send_message(ADMIN_ID, f"🔔 Тестовое сообщение администратору от бота. Ваш ID: {ADMIN_ID}")
        bot.reply_to(message, f"✅ Тестовое сообщение отправлено администратору ({ADMIN_ID}). Проверьте Telegram!")
        logger.info(f"✅ Тестовое сообщение отправлено администратору {ADMIN_ID}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке тестового сообщения: {e}")
        logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")

# ========== ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        logger.info(f"📩 Входящее сообщение от {user_id} ({user_name}): {user_text[:50]}")

        # Если это команда /admin — обработана выше
        if user_text.startswith('/admin'):
            return

        # Если это команда /start — обработана выше
        if user_text.startswith('/start'):
            return

        # Медиа
        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            bot.send_message(ADMIN_ID, f"📩 Медиа от {user_name} (ID: {user_id})")
            bot.reply_to(message, "✅ Медиа отправлено администратору.")
            logger.info(f"📷 Медиа от {user_id} переслано администратору")
            return

        # Текстовые сообщения
        if user_text:
            # ВСЕГДА пересылаем администратору
            forward_text = f"📩 Сообщение от {user_name} (ID: {user_id}):\n\n{user_text}"
            bot.send_message(ADMIN_ID, forward_text)
            bot.reply_to(message, "✅ Сообщение отправлено администратору.")
            logger.info(f"📤 Сообщение от {user_id} переслано администратору ({ADMIN_ID})")
            return

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        try:
            bot.reply_to(message, "❌ Произошла ошибка.")
        except:
            pass

if __name__ == "__main__":
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    logger.info(f"🤖 @{bot.get_me().username}")
    logger.info(f"👤 Администратор: {ADMIN_ID}")
    logger.info("💬 Ожидание сообщений...")
    logger.info("📌 Команды: /start - приветствие, /admin - тест связи с администратором")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            time.sleep(5)
