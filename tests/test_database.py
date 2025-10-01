
import os

import pytest
import aiosqlite

import config
from app.database import get_async_sqlite_session, updates_tables

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
