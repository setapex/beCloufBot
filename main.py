import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN
from models import async_main
from requests import *

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['reg'])
async def register_user(message: types.Message):
    try:
        if not await compare_users_id(message.from_user.id):
            await set_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                           message.from_user.username, None)
            await message.answer(
                f"Пользователь @{message.from_user.username} id: {message.from_user.id} успешно зарегистрирован!")
        else:
            await message.answer("Вы уже зарегистрированы")
    except Exception as e:
        print(f"Ошибка {e}")


async def check_status():
    users = await get_users()
    for user in users:
        if user.end_date == date.today():
            await update_status(user.id, 'active')


@dp.message_handler(commands=['send'])
async def handle_send_command(message: types.Message):
    try:
        admin_user = await compare_users_id(message.from_user.id)
        if admin_user.is_admin:
            users = await get_users()
            await check_status()
            await zero_votes()
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
            keyboard.add(types.InlineKeyboardButton(text="Нет", callback_data="No"))

            for user in users:
                try:
                    if user.condition == 'active':
                        await bot.send_message(user.id, "Будешь на работе?", reply_markup=keyboard)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения с кнопками пользователю {user.id}: {e}")
        else:
            await message.answer("У Вас нет доступа к этой команде")
    except Exception as e:
        print(f'Ошибка {e}')


async def send_reason_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Болею", callback_data="sick"))
    keyboard.add(types.InlineKeyboardButton(text="Отпуск", callback_data="vacation"))

    await bot.send_message(user_id, "Выберите причину:", reply_markup=keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data in ['Yes', 'No'])
async def handle_vote_callback(callback_query: types.CallbackQuery):
    vote = callback_query.data
    user_id = callback_query.from_user.id
    try:
        if vote == 'No':
            await send_reason_keyboard(user_id)
        else:
            await update_votes(vote, user_id)
            await bot.answer_callback_query(callback_query.id, 'Ваш голос принят')
    except Exception as e:
        print(f'Ошибка {e}')


@dp.callback_query_handler(lambda callback_query: callback_query.data in ['sick', 'vacation'])
async def handle_reason_selection(callback_query: types.CallbackQuery):
    reason_mapping = {
        'sick': 'Болею',
        'vacation': 'Отпуск',
    }
    try:
        await update_status(callback_query.from_user.id, reason_mapping.get(callback_query.data))
        await bot.send_message(callback_query.from_user.id,
                               f"Вы выбрали причину: {reason_mapping.get(callback_query.data)}")
        await update_start_date(callback_query.from_user.id)
        await bot.send_message(callback_query.from_user.id, 'Отправьте дату в формате ГГГГ-ММ-ДД')

        @dp.message_handler(lambda message: message.from_user.id == callback_query.from_user.id)
        async def handle_date(message: types.Message):
            try:
                await process_date(callback_query.from_user.id, message.text)
            except Exception as e:
                await message.answer(f"Вы ввели неверный формат даты {e}")
    except Exception as e:
        print(f'Ошибка {e}')


async def process_date(user_id, date_text):
    end_date = date.fromisoformat(date_text)
    await update_end_date(user_id, end_date)
    await bot.send_message(user_id, f"Вы отправили дату: {end_date}")
    user = await compare_users_id(user_id)

    admins = await get_admins()
    for admin in admins:
        await bot.send_message(admin.id,f"Пользователь {user.name} {user.surname} @{user.username}"
                                           f" будет отсутствовать до {user.end_date}"
                                           f" по причине {user.condition}")


@dp.message_handler(commands=['res'])
async def handle_results_command(message: types.Message):
    admin_user = await compare_users_id(message.from_user.id)
    if admin_user.is_admin:
        users = await get_users()
        voted_yes = []
        voted_sick = []
        voted_vacation = []
        not_voted = []
        for user in users:
            if user.vote == 'Yes':
                voted_yes.append("{} {} @{}".format(user.name, user.surname, user.username))
            elif user.condition == 'Болею':
                voted_sick.append("{} {} @{} до {}".format(user.name, user.surname, user.username, user.end_date))
            elif user.condition == 'Отпуск':
                voted_vacation.append("{} {} @{} до {}".format(user.name, user.surname, user.username, user.end_date))
            else:
                not_voted.append("{} {} @{}".format(user.name, user.surname, user.username))

        output = "Да\n{}\n\nБолеет\n{}\n\nВ отпуске\n{}\n\nНе проголосовали\n{}".format(
            "\n".join(voted_yes) if voted_yes else "Никто",
            "\n".join(voted_sick) if voted_sick else "Никто",
            "\n".join(voted_vacation) if voted_vacation else "Никто",
            "\n".join(not_voted) if not_voted else "Никто")
        await message.answer(output)
    else:
        await message.answer("У Вас нет доступа к этой команде")


@dp.message_handler(commands=['users'])
async def handle_show_users(message: types.Message):
    try:
        admin_user = await compare_users_id(message.from_user.id)
        if admin_user.is_admin:
            users = await get_users()

            output = "Список пользователей:\n\n"
            for user in users:
                output += f"id: {user.id} {user.name} {user.surname} @{user.username}\n"
            await message.answer(output)
        else:
            await message.answer("У Вас нет доступа к этой команде")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


@dp.message_handler(commands=['ban'])
async def handle_ban_command(message: types.Message):
    admin_user = await compare_users_id(message.from_user.id)
    if admin_user.is_admin:
        user_id_to_ban = None
        if message.get_args():
            try:
                user_id_to_ban = int(message.get_args().split()[0])
            except ValueError:
                await message.answer("Неверный формат команды. Используйте /ban <user_id>")
                return

        if not user_id_to_ban:
            await message.answer("Не указан ID пользователя для бана.")
            return

        try:
            if not await compare_users_id(user_id_to_ban):
                await message.answer(f"Пользователь с ID {user_id_to_ban} не был найден.")
            else:
                await delete_user_by_id(user_id_to_ban)
                await message.answer(f"Пользователь с ID {user_id_to_ban} забанен и удален из базы данных.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    else:
        await message.answer("У Вас нет доступа к этой команде")


async def main():
    await async_main()
    tracemalloc.start()
    try:
        await dp.start_polling()
    finally:
        await dp.stop_polling()
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
