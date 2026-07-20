import telebot
import os
import time
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# ========== AI-ПОМОЩНИК ==========
def get_ai_response(question):
    """Отвечает на вопросы по квесту"""
    q = question.lower().strip()
    
    if re.search(r'(привет|здравствуй|hello|hi)', q):
        return "👋 Привет! Я AI-помощник квеста «Тайны вашего города». Спрашивайте о маршрутах, баллах, загадках — я помогу!"
    
    if re.search(r'(балл|очк|правил|score|как набрать|сколько)', q):
        return "⭐ **Правила начисления баллов:**\n• 1 попытка — 3 балла\n• 2 попытка — 2 балла\n• 3 попытка — 1 балл\n• После 3 ошибок — подсказка и 0 баллов\n\n🎯 Максимум за квест: 30–45 баллов."
    
    if re.search(r'(подсказк|hint|помощь|как найти|где искать)', q):
        return "💡 **Подсказки:**\n• Каждая точка — реальный объект (памятник, здание, табличка).\n• Ищите информацию на фасадах, стендах и информационных щитах.\n• Если застряли — попробуйте найти точку на карте."
    
    if re.search(r'(маршрут|протяжённ|длина|расстояни|километр|км|время)', q):
        return "📍 **Маршруты:**\n• Тобольск — 6.3 км, ~1.9 часа\n• Роттердам — 5.5 км, ~2 часа\n• Венеция — 6.5 км, ~3 часа\n\n🔥 Примерно 300–370 ккал (как один бургер!)"
    
    if re.search(r'(город|city|какие города|доступн|выбрать)', q):
        return "🏙️ **Доступные города:**\n• Тобольск (Россия) — 12 точек\n• Роттердам (Нидерланды) — 10 точек\n• Венеция (Италия) — 11 точек\n\nНовые города добавляются регулярно!"
    
    if re.search(r'(загадк|riddle|сложн|трудн|ответ)', q):
        return "🔍 **Про загадки:**\n• Внимательно читайте текст — ключ к ответу всегда в нём.\n• Используйте логику и наблюдательность.\n• Если совсем трудно — AI-помощник даст подсказку."
    
    if re.search(r'(помощь|help|support|контакт|админ|разработчик|телеграм|email)', q):
        return "📩 **Контакты:**\n• Telegram: @Quest_supportbot\n• Email: quest@tobolsk-quest.com\n• Или нажмите кнопку «Обратная связь» в приложении."
    
    return "🤔 Я не совсем понял ваш вопрос. Попробуйте спросить о:\n• баллах и правилах\n• маршрутах и городах\n• подсказках и загадках\n• контактах для связи"

# ========== ЕДИНЫЙ ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        # Если это команда /start
        if user_text.startswith('/start'):
            bot.reply_to(message, "👋 Привет! Я AI-помощник квеста «Тайны вашего города».\n\nЗадавайте любые вопросы по квесту — я помогу! ✨")
            logger.info(f"Команда /start от {user_id}")
            return
        
        # Если это медиа (фото, голос, стикер)
        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            prefix = f"📩 Новое медиа от {user_name} (ID: {user_id})"
            if message.photo:
                caption = message.caption or ""
                bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{prefix}:\n\n{caption}")
            elif message.voice:
                bot.send_voice(ADMIN_ID, message.voice.file_id, caption=prefix)
            elif message.sticker:
                bot.send_sticker(ADMIN_ID, message.sticker.file_id)
            elif message.document:
                caption = message.caption or ""
                bot.send_document(ADMIN_ID, message.document.file_id, caption=f"{prefix}:\n\n{caption}")
            elif message.video:
                caption = message.caption or ""
                bot.send_video(ADMIN_ID, message.video.file_id, caption=f"{prefix}:\n\n{caption}")
            elif message.audio:
                caption = message.caption or ""
                bot.send_audio(ADMIN_ID, message.audio.file_id, caption=f"{prefix}:\n\n{caption}")
            else:
                bot.send_message(ADMIN_ID, f"{prefix} (тип: {message.content_type})")
            
            bot.reply_to(message, "✅ Ваше медиа отправлено администратору.")
            logger.info(f"Медиа от {user_id} переслано администратору")
            return
        
        # Если это текстовое сообщение
        if user_text:
            # Проверяем, похоже ли сообщение на вопрос по квесту
            quest_keywords = ['балл', 'очк', 'правил', 'маршрут', 'город', 'загадк', 'подсказк', 
                             'как', 'где', 'что', 'кто', 'когда', 'почему', 'сколько', 
                             'бонус', 'квест', 'точк', 'пройти', 'пройден', 'финиш', 'помощь', 
                             'спасиб', 'контакт', 'админ', 'email', 'телеграм']
            
            is_quest_question = any(keyword in user_text.lower() for keyword in quest_keywords)
            
            if is_quest_question:
                # Отвечаем как AI-помощник
                response = get_ai_response(user_text)
                bot.send_message(user_id, response)
                logger.info(f"AI-ответ для {user_id}: {response[:50]}...")
            else:
                # Если не похоже на вопрос по квесту — пересылаем администратору
                forward_text = f"📩 Новое сообщение от {user_name} (ID: {user_id}):\n\n{user_text}"
                bot.send_message(ADMIN_ID, forward_text)
                bot.reply_to(message, "✅ Ваше сообщение отправлено администратору.")
                logger.info(f"Сообщение от {user_id} переслано администратору")
            
            return
        
        # Если ничего не подошло
        bot.send_message(ADMIN_ID, f"⚠️ Неизвестное сообщение от {user_name} (ID: {user_id})")
        logger.warning(f"Неизвестное сообщение от {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике: {e}")
        try:
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте ещё раз.")
        except:
            pass

# ========== ОТВЕТЫ АДМИНИСТРАТОРА ==========
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
        bot.send_message(ADMIN_ID, "❌ Не удалось найти ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")
        bot.send_message(ADMIN_ID, f"❌ Ошибка: {e}")

if __name__ == "__main__":
    logger.info("🚀 Бот запущен!")
    logger.info(f"Бот: @{bot.get_me().username}")
    logger.info(f"Администратор: {ADMIN_ID}")
    logger.info("💬 AI-помощник и пересыльщик сообщений активны!")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка polling: {e}")
            time.sleep(5)
