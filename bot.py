import logging
import openai
import os
from aiogram import Bot, Dispatcher, executor, types
import asyncio
from dotenv import load_dotenv

load_dotenv()

# 🔑 Конфиг из .env
API_TOKEN = os.getenv("TG_BOT_TOKEN")
CHANNEL_ID = '@One_win_Aviator_Profit'
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_IDS = [1463957271, 483673956]

openai.api_key = OPENAI_KEY
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ✨ Генерация поста
async def generate_hindi_post():
    prompt = (
        "Generate a short Telegram post in Hindi (Latin script) for Aviator betting channel. "
        "Include current game vibes, note that admin earns well daily, and invites others to join. "
        "Use 2 emojis and end with 'लिखो मुझे @Emiway_Ban'"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

# 🚀 Кнопка мгновенного поста
@dp.message_handler(commands=['panel'])
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📤 Пост сейчас", callback_data='post_now'))
    await message.answer("📲 Панель управления", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'post_now')
async def post_now(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS:
        return
    post = await generate_hindi_post()
    await bot.send_message(CHANNEL_ID, post)
    await bot.answer_callback_query(callback_query.id, text="✅ Пост опубликован")

# ⏱ Автопостинг каждые 30 мин
async def periodic_posting():
    while True:
        post = await generate_hindi_post()
        await bot.send_message(CHANNEL_ID, post)
        await asyncio.sleep(1800)

# ▶️ Старт
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_posting())
    executor.start_polling(dp, skip_updates=True)
