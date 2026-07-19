import telebot
import os

# Получаем токен бота и ваш ID из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

# Проверяем, что переменные заданы
if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("Переменные окружения BOT_TOKEN и ADMIN_ID должны быть заданы!")

# Преобразуем ADMIN_ID в целое число
ADMIN_ID = int(ADMIN_ID)

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Глобальный словарь для хранения состояния чата с пользователем
# (чтобы знать, кому пересылать ответ администратора)
user_chat_states = {}

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def handle_admin_reply(message):
    """
    Обрабатывает ответы администратора на пересланные сообщения.
    """
    try:
        # Получаем ID пользователя из reply_to_message
        original_message = message.reply_to_message
        # Проверяем, есть ли ID пользователя в тексте пересланного сообщения
        if original_message and original_message.text:
            parts = original_message.text.split('\n')
            user_id_part = next((p for p in parts if p.startswith('ID пользователя:')), None)
            if user_id_part:
                user_id = int(user_id_part.split(':')[1].strip())
                # Отправляем ответ пользователю
                bot.send_message(user_id, message.text)
                bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю.")
                return

        bot.send_message(ADMIN_ID, "❌ Не удалось найти ID пользователя в пересланном сообщении.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Ошибка при отправке ответа: {e}")

@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_message(message):
    """
    Пересылает сообщение от пользователя администратору.
    """
    # Сохраняем ID пользователя для ответа
    user_id = message.chat.id
    user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()

    # Формируем текст для администратора
    forward_text = (
        f"📩 Новое сообщение от {user_name} (ID: {user_id}):\n\n"
        f"{message.text}"
    )

    # Отправляем администратору
    bot.send_message(ADMIN_ID, forward_text)

    # Подтверждаем пользователю
    bot.reply_to(message, "✅ Ваше сообщение отправлено. Ожидайте ответа.")

if __name__ == "__main__":
    print("Бот запущен и готов к работе...")
    bot.polling(none_stop=True)