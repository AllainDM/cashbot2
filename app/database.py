
import sqlite3
import logging
from typing import Optional

import aiosqlite

import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


"""Модуль для создания соединения с БД"""

async def get_async_sqlite_session() -> Optional[aiosqlite.Connection]:
    """
    Асинхронное создание или подключение к базе данных SQLite с помощью aiosqlite.
    """
    try:
        # Создаем асинхронное соединение с базой данных
        conn = await aiosqlite.connect(config.DATABASE_NAME)
        # Устанавливаем row_factory для вывода данных в виде словаря
        conn.row_factory = aiosqlite.Row
        logger.debug("Асинхронное соединение с БД установлено.")
        return conn
    except Exception as e:
        logger.error(f"Ошибка асинхронного соединения с БД: {e}")
        return None

async def update_tables():
    """
    Асинхронное создание таблиц, если они не существуют.
    """
    conn = await get_async_sqlite_session()
    if conn is None:
        logger.error("Не удалось получить соединение с БД для создания таблиц.")
        return

    try:
        # Асинхронное выполнение SQL-запроса
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS "out" (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER NOT NULL,
                category TEXT,
                sub_category TEXT,
                summ TEXT,
                description TEXT,
                date TEXT
            );
        """)
        logger.info("Таблица 'out' проверена/создана.")
        # Асинхронный commit
        await conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
    finally:
        # Обязательно асинхронно закрываем соединение
        await conn.close()
        logger.debug(f"Соединение с БД {config.DATABASE_NAME} закрыто.")
