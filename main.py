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
def get_ai_response(text):
    q = text.lower()
    
    # Приветствия
    if re.search(r'(привет|здравствуй|hello|hi|добрый день|доброе утро)', q):
        return "👋 Привет! Я AI-помощник квеста «Тайны вашего города». Спрашивайте о баллах, маршрутах, городах и загадках!"

    # Баллы
    if re.search(r'(балл|очк|правил|score|как набрать|сколько|максимум|рейтинг)', q):
        return "⭐ **Правила начисления баллов:**\n• 1-я попытка — 3 балла\n• 2-я попытка — 2 балла\n• 3-я попытка — 1 балл\n• После 3 ошибок — подсказка (0 баллов)\n\n🎯 Максимум: 36 баллов в Тобольске, 30 в Роттердаме, 33 в Венеции."

    # Маршруты
    if re.search(r'(маршрут|протяжённ|длина|расстояни|километр|км|время|часов|идти)', q):
        return "📍 **Маршруты:**\n• Тобольск — 6.3 км, ~1.9 часа (🔥 ~360 ккал)\n• Роттердам — 5.5 км, ~2.0 часа (🔥 ~310 ккал)\n• Венеция — 6.5 км, ~3.0 часа (🔥 ~370 ккал)"

    # Города
    if re.search(r'(город|city|какие города|доступн|выбрать|список|новые города)', q):
        return "🏙️ **Доступные города:**\n• Тобольск (Россия) — 12 точек\n• Роттердам (Нидерланды) — 10 точек\n• Венеция (Италия) — 11 точек\n\n🌍 Новые города появляются регулярно!"

    # Подсказки
    if re.search(r'(подсказк|hint|помощь|как найти|где искать|не могу найти|застрял|трудн)', q):
        return "💡 **Как искать точки:**\n• Каждая точка — реальный объект (памятник, здание, табличка)\n• Ищите информацию на фасадах, стендах и информационных щитах\n• Используйте карту в приложении\n• Если совсем трудно — я дам подсказку, но балл снизится"

    # Загадки
    if re.search(r'(загадк|riddle|сложн|ответ|не понимаю|что значит|как решить)', q):
        return "🔍 **Про загадки:**\n• Внимательно читайте текст — ключ к ответу всегда в нём\n• Используйте логику и наблюдательность\n• Ответ — обычно одно слово или короткая фраза\n• Если трудно — попросите подсказку"

    # Контакты
    if re.search(r'(контакт|админ|разработчик|телеграм|email|поддержк|help|support|жалоб|отзыв)', q):
        return "📩 **Контакты:**\n• Telegram: @Quest_supportbot\n• Email: quest@tobolsk-quest.com\n• В приложении: кнопка «Обратная связь»"

    # Семья
    if re.search(r'(дет|ребенк|семь|друзь|команд|групп|вместе|коллектив)', q):
        return "👨‍👩‍👧‍👦 **Семейный режим:**\n• Подходит для детей от 8 лет\n• Можно играть в команде — общие баллы\n• Идеально для прогулок с друзьями и семьёй\n• Не забудьте сделать фото на финише!"

    # Калории
    if re.search(r'(калори|ккал|сжигать|фитнес|здоровь|польз|активн)', q):
        return "🔥 **Сжигайте калории:**\n• Тобольск: ~360 ккал\n• Роттердам: ~310 ккал\n• Венеция: ~370 ккал\n\n🚶 10 000 шагов — легко! Квест превращает прогулку в приключение."

    # Прощание
    if re.search(r'(пока|до свидания|bye|goodbye|прощай)', q):
        return "До свидания! Удачного квеста! 🗺️"

    # Благодарность
    if re.search(r'(спасиб|thank|thanks|благодар|крут|класс|супер|отлично)', q):
        return "Пожалуйста! Рад помочь! 🗺️"

    # Если ничего не подошло
    return None

# ========== ОСНОВНАЯ ЛОГИКА ==========

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "👋 Привет! Я AI-помощник квеста «Тайны вашего города».\n\nЯ отвечаю на вопросы о:\n• баллах и правилах\n• маршрутах и городах\n• подсказках и загадках\n• контактах\n\nЕсли я не пойму вопрос — перешлю его администратору.")
    logger.info(f"✅ /start от {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        # Пропускаем команды
        if user_text.startswith('/'):
            return

        # Медиа — всегда пересылаем администратору
        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            bot.send_message(ADMIN_ID, f"📩 Медиа от {user_name} (ID: {user_id})")
            bot.reply_to(message, "✅ Медиа отправлено администратору.")
            logger.info(f"📷 Медиа от {user_id} переслано администратору")
            return

        # Если это текст
        if user_text:
            # Пытаемся получить AI-ответ
            ai_response = get_ai_response(user_text)
            
            if ai_response:
                # Если AI понял вопрос — отвечаем И НЕ ПЕРЕСЫЛАЕМ
                bot.send_message(user_id, ai_response)
                logger.info(f"🤖 AI-ответ для {user_id}: {ai_response[:50]}...")
            else:
                # Если AI не понял — пересылаем администратору
                forward_text = f"📩 Сообщение от {user_name} (ID: {user_id}):\n\n{user_text}"
                bot.send_message(ADMIN_ID, forward_text)
                bot.reply_to(message, "✅ Ваше сообщение отправлено администратору.")
                logger.info(f"📤 Сообщение от {user_id} переслано администратору")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        try:
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте ещё раз.")
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
                    bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю.")
                    logger.info(f"✅ Ответ отправлен пользователю {user_id}")
                    return
        bot.send_message(ADMIN_ID, "❌ Не найден ID пользователя.")
    except Exception as e:
        logger.error(f"❌ Ошибка ответа: {e}")

if __name__ == "__main__":
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    logger.info(f"🤖 @{bot.get_me().username}")
    logger.info(f"👤 Администратор: {ADMIN_ID}")
    logger.info("💬 Режим: AI отвечает на вопросы по квесту, остальное — пересылает администратору")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            time.sleep(5)
