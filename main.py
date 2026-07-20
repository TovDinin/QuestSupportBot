import telebot
import os
import time
import logging
import re
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# ========== AI-ЛОГИКА (сокращённо для ясности) ==========
def get_ai_response(text):
    q = text.lower()
    if re.search(r'(балл|очк|правил|score)', q):
        return "⭐ 1 попытка — 3 балла, 2 — 2 балла, 3 — 1 балл, после 3 — 0."
    if re.search(r'(маршрут|протяжённ|длина|км)', q):
        return "📍 Тобольск 6.3 км, Роттердам 5.5 км, Венеция 6.5 км."
    if re.search(r'(привет|здравствуй|hello)', q):
        return "👋 Привет! Я AI-помощник квеста. Чем могу помочь?"
    return "🤔 Я не понял вопрос. Попробуйте спросить о баллах, маршрутах или городах."

# ========== ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        # Логируем входящее сообщение
        logger.info(f"📩 Входящее сообщение от {user_id} ({user_name}): {user_text[:50]}")

        # Команда /start
        if user_text.startswith('/start'):
            bot.reply_to(message, "👋 Привет! Я AI-помощник квеста. Спрашивайте!")
            logger.info(f"✅ /start от {user_id}")
            return

        # Медиа — пересылаем администратору
        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            bot.send_message(ADMIN_ID, f"📩 Медиа от {user_name} (ID: {user_id})")
            bot.reply_to(message, "✅ Медиа отправлено администратору.")
            logger.info(f"📷 Медиа от {user_id} переслано администратору")
            return

        # Если это текст — решаем, что делать
        if user_text:
            quest_keywords = ['балл', 'очк', 'маршрут', 'город', 'загадк', 'подсказк', 'квест', 'как', 'где', 'что']
            is_quest = any(k in user_text.lower() for k in quest_keywords)
            
            if is_quest:
                response = get_ai_response(user_text)
                bot.send_message(user_id, response)
                logger.info(f"🤖 AI-ответ для {user_id}")
            
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

# ========== ОТВЕТЫ АДМИНИСТРАТОРА ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def handle_admin_reply(message):
    try:
        original = message.reply_to_message
        if original and original.text:
            parts = original.text.split('\n')
            for p in parts:
                if p.startswith('ID пользователя:'):
                    user_id = int(p.split(':')[1].strip())
                    bot.send_message(user_id, message.text)
                    bot.send_message(ADMIN_ID, "✅ Ответ отправлен.")
                    logger.info(f"✅ Ответ администратора отправлен {user_id}")
                    return
        bot.send_message(ADMIN_ID, "❌ Не найден ID пользователя.")
    except Exception as e:
        logger.error(f"❌ Ошибка ответа: {e}")

if __name__ == "__main__":
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    logger.info(f"🤖 @{bot.get_me().username}")
    logger.info(f"👤 Администратор: {ADMIN_ID}")
    logger.info("💬 Ожидание сообщений...")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            time.sleep(5)
