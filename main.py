import telebot
import os
import time
import logging
import re
import random
from datetime import datetime
import json
import sys
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

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

@bot.message_handler(commands=['donate_100', 'donate_250', 'donate_500', 'donate_1000'])
def handle_donate_preset(message):
    amounts = {
        '/donate_100': 100,
        '/donate_250': 250,
        '/donate_500': 500,
        '/donate_1000': 1000
    }
    amount = amounts.get(message.text, 100)
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
        
        # Сумма в КОПЕЙКАХ
        prices = [telebot.types.LabeledPrice(label=f"{amount} ₽", amount=amount * 100)]
        
        # Данные для чека (если включена онлайн-касса)
        provider_data = {
            "receipt": {
                "items": [{
                    "description": "Поддержка проекта «Тайны вашего города»",
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{amount}.00",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }]
            }
        }
        
        logger.info(f"💰 Создание инвойса для {user_id} на сумму {amount} ₽ (в копейках: {amount * 100})")
        
        invoice = bot.send_invoice(
            chat_id=user_id,
            title="☕ Поддержка квеста «Тайны вашего города»",
            description=f"Спасибо за вашу поддержку! 🌟\n\nСумма: {amount} ₽",
            invoice_payload=f"donate_{user_id}_{int(time.time())}",
            provider_token="390540012:LIVE:100763",  # Ваш токен от @BotFather
            currency="RUB",
            prices=prices,
            start_parameter="donate",
            need_name=False,
            need_phone_number=False,
            need_email=True,
            send_email_to_provider=True,
            provider_data=json.dumps(provider_data),
            is_flexible=False
        )
        logger.info(f"💰 Инвойс на {amount} ₽ создан для {user_id}")
        return invoice
    except Exception as e:
        logger.error(f"❌ Ошибка создания инвойса: {e}")
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
            f"🌟 Огромное спасибо за поддержку {amount} ₽!\n\nВаш донат поможет сделать квест ещё лучше! 🗺️",
            f"🎉 Спасибо за {amount} ₽! Вы — настоящий герой! 🚀",
            f"💫 {amount} ₽ получены! Вы официально в клубе «Друзей квеста»! 😄",
            f"☕ Спасибо за угощение на {amount} ₽! Мы выпьем кофе за вас! 🗺️"
        ]
        bot.send_message(user_id, random.choice(thank_messages))
        logger.info(f"💰 Донат {amount} ₽ от {user_id} ({user_name})")
        
        admin_msg = f"💰 НОВЫЙ ДОНАТ!\n\nОт: {user_name} (ID: {user_id})\nСумма: {amount} ₽\nВсего собрано: {donations['total_stars']} ₽"
        bot.send_message(ADMIN_ID, admin_msg)
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки доната: {e}")

# ========== ОСТАЛЬНОЙ КОД ==========
# Здесь должен быть ваш остальной код (AI-логика, обработчики сообщений и т.д.)

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
