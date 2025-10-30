from datetime import datetime
from typing import Callable, Awaitable, Any, Dict, List

import aiosqlite
from aiogram import types

from config import MONTH_MAP


class ReportHandler:
    def __init__(self, message: types.Message, db_conn: aiosqlite.Connection,
                 crud_func: Callable[..., Awaitable[List[Dict[str, Any]]]]):
        self.message = message                      # Сообщение из тг, для ответа и ид юзера.
        self.month_name = None                      # Название месяца, для ответа.
        self.month_number = None                    # Номер месяца(1-12) для получения записей отчета
        self.current_year = None                    # Год для получения записей отчета.
        self.user_id = self.message.from_user.id    # Получаем ID пользователя.
        self.db_conn = db_conn                      # Соединение.
        self.crud_func = crud_func                  # Функция из CRUD.
        self.notes = None                           # Записи из БД по нашему запросу.

    async def get_month_report(self):
        await self._get_month() # Получим месяц и год
        if self.month_number is None:
            return None
        await self._get_notes()

        return f"Ваш отчет за {self.month_name.capitalize()}"


    async def _get_month(self):
        args = self.message.text.split(maxsplit=1)  # Разделить только по первому пробелу
        # TODO тут идет всегда текущий год
        self.current_year = datetime.now().year  # Всегда получаем текущий год по умолчанию

        if len(args) < 2:
            # Если месяц не указан, используем текущий
            self.month_number = datetime.now().month
            # Получим название месяца для ответа
            self.month_name = list(MONTH_MAP.keys())[list(MONTH_MAP.values()).index(self.month_number)]
            await self.message.reply(f"Месяц не указан. Формирую отчет за {self.month_name.capitalize()} {self.current_year} года.")
        else:
            # Если месяц указан, обрабатываем его как раньше
            self.month_name = args[1].lower()
            self.month_number = MONTH_MAP.get(self.month_name)
            if self.month_number is None:
                await self.message.reply(
                    "Не удалось распознать месяц. Пожалуйста, используйте полное название месяца (например, 'июль')."
                )
                return

    async def _get_notes(self):
        # Вызов функции из CRUD для получения данных
        self.notes = await self.crud_func(
            conn=self.db_conn,
            user_tg_id=self.user_id,
            month=self.month_number,
            year=self.current_year      # TODO Пока всегда текущий год
        )

        if not self.notes:
            await self.message.reply(f"Записи для {self.month_name.capitalize()} {self.current_year} года не найдены.")
            return

