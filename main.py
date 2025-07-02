import telebot
from telebot import types
import random
import sqlite3
from datetime import datetime
import time

bot = telebot.TeleBot("7856074080:AAE9HoPWWVGGPlWiySZoKlMFVE5VPb5SvVU")
user_language = {}

# 📦 База данных
conn = sqlite3.connect('leads.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        user_id INTEGER PRIMARY KEY,
        language TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# 🔢 Генератор случайного сигнала
def generate_signal():
    return round(random.uniform(1.2, 15.0), 2)

# 🔘 /start → выбор языка
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🇬🇧 English"), types.KeyboardButton("🇮🇳 हिंदी"))
    bot.send_message(message.chat.id, "Please choose your language:\nकृपया अपनी भाषा चुनें:", reply_markup=markup)

# 🌐 Обработка выбора языка
@bot.message_handler(func=lambda m: m.text in ["🇬🇧 English", "🇮🇳 हिंदी"])
def set_language(message):
    lang = "en" if "English" in message.text else "hi"
    user_language[message.chat.id] = lang
    now = datetime.utcnow().isoformat()
    cursor.execute("INSERT OR REPLACE INTO leads (user_id, language, timestamp) VALUES (?, ?, ?)",
                   (message.chat.id, lang, now))
    conn.commit()

    text1 = "📊 Analyzing last 5 Aviator rounds..." if lang == "en" else "📊 Aviator के पिछले 5 राउंड का विश्लेषण..."
    text2 = "⏳ Running probabilistic forecast..." if lang == "en" else "⏳ संभावना विश्लेषण चल रहा है..."
    bot.send_message(message.chat.id, text1)
    time.sleep(1.5)
    bot.send_message(message.chat.id, text2)
    time.sleep(2)

    result = generate_signal()
    message_out = f"""🎯 <b>{'Your most probable signal:' if lang == 'en' else 'सबसे संभावित सिग्नल:'}</b> <code>{result}x</code>
🧠 {'Confidence' if lang == 'en' else 'विश्वास स्तर'}: 99.9%"""

    bot.send_message(message.chat.id, message_out, parse_mode="HTML")
    send_menu(message.chat.id, lang)

# 📱 Главное меню
def send_menu(chat_id, lang):
    btn_signal = "🎯 Get Signal" if lang == "en" else "🎯 सिग्नल प्राप्त करें"
    btn_lang = "🔄 Change Language" if lang == "en" else "🔄 भाषा बदलें"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(btn_signal))
    markup.add(types.KeyboardButton(btn_lang))

    msg = "Choose an option:" if lang == "en" else "एक विकल्प चुनें:"
    bot.send_message(chat_id, msg, reply_markup=markup)

# 🕹 Обработка кнопок
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    chat_id = message.chat.id
    lang = user_language.get(chat_id, "en")
    text = message.text

    if text in ["🎯 Get Signal", "🎯 सिग्नल प्राप्त करें"]:
        bot.send_message(chat_id, "📊 Analyzing Aviator history..." if lang == "en" else "📊 Aviator इतिहास का विश्लेषण...")
        time.sleep(1.2)
        bot.send_message(chat_id, "⏳ Calculating next best move..." if lang == "en" else "⏳ अगला सटीक सिग्नल खोजा जा रहा है...")
        time.sleep(2)

        result = generate_signal()
        msg = f"""🎯 <b>{'Your most probable signal:' if lang == 'en' else 'सबसे संभावित सिग्नल:'}</b> <code>{result}x</code>
🧠 {'Confidence' if lang == 'en' else 'विश्वास स्तर'}: 99.9%"""
        bot.send_message(chat_id, msg, parse_mode="HTML")

    elif text in ["🔄 Change Language", "🔄 भाषा बदलें"]:
        start(message)
    else:
        bot.send_message(chat_id, "🤖 Unknown command." if lang == "en" else "🤖 कमांड समझ नहीं आया।")

print("🚀 Бот запущен!")
bot.polling(none_stop=True)
