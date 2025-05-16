import os
import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CURRENCY_MANAGER_URL = os.getenv("CURRENCY_MANAGER_URL")
DATA_MANAGER_URL = os.getenv("DATA_MANAGER_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ManageCurrencyStates(StatesGroup):
    choosing_action = State()
    add_name = State()
    add_rate = State()
    delete_name = State()
    update_name = State()
    update_rate = State()

class ConvertStates(StatesGroup):
    waiting_currency_name = State()
    waiting_amount = State()


def main_menu_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.row(
        types.KeyboardButton(text="/manage_currency"),
        types.KeyboardButton(text="/get_currencies")
    )
    kb.row(
        types.KeyboardButton(text="/convert")
    )
    return kb.as_markup(resize_keyboard=True)


def manage_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="Добавить валюту"),
           types.KeyboardButton(text="Удалить валюту"))
    kb.row(types.KeyboardButton(text="Изменить курс валюты"),
           types.KeyboardButton(text="Отмена"))
    return kb.as_markup(resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать! Выберите команду:", reply_markup=main_menu_keyboard())


@dp.message(Command("manage_currency"))
async def cmd_manage_currency(message: types.Message, state: FSMContext):
    await message.answer("Выберите действие:", reply_markup=manage_keyboard())
    await state.set_state(ManageCurrencyStates.choosing_action)

@dp.message(ManageCurrencyStates.choosing_action)
async def handle_action(message: types.Message, state: FSMContext):
    text = message.text.lower()
    if text == "добавить валюту":
        await message.answer("Введите название валюты:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(ManageCurrencyStates.add_name)
    elif text == "удалить валюту":
        await message.answer("Введите название валюты для удаления:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(ManageCurrencyStates.delete_name)
    elif text == "изменить курс валюты":
        await message.answer("Введите название валюты:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(ManageCurrencyStates.update_name)
    elif text == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Пожалуйста, выберите действие из списка.")


@dp.message(ManageCurrencyStates.add_name)
async def add_name_received(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    try:
        async with ClientSession() as session:
            async with session.get(f"{CURRENCY_MANAGER_URL}/check_currency/{name}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("exists"):
                        await message.answer("Данная валюта уже существует.")
                        await state.clear()
                        await message.answer("Вернуться в меню команд: /start", reply_markup=main_menu_keyboard())
                        return
    except Exception as e:
        await message.answer("Ошибка при подключении к сервису.")
        await state.clear()
        return

    await state.update_data(currency_name=name)
    await message.answer("Введите курс к рублю:")
    await state.set_state(ManageCurrencyStates.add_rate)

@dp.message(ManageCurrencyStates.add_rate)
async def add_rate_received(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат курса. Введите число.")
        return

    data = await state.get_data()
    name = data["currency_name"]

    try:
        async with ClientSession() as session:
            async with session.post(
                f"{CURRENCY_MANAGER_URL}/load",
                json={"currency_name": name, "rate": rate}
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("status") == "OK":
                    await message.answer(f"Валюта {name} успешно добавлена с курсом {rate}.")
                else:
                    await message.answer(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
    except Exception:
        await message.answer("Ошибка при добавлении валюты.")
    await state.clear()
    await message.answer("Вернуться в меню команд: /start", reply_markup=main_menu_keyboard())


@dp.message(ManageCurrencyStates.delete_name)
async def delete_currency_received(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    try:
        async with ClientSession() as session:
            async with session.post(
                f"{CURRENCY_MANAGER_URL}/delete",
                json={"currency_name": name}
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("status") == "OK":
                    await message.answer(f"Валюта {name} успешно удалена.")
                else:
                    await message.answer(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
    except Exception:
        await message.answer("Ошибка при удалении валюты.")
    await state.clear()
    await message.answer("Вернуться в меню команд: /start", reply_markup=main_menu_keyboard())


@dp.message(ManageCurrencyStates.update_name)
async def update_name_received(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    await state.update_data(currency_name=name)
    await message.answer("Введите новый курс к рублю:")
    await state.set_state(ManageCurrencyStates.update_rate)

@dp.message(ManageCurrencyStates.update_rate)
async def update_rate_received(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат курса. Введите число.")
        return

    data = await state.get_data()
    name = data["currency_name"]

    try:
        async with ClientSession() as session:
            async with session.post(
                f"{CURRENCY_MANAGER_URL}/update_currency",
                json={"currency_name": name, "rate": rate}
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("status") == "OK":
                    await message.answer(f"Курс валюты {name} успешно обновлён.")
                else:
                    await message.answer(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
    except Exception:
        await message.answer("Ошибка при обновлении курса.")
    await state.clear()
    await message.answer("Вернуться в меню команд: /start", reply_markup=main_menu_keyboard())


@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    try:
        async with ClientSession() as session:
            async with session.get(f"{DATA_MANAGER_URL}/currencies") as resp:
                if resp.status != 200:
                    await message.answer("Не удалось получить данные о валютах.")
                    return
                currencies = await resp.json()
                if not currencies:
                    await message.answer("Валюты не найдены.")
                    return

                msg = "Список валют:\n"
                for c in currencies:
                    msg += f"• {c.get('currency_name', '???')}: {c.get('rate', '???')} ₽\n"

                await message.answer(msg)
    except Exception:
        await message.answer("Ошибка при подключении к сервису.")


@dp.message(Command("convert"))
async def cmd_convert_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(ConvertStates.waiting_currency_name)

@dp.message(ConvertStates.waiting_currency_name)
async def process_convert_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите сумму:")
    await state.set_state(ConvertStates.waiting_amount)

@dp.message(ConvertStates.waiting_amount)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат суммы. Введите число.")
        return

    data = await state.get_data()
    currency_name = data.get("currency_name")

    try:
        async with ClientSession() as session:
            async with session.get(
                f"{DATA_MANAGER_URL}/convert",
                params={"currency": currency_name, "amount": amount}
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and "converted_amount" in data:
                    await message.answer(
                        f"{amount} {currency_name} = {data['converted_amount']} руб. (курс {data['rate']})"
                    )
                else:
                    await message.answer(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
    except Exception:
        await message.answer("Ошибка при подключении к сервису.")

    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())