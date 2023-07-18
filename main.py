import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BadRequest

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token='6390559042:AAFvfBtG2lqqz_wvFAcg5Lgp3Ir3kexdy28')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Словарь для хранения результатов голосования
votes = {}


@dp.message_handler(commands=['check'])
async def handle_check_command(message: types.Message):
    votes.clear()
    # Создаем сообщение с кнопками "Да" и "Нет"
    buttons = [
        types.InlineKeyboardButton(text='Да', callback_data='vote:yes'),
        types.InlineKeyboardButton(text='Нет', callback_data='vote:no')
    ]
    keyboard = types.InlineKeyboardMarkup().add(*buttons)

    await message.reply('Будешь на работе?', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('vote:'))
async def handle_vote_callback(callback_query: types.CallbackQuery):
    vote = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id

    if vote == 'yes':
        votes[user_id] = 'Да'
    elif vote == 'no':
        votes[user_id] = 'Нет'

    await bot.answer_callback_query(callback_query.id, 'Ваш голос принят')


@dp.message_handler(commands=['result'])
async def handle_result_command(message: types.Message):
    yes_votes = []
    no_votes = []
    not_voted = []

    try:
        chat_admins = await bot.get_chat_administrators(chat_id=message.chat.id)

        for admin in chat_admins:
            user = admin.user
            if user.id in votes:
                vote = votes[user.id]
                if vote == 'Да':
                    yes_votes.append(user.full_name)
                elif vote == 'Нет':
                    no_votes.append(user.full_name)
            else:
                not_voted.append(user.full_name)

        not_voted = [username for username in not_voted if username is not None]

        result_text = f'Голосовавшие "Да":\n'
        result_text += '\n'.join(yes_votes)
        result_text += '\n\nГолосовавшие "Нет":\n'
        result_text += '\n'.join(no_votes)
        result_text += '\n\nНе проголосовавшие:\n'
        result_text += '\n'.join(not_voted)

        await message.reply(result_text)

    except BadRequest as e:
        logging.error(f"Ошибка при получении информации о чате: {e}")


async def main():
    tracemalloc.start()
    try:
        await dp.start_polling()
    finally:
        await dp.stop_polling()  # Остановка опроса
        await dp.storage.close()  # Закрытие хранилища (если используется)
        await dp.storage.wait_closed()  # Ожидание закрытия хранилища
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
