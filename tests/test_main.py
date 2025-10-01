
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User  # Используем настоящий класс Message для имитации структуры

from app.main import echo_mess

USER_ID = 123456  # ид пользователя для проверки авторизации


# Неавторизованный пользователь.
@pytest.mark.asyncio
@patch('app.main.config')           # Конфиг со списком пользователей.
@patch('app.main.crud')             # Не должен вызваться.
@patch('app.main.split_message')    # Не должен вызваться.
async def test_unauthorized_user_is_ignored(mock_split, mock_crud, mock_config):
    # 1. Настройка
    mock_config.USERS = [11111]  # Список без нашего USER_ID
    unauth_user_id = 99999

    user_mock = AsyncMock(id=unauth_user_id)
    message_mock = AsyncMock(spec=Message, text="100 Еда Обед", from_user=user_mock)

    # 2. Выполнение
    await echo_mess(message_mock)

    # 3. Проверка
    # Проверяем, что парсер и запись в БД НЕ были вызваны
    mock_split.assert_not_called()
    mock_crud.add_note.assert_not_called()
    # TODO может измениться бот начнет всем отвечать
    message_mock.answer.assert_not_called()


# Добавление записи в БД
@pytest.mark.asyncio
@patch('app.main.config')           # Конфиг со списком пользователей.
@patch('app.main.crud')             # Модуль взаимодействия с бд.
@patch('app.main.split_message')    # Парсер сообщений(разделение на сумму и категории).
async def test_successful_note_creation(mock_split, mock_crud, mock_config):
    # 1. Настройка
    # Делаем add_note асинхронным моком
    mock_crud.add_note = AsyncMock(return_value=True)

    # Имитируем, что пользователь авторизован
    mock_config.USERS = [USER_ID]
    user_mock = AsyncMock(spec=User)

    # Имитируем, что парсер успешно обработал сообщение
    # (summ, cat, sub_cat, descr)
    mock_split.return_value = ("100", "Еда", "Обед", "Еда Обед")

    # Имитируем объект сообщения (минимум полей)
    message_mock = AsyncMock(spec=Message, text="100 Еда Обед", from_user=user_mock)
    message_mock.from_user.id = USER_ID

    # 2. Выполнение
    await echo_mess(message_mock)

    # 3. Проверка
    mock_split.assert_called_once_with("100 Еда Обед")
    mock_crud.add_note.assert_called_once_with(
        user_tg_id=USER_ID,
        category="Еда",
        sub_category="Обед",
        summ="100",
        description="Еда Обед"
    )


# Парсер сообщения. Отправим сообщение с ошибкой.
@pytest.mark.asyncio
@patch('app.main.config')           # Конфиг со списком пользователей.
@patch('app.main.crud')             # Модуль взаимодействия с бд.
@patch('app.main.split_message')    # Парсер сообщений(разделение на сумму и категории).
async def test_parsing_failure_sends_error_message(mock_split, mock_crud, mock_config):
    # 1. Настройка: Что должны возвращать наши моки
    # Имитируем, что пользователь авторизован
    mock_config.USERS = [USER_ID]
    user_mock = AsyncMock(spec=User)

    # Имитируем ошибку парсера
    mock_split.return_value = (None, None, None, None)

    # Имитируем объект сообщения (минимум полей)
    message_mock = AsyncMock(spec=Message, text="некорректный_формат", from_user=user_mock)
    message_mock.from_user.id = USER_ID

    # Добавляем асинхронный мок для message.answer
    message_mock.answer = AsyncMock()

    # 2. Выполнение тестируемой функции
    await echo_mess(message_mock)

    # 3. Проверка
    mock_split.assert_called_once()
    mock_crud.add_note.assert_not_called() # Проверяем, что в БД ничего не попало

    # Проверяем, что бот ответил пользователю (ответ по умолчанию)
    message_mock.answer.assert_called_once()
    # Без проверки текста ответа:
    # message_mock.answer.assert_called_once_with("Сообщение об ошибке")

