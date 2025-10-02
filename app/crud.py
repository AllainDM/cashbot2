
import logging
from csv import excel
from typing import Optional
from datetime import datetime

import aiosqlite

import config
from app.database import get_async_sqlite_session

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_note(user_tg_id: int, category: str, sub_category: str, summ: str | int, description: str) -> bool:
    """
    Асинхронно добавляет новую запись в базу данных SQLite.
    Использует aiosqlite для неблокирующих операций.
    """
    logger.info("Запуск асинхронной функции add_note")

    connection = await get_async_sqlite_session() # 1. Получаем соединение
    if connection is None:
        return False

    try:
        # Используем асинхронный контекстный менеджер 'async with',
        # который предоставляет функция get_async_sqlite_session.
        # Это обеспечивает получение и автоматическое закрытие/освобождение соединения.
        # async with await get_async_sqlite_session() as connection:
        # async with aiosqlite.connect(config.DATABASE_NAME) as connection:

        date = datetime.now().strftime("%d.%m.%Y")  # Формат даты: день, месяц, год

        # Асинхронное выполнение SQL-запроса
        # В aiosqlite можно использовать .execute() прямо на объекте connection
        await connection.execute(
            "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) VALUES (?, ?, ?, ?, ?, ?)",
            (user_tg_id, category, sub_category, summ, description, date)
        )

        # Асинхронное подтверждение транзакции (commit)
        await connection.commit()

        logger.info(f"Запись успешно добавлена для пользователя ID: {user_tg_id}.")
        return True

    except Exception as ex:
        # Обработка любых исключений (например, ошибок БД или подключения)
        logger.error(f"Ошибка добавления данных в БД для пользователя ID {user_tg_id}: {ex}", exc_info=True)
        return False

    finally:
        await connection.close()