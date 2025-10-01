import os
import asyncio
import logging

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

import config
# import app.crud

from app import crud
from app.parser import split_message

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_API_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()


# Тестовый обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Узнаем ид пользователя.
    user_id = message.from_user.id
    # Авторизация
    if user_id in config.USERS:
        logger.info(f"Запрос от пользователя {user_id}")
        await message.answer("Привет! Я бот...")


# Основной обработчик сообщений от пользователя.
@dp.message()
async def echo_mess(message: types.Message):
    # Узнаем ид пользователя.
    user_id = message.from_user.id
    # Авторизация
    if user_id in config.USERS:
        logger.info(f"Запрос от пользователя {user_id}")
        # TODO написать отдельную функцию после теста
        # 1. Получим сообщение для дальнейшей обработки
        msg = message.text
        summ, cat, sub_cat, descr = await split_message(msg)
        # 2. Передадим на запись
        if summ:
            ...
            # await crud.add_note(user_tg_id=user_id, category=cat, sub_category=cat, summ=summ, description=descr)
        else:
            logger.info(f"Сообщение не для записи: {msg}")
            await message.answer(f"Сообщение не для записи: {msg}")
    else:
        logger.info(f"Запрос от неавторизованного пользователя {user_id}")


# Основная функция запуска бота
async def main():
    # Удаляем вебхук, если он был установлен
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем поллинг
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
