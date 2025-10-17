
import logging
from csv import excel
from datetime import datetime
from typing import List, Dict, Any, Optional

import aiosqlite

import config
from app.database import get_async_sqlite_session

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_note(user_tg_id: int, category: str, sub_category: str, summ: int, description: str) -> bool:
    """
    Асинхронно добавляет новую запись в базу данных SQLite.
    Использует aiosqlite для неблокирующих операций.
    """
    logger.info("Запуск асинхронной функции add_note")

    # 1. Получаем соединение
    connection = await get_async_sqlite_session()
    if connection is None:
        return False

    try:
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


async def get_notes_by_user_and_month(conn: aiosqlite.Connection, user_tg_id: int, month: int, year: int):
    """
            Асинхронно получает все записи для указанного пользователя за определенный месяц и год
            с использованием уже установленного асинхронного соединения (aiosqlite.Connection).

            :param conn: Асинхронное соединение с базой данных (aiosqlite.Connection).
            :param user_tg_id: Telegram ID пользователя.
            :param month: Номер месяца (1-12).
            :param year: Год.
            :return: Список словарей с записями или пустой список, если записей нет/произошла ошибка.
            """
    logger.info(
        f"Запуск асинхронной функции get_notes_by_user_and_month для user_tg_id={user_tg_id}, month={month}, year={year}")

    notes: List[Dict[str, Any]] = []

    # SQL-запрос для выбора записей.
    # Используется логика преобразования строки даты "ДД.ММ.ГГГГ" в формат YYYY-MM-DD
    # для корректного использования функций STRFTIME в SQLite.
    query = """
                SELECT user_tg_id, category, summ, description, date
                FROM out
                WHERE user_tg_id = ?
                  AND STRFTIME('%m', SUBSTR(date, 7, 4) || '-' || SUBSTR(date, 4, 2) || '-' || SUBSTR(date, 1, 2)) = ?
                  AND STRFTIME('%Y', SUBSTR(date, 7, 4) || '-' || SUBSTR(date, 4, 2) || '-' || SUBSTR(date, 1, 2)) = ?;
            """
    # Преобразуем month в строку с ведущим нулем (например, '01' вместо '1')
    month_str = f"{month:02d}"
    year_str = str(year)
    params = (user_tg_id, month_str, year_str)

    try:
        # 1. Асинхронное создание курсора и выполнение запроса.
        # Используем async with для управления курсором, хотя conn.execute/fetchall тоже можно.
        async with conn.cursor() as cur:
            await cur.execute(query, params)

            # 2. Асинхронное получение всех результатов
            rows = await cur.fetchall()

        for row in rows:
            # Поскольку в get_async_sqlite_session() установлено conn.row_factory = aiosqlite.Row,
            # row ведет себя как словарь, поэтому преобразуем его для явности.
            notes.append(dict(row))

        logger.info(f"Получено {len(notes)} записей для user_tg_id={user_tg_id} за {month}.{year}.")
        return notes

    except Exception as ex:
        logger.error(f"Ошибка асинхронного получения данных из БД для user_tg_id {user_tg_id}: {ex}", exc_info=True)
        return []

