import psycopg2
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


conn = psycopg2.connect(
    host="localhost",
    database="telegram_bot_db",
    user="postgres",
    password="postgres"
)
cursor = conn.cursor()


cursor.execute(
    "CREATE TABLE IF NOT EXISTS users ("
    "chat_id BIGINT PRIMARY KEY,"
    "login TEXT NOT NULL)"
)

cursor.execute(
    "CREATE TABLE IF NOT EXISTS operations ("
    "id SERIAL PRIMARY KEY,"
    "chat_id BIGINT NOT NULL REFERENCES users(chat_id),"
    "type TEXT NOT NULL CHECK (type IN ('РАСХОД','ДОХОД')),"
    "amount NUMERIC NOT NULL,"
    "date DATE NOT NULL)"
)
conn.commit()


rates = {'RUB': 1.0, 'EUR': 1.0, 'USD': 1.0}

async def update_rates():
    async with aiohttp.ClientSession() as session:
        for curr in ('EUR', 'USD'):
            try:
                async with session.get(
                    'http://127.0.0.1:5000/rate',
                    params={'currency': curr},
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        rate = data.get('rate')
                        if isinstance(rate, (int, float)):
                            rates[curr] = float(rate)
                        else:
                            print(f"Недопустимый формат курса для {curr}: {rate}")
                    else:
                        print(f"Не удалось получить курс для {curr}, статус {resp.status}")
            except Exception as e:
                print(f"Ошибка при получении курса для {curr}: {e}")

class RegStates(StatesGroup):
    waiting_for_login = State()

class OpStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_amount = State()
    waiting_for_date = State()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.reply(
        "Привет! Я бот-финансист.\n"
        "/reg — регистрация\n"
        "/add_operation — добавить операцию\n"
        "/operations — показать операции"
    )

@dp.message(Command('reg'))
async def cmd_reg(message: Message, state: FSMContext):
    cursor.execute("SELECT 1 FROM users WHERE chat_id = %s", (message.chat.id,))
    if cursor.fetchone():
        await message.reply("Вы уже зарегистрированы.")
        return
    await message.reply("Введите ваш логин:")
    await state.set_state(RegStates.waiting_for_login)

@dp.message(RegStates.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    login = message.text.strip()
    cursor.execute(
        "INSERT INTO users (chat_id, login) VALUES (%s, %s)",
        (message.chat.id, login)
    )
    conn.commit()
    await message.reply(f"Зарегистрированы как {login}.")
    await state.clear()

@dp.message(Command('add_operation'))
async def cmd_add_op(message: Message, state: FSMContext):
    cursor.execute("SELECT 1 FROM users WHERE chat_id = %s", (message.chat.id,))
    if not cursor.fetchone():
        await message.reply("Сначала /reg.")
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="РАСХОД"),
            KeyboardButton(text="ДОХОД")
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply("Выберите тип:", reply_markup=kb)
    await state.set_state(OpStates.waiting_for_type)

@dp.message(OpStates.waiting_for_type)
async def op_type_chosen(message: Message, state: FSMContext):
    op_type = message.text.upper()
    if op_type not in ('РАСХОД','ДОХОД'):
        await message.reply("Введите РАСХОД или ДОХОД.")
        return
    await state.update_data(op_type=op_type)
    
    empty_kb = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    await message.reply("Сумма в рублях:", reply_markup=empty_kb)
    await state.set_state(OpStates.waiting_for_amount)

@dp.message(OpStates.waiting_for_amount)
async def op_amount_entered(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',','.'))
    except ValueError:
        await message.reply("Неверный формат суммы.")
        return
    await state.update_data(amount=amount)
    await message.reply("Дата (ГГГГ-MM-DD):")
    await state.set_state(OpStates.waiting_for_date)

@dp.message(OpStates.waiting_for_date)
async def op_date_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        op_date = datetime.strptime(message.text, '%Y-%m-%d').date()
    except ValueError:
        await message.reply("Неверный формат даты.")
        return
    cursor.execute(
        "INSERT INTO operations (chat_id, type, amount, date) VALUES (%s,%s,%s,%s)",
        (message.chat.id, data['op_type'], data['amount'], op_date)
    )
    conn.commit()
    await message.reply("Операция добавлена.")
    await state.clear()

@dp.message(Command('operations'))
async def cmd_operations(message: Message, state: FSMContext):
    cursor.execute("SELECT 1 FROM users WHERE chat_id = %s", (message.chat.id,))
    if not cursor.fetchone():
        await message.reply("Сначала /reg.")
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="RUB"),
            KeyboardButton(text="EUR"),
            KeyboardButton(text="USD")
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply("Валюта:", reply_markup=kb)

@dp.message(lambda m: m.text in ('RUB','EUR','USD'))
async def show_operations(message: Message):
    target = message.text
    update_rates()
    cursor.execute(
        "SELECT type, amount, date FROM operations WHERE chat_id = %s ORDER BY date",
        (message.chat.id,)
    )
    rows = cursor.fetchall()
    empty_kb = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    if not rows:
        await message.reply("Нет операций.", reply_markup=empty_kb)
        return
    lines = ["Операции:"]
    total_income = 0.0
    total_expense = 0.0
    for op_type, amount, op_date in rows:
        if target == 'RUB':
            converted = float(amount)
        else:
            converted = float(amount) / rates.get(target, 1.0)

        lines.append(f"{op_date} – {op_type} – {converted:.2f} {target}")
        if op_type == 'ДОХОД':
            total_income += converted
        else:
            total_expense += converted

    lines.append(f"\nОбщий доход: {total_income:.2f} {target}")
    lines.append(f"Общий расход: {total_expense:.2f} {target}")
    await message.reply("\n".join(lines), reply_markup=empty_kb)

async def main():
    await update_rates()
    await bot.set_my_commands([
        BotCommand(command='start', description='Старт'),
        BotCommand(command='reg', description='Регистрация'),
        BotCommand(command='add_operation', description='Добавить'),
        BotCommand(command='operations', description='Показать'),
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
