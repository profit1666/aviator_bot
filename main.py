from flask import Flask, request
from threading import Thread
import telebot
from telebot import types
import sqlite3
import random
import time
from datetime import datetime

# 🌐 Flask для Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/postback', methods=['GET', 'POST'])
def handle_postback():
    data = request.args if request.method == 'GET' else request.form

    sub_id = data.get('subid101')             # Telegram ID лида
    event = data.get('event')              # Тип события
    amount = data.get('sum', '—')          # Сумма депозита
    status = data.get('status', '—')       # Статус, например "ok"
    timestamp = datetime.utcnow().isoformat()

    if not sub_id or not event:
        return "❌ Не хватает данных", 400

    message = f"""📨 Событие от 1win:
👤 Лид: <code>{sub_id}</code>
🎬 Событие: <b>{event.upper()}</b>
💰 Сумма: {amount}
📋 Статус: {status}
🕒 Время: {timestamp}"""

    try:
        bot.send_message(ADMIN_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")

    return "OK", 200

    data = request.args if request.method == 'GET' else request.form
    sub_id = data.get('sub1')        # Telegram ID лида
    event = data.get('type')         # Событие: registration, deposit
    amount = data.get('amount', '—') # Сумма, если есть
    timestamp = datetime.utcnow().isoformat()

    if not sub_id or not event:
        return "❌ Не хватает данных", 400

    message = f"""📨 Событие от 1win:\n
👤 Лид: <code>{sub_id}</code>\n
🎬 Событие: <b>{event.upper()}</b>\n
💰 Сумма: {amount}\n
🕒 Время: {timestamp}"""

    try:
        bot.send_message(ADMIN_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")

    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()

# 🔑 Настройки
TOKEN = "7856074080:AAGPBNStc9JixmgxaILGsPBxm2n3M88hhwU"
ADMIN_ID = 1463957271
bot = telebot.TeleBot(TOKEN)

user_language = {}
user_language[ADMIN_ID] = "ru"

# 📦 База данных SQLite
conn = sqlite3.connect('leads.db', check_same_thread=False)
with conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS access_requests (
        user_id INTEGER PRIMARY KEY,
        status TEXT,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        lang_code TEXT,
        permanent INTEGER DEFAULT 0
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS signal_log (
        user_id INTEGER,
        timestamp TEXT
    )''')

# 🎯 Генератор сигнала Aviator
def generate_signal():
    return round(random.uniform(1.2, 15.0), 2)
# 🚀 Обработка /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or "—"
    first_name = message.from_user.first_name or "—"
    last_name = message.from_user.last_name or "—"
    lang_code = message.from_user.language_code or "—"

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            if row[0] == "approved":
                show_language_menu(user_id)
                return
            elif row[0] == "pending":
                bot.send_message(user_id, "🔒 Запрос уже отправлен. Ожидайте одобрения.")
                return

        cursor.execute('''INSERT INTO access_requests (user_id, status, username, first_name, last_name, lang_code)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (user_id, 'pending', username, first_name, last_name, lang_code))

    info = f"""🔔 Новый лидер:
👤 ID: <code>{user_id}</code>
📛 Имя: {first_name} {last_name}
🏷 username: @{username}
🌍 Язык Telegram: {lang_code}"""

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"deny_{user_id}")
    )

    bot.send_message(ADMIN_ID, info, parse_mode="HTML", reply_markup=markup)
    bot.send_message(user_id, "🔒 Ваша заявка отправлена. Ожидайте подтверждения.")

# ✅ Обработка решения админа
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("deny_"))
def handle_access_decision(call):
    action, user_id = call.data.split("_")
    user_id = int(user_id)

    if call.message.chat.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 Только админ.")
        return

    with conn:
        cursor = conn.cursor()
        status = "approved" if action == "approve" else "denied"
        cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        permanent_flag = 1 if existing and existing[0] == "approved" else 0
        cursor.execute("UPDATE access_requests SET status = ?, permanent = ? WHERE user_id = ?",
                       (status, permanent_flag, user_id))

    if status == "approved":
        bot.send_message(user_id, "✅ Доступ подтверждён! Выберите язык 👇")
        show_language_menu(user_id)
    else:
        bot.send_message(user_id, "❌ Доступ отклонён.")

    bot.send_message(call.message.chat.id, f"📬 Статус обновлён: {status}")
# 🌍 Меню выбора языка
def show_language_menu(chat_id):
    if chat_id == ADMIN_ID:
        user_language[chat_id] = "ru"
        show_main_menu(chat_id, "ru")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton("🇬🇧 English"),
        types.KeyboardButton("🇮🇳 हिंदी")
    )
    bot.send_message(chat_id, "Please choose a language:", reply_markup=markup)

# 🌍 Обработка выбранного языка
@bot.message_handler(func=lambda m: m.text in ["🇬🇧 English", "🇮🇳 हिंदी"])
def set_language(message):
    user_id = message.chat.id
    lang = "en" if message.text == "🇬🇧 English" else "hi"
    user_language[user_id] = lang

    timestamp = datetime.utcnow().isoformat()

    with conn:
        conn.execute("INSERT OR REPLACE INTO signal_log (user_id, timestamp) VALUES (?, ?)", (user_id, timestamp))
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM signal_log WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()

    recent = [r for r in rows if (datetime.utcnow() - datetime.fromisoformat(r[0])).total_seconds() < 3600]

    if len(recent) >= 3:
        msg = {
            "en": "⛔ Limit: max 3 signals/hour. Try later.",
            "hi": "⛔ सीमा: प्रति घंटा अधिकतम 3 सिग्नल। बाद में प्रयास करें।"
        }
        bot.send_message(user_id, msg[lang])
        return

    result = generate_signal()
    conn.execute("INSERT INTO signal_log (user_id, timestamp) VALUES (?, ?)", (user_id, timestamp))

    msg = {
        "en": f"""🎯 <b>Signal:</b> <code>{result}x</code>\n🧠 Confidence: 99.9%""",
        "hi": f"""🎯 <b>सिग्नल:</b> <code>{result}x</code>\n🧠 विश्वास स्तर: 99.9%"""
    }
    bot.send_message(user_id, msg[lang], parse_mode="HTML")
    show_main_menu(user_id, lang)

# 📱 Главное меню
def show_main_menu(chat_id, lang):
    buttons = {
        "ru": ("🎯 Получить сигнал", "🔄 Сменить язык", "Выберите действие:"),
        "en": ("🎯 Get Signal", "🔄 Change Language", "Choose an option:"),
        "hi": ("🎯 सिग्नल प्राप्त करें", "🔄 भाषा बदलें", "कोई विकल्प चुनें:")
    }

    signal_btn, lang_btn, prompt = buttons.get(lang, buttons["en"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(signal_btn), types.KeyboardButton(lang_btn))
    bot.send_message(chat_id, prompt, reply_markup=markup)
# 🔘 Обработка кнопок меню
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    user_id = message.chat.id
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM access_requests WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] != "approved":
        bot.send_message(user_id, "🚫 У вас нет доступа.")
        return

    lang = user_language.get(user_id, "ru")
    text = message.text

    signals = {
        "ru": "🎯 Получить сигнал",
        "en": "🎯 Get Signal",
        "hi": "🎯 सिग्नल प्राप्त करें"
    }
    lang_change = {
        "ru": "🔄 Сменить язык",
        "en": "🔄 Change Language",
        "hi": "🔄 भाषा बदलें"
    }

    if text == signals.get(lang):
        cursor.execute("SELECT timestamp FROM signal_log WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        recent = [r for r in rows if (datetime.utcnow() - datetime.fromisoformat(r[0])).total_seconds() < 3600]
        if len(recent) >= 3:
            msg = {
                "ru": "⛔ Лимит: максимум 3 сигнала в час.",
                "en": "⛔ Limit: max 3 signals/hour.",
                "hi": "⛔ सीमा: प्रति घंटा अधिकतम 3 सिग्नल।"
            }
            bot.send_message(user_id, msg[lang])
            return

        timestamp = datetime.utcnow().isoformat()
        conn.execute("INSERT INTO signal_log (user_id, timestamp) VALUES (?, ?)", (user_id, timestamp))
        result = generate_signal()
        msg = {
            "ru": f"""🎯 <b>Сигнал:</b> <code>{result}x</code>\n🧠 Уверенность: 99.9%""",
            "en": f"""🎯 <b>Signal:</b> <code>{result}x</code>\n🧠 Confidence: 99.9%""",
            "hi": f"""🎯 <b>सिग्नल:</b> <code>{result}x</code>\n🧠 विश्वास स्तर: 99.9%"""
        }
        bot.send_message(user_id, msg[lang], parse_mode="HTML")
        show_main_menu(user_id, lang)

    elif text == lang_change.get(lang):
        show_language_menu(user_id)

    elif text == "/admin" and user_id == ADMIN_ID:
        show_admin_panel(user_id)

# 🎛 Админ-панель
def show_admin_panel(chat_id):
    if chat_id != ADMIN_ID:
        bot.send_message(chat_id, "🚫 У вас нет прав администратора.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📍 Активные", callback_data="show_active"),
        types.InlineKeyboardButton("⏳ Ожидающие", callback_data="show_pending"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
    )
    bot.send_message(chat_id, "🎛 Панель управления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_"))
def handle_admin_view(call):
    if call.message.chat.id != ADMIN_ID:
        return

    cursor = conn.cursor()

    if call.data == "show_active":
        cursor.execute("SELECT user_id, username FROM access_requests WHERE status = 'approved'")
        rows = cursor.fetchall()
        if not rows:
            bot.send_message(call.message.chat.id, "🙁 Нет активных пользователей.")
            return
        for uid, uname in rows:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Забрать доступ", callback_data=f"revoke_{uid}"))
            bot.send_message(call.message.chat.id, f"🔹 ID: {uid} | @{uname}", reply_markup=markup)

    elif call.data == "show_pending":
        cursor.execute("SELECT user_id, username FROM access_requests WHERE status = 'pending'")
        rows = cursor.fetchall()
        if not rows:
            bot.send_message(call.message.chat.id, "🙁 Нет ожидающих заявок.")
            return
        for uid, uname in rows:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Вернуть доступ", callback_data=f"return_{uid}"))
            bot.send_message(call.message.chat.id, f"🔸 ID: {uid} | @{uname}", reply_markup=markup)

    elif call.data == "show_stats":
        cursor.execute("SELECT COUNT(*) FROM access_requests")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM access_requests WHERE status = 'approved'")
        approved = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM access_requests WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM access_requests WHERE status = 'denied'")
        denied = cursor.fetchone()[0]
        cursor.execute("SELECT lang_code FROM access_requests")
        rows = cursor.fetchall()
        lang_stats = {}
        for r in rows:
            lang = r[0]
            if lang:
                lang_stats[lang] = lang_stats.get(lang, 0) + 1
        text = f"""📊 Статистика:
👥 Всего лидов: {total}
✅ Одобрено: {approved}
⏳ В ожидании: {pending}
❌ Отклонено: {denied}
🌍 Языки Telegram:"""
        for lang, count in lang_stats.items():
            text += f"\n🔤 {lang}: {count}"
        bot.send_message(call.message.chat.id, text)

# ✅ / ❌ Управление доступом
@bot.callback_query_handler(func=lambda call: call.data.startswith("return_") or call.data.startswith("revoke_"))
def handle_access_update(call):
    if call.message.chat.id != ADMIN_ID:
        return
    action, uid = call.data.split("_")
    uid = int(uid)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM access_requests WHERE user_id = ?", (uid,))
    user = cursor.fetchone()
    uname = user[0] if user else "—"

    if action == "return":
        cursor.execute("UPDATE access_requests SET status = 'approved' WHERE user_id = ?", (uid,))
        conn.commit()
        bot.send_message(uid, "✅ Ваш доступ был восстановлен!")
        bot.send_message(call.message.chat.id, f"✅ Доступ возвращён для @{uname}")
        show_language_menu(uid)
    elif action == "revoke":
        cursor.execute("UPDATE access_requests SET status = 'denied' WHERE user_id = ?", (uid,))
        conn.commit()
        bot.send_message(uid, "❌ Ваш доступ был отозван.")
        bot.send_message(call.message.chat.id, f"❌ Доступ отозван у @{uname}")

# 🔁 Защита polling + уведомление админу
def start_bot():
    while True:
        try:
            print("🚀 Запуск Telegram-бота...")
            bot.polling(none_stop=True)
        except Exception as e:
            error_message = f"❌ Бот упал: {str(e)}"
            print(error_message)
            try:
                bot.send_message(ADMIN_ID, error_message)
            except:
                pass
        time.sleep(10)

# 🟢 Старт
start_bot()
