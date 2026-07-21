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

# ========== ФУНКЦИЯ ПРИНУДИТЕЛЬНОЙ ОТПРАВКИ ==========
def force_send(chat_id, text):
    """Отправляет сообщение с повторной попыткой в случае ошибки"""
    try:
        bot.send_message(chat_id, text)
        logger.info(f"✅ Сообщение отправлено {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        # Пробуем через API напрямую (обходной путь)
        try:
            import requests
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            response = requests.post(url, data=data)
            if response.ok:
                logger.info(f"✅ Сообщение отправлено через API {chat_id}")
                return True
            else:
                logger.error(f"❌ Ошибка API: {response.text}")
                return False
        except Exception as e2:
            logger.error(f"❌ Ошибка API: {e2}")
            return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "👋 Привет! Бот работает.")
    logger.info(f"✅ /start от {message.chat.id}")

@bot.message_handler(commands=['admin'])
def handle_admin_check(message):
    """Проверка связи с администратором"""
    result = force_send(ADMIN_ID, f"🔔 Тестовое сообщение администратору. Ваш ID: {ADMIN_ID}")
    if result:
        bot.reply_to(message, f"✅ Тестовое сообщение отправлено администратору ({ADMIN_ID}). Проверьте Telegram!")
    else:
        bot.reply_to(message, f"❌ Не удалось отправить сообщение администратору. Проверьте логи.")
    logger.info(f"📤 Тестовое сообщение администратору {ADMIN_ID}: {'✅' if result else '❌'}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        logger.info(f"📩 Входящее сообщение от {user_id} ({user_name}): {user_text[:50]}")

        if user_text.startswith('/start') or user_text.startswith('/admin'):
            return

        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            force_send(ADMIN_ID, f"📩 Медиа от {user_name} (ID: {user_id})")
            bot.reply_to(message, "✅ Медиа отправлено администратору.")
            return

        if user_text:
            forward_text = f"📩 Сообщение от {user_name} (ID: {user_id}):\n\n{user_text}"
            force_send(ADMIN_ID, forward_text)
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
    logger.info("📌 Команды: /start - приветствие, /admin - тест связи")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            time.sleep(5)
