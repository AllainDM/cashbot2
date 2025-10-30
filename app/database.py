
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
    conn = None
    try:
        # Создаем асинхронное соединение с базой данных
        conn = await aiosqlite.connect(config.DATABASE_NAME)
        # Устанавливаем row_factory для вывода данных в виде словаря
        conn.row_factory = aiosqlite.Row
        logger.debug("Асинхронное соединение с БД установлено.")
        yield conn # Возвращаем соединение для использования в блоке 'async with'
    except Exception as e:
        logger.error(f"Ошибка асинхронного соединения с БД: {e}")
        # Если соединение не удалось, yield не произойдет
        # raise  # Переподнимаем исключение, чтобы вызывающий код мог его обработать
        yield None
    finally:
        if conn:
            await conn.close()
            logger.debug("Асинхронное соединение с БД закрыто.")


async def update_tables():
    """
    Асинхронное создание таблиц, если они не существуют,
    с использованием контекстного менеджера.
    """
    # conn = await get_async_sqlite_session()
    # if conn is None:
    #     logger.error("Не удалось получить соединение с БД для создания таблиц.")
    #     return
    try:
        async with get_async_sqlite_session() as conn:
            # Асинхронное выполнение SQL-запроса
            await conn.execute("""
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
            await conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
    # Блок finally для закрытия conn не нужен,
    # так как его обрабатывает контекстный менеджер.
    # finally:
    #     await conn.close()
    #     logger.debug(f"Соединение с БД {config.DATABASE_NAME} закрыто.")
