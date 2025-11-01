from datetime import datetime

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User  # Используем настоящий класс Message для имитации структуры

from app.main import echo_mess
from app.main import cmd_report
from app.report_handler import ReportHandler

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


# Запрос отчета за месяц
@pytest.mark.asyncio
@patch('app.main.config')           # Конфиг со списком пользователей.
@patch('app.main.ReportHandler')    # Модуль взаимодействия с бд.
@patch('app.main.crud.get_notes_by_user_and_month')
@patch('app.main.get_async_sqlite_session', new_callable=MagicMock)
async def test_get_report_for_month(mock_db_conn_context, mock_crud_func,  mock_report_handler_class, mock_config):
    # 1. Настройка: Что должны возвращать наши моки
    # Имитируем, что пользователь авторизован
    # USER_ID = 123456 # ИД для теста
    mock_config.USERS = [USER_ID]
    user_mock = AsyncMock(spec=User)

    # Создаем минимально необходимый мок сообщения
    mock_message = AsyncMock(spec=Message, from_user=user_mock)
    mock_message.from_user.id = USER_ID
    mock_message.text = "/report"

    # Мок ответа бота
    mock_message.answer = AsyncMock()
    mock_message.reply = AsyncMock()

    # Создаем мок для самого объекта соединения.
    mock_db_conn = AsyncMock(name='db_conn')
    # Настраиваем: при входе в контекстный менеджер (.__aenter__()) возвращается mock_db_conn.
    mock_db_conn_context.return_value.__aenter__.return_value = mock_db_conn

    # Получаем фиктивный экземпляр класса ReportHandler, который вернется при ReportHandler()
    mock_report_handler_instance = mock_report_handler_class.return_value
    # Настраиваем асинхронный метод на фиктивном экземпляре.
    mock_report_handler_instance.get_month_report = AsyncMock()

    # Имитируем, что метод get_month_report возвращает некий отчет
    expected_report_text = "Временный текст отчета"
    mock_report_handler_instance.get_month_report.return_value = expected_report_text

    # 2. Выполнение
    await cmd_report(mock_message)

    # 3. Проверка
    # Проверяем, что контекстный менеджер был вызван
    mock_db_conn_context.assert_called_once()

    # Проверяем, что класс ReportHandler был вызван с новыми именованными аргументами!
    mock_report_handler_class.assert_called_once_with(
        message=mock_message,
        db_conn=mock_db_conn,
        crud_func=mock_crud_func
    )

    # Проверяем, что метод get_month_report был вызван на экземпляре
    mock_report_handler_instance.get_month_report.assert_awaited_once()

    # Мы ожидаем, что mock_message.reply или mock_message.answer будет вызван с текстом отчета.
    # mock_message.reply.assert_awaited_once_with(expected_report_text)


# Запрос отчета за месяц с неверным количеством аргументов
@pytest.mark.asyncio
@patch('app.main.config')
# Мокируем ТОЛЬКО асинхронный метод получения отчета, чтобы проверить
# корректность создания экземпляра ReportHandler внутри cmd_report.
@patch.object(ReportHandler, 'get_month_report', new_callable=AsyncMock)
async def test_get_report_for_month_with_strict_constructor_check(mock_get_month_report, mock_config):
    # 1. Настройка
    mock_config.USERS = [USER_ID]
    user_mock = AsyncMock(spec=User)
    mock_message = AsyncMock(spec=Message, from_user=user_mock)
    mock_message.from_user.id = USER_ID
    mock_message.reply = AsyncMock()

    # Настраиваем возвращаемое значение мок-метода
    expected_report_text = "Временный текст отчета"
    mock_get_month_report.return_value = expected_report_text

    # 2. Выполнение команды
    try:
        # Вызов команды: здесь используется РЕАЛЬНЫЙ конструктор ReportHandler(message).
        # Если конструктор ReportHandler в main.py вызывает TypeError из-за неверных
        # аргументов, тест немедленно провалится (станет КРАСНЫМ).
        await cmd_report(mock_message)
    except TypeError as e:
        # Обработка TypeError: проверяем, что вызов конструктора ReportHandler(message)
        # прошел корректно. Если произошел TypeError, который указывает на
        # нехватку аргументов, это означает ошибку в main.py.

        # Пример: Если ожидается, что конструктор упадет из-за нехватки аргументов:
        if "missing 2 required positional arguments" in str(e):
            pytest.fail(f"Ошибка TypeError: {e} - Проблема с вызовом конструктора ReportHandler в main.py")
        else:
            raise e  # Пробрасываем другие TypeError, которые не связаны с конструктором

    # 3. Проверка результата (Выполняется только в случае успешного вызова)
    # Проверяем, что мок-метод получения отчета был вызван
    mock_get_month_report.assert_awaited_once()

    # Проверяем, что команда отправила корректный ответ пользователю
    # mock_message.reply.assert_awaited_once_with(expected_report_text)

