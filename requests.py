from datetime import date

from sqlalchemy import select, insert, update

from models import User, async_session


async def get_users():
    async with async_session() as session:
        return await session.scalars(select(User))


async def get_admins():
    async with async_session() as session:
        return await session.scalars(select(User).where(User.is_admin == True))


async def compare_users_id(id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.id == id))


# 80172395596 9782
async def delete_user_by_id(id: int):
    async with async_session() as session:
        user = await compare_users_id(id)
        if user:
            await session.delete(user)
            await session.commit()


async def set_user(id: int, name: str, surname: str, username: str, vote: None):
    async with async_session() as session:
        user = await compare_users_id(id)

        if not user:
            await session.execute(insert(User).values(id=id, name=name, surname=surname, username=username,
                                                      vote=None, condition="active"))
            await session.commit()


async def zero_votes():
    async with async_session() as session:
        await session.execute(update(User).values(vote=None))
        await session.commit()


async def update_votes(vote: str, id: int):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == id).values(vote=vote))
        await session.commit()


async def update_status(id: int, status: str):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == id).values(condition=status))
        await session.commit()


async def update_start_date(id: int):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == id).values(start_date=date.today()))
        await session.commit()


async def update_end_date(id: int, date: date):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == id).values(end_date=date))
        await session.commit()
