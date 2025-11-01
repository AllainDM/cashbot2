
from datetime import datetime

import pytest
from aiogram import types
from unittest.mock import AsyncMock, patch, Mock

from config import MONTH_MAP
from app.report_handler import ReportHandler


# Имитация объекта Message
def create_mock_message(text: str) -> types.Message:
    """Создает мок-объект для aiogram.types.Message."""
    # Создаем мок-объект для пользователя (откуда берется id)
    mock_user = Mock(id=12345, full_name="Test User")

    # Создаем мок-объект для сообщения
    mock_message = Mock(spec=types.Message)
    # Нам нужно, чтобы у сообщения были атрибуты:
    mock_message.text = text
    mock_message.from_user = mock_user
    # Если ReportHandler использует message.reply, его тоже нужно замокать
    mock_message.reply = AsyncMock()

    # Можно добавить еще и chat, если нужно
    # mock_message.chat = Mock(id=111, type='private')

    return mock_message


@pytest.mark.asyncio
async def test_reply_is_called_when_month_is_missing():
    """
    Тест проверяет, что при отсутствии месяца в команде (/report),
    бот отправляет пользователю уведомление через message.reply().
    """

    # 1. Настройка.
    # Создаем мок-сообщение, имитирующее команду без аргумента: /report
    mock_message = create_mock_message("/report")

    # МОК для соединения с БД (пока достаточно простого Mock)
    mock_db_conn = Mock()

    # МОК для функции из CRUD
    mock_crud_func = AsyncMock(return_value=[])

    # Инициализируем обработчик, передавая мок-сообщение.
    handler = ReportHandler(message=mock_message, db_conn=mock_db_conn, crud_func=mock_crud_func)

    # 2. Выполнение.
    # Вызываем метод, который содержит логику проверки месяца и отправки ответа
    # Мы можем вызвать _get_month напрямую, или через get_month_report
    # Поскольку _get_month содержит логику уведомления, вызовем его.
    await handler._get_month()

    # 3. Проверка
    # Проверяем, что message.reply был вызван.
    mock_message.reply.assert_called_once()

    # Проверяем, что message.reply был вызван ровно 1 раз. Повторяет проверку выше.
    # assert mock_message.reply.call_count == 1

    # Получаем текущий номер месяца, чтобы знать, какое название месяца ожидать
    current_month_number = datetime.now().month
    # Находим ожидаемое название месяца
    expected_month_name = list(MONTH_MAP.keys())[list(MONTH_MAP.values()).index(current_month_number)].capitalize()
    expected_year = datetime.now().year

    # Проверяем, что сообщение содержит ключевые слова и название текущего месяца
    expected_text = f"Месяц не указан. Формирую отчет за {expected_month_name} {expected_year} года."

    mock_message.reply.assert_called_with(expected_text)


@pytest.mark.asyncio
async def test_get_month_report_includes_current_month_name():
    """
    Тест проверяет, что ReportHandler.get_month_report() возвращает отчет.
    Совпадение по первым словам отчета.
    """

    # 1. Настройка.
    # Создаем мок-сообщение, имитирующее команду без аргумента: /report
    mock_message = create_mock_message("/report Июль")

    # МОК для соединения с БД (пока достаточно простого Mock)
    mock_db_conn = Mock()

    # Мок-функция возвращает тестовые данные, чтобы ReportHandler мог посчитать записи
    mock_crud_func = AsyncMock(return_value=[
        {"summ": 1100, "category": "Еда"},
        {"summ": 900, "category": "Еда"},
        {"summ": 800, "category": "Продукты"}
    ])

    # Инициализируем обработчик, передавая мок-сообщение.
    handler = ReportHandler(message=mock_message, db_conn=mock_db_conn, crud_func=mock_crud_func)

    # Получаем текущее название месяца на английском
    # current_month_english = datetime.now().strftime("%B")
    # print(f"current_month_english {current_month_english}")

    # Создадим ожидаемое ключевое слово, которое ДОЛЖНО быть в отчете
    # Например, мы ожидаем увидеть в отчете, например: "Ваш отчет за Октябрь 2025 года"
    expected_keyword_start = "Ваш отчет за"

    # Получаем год, который используется в ReportHandler
    report_year = 2025

    # Ожидаемый полный отчет должен точно соответствовать форматированию из _send_report
    expected_full_report = (
        f"Ваш отчет за Июль {report_year} года по категориям:\n\n"
        f"🏷️ Еда: 2000 руб.\n"  
        f"🏷️ Продукты: 800 руб.\n"  
        f"\nОбщая сумма по всем категориям: 2800 руб."
    )

    # 2. Выполнение
    report_text = await handler.get_month_report()

    # 3. Проверка
    # Проверяем, что отчет начинается с ожидаемой фразы (или содержит её)
    assert report_text.startswith(expected_keyword_start)

    assert report_text.strip() == expected_full_report.strip()

    # assert (("Ваш отчет за Июль по категориям:\n\n"
    #         "🏷️ Еда: 2000 руб.\n"
    #         "🏷️ Продукты: 800 руб.\n"
    #         "\nОбщая сумма по всем категориям: 2800 руб."
    #          )
    #         in report_text)

    # Дополнительная проверка, чтобы убедиться, что тест действительно ожидает
    # более сложный контент, чем заглушка.
    assert "текст" not in report_text.lower()
