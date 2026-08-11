import telebot
import os
import time
import logging
import re
import random
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
DONATE_CHANNEL = os.environ.get('DONATE_CHANNEL', '')

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# ========== ХРАНИЛИЩЕ ДОНАТОВ ==========
DONATIONS_FILE = 'donations.json'

def load_donations():
    try:
        with open(DONATIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'total_stars': 0, 'donors': [], 'transactions': []}

def save_donations(data):
    try:
        with open(DONATIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

# ========== КОНТЕКСТ ПОЛЬЗОВАТЕЛЕЙ ==========
USER_CONTEXT = {}

# ========== ПРИВЕТСТВИЯ И ПРОЩАНИЯ ==========
GREETINGS = [
    "👋 Привет! Я AI-помощник квеста «Тайны вашего города». Готов к приключениям!",
    "Здравствуйте! Я здесь, чтобы помочь вам открыть тайны города. Спрашивайте!",
    "Приветствую, искатель приключений! Чем могу помочь?",
    "О, новый гость! Добро пожаловать. Я AI-проводник по квесту.",
    "Привет! Я как GPS, только с чувством юмора. Чем могу помочь?"
]

FAREWELLS = [
    "До встречи! Пусть ваш квест будет полон открытий! 🗺️",
    "Пока-пока! Не забудьте взять с собой хорошее настроение! 😄",
    "Счастливого пути! Если что — я всегда на связи.",
    "Удачи! И помните: в квесте главное — не победа, а приключения! ⭐"
]

THANKS = [
    "Пожалуйста! Я для этого и создан 😊",
    "Всегда рад помочь! 🗺️",
    "Обращайтесь ещё! У меня есть ещё парочка интересных фактов.",
    "Пожалуйста! Если нужна будет помощь — я тут как тут."
]

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "👋 Привет! Я AI-помощник квеста «Тайны вашего города».\n\nЯ отвечаю на вопросы о:\n• баллах и правилах\n• маршрутах и городах\n• подсказках и загадках\n• донатах\n\nА ещё я умею шутить! Попробуйте спросить что-нибудь сложное! 😄")
    logger.info(f"✅ /start от {message.chat.id}")

# ========== КОМАНДЫ ДОНАТОВ ==========

@bot.message_handler(commands=['donate'])
def handle_donate_command(message):
    text = """☕ **Поддержать проект «Тайны вашего города»**

Спасибо, что хотите нас поддержать! Ваш донат поможет:

• Создавать новые квесты в других городах
• Улучшать приложение и AI-помощника
• Добавлять новые функции и маршруты

💰 **Суммы доната (в рублях):**

50 ₽ — /donate_50
100 ₽ — /donate_100
250 ₽ — /donate_250
500 ₽ — /donate_500
/donate_custom — указать свою сумму

💳 **Способы оплаты:**
• Банковские карты (Visa, MasterCard, МИР)
• СБП
• Telegram Stars (для международных пользователей)

💡 **Как это работает:**
1. Выберите сумму
2. Оплата через защищённый сервис ЮKassa
3. Мы получим уведомление и поблагодарим вас!

🔮 **Бонус для донатеров:**
• Имя в списке благодарностей (при желании)
• Доступ к закрытым новостям о разработке
• Ваше предложение по новому городу — в приоритете!

💬 Если хотите анонимно — просто напишите об этом в комментарии к донату.

📄 **Юридические документы:**
• Публичная оферта: https://tovdinin.github.io/offer.html
• Политика конфиденциальности: https://tovdinin.github.io/privacy.html

📩 **Контакты:**
• Telegram: @Questsupportpaybot
• Email: quest.supportteam@gmail.com

Спасибо, что делаете квест лучше! 🙌
"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['donate_50', 'donate_100', 'donate_250', 'donate_500'])
def handle_donate_preset(message):
    amounts = {
        '/donate_50': 50,
        '/donate_100': 100,
        '/donate_250': 250,
        '/donate_500': 500
    }
    amount = amounts.get(message.text, 50)
    create_donate_invoice(message.chat.id, amount)

@bot.message_handler(commands=['donate_custom'])
def handle_donate_custom(message):
    bot.reply_to(message, "🌟 Напишите сумму в Telegram Stars (число):")
    bot.register_next_step_handler(message, process_custom_donate)

def process_custom_donate(message):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            bot.reply_to(message, "❌ Минимальная сумма — 1 ⭐. Попробуйте ещё раз.")
            return
        if amount > 10000:
            bot.reply_to(message, "😅 Вау! 10 000 ⭐ — это очень щедро! Но давайте не будем перегружать систему. Максимум 1000 ⭐.")
            return
        create_donate_invoice(message.chat.id, amount)
    except ValueError:
        bot.reply_to(message, "❌ Введите число, например: 50")

@bot.message_handler(commands=['donate_stats'])
def handle_donate_stats(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ Эта команда только для администратора.")
        return
    
    donations = load_donations()
    total = donations['total_stars']
    count = len(donations['donors'])
    
    text = f"💰 **Статистика донатов:**\n\n"
    text += f"⭐ Всего собрано: {total} звёзд\n"
    text += f"👤 Количество донатеров: {count}\n\n"
    
    if donations['donors']:
        text += "**Последние донаты:**\n"
        for donor in donations['donors'][-5:]:
            text += f"• {donor['name']}: +{donor['amount']} ⭐ ({donor['date'][:10]})\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== ДОНАТЫ (ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ) ==========

def create_donate_invoice(user_id, amount):
    try:
        amount = int(amount)
        # Передаём сумму в рублях (без умножения на 100)
        link = bot.create_invoice_link(
            title="☕ Поддержка квеста «Тайны вашего города»",
            description=f"Спасибо за вашу поддержку! 🌟\n\nСумма: {amount} ₽",
            payload=f"donate_{user_id}_{int(time.time())}",
            provider_token="390540012:LIVE:100763",
            currency="RUB",
            prices=[telebot.types.LabeledPrice(label=f"{amount} ₽", amount=amount)],
            need_email=True,
            send_email_to_provider=True,
        )
        bot.send_message(user_id, f"🔗 Ссылка на оплату:\n{link}\n\nПосле оплаты нажмите /confirm, чтобы подтвердить платёж.")
        logger.info(f"💰 Ссылка на оплату {amount} ₽ создана для {user_id}")
        return link
    except Exception as e:
        logger.error(f"❌ Ошибка создания ссылки на оплату: {e}")
        return None

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    try:
        bot.answer_pre_checkout_query(query.id, ok=True)
        logger.info(f"✅ Pre-checkout успешен для {query.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка pre-checkout: {e}")
        bot.answer_pre_checkout_query(query.id, ok=False, error_message="Произошла ошибка. Попробуйте ещё раз.")

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    try:
        user_id = message.from_user.id
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        amount = message.successful_payment.total_amount
        
        donations = load_donations()
        donations['total_stars'] += amount
        donations['donors'].append({
            'user_id': user_id,
            'name': user_name,
            'amount': amount,
            'date': datetime.now().isoformat()
        })
        donations['transactions'].append({
            'user_id': user_id,
            'amount': amount,
            'date': datetime.now().isoformat()
        })
        save_donations(donations)
        
        thank_messages = [
            f"🌟 Огромное спасибо за поддержку {amount} ⭐!\n\nВаш донат поможет сделать квест ещё лучше! 🗺️",
            f"🎉 Спасибо за {amount} ⭐! Вы — настоящий герой! 🚀",
            f"💫 {amount} ⭐ получены! Вы официально в клубе «Друзей квеста»! 😄",
            f"☕ Спасибо за угощение на {amount} ⭐! Мы выпьем кофе за вас! 🗺️"
        ]
        bot.send_message(user_id, random.choice(thank_messages))
        logger.info(f"💰 Донат {amount} ⭐ от {user_id} ({user_name})")
        
        admin_msg = f"💰 НОВЫЙ ДОНАТ!\n\nОт: {user_name} (ID: {user_id})\nСумма: {amount} ⭐\nВсего звёзд: {donations['total_stars']}"
        bot.send_message(ADMIN_ID, admin_msg)
        
        if DONATE_CHANNEL:
            try:
                bot.send_message(DONATE_CHANNEL, f"🌟 {user_name} поддержал проект на {amount} ⭐! Спасибо!")
            except:
                pass
    except Exception as e:
        logger.error(f"❌ Ошибка обработки доната: {e}")

# ========== AI-ЛОГИКА ==========

def get_ai_response(text, user_id=None):
    q = text.lower().strip()
    
    context = USER_CONTEXT.get(user_id, {})
    topic_count = context.get('topic_count', 0)
    
    # Приветствия
    if re.search(r'^(привет|здравствуй|здравствуйте|hello|hi|хай|салам|добрый день|доброе утро|добрый вечер|ку)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'greeting', 'topic_count': 0}
        return random.choice(GREETINGS)
    
    # Прощания
    if re.search(r'^(пока|до свидания|bye|goodbye|прощай|всего хорошего|удачи|счастливо)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'farewell', 'topic_count': 0}
        return random.choice(FAREWELLS)
    
    # Благодарности
    if re.search(r'(спасиб|thank|thanks|благодар|класс|супер|отлично|здорово|круто|офигенно)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'thanks', 'topic_count': topic_count + 1}
        return random.choice(THANKS)
    
    # Донаты
    if re.search(r'(донат|поддерж|звезд|star|перевести|кинуть|бросить|закинуть)', q):
        return """☕ **Поддержать проект можно через Telegram Stars!**

Просто отправьте команду /donate и выберите сумму.

Ваш донат поможет нам создавать новые квесты и улучшать приложение. Спасибо! 🙌

💡 Если не знаете, что такое Telegram Stars — это внутренняя валюта Telegram. Вы покупаете их в магазине приложений и можете отправлять разработчикам."""
    
    # Баллы
    if re.search(r'(балл|очк|счёт|score|набрать|сколько|максимум|рейтинг|кубок)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'score', 'topic_count': topic_count + 1}
        return random.choice([
            "⭐ **Правила начисления баллов:**\n• 1-я попытка — 3 балла (вы гений!)\n• 2-я попытка — 2 балла (почти гений)\n• 3-я попытка — 1 балл (ну, бывает)\n• После 3 ошибок — подсказка, но 0 баллов (но вы хотя бы узнали что-то новое!)\n\n🎯 Максимум: 36 баллов в Тобольске. Докажите, что вы достойны Кубка Сибири!",
            "🏆 Как набрать максимум? Читайте загадки внимательно, не торопитесь и не нажимайте «Проверить» с закрытыми глазами. Шутка. Ну почти. 😄\n\n• 1 попытка = 3 балла\n• 2 попытка = 2 балла\n• 3 попытка = 1 балл\n\nУдачи, эрудит!"
        ])
    
    # Маршруты
    if re.search(r'(маршрут|протяжённ|длина|расстояни|километр|км|время|часов|идти|сколько идти)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'route', 'topic_count': topic_count + 1}
        return "📍 **Маршруты (и сколько калорий вы сожжёте):**\n\n• **Тобольск** — 6.3 км, ~1.9 часа (🔥 ~360 ккал — как бургер!)\n• **Роттердам** — 5.5 км, ~2.0 часа (🔥 ~310 ккал — почти пицца!)\n• **Венеция** — 6.5 км, ~3.0 часа (🔥 ~370 ккал — как два круассана!)\n\n😄 Если вы прошли все три — вы официально сожгли недельный запас шоколада!"
    
    # Города
    if re.search(r'(город|city|какие города|доступн|выбрать|список|новые города|добавят)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'cities', 'topic_count': topic_count + 1}
        return "🏙️ **Доступные города для квеста:**\n\n• **Тобольск** — 12 точек (древняя столица Сибири, между прочим!)\n• **Роттердам** — 10 точек (город современных кубов и мостов)\n• **Венеция** — 11 точек (город, где вместо дорог — каналы. Надевайте удобную обувь!)\n\n🌍 Новые города появляются… когда мы успеваем их придумать! 😄 Если хотите добавить свой город — напишите нам."
    
    # Подсказки
    if re.search(r'(подсказк|hint|помощь|как найти|где искать|не могу найти|застрял|трудн|сложн|не понимаю)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'hint', 'topic_count': topic_count + 1}
        return random.choice([
            "💡 **Как искать точки (и не сойти с ума):**\n\n• Каждая точка — реальный объект: памятник, табличка, здание с историей.\n• Осмотритесь вокруг! Иногда ответ прямо перед вами.\n• Используйте карту в приложении — она вас не подведёт.\n• Если застряли — вернитесь и перечитайте загадку. Иногда ответ в ней зашифрован!",
            "🔍 Не можете найти точку? Попробуйте подойти к вопросу с юмором. Например, спросите себя: «А где бы я спрятал загадку, если бы был архитектором XIX века?» 😄\n\nСовет: ищите нестандартные детали — старые фонари, барельефы, таблички с датами."
        ])
    
    # Загадки
    if re.search(r'(загадк|riddle|ответ|что значит|как решить|не могу разгадать)', q):
        USER_CONTEXT[user_id] = {'last_topic': 'riddle', 'topic_count': topic_count + 1}
        return "🔍 **Как разгадывать загадки:**\n\n• Внимательно читайте текст — ключ к ответу всегда в нём.\n• Думайте нестандартно! Загадки часто играют с ассоциациями.\n• Ответ — обычно одно слово или короткая фраза.\n\n😄 Если совсем трудно — попросите подсказку. Но помните: подсказка стоит 0 баллов, зато вы сохраните нервные клетки!"
    
    # Контакты
    if re.search(r'(контакт|админ|разработчик|телеграм|email|поддержк|help|support|жалоб|отзыв|проблем)', q):
        return "📩 **Связаться с нами:**\n\n• **Telegram:** @Questsupportpaybot\n• **Email:** quest.supportteam@gmail.com\n• **В приложении:** кнопка «Обратная связь»\n\n😄 Если вы пишете жалобу — сначала расскажите анекдот, чтобы мы не грустили!"
    
    # Юмор
    if re.search(r'(шутк|анекдот|смешн|забавн|прикол|рассмеш)', q):
        return random.choice([
            "😂 Хотите анекдот?\n\n— Почему квест в Тобольске такой длинный?\n— Потому что сибиряки любят гулять!\n\n😄 Ну как?",
            "🤣 Анекдот дня:\n\nВстречаются два туриста в Венеции:\n— Ты уже нашёл нужный мост?\n— Нет, но я уже 10 раз пересёк Гранд-канал!\n\nА вы нашли свой мост? 😄"
        ])
    
    # Бессвязные
    if len(q) < 5 or re.search(r'(абракадабра|ыва|фыв|олд|шшш|ххх)', q):
        return random.choice([
            "😄 Я бы ответил, но это звучит как загадка из другого квеста. Попробуйте перефразировать!",
            "😅 Ой, я потерял нить разговора. Вы точно не пытаетесь взломать меня через тарабарщину?",
            "🤖 БИП-БУП! Не понял. Может быть, вы случайно нажали на клавиатуру? Попробуйте ещё раз, только по-человечески. 😄"
        ])
    
    # Если не распознан
    return random.choice([
        "🤔 Хм... Я не совсем уловил суть. Вот что я умею:\n\n• **Баллы** — как набрать максимум\n• **Маршруты** — длина и калории\n• **Города** — какие доступны\n• **Подсказки** — как не заблудиться\n• **Загадки** — как разгадывать\n• **Донаты** — поддержать проект\n• **Юмор** — анекдоты и шутки\n\nПопробуйте спросить о чём-то из этого! 😊",
        "😄 Я бы хотел помочь, но ваш вопрос звучит как загадка Сфинкса. Попробуйте спросить про баллы, маршруты или донаты — я в этом силён!"
    ])

# ========== ОСНОВНОЙ ОБРАБОТЧИК ==========

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.chat.id
        user_text = message.text or ""
        user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        if user_text.startswith('/'):
            return
        
        if message.content_type in ['photo', 'voice', 'sticker', 'document', 'video', 'audio']:
            bot.send_message(ADMIN_ID, f"📩 Медиа от {user_name} (ID: {user_id})")
            bot.reply_to(message, "✅ Медиа отправлено администратору.")
            logger.info(f"📷 Медиа от {user_id} переслано администратору")
            return
        
        if user_text:
            ai_response = get_ai_response(user_text, user_id)
            
            if ai_response:
                bot.send_message(user_id, ai_response)
                logger.info(f"🤖 AI-ответ для {user_id}: {ai_response[:50]}...")
            else:
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
    logger.info("🧠 Умный AI-помощник с донатами активен!")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            time.sleep(5)
