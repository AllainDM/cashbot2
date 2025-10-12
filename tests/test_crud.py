from datetime import datetime

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.crud import add_note


# Константы для теста
TEST_USER_ID = 123456
TEST_CATEGORY = "Еда"
TEST_SUB_CATEGORY = "Обед"
TEST_SUMM = 100
TEST_DESCRIPTION = "Еда Обед"

@pytest.mark.asyncio
@patch('app.crud.datetime')
@patch('app.crud.get_async_sqlite_session')
async def test_crud_add_note_success(mock_get_session, mock_datetime):
    # 1. Настройка Моков.

    # Устанавливаем предсказуемую дату, которую crud.py будет использовать.
    # Это позволяет нам проверить, что SQL-запрос содержит правильную дату.
    fixed_date_str = "05.10.2025"
    mock_datetime.now.return_value.strftime.return_value = fixed_date_str

    # Создаем мок объекта соединения (connection).
    mock_connection = AsyncMock()
    # Настройка мока, чтобы get_async_sqlite_session() вернула наш mock_connection.
    mock_get_session.return_value = mock_connection

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
    mock_connection.close.assert_called_once()

    # Проверяем, что функция вернула успешный результат.
    assert result is True


# --- Тест обработки ошибки БД ---
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

