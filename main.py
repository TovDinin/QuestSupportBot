import telebot
import os
import time
import logging
import re
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# ========== РАСШИРЕННАЯ БАЗА ЗНАНИЙ ==========

# Контекстные ответы (для поддержки диалога)
USER_CONTEXT = {}

# Приветствия и прощания
GREETINGS = {
    'patterns': [r'(привет|здравствуй|hello|hi|добрый день|доброе утро|салам|хай)', r'(пока|до свидания|bye|goodbye|прощай)'],
    'responses': {
        'greeting': [
            "👋 Привет! Я AI-помощник квеста «Тайны вашего города». Чем могу помочь?",
            "Здравствуйте! Рада видеть вас в нашем квесте. Спрашивайте — я отвечу на любые вопросы!",
            "Приветствую! Я здесь, чтобы сделать ваш квест незабываемым. О чём хотите узнать?"
        ],
        'farewell': [
            "До свидания! Удачного квеста! 🗺️",
            "Пока! Если появятся вопросы — я всегда здесь. 😊",
            "Всего хорошего! Надеюсь, вам понравится квест! ⭐"
        ]
    }
}

# Темы и ключевые слова для разных типов вопросов
TOPICS = {
    'baly': {
        'patterns': [r'балл', r'очк', r'счёт', r'score', r'набрать', r'сколько', r'максимум', r'рейтинг'],
        'response': "⭐ **Правила начисления баллов:**\n• 1-я попытка — 3 балла\n• 2-я попытка — 2 балла\n• 3-я попытка — 1 балл\n• После 3 ошибок — подсказка (0 баллов)\n\n🎯 **Максимум:** 36 баллов в Тобольске, 30 в Роттердаме, 33 в Венеции.\n\n💡 Совет: читайте загадки внимательно, часто ответ уже в тексте!"
    },
    'route': {
        'patterns': [r'маршрут', r'протяжённ', r'длина', r'расстояни', r'километр', r'км', r'время', r'часов', r'идти'],
        'response': "📍 **Маршруты и время:**\n• **Тобольск** — 6.3 км, ~1.9 часа (🔥 ~360 ккал)\n• **Роттердам** — 5.5 км, ~2.0 часа (🔥 ~310 ккал)\n• **Венеция** — 6.5 км, ~3.0 часа (🔥 ~370 ккал)\n\n✨ Средний темп — 3–4 км/ч. Не торопитесь, наслаждайтесь видами!"
    },
    'cities': {
        'patterns': [r'город', r'city', r'какие города', r'доступн', r'выбрать', r'список', r'новые города', r'добавят'],
        'response': "🏙️ **Доступные города:**\n• **Тобольск** (Россия) — 12 точек\n• **Роттердам** (Нидерланды) — 10 точек\n• **Венеция** (Италия) — 11 точек\n\n🌍 Новые города появляются регулярно. Подписывайтесь на обновления! Если хотите добавить свой город — напишите нам."
    },
    'hint': {
        'patterns': [r'подсказк', r'hint', r'помощь', r'как найти', r'где искать', r'не могу найти', r'застрял', r'трудн'],
        'response': "💡 **Как искать точки:**\n• Каждая точка — реальный объект: памятник, здание, табличка, мемориальная доска.\n• Ищите информацию на фасадах, стендах и информационных щитах.\n• Используйте карту в приложении — она показывает ваше местоположение.\n• Если совсем трудно — вернитесь на шаг назад и перечитайте загадку.\n\n🤖 Я могу дать дополнительную подсказку, но это уменьшит ваш балл за точку."
    },
    'riddle': {
        'patterns': [r'загадк', r'riddle', r'сложн', r'ответ', r'не понимаю', r'что значит', r'как решить'],
        'response': "🔍 **Про загадки:**\n• Внимательно читайте текст — ключ к ответу всегда в нём.\n• Используйте логику и наблюдательность.\n• Ответ — это обычно одно слово или короткая фраза.\n• Если совсем трудно — попросите подсказку (я дам, но балл снизится).\n\n💪 Помните: каждая загадка — это шаг к новому знанию о городе!"
    },
    'feedback': {
        'patterns': [r'контакт', r'админ', r'разработчик', r'телеграм', r'email', r'поддержк', r'help', r'support', r'жалоб', r'отзыв'],
        'response': "📩 **Как связаться с нами:**\n• **Telegram:** @Quest_supportbot\n• **Email:** quest@tobolsk-quest.com\n• **В приложении:** кнопка «Обратная связь»\n\n🙏 Спасибо, что помогаете делать квест лучше! Ваше мнение важно для нас."
    },
    'about': {
        'patterns': [r'квест', r'quest', r'что это', r'суть', r'как играть', r'правила игры', r'прохождение', r'интересн'],
        'response': "🗺️ **Что такое «Тайны вашего города»?**\n\nЭто пешеходный квест по городам мира. Вы гуляете по улицам, разгадываете загадки и узнаёте историю города.\n\n**Правила простые:**\n1. Выберите город\n2. Следуйте маршруту (карта подскажет)\n3. Разгадайте загадку на каждой точке\n4. Набирайте баллы и поднимайтесь в рейтинге!\n\n🌟 Идеально для прогулок с друзьями и семьёй. Сжигайте калории и узнавайте новое!"
    },
    'family': {
        'patterns': [r'дет', r'ребенк', r'семь', r'друзь', r'команд', r'групп', r'вместе', r'коллектив'],
        'response': "👨‍👩‍👧‍👦 **Семейный и дружеский режим:**\n\nИграйте в команде!\n• Общие баллы — каждый вносит вклад\n• Подходят для детей от 8 лет (есть упрощённые загадки)\n• Идеально для компаний друзей — соревнуйтесь, кто быстрее пройдёт маршрут!\n• Можно проходить по очереди: один читает загадку, другой ищет ответ.\n\n😄 Не забудьте сделать фото на финише и поделиться в соцсетях!"
    },
    'calories': {
        'patterns': [r'калори', r'ккал', r'сжигать', r'фитнес', r'здоровь', r'польз', r'активн', r'движени'],
        'response': "🔥 **Сжигайте калории с пользой!**\n\n• **Тобольск:** ~360 ккал (≈ 1.5 бургера)\n• **Роттердам:** ~310 ккал (≈ 1.3 бургера)\n• **Венеция:** ~370 ккал (≈ 1.6 бургера)\n\n🚶 10 000 шагов — легко! Квест превращает прогулку в приключение. Сжигайте калории, узнавайте историю и получайте удовольствие!"
    },
    'technical': {
        'patterns': [r'ошибк', r'bug', r'завис', r'не работает', r'не открывается', r'проблем', r'глюк', r'сбой'],
        'response': "🛠️ **Технические проблемы:**\n\nЕсли приложение работает некорректно:\n1. Перезапустите приложение\n2. Проверьте интернет-соединение\n3. Обновите страницу (для PWA)\n4. Если проблема сохраняется — напишите нам в поддержку.\n\n📩 **Контакты:** @Quest_supportbot или quest@tobolsk-quest.com\n\nМы оперативно решаем все проблемы!"
    }
}

# Разговорные фразы (маленькие хитрости для живого общения)
CHITCHAT = {
    'patterns': [
        r'(спасиб|thank|thanks|благодар|оцен|крут|класс|супер|отлично|лучше|здоров)',
        r'(понятн|понял|ясн|окей|ok|ладно|договорились)',
        r'(смешн|забавн|прикол|улыб|хаха|хех|шутк|смех)',
        r'(интересн|увлекательн|захватывающ|обалденн|потрясающ|шикарн)'
    ],
    'responses': {
        'thanks': [
            "Пожалуйста! Рад помочь! 🗺️",
            "Всегда рад! Удачного квеста! ✨",
            "Обращайтесь ещё! 😊"
        ],
        'understand': [
            "Отлично! Если что-то ещё нужно — я здесь!",
            "Супер! Двигаемся дальше! ⭐",
            "Здорово! Продолжаем приключение! 🏰"
        ],
        'funny': [
            "😄 Рад, что вам весело! Квесты должны быть увлекательными!",
            "Юмор — лучшее топливо для путешествий! 😆",
            "Хорошее настроение — ключ к победе! 🎉"
        ],
        'excited': [
            "🔥 Вот это энтузиазм! Так держать!",
            "Ваш азарт передаётся и мне! 🚀",
            "Лучшее приключение начинается с хорошего настроения! ⭐"
        ]
    }
}

# ========== ФУНКЦИЯ ОПРЕДЕЛЕНИЯ НАМЕРЕНИЯ ==========

def detect_intent(text):
    """Определяет тему вопроса с помощью анализа ключевых слов"""
    text_lower = text.lower()
    
    # Проверяем приветствия и прощания
    if re.search(r'(привет|здравствуй|hello|hi|добрый день|доброе утро)', text_lower):
        return 'greeting'
    if re.search(r'(пока|до свидания|bye|goodbye|прощай)', text_lower):
        return 'farewell'
    
    # Проверяем разговорные фразы
    if re.search(r'(спасиб|thank|thanks|благодар)', text_lower):
        return 'thanks'
    if re.search(r'(понятн|понял|ясн|окей|ok)', text_lower):
        return 'understand'
    if re.search(r'(смешн|забавн|прикол|улыб|хаха|хех)', text_lower):
        return 'funny'
    if re.search(r'(интересн|увлекательн|захватывающ|обалденн|потрясающ)', text_lower):
        return 'excited'
    
    # Проверяем основные темы
    for topic, data in TOPICS.items():
        if any(re.search(pattern, text_lower) for pattern in data['patterns']):
            return topic
    
    return None

# ========== ГЕНЕРАТОР ОТВЕТОВ ==========

def get_ai_response(text, user_id=None):
    """Умный ответ с учётом контекста и намерения"""
    intent = detect_intent(text)
    
    # Если есть контекст для пользователя — используем его
    if user_id and user_id in USER_CONTEXT:
        context = USER_CONTEXT[user_id]
        # Если пользователь уже спрашивал о чём-то и продолжает тему
        if context.get('last_topic') and len(text) < 30:
            # Если похоже на продолжение предыдущей темы
            pass
    
    # Приветствие
    if intent == 'greeting':
        return random.choice(GREETINGS['responses']['greeting'])
    
    # Прощание
    if intent == 'farewell':
        return random.choice(GREETINGS['responses']['farewell'])
    
    # Разговорные фразы
    if intent == 'thanks':
        return random.choice(CHITCHAT['responses']['thanks'])
    if intent == 'understand':
        return random.choice(CHITCHAT['responses']['understand'])
    if intent == 'funny':
        return random.choice(CHITCHAT['responses']['funny'])
    if intent == 'excited':
        return random.choice(CHITCHAT['responses']['excited'])
    
    # Основные темы
    if intent and intent in TOPICS:
        # Сохраняем контекст
        if user_id:
            USER_CONTEXT[user_id] = {'last_topic': intent, 'timestamp': datetime.now()}
        return TOPICS[intent]['response']
    
    # Если ничего не подошло — общий ответ с предложением тем
    return "🤔 Хм... Я не совсем понял ваш вопрос. Вот что я умею:\n\n• **Баллы** — как начисляются и сколько можно получить\n• **Маршруты** — длина, время, калории\n• **Города** — какие доступны для квеста\n• **Подсказки** — как искать точки\n• **Загадки** — советы по разгадыванию\n• **Связь** — как написать разработчикам\n\nПопробуйте спросить о чём-то из этого списка! 😊"

# ========== ОБРАБОТЧИКИ ==========

@bot.message_handler(commands=['start'])
def handle_start(message):
    response = "👋 Привет! Я AI-помощник квеста «Тайны вашего города».\n\nЯ умею отвечать на вопросы о:\n• **баллах и правилах**\n• **маршрутах и городах**\n• **подсказках и загадках**\n• **связи с поддержкой**\n\nСпрашивайте — я помогу! ✨"
    bot.reply_to(message, response)
    logger.info(f"Команда /start от {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        # Медиа — пересылаем администратору
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
        
        if not user_text:
            return
        
        # Определяем, похоже ли сообщение на вопрос по квесту
        quest_keywords = ['балл', 'очк', 'правил', 'маршрут', 'город', 'загадк', 'подсказк', 
                         'как', 'где', 'что', 'кто', 'когда', 'почему', 'сколько', 'бонус', 
                         'квест', 'точк', 'пройти', 'пройден', 'финиш', 'помощь', 'спасиб', 
                         'контакт', 'админ', 'email', 'телеграм', 'привет', 'здравствуй', 
                         'пока', 'до свидания', 'интересн', 'увлекательн', 'класс', 'супер', 
                         'спасибо', 'отлично', 'смешн', 'забавн']
        
        is_quest_question = any(keyword in user_text.lower() for keyword in quest_keywords)
        
        if is_quest_question:
            # Отвечаем как умный AI-помощник
            response = get_ai_response(user_text, user_id)
            bot.send_message(user_id, response)
            logger.info(f"AI-ответ для {user_id}: {response[:50]}...")
        else:
            # Пересылаем администратору
            forward_text = f"📩 Новое сообщение от {user_name} (ID: {user_id}):\n\n{user_text}"
            bot.send_message(ADMIN_ID, forward_text)
            bot.reply_to(message, "✅ Ваше сообщение отправлено администратору.")
            logger.info(f"Сообщение от {user_id} переслано администратору")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике: {e}")
        try:
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте ещё раз.")
        except:
            pass

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
    logger.info("🧠 Умный AI-помощник активен!")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка polling: {e}")
            time.sleep(5)
