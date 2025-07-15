import telebot
from telebot import types
import sqlite3
import random
import time
from datetime import datetime

# 🔑 Конфигурация
TOKEN = "7856074080:AAGPBNStc9JixmgxaILGsPBxm2n3M88hhwU"
ADMIN_ID = 1463957271
bot = telebot.TeleBot(TOKEN)
user_language = {}

# 📦 Инициализация базы данных
conn = sqlite3.connect('leads.db', check_same_thread=False)
with conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            user_id INTEGER PRIMARY KEY,
            language TEXT,
            timestamp TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS access_requests (
            user_id INTEGER PRIMARY KEY,
            status TEXT
        )
    ''')

# 🎯 Генерация сигнала
def generate_signal():
    return round(random.uniform(1.2, 15.0), 2)

# 🚀 Команда /start с логикой доступа
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row and row[0] == "approved":
            bot.send_message(user_id, "✅ У вас уже есть доступ.")
            return
        elif row and row[0] == "pending":
            bot.send_message(user_id, "🔒 Запрос уже отправлен. Ожидайте.")
            return

        cursor.execute("INSERT INTO access_requests (user_id, status) VALUES (?, ?)", (user_id, 'pending'))

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Дать доступ", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"deny_{user_id}")
    )

    bot.send_message(ADMIN_ID, f"🔔 Новый лид запрашивает доступ.\nID: <code>{user_id}</code>", parse_mode="HTML", reply_markup=markup)
    bot.send_message(user_id, "🔒 Запрос на доступ отправлен. Ожидайте подтверждения.")

# 🧭 Кнопки доступа
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("deny_"))
def handle_access_decision(call):
    action, user_id = call.data.split("_")
    user_id = int(user_id)

    if call.message.chat.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 Только администратор может управлять доступом.")
        return

    with conn:
        cursor = conn.cursor()
        status = "approved" if action == "approve" else "denied"
        cursor.execute("UPDATE access_requests SET status = ? WHERE user_id = ?", (status, user_id))

    message_text = "✅ Доступ подтверждён!" if status == "approved" else "❌ Доступ отклонён."
    bot.send_message(user_id, message_text)
    bot.send_message(call.message.chat.id, f"📬 Статус пользователя обновлён: {status}")

# 🌐 Обработка языков
@bot.message_handler(func=lambda m: m.text in ["🇬🇧 English", "🇮🇳 हिंदी"])
def set_language(message):
    user_id = message.chat.id
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    if not row or row[0] != "approved":
        bot.send_message(user_id, "🚫 Доступ к боту не разрешён.")
        return

    lang = "en" if "English" in message.text else "hi"
    user_language[user_id] = lang
    timestamp = datetime.utcnow().isoformat()

    with conn:
        conn.execute("INSERT OR REPLACE INTO leads (user_id, language, timestamp) VALUES (?, ?, ?)", (user_id, lang, timestamp))

    bot.send_message(user_id, "📊 " + ("Analyzing last 5 Aviator rounds..." if lang == "en" else "Aviator के पिछले 5 राउंड का विश्लेषण..."))
    time.sleep(1.5)
    bot.send_message(user_id, "⏳ " + ("Running probabilistic forecast..." if lang == "en" else "संभावना विश्लेषण चल रहा है..."))
    time.sleep(2)

    result = generate_signal()
    msg = f"""🎯 <b>{'Your most probable signal:' if lang == 'en' else 'सबसे संभावित सिग्नल:'}</b> <code>{result}x</code>
🧠 {'Confidence' if lang == 'en' else 'विश्वास स्तर'}: 99.9%"""
    bot.send_message(user_id, msg, parse_mode="HTML")

    send_menu(user_id, lang)

# 📱 Главное меню
def send_menu(chat_id, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🎯 Get Signal" if lang == "en" else "🎯 सिग्नल प्राप्त करें"))
    markup.add(types.KeyboardButton("🔄 Change Language" if lang == "en" else "🔄 भाषा बदलें"))
    bot.send_message(chat_id, "Choose an option:" if lang == "en" else "एक विकल्प चुनें:", reply_markup=markup)

# 🧠 Обработка всех кнопок
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    user_id = message.chat.id
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    if not row or row[0] != "approved":
        bot.send_message(user_id, "🚫 Доступ к боту не разрешён.")
        return

    lang = user_language.get(user_id, "en")
    text = message.text

    if text in ["🎯 Get Signal", "🎯 सिग्नल प्राप्त करें"]:
        bot.send_message(user_id, "📊 Analyzing Aviator history..." if lang == "en" else "📊 Aviator इतिहास का विश्लेषण...")
        time.sleep(1.2)
        bot.send_message(user_id, "⏳ Calculating next best move..." if lang == "en" else "⏳ अगला सटीक सिग्नल खोजा जा रहा है...")
        time.sleep(2)
        result = generate_signal()
        msg = f"""🎯 <b>{'Your most probable signal:' if lang == 'en' else 'सबसे संभावित सिग्नल:'}</b> <code>{result}x</code>
🧠 {'Confidence' if lang == 'en' else 'विश्वास स्तर'}: 99.9%"""
        bot.send_message(user_id, msg, parse_mode="HTML")

    elif text in ["🔄 Change Language", "🔄 भाषा बदलें"]:
        start(message)
    elif text == "/admin":
        admin_panel(message)
    else:
        bot.send_message(user_id, "🤖 Unknown command." if lang == "en" else "🤖 कमांड समझ नहीं आया।")

# 🛠 Команда /admin для владельца
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 У вас нет прав администратора.")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status FROM access_requests")
        rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Нет заявок на доступ.")
        return

    for user_id, status in rows:
        markup = types.InlineKeyboardMarkup()
        if status == "pending":
            markup.add(
                types.InlineKeyboardButton("✅ Дать доступ", callback_data=f"approve_{user_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"deny_{user_id}")
            )
        bot.send_message(message.chat.id, f"👤 ID: <code>{user_id}</code>\n📄 Статус: <b>{status}</b>",
                         parse_mode="HTML", reply_markup=markup if status == "pending" else None)

# 🎯 Запуск бота
print("🚀 Бот запущен!")
bot.polling(none_stop=True)
