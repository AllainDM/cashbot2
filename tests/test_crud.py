from datetime import datetime

import pytest
from typing import Optional
from unittest.mock import patch, AsyncMock, MagicMock, Mock

from app.crud import add_note
from app.crud import get_notes_by_user_and_month
from tests.test_db_utils import get_test_db_session, setup_test_db


# Константы для теста
TEST_USER_ID = 123456
TEST_CATEGORY = "Еда"
TEST_SUB_CATEGORY = "Обед"
TEST_SUMM = 100
TEST_DESCRIPTION = "Еда Обед"


# Тест успешного добавления записи в БД.
@pytest.mark.asyncio
@patch('app.crud.datetime')
@patch('app.crud.get_async_sqlite_session')
async def test_crud_add_note_success(mock_get_session, mock_datetime):
    # 1. Настройка Моков.

    # Устанавливаем предсказуемую дату, которую crud.py будет использовать.
    #   Чтобы быть уверенным, что тест падает от реальной ошибки.
    fixed_date_str = "05.10.2025"
    mock_datetime.now.return_value.strftime.return_value = fixed_date_str

    # Создаем мок объекта, который будет возвращен в 'as connection'
    mock_connection = AsyncMock()

    # Создаем мок, который будет вести себя как асинхронный контекстный менеджер
    #    Обычный MagicMock уже имеет методы __enter__ и __exit__,
    #    но для асинхронного контекстного менеджера нужны __aenter__ и __aexit__.
    mock_context_manager = MagicMock()

    # Настраиваем, что произойдет при входе в 'async with' (т.е. при вызове __aenter__)
    #    Он должен быть AWAITABLE и возвращать mock_connection
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_connection)

    # Настраиваем, что произойдет при выходе из 'async with' (т.е. при вызове __aexit__)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)  # Ничего не возвращает

    # Настраиваем патч get_async_sqlite_session, чтобы он возвращал наш контекстный менеджер
    #    get_async_sqlite_session() -> mock_context_manager
    mock_get_session.return_value = mock_context_manager

    # 2. Выполнение.
    result = await add_note(
        user_tg_id=TEST_USER_ID,
        category=TEST_CATEGORY,
        sub_category=TEST_SUB_CATEGORY,
        summ=TEST_SUMM,
        description=TEST_DESCRIPTION
    )

    # 3. Проверка.
    # Проверяем, что функция получения соединения была вызвана один раз.
    mock_get_session.assert_called_once()
    mock_context_manager.__aenter__.assert_called_once()
    mock_context_manager.__aexit__.assert_called_once()

    # Ожидаемый SQL-запрос и параметры.
    expected_sql = (
        "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    expected_params = (
        TEST_USER_ID,
        TEST_CATEGORY,
        TEST_SUB_CATEGORY,
        TEST_SUMM,
        TEST_DESCRIPTION,
        fixed_date_str # Используем замоканную дату.
    )

    # Проверяем, что на мок-соединении вызвали execute с правильными данными.
    mock_connection.execute.assert_called_once_with(expected_sql, expected_params)

    # Проверяем, что была вызвана фиксация транзакции (commit).
    mock_connection.commit.assert_called_once()

    # Проверяем, что соединение было закрыто (независимо от результата).
    # !!! Нет необходимости, работа через контекстный менеджер
    # mock_connection.close.assert_called_once()

    # Проверяем, что функция вернула успешный результат.
    assert result is True


# Тест получения записей из БД. С тестовой БД в памяти и добавлением в нее данных.
@pytest.mark.asyncio
async def test_get_notes_by_user_and_month_success():
    # 1. Подготовка
    conn = await get_test_db_session()
    assert conn is not None
    await setup_test_db(conn)  # Создаем таблицу

    # Дата для теста: 15.01.2025
    test_user_id = 12345

    # 2. Добавление тестовых данных.
    # Добавляем 2 записи за январь 2025 (должны быть получены)
    await conn.execute(
        "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) VALUES (?, ?, ?, ?, ?, ?)",
        (test_user_id, 'Еда', 'Обед', 500, 'Еда обед бизнес-ланч', '15.01.2025')
    )
    await conn.execute(
        "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) VALUES (?, ?, ?, ?, ?, ?)",
        (test_user_id, 'Развлечения', 'Кино', 1200, 'Развлечения кино', '20.01.2025')
    )

    # Добавляем 1 запись за ФЕВРАЛЬ 2025 (не должна быть получена)
    await conn.execute(
        "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) VALUES (?, ?, ?, ?, ?, ?)",
        (test_user_id, 'Продукты', 'Магазин', 800, 'Молоко', '01.02.2025')
    )

    # Добавляем 1 запись для другого пользователя (не должна быть получена)
    await conn.execute(
        "INSERT INTO out (user_tg_id, category, sub_category, summ, description, date) VALUES (?, ?, ?, ?, ?, ?)",
        (54321, 'Еда', 'Ужин', 700, 'Роллы', '15.01.2025')
    )
    await conn.commit()

    # 3. Вызов тестируемой функции и проверка
    notes = await get_notes_by_user_and_month(conn, test_user_id, 1, 2025)

    # Проверяем, что получено ровно 2 записи
    assert len(notes) == 2, f"Ожидалось 2 записи, получено {len(notes)}"

    # Проверяем содержимое одной из записей, чтобы убедиться в правильности данных
    # Поскольку порядок не гарантирован, проверим наличие нужных сумм
    sums = {note['summ'] for note in notes}
    assert 500 in sums
    assert 1200 in sums
    assert 800 not in sums  # Запись за Февраль не должна быть здесь

    # 4. Очистка
    await conn.close()


# Тест обработки ошибки БД.
@pytest.mark.asyncio
@patch('app.crud.get_async_sqlite_session')
async def test_crud_add_note_db_failure(mock_get_session):
    # 1. Настройка Моков.
    # Создаем мок объекта соединения.
    mock_connection = AsyncMock()
    mock_get_session.return_value = mock_connection

    # Имитируем ошибку: заставляем execute() выбросить исключение.
    mock_connection.execute.side_effect = Exception("Database error!")

    # 2. Выполнение
    result = await add_note(
        user_tg_id=TEST_USER_ID,
        category=TEST_CATEGORY,
        sub_category=TEST_SUB_CATEGORY,
        summ=TEST_SUMM,
        description=TEST_DESCRIPTION
    )

    # 3. Проверка.
    # Проверяем, что execute была вызвана, но вызвала ошибку.
    mock_connection.execute.assert_called_once()

    # Проверяем, что commit НЕ был вызван (транзакция не фиксируется при ошибке)
    mock_connection.commit.assert_not_called()

    # Проверяем, что соединение было закрыто (в блоке finally).
    mock_connection.close.assert_called_once()

    # Проверяем, что функция вернула False при ошибке.
    assert result is False

