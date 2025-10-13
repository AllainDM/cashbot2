import aiosqlite
from typing import Optional

# ТЕСТОВАЯ версия функции для получения соединения с in-memory БД
async def get_test_db_session() -> Optional[aiosqlite.Connection]:
    """Создает асинхронное соединение с in-memory БД для тестов."""
    try:
        # Используем ':memory:' для in-memory SQLite БД
        conn = await aiosqlite.connect(':memory:')
        conn.row_factory = aiosqlite.Row
        return conn
    except Exception as e:
        # В реальном коде заменить на logger.error
        print(f"Ошибка тестового соединения с БД: {e}")
        return None

async def setup_test_db(conn: aiosqlite.Connection):
    """Создает необходимую таблицу 'out' для теста."""
    await conn.execute("""
        CREATE TABLE out (
            id INTEGER PRIMARY KEY,
            user_tg_id INTEGER,
            category TEXT,
            sub_category TEXT,
            summ INTEGER,
            description TEXT,
            date TEXT
        )
    """)
    await conn.commit()
