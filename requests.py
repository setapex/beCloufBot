from sqlalchemy import select, insert, update

from models import User, async_session


async def get_users():
    async with async_session() as session:
        return await session.scalars(select(User))


async def compare_users_id(id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.id == id))


async def delete_user_by_id(id: int):
    async with async_session() as session:
        user = await compare_users_id(id)
        if user:
            await session.delete(user)
            await session.commit()


async def set_user(id: int, name: str, surname: str, username: str, vote:None):
    async with async_session() as session:
        user = await compare_users_id(id)

        if not user:
            await session.execute(insert(User).values(id=id, name=name, surname=surname, username=username, vote=None))
            await session.commit()


async def zero_votes():
    async with async_session() as session:
        await session.execute(update(User).values(vote=None))
        await session.commit()


async def update_votes(vote:str, id:int):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == id).values(vote=vote))
        await session.commit()

