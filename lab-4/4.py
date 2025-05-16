import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

currency_data = {}

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сохранить курс")],
        [KeyboardButton(text="Конвертировать сохраненный курс")]
    ],
    resize_keyboard=True
)


class SaveCurrency(StatesGroup):
    waiting_for_name = State()
    waiting_for_rate = State()

class ConvertCurrency(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()

@dp.message(Command("start"))
async def start_bot(message: Message):
    await message.answer("Привет! Выберите действие:", reply_markup=main_menu)
    await message.answer(f"d: {message.chat.id}")

@dp.message(lambda msg: msg.text == "Сохранить курс")
async def handle_save_start(message: Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(SaveCurrency.waiting_for_name)

@dp.message(lambda msg: msg.text == "Конвертировать сохраненный курс")
async def handle_convert_button(message: Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(ConvertCurrency.waiting_for_name)

@dp.message(SaveCurrency.waiting_for_name)
async def handle_currency_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.upper())
    await message.answer("Теперь введите курс этой валюты к рублю (например, 92.50):")
    await state.set_state(SaveCurrency.waiting_for_rate)

@dp.message(SaveCurrency.waiting_for_rate)
async def handle_currency_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите число, например: 100.50")
        return
    data = await state.get_data()
    name = data.get("name")
    currency_data[name] = rate

    await message.answer(f"Курс сохранён: 1 {name} = {rate:.2f} RUB")
    await state.clear()

@dp.message(Command("convert"))
async def handle_convert_start(message: Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(ConvertCurrency.waiting_for_name)

@dp.message(ConvertCurrency.waiting_for_name)
async def handle_convert_currency_name(message: Message, state: FSMContext):
    name = message.text.upper()
    if name not in currency_data:
        await message.answer("Такой валюты нет в памяти. Сначала сохраните её через 'Сохранить курс'.")
        await state.clear()
        return

    await state.update_data(name=name)
    await message.answer(f"Введите сумму в {name}, которую нужно перевести в рубли:")
    await state.set_state(ConvertCurrency.waiting_for_amount)

@dp.message(ConvertCurrency.waiting_for_amount)
async def handle_convert_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return
    data = await state.get_data()
    name = data["name"]
    rate = currency_data[name]
    result = amount * rate

    await message.answer(f"{amount:.2f} {name} = {result:.2f} RUB")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
