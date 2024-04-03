import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://postgres:Konoplev27@localhost/db_bot'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token='6390559042:AAFvfBtG2lqqz_wvFAcg5Lgp3Ir3kexdy28')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['reg'])
async def register_user(message: types.Message):
    user_info = message.from_user
    user_id = user_info.id

    db = SessionLocal()
    try:
        query = text(f"SELECT * FROM users WHERE id = :user_id")
        result = db.execute(query, {"user_id": user_id})
        db_user = result.fetchone()

        if db_user is None:
            query = text(
                f"INSERT INTO users (id, name, surname, username, vote) VALUES (:user_id, :name, :surname, :username, NULL)")
            db.execute(query, {"user_id": user_id, "name": user_info.first_name, "surname": user_info.last_name,
                               "username": user_info.username})
            db.commit()
            await message.answer(f"Пользователь @{user_info.username} id: {user_info.id} успешно зарегистрирован!")
        else:
            await message.answer("Вы уже зарегистрированы.")
    finally:
        db.close()


def clear_all_votes():
    db = SessionLocal()
    try:
        query = text("UPDATE users SET vote = NULL")
        db.execute(query)
        db.commit()
    finally:
        db.close()


async def send_to_registered_users():
    db = SessionLocal()
    try:
        clear_all_votes()
        query = text("SELECT id FROM users")
        result = db.execute(query)
        registered_users = [row[0] for row in result.fetchall()]

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
        keyboard.add(types.InlineKeyboardButton(text="Нет", callback_data="No"))

        for user_id in registered_users:
            try:
                await bot.send_message(user_id, "Будешь на работе?", reply_markup=keyboard)
            except Exception as e:
                print(f"Ошибка при отправке сообщения с кнопками пользователю {user_id}: {e}")
    finally:
        db.close()


@dp.message_handler(commands=['send'])
async def handle_send_command(message: types.Message):
    await send_to_registered_users()


@dp.callback_query_handler(lambda callback_query: callback_query.data in ['Yes', 'No'])
async def handle_vote_callback(callback_query: types.CallbackQuery):
    vote = callback_query.data
    user_id = callback_query.from_user.id

    db = SessionLocal()
    try:
        if vote == 'No':
            await bot.send_message(user_id, "Отправьте сообщение с обьяснением причины.")
        else:
            query = text("UPDATE users SET vote = :vote WHERE id = :user_id")
            db.execute(query, {"vote": vote, "user_id": user_id})
            db.commit()

            await bot.answer_callback_query(callback_query.id, 'Ваш голос принят')
    finally:
        db.close()


@dp.message_handler(commands=['res'])
async def handle_results_command(message: types.Message):
    db = SessionLocal()
    try:
        query = text("SELECT name, surname, username, vote FROM users")
        result = db.execute(query)
        users_data = result.fetchall()

        voted_yes = []
        voted_no = []
        not_voted = []
        for name, surname, username, vote in users_data:
            if vote == 'Yes':
                voted_yes.append("{} {} @{}".format(name, surname, username))
            elif vote == 'No':
                voted_no.append("{} {} @{}".format(name, surname, username))
            else:
                not_voted.append("{} {} @{}".format(name, surname, username))

        output = "Да\n{}\n\nНет\n{}\n\nНе проголосовали\n{}".format(
            "\n".join(voted_yes) if voted_yes else "Никто",
            "\n".join(voted_no) if voted_no else "Никто",
            "\n".join(not_voted) if not_voted else "Никто"
        )
        await message.answer(output)
    finally:
        db.close()


@dp.message_handler(commands=['users'])
async def handle_show_users(message: types.Message):
    db = SessionLocal()
    try:
        query = text("SELECT id, name, surname, username FROM users")
        result = db.execute(query)
        users_data = result.fetchall()

        output = "Список пользователей:\n\n"
        for user_id, name, surname, username in users_data:
            output += f"id: {user_id} {name} {surname} @{username}\n"
        await message.answer(output)
    finally:
        db.close()


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

    db = SessionLocal()
    try:
        query = text("DELETE FROM users WHERE id = :user_id")
        db.execute(query, {"user_id": user_id_to_ban})
        db.commit()

        await message.answer(f"Пользователь с ID {user_id_to_ban} забанен и удален из базы данных.")
    finally:
        db.close()


async def main():
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
