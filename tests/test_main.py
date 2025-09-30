
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User  # Используем настоящий класс Message для имитации структуры

from app.main import echo_mess

USER_ID = 123456


@pytest.mark.asyncio
@patch('app.main.config')  # Мокируем config
# @patch('main.crud')  # Мокируем crud
@patch('app.main.split_message')  # Мокируем парсер
async def test_authorized_user_with_sum(mock_split, mock_config):
    # 1. Настройка: Что должны возвращать наши моки

    # Имитируем, что пользователь авторизован
    mock_config.USERS = [USER_ID]
    user_mock = AsyncMock(spec=User)

    # Имитируем, что парсер успешно обработал сообщение
    mock_split.return_value = ("100", "Еда", "Обед", "Еда Обед")

    # Имитируем объект сообщения (минимум полей)
    message_mock = AsyncMock(spec=Message, text="100 Еда Обед", from_user=user_mock)
    message_mock.from_user.id = USER_ID

    # 2. Выполнение тестируемой функции
    await echo_mess(message_mock)

    # 3. Проверка (Assertions)

    # Проверяем, что парсер был вызван
    mock_split.assert_called_once_with("100 Еда Обед")

    # # Проверяем, что была вызвана запись в БД с корректными параметрами
    # mock_crud.add_note.assert_called_once_with(
    #     user_tg_id=USER_ID,
    #     category="Еда",
    #     sub_category="Обед",
    #     summ="100",
    #     description="Еда Обед"
    # )
