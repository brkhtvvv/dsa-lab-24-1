import os
import asyncio
import psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

conn = psycopg2.connect(
    host="localhost",
    database="telegram_bot_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

cur.execute(
    "CREATE TABLE IF NOT EXISTS currencies ("
    "id INTEGER PRIMARY KEY,"
    "currency_name VARCHAR,"
    "rate NUMERIC)"
)

cur.execute(
    "CREATE TABLE IF NOT EXISTS admins ("
    "id INTEGER PRIMARY KEY,"
    "chat_id VARCHAR)"
)

conn.commit()
cur.close()
conn.close()

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
            cur.execute(
                "SELECT 1 FROM admins WHERE chat_id = %s",
                (str(chat_id),)
            )
            return cur.fetchone() is not None

def currency_exists(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM currencies WHERE UPPER(currency_name) = %s",
                (name.upper(),)
            )
            return cur.fetchone() is not None

def add_currency(name, rate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM currencies")
            new_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO currencies (id, currency_name, rate) VALUES (%s, %s, %s)",
                (new_id, name.upper(), rate)
            )
            conn.commit()

def delete_currency(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM currencies WHERE UPPER(currency_name) = %s",
                (name.upper(),)
            )
            conn.commit()

def update_currency_rate(name, rate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE currencies SET rate = %s WHERE UPPER(currency_name) = %s",
                (rate, name.upper())
            )
            conn.commit()

def get_all_currencies():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT currency_name, rate FROM currencies ORDER BY currency_name"
            )
            return cur.fetchall()

def get_currency_rate(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rate FROM currencies WHERE UPPER(currency_name) = %s",
                (name.upper(),)
            )
            result = cur.fetchone()
            if result:
                return result[0]
            return None

async def set_user_commands(bot: Bot, chat_id: int):
    if is_admin(chat_id):
        commands = [
            BotCommand(command="start", description="Показать меню"),
            BotCommand(command="manage_currency", description="Управление валютами"),
            BotCommand(command="get_currencies", description="Посмотреть курсы валют"),
            BotCommand(command="convert", description="Конвертировать валюту в рубли")
        ]
    else:
        commands = [
            BotCommand(command="start", description="Показать меню"),
            BotCommand(command="get_currencies", description="Посмотреть курсы валют"),
            BotCommand(command="convert", description="Конвертировать валюту в рубли")
        ]
    await bot.set_my_commands(commands, scope={"type": "chat", "chat_id": chat_id})

currency_actions_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Добавить валюту", callback_data="add_currency"),
        InlineKeyboardButton(text="Удалить валюту", callback_data="delete_currency"),
        InlineKeyboardButton(text="Изменить курс валюты", callback_data="edit_currency")
    ]
])

class CurrencyManage(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_delete_currency = State()
    waiting_for_edit_name = State()
    waiting_for_edit_rate = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()

@dp.message(Command("manage_currency"))
async def manage_currency(message: Message):
    if not is_admin(message.chat.id):
        await message.answer("Нет доступа к команде")
        return
    await message.answer("Выберите действие:", reply_markup=currency_actions_kb)

@dp.callback_query(F.data == "add_currency")
async def process_add_currency(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название валюты:")
    await state.set_state(CurrencyManage.waiting_for_currency_name)
    await callback_query.answer()

@dp.message(CurrencyManage.waiting_for_currency_name)
async def process_currency_name(message: Message, state: FSMContext):
    name = message.text.upper()
    if currency_exists(name):
        await message.answer("Данная валюта уже существует.")
        await state.clear()
        return
    await state.update_data(name=name)
    await message.answer("Введите курс к рублю:")
    await state.set_state(CurrencyManage.waiting_for_currency_rate)

@dp.message(CurrencyManage.waiting_for_currency_rate)
async def process_currency_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите число, например: 100.50")
        return
    data = await state.get_data()
    name = data["name"]
    add_currency(name, rate)
    await message.answer(f"Валюта {name} успешно добавлена.")
    await state.clear()

@dp.callback_query(F.data == "delete_currency")
async def process_delete_currency(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название валюты:")
    await state.set_state(CurrencyManage.waiting_for_delete_currency)
    await callback_query.answer()

@dp.message(CurrencyManage.waiting_for_delete_currency)
async def handle_delete_currency(message: Message, state: FSMContext):
    name = message.text.upper()
    delete_currency(name)
    await message.answer(f"Валюта {name} удалена.")
    await state.clear()

@dp.callback_query(F.data == "edit_currency")
async def process_edit_currency(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название валюты:")
    await state.set_state(CurrencyManage.waiting_for_edit_name)
    await callback_query.answer()

@dp.message(CurrencyManage.waiting_for_edit_name)
async def handle_edit_name(message: Message, state: FSMContext):
    name = message.text.upper()
    if not currency_exists(name):
        await message.answer("Такой валюты нет.")
        await state.clear()
        return
    await state.update_data(name=name)
    await message.answer("Введите новый курс к рублю:")
    await state.set_state(CurrencyManage.waiting_for_edit_rate)

@dp.message(CurrencyManage.waiting_for_edit_rate)
async def handle_edit_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите число, например: 75.50")
        return
    data = await state.get_data()
    name = data["name"]
    update_currency_rate(name, rate)
    await message.answer(f"Курс валюты {name} обновлён.")
    await state.clear()

@dp.message(Command("get_currencies"))
async def get_currencies(message: Message):
    currencies = get_all_currencies()
    if not currencies:
        await message.answer("Список валют пуст.")
        return
    response = "Курсы валют к рублю:\n"
    for name, rate in currencies:
        response += f"• {name}: {rate:.2f}\n"
    await message.answer(response)

@dp.message(Command("convert"))
async def convert_command(message: Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(CurrencyManage.waiting_for_convert_currency)

@dp.message(CurrencyManage.waiting_for_convert_currency)
async def handle_convert_currency(message: Message, state: FSMContext):
    name = message.text.upper()
    rate = get_currency_rate(name)
    if rate is None:
        await message.answer("Такой валюты нет.")
        await state.clear()
        return
    await state.update_data(currency_name=name, rate=rate)
    await message.answer("Введите сумму:")
    await state.set_state(CurrencyManage.waiting_for_convert_amount)

@dp.message(CurrencyManage.waiting_for_convert_amount)
async def handle_convert_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
        return
    data = await state.get_data()
    rate = float(data["rate"])
    result = amount * rate
    await message.answer(f"{amount:.2f} {data['currency_name']} = {result:.2f} RUB")
    await state.clear()

@dp.message(Command("start"))
async def start_command(message: Message):
    await set_user_commands(bot, message.chat.id)
    await message.answer("Привет! Открой меню, чтобы начать работу с валютой")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())