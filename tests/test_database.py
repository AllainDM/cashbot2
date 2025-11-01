
import os

import pytest
import aiosqlite
from pytest_asyncio import fixture as async_fixture

import config
from app.database import get_async_sqlite_session, update_tables

# Назначаем имя для тестовой базы данных, чтобы избежать конфликтов с рабочей.
TEST_DATABASE_NAME = 'test_database.db'

# Замена глобальной переменной в модуле database для тестов
@pytest.fixture(scope="session", autouse=True)
def setup_test_db_name():
    # 1. Сохраняем оригинальное имя
    original_db_file = config.DATABASE_NAME

    # 2. Заменяем на тестовое имя
    config.DATABASE_NAME = TEST_DATABASE_NAME

    # 3. Выполняем тесты
    yield

    # 4. Восстанавливаем оригинальное имя после всех тестов
    config.DATABASE_NAME = original_db_file


@async_fixture(scope="function", autouse=True)
async def cleanup_test_db():
    """
    Фикстура для удаления тестовой БД после каждого теста,
    используя текущее (тестовое) имя из config.
    """
    # Тест выполняется здесь
    yield

    # После теста: удаляем файл БД
    db_file_to_cleanup = config.DATABASE_NAME
    if os.path.exists(db_file_to_cleanup):
        os.remove(db_file_to_cleanup)
        print(f"\n[CLEANUP] Удален тестовый файл БД: {db_file_to_cleanup}")


@pytest.mark.asyncio
async def test_get_async_sqlite_session_success():
    """Тест успешного асинхронного соединения с тестовой БД."""
    # conn = await get_async_sqlite_session()
    async with get_async_sqlite_session() as connection:
        assert connection is not None
        assert isinstance(connection, aiosqlite.Connection)

        # Проверяем, что файл создан именно с тестовым именем
        assert os.path.exists(config.DATABASE_NAME)

        await connection.close()


@pytest.mark.asyncio
async def test_updates_tables_creates_table():
    """Тест, проверяющий, что функция updates_tables создает таблицу 'out'."""

    # 1. Запускаем функцию создания таблиц (она использует config.DATABASE_NAME)
    await update_tables()

    # 2. Подключаемся для проверки структуры напрямую к тестовому файлу
    conn = await aiosqlite.connect(config.DATABASE_NAME)

    # 3. Проверяем, что таблица 'out' была создана
    cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='out';")
    table_exists = await cursor.fetchone()

    assert table_exists is not None
    assert table_exists[0] == 'out'

    await conn.close()