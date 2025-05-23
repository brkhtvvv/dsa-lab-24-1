import asyncio
import os
from dotenv import load_dotenv
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="telegram_bot_db",
        user="postgres",
        password="postgres"
    )

def is_admin(chat_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM admins WHERE chat_id = %s",
                (str(chat_id),)
            )
            return cur.fetchone() is not None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = message.chat.id
    if is_admin(chat_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Перейти в админ-панель", url="http://192.168.56.1:5000/admin-panel")]
            ]
        )
        await message.answer("Добро пожаловать, администратор!", reply_markup=keyboard)
    else:
        await message.answer("У вас нет доступа к админ-функциям.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
