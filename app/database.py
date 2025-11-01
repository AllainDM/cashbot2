
import sqlite3
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite

import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# """Модуль для создания соединения с БД"""
@asynccontextmanager
async def get_async_sqlite_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Асинхронный контекстный менеджер для соединения с БД.
    Гарантирует, что соединение будет закрыто.
    """
    connection = None
    try:
        # Создаем асинхронное соединение с базой данных
        # Если здесь ошибка, исключение будет поднято,
        # yield connection не выполнится, блок 'async with' не запустится.
        connection = await aiosqlite.connect(config.DATABASE_NAME)
        # Устанавливаем row_factory для вывода данных в виде словаря
        connection.row_factory = aiosqlite.Row
        logger.debug("Асинхронное соединение с БД установлено.")
        yield connection # Возвращаем соединение для использования в блоке 'async with'
    # Если исключение возникло до yield, finally все равно выполнится
    except Exception as e:
        logger.error(f"Ошибка асинхронного соединения с БД: {e}")
        raise  # Переподнимаем исключение, чтобы вызывающий код мог его обработать
        # yield None
    finally:
        if connection:
            await connection.close()
            logger.debug("Асинхронное соединение с БД закрыто.")


async def update_tables():
    """
    Асинхронное создание таблиц, если они не существуют,
    с использованием контекстного менеджера.
    """
    try:
        async with get_async_sqlite_session() as connection:
            # Асинхронное выполнение SQL-запроса
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS "out" (
                    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_tg_id INTEGER NOT NULL,
                    category TEXT,
                    sub_category TEXT,
                    summ INTEGER,
                    description TEXT,
                    date TEXT
                );
            """)
            logger.info("Таблица 'out' проверена/создана.")
            # Асинхронный commit
            await connection.commit()
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
