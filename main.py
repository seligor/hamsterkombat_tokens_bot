import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from sqlalchemy import create_engine, Column, Integer, String, Date, select, func
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import asyncio
from contextlib import contextmanager

START_MESSAGE = "Привет! Отправь /get_records, чтобы получить токены."
LIMIT_REACHED_MESSAGE = "Вы уже получили 24 токенов сегодня. Попробуйте снова завтра."
NO_RECORDS_MESSAGE = "Нет доступных записей на сегодня."


# Configuration from environment variables
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not API_TOKEN or not DATABASE_URL:
    logging.critical("API_TOKEN and DATABASE_URL must be set")
    raise EnvironmentError("API_TOKEN and DATABASE_URL must be set")

# Logging setup
logging.basicConfig(level=logging.INFO)

# Database setup
Base = declarative_base()
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800
    )

except Exception as e:
    logging.error(f"Failed to create engine: {e}")
    raise
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logging.error(f"Session error: {e}")
        raise
    finally:
        session.close()

class Record(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    content = Column(String(255))
    date_sent = Column(Date)

Base.metadata.create_all(engine)

# Bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

today = datetime.date.today()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply(START_MESSAGE)

@dp.message(Command("get_records"))
async def get_records_command(message: types.Message):
    logging.debug(f"Processing /get_records command for user {message.from_user.id}")
    user_id = message.from_user.id

    with get_session() as session:
        issued_tokens_count = session.query(Record).filter(
            Record.user_id == user_id,
            Record.date_sent == today
        ).count()

        if issued_tokens_count >= 24:
            await message.reply(LIMIT_REACHED_MESSAGE)
            return

        types = ["CLONE", "CUBE", "TRAIN", "BIKE", "MERGE", "TWERK"]
        records = []

        remaining_tokens = 24 - issued_tokens_count
        for record_type in types:
            records.extend(
                session.query(Record)
                .filter(Record.content.like(f"{record_type}%"), Record.user_id.is_(None))
                .order_by(func.random())
                .limit(remaining_tokens // len(types))
                .all()
            )

        if records:
            tokens_to_issue = min(remaining_tokens, len(records))
            for idx in range(tokens_to_issue):
                record = records[idx]
                await message.answer(record.content)
                record.user_id = user_id
                record.date_sent = today
                session.commit()
        else:
            await message.reply(NO_RECORDS_MESSAGE)

async def update_today_variable():
    global today
    while True:
        # Calculate the number of seconds until midnight
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (next_midnight - now).total_seconds()

        # Sleep until midnight
        await asyncio.sleep(seconds_until_midnight)

        # Update the `today` variable
        today = datetime.date.today()
        logging.info("Updated the `today` variable for the new day.")

async def main():
    # Start the update_today_variable coroutine
    asyncio.create_task(update_today_variable())
    # Start polling for messages
    await dp.start_polling(bot)



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
