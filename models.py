from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from config import SQLALCHEMY_URL

engine = create_async_engine(SQLALCHEMY_URL, echo=True)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # тг айди
    name: Mapped[str] = mapped_column(String, nullable=False)  # имя
    surname: Mapped[str] = mapped_column(String,nullable=True)  # фамилия
    username: Mapped[str] = mapped_column(String,nullable=True)  # никнейм
    start_date: Mapped[str] = mapped_column(String,nullable=True)  # дата с какого
    end_date: Mapped[str] = mapped_column(String,nullable=True)  # дата по какое
    is_admin: Mapped[bool] = mapped_column(Boolean,nullable=True)  # админ
    condition: Mapped[str] = mapped_column(String,nullable=True)  # состояние(болен, отпуск итд)
    description: Mapped[str] = mapped_column(String,nullable=True)  # обьяснение причины отсутствия
    vote: Mapped[str] = mapped_column(String,nullable=True) # голоса в опросе


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
