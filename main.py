import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN
from models import async_main
from requests import get_users, delete_user_by_id, compare_users_id, set_user,update_votes,zero_votes


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
            await message.answer(f"Пользователь @{message.from_user.username} id: {message.from_user.id} успешно зарегистрирован!")
        else:
            await message.answer("Вы уже зарегистрированы")
    except Exception as e:
        print(f"Ошибка {e}")


@dp.message_handler(commands=['send'])
async def handle_send_command(message: types.Message):
    try:
        await zero_votes()
        users = await get_users()

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
        keyboard.add(types.InlineKeyboardButton(text="Нет", callback_data="No"))

        for user in users:
            try:
                await bot.send_message(user.id, "Будешь на работе?", reply_markup=keyboard)
            except Exception as e:
                print(f"Ошибка при отправке сообщения с кнопками пользователю {user.id}: {e}")
    except Exception as e:
        print(f'Ошибка {e}')


@dp.callback_query_handler(lambda callback_query: callback_query.data in ['Yes', 'No'])
async def handle_vote_callback(callback_query: types.CallbackQuery):
    vote = callback_query.data
    user_id = callback_query.from_user.id

    try:
        if vote == 'No':
            await bot.send_message(user_id, "Отправьте сообщение с обьяснением причины.")
        else:
            await update_votes(vote,user_id)
            await bot.answer_callback_query(callback_query.id, 'Ваш голос принят')
    except Exception as e:
        print(f'Ошибка {e}')


@dp.message_handler(commands=['res'])
async def handle_results_command(message: types.Message):
    users = await get_users()
    voted_yes = []
    voted_no = []
    not_voted = []
    for user in users:
        if user.vote == 'Yes':
            voted_yes.append("{} {} @{}".format(user.name, user.surname, user.username))
        elif user.vote == 'No':
            voted_no.append("{} {} @{}".format(user.name, user.surname, user.username))
        else:
            not_voted.append("{} {} @{}".format(user.name, user.surname, user.username))

    output = "Да\n{}\n\nНет\n{}\n\nНе проголосовали\n{}".format(
        "\n".join(voted_yes) if voted_yes else "Никто",
        "\n".join(voted_no) if voted_no else "Никто",
        "\n".join(not_voted) if not_voted else "Никто"
    )
    await message.answer(output)


@dp.message_handler(commands=['users'])
async def handle_show_users(message: types.Message):
    try:
        users = await get_users()

        output = "Список пользователей:\n\n"
        for user in users:
            output += f"id: {user.id} {user.name} {user.surname} @{user.username}\n"
        await message.answer(output)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


@dp.message_handler(commands=['ban'])
async def handle_ban_command(message: types.Message):
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
