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
        self.category_sums = {}                     # Собранный отчет по категориям
        self.report_text = None                     # Готовый текст ответа для пользователя

    async def get_month_report(self):
        # Получим месяц и год
        await self._get_month()
        if self.month_number is None:
            return None

        # Получение записей из БД
        await self._get_notes()
        if not self.notes:  # Проверка, найдены ли записи. _get_notes() уже отправил сообщение об их отсутствии
            return None

        # Сборка отчета по категориям
        await self._process_notes()
        if self.category_sums is None:
            return None

        # Подготовка и отправка теста отчета.
        await self._send_report()
        if self.report_text:
            return self.report_text     # Вернем ответ для логирования. Пользователю ответ уже отправлен.
        else:
            return None


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

    async def _process_notes(self):
        """
        Обрабатывает записи (self.notes) и собирает суммы по категориям.
        Возвращает словарь: {category: total_sum}.
        """
        for note in self.notes:
            try:
                # Предполагаем, что 'summ' и 'category' - ключи в словаре note
                summ_float = float(note['summ'])
                category = note['category']
                self.category_sums[category] = self.category_sums.get(category, 0.0) + summ_float
            except (ValueError, TypeError, KeyError) as e:
                # Логирование ошибки для некорректных данных
                print(f"Warning: Failed to process note: {note}. Error: {e}")  # Замените на ваш logger
                # Пропускаем некорректную запись
                continue

    async def _send_report(self):
        """
        Формирует и отправляет отчет пользователю.
        Возвращает итоговый текст отчета.
        """
        if not self.category_sums:
            # Если после обработки категории пусты (например, из-за некорректных данных),
            # отправляем соответствующее сообщение.
            await self.message.reply(
                f"Не удалось подсчитать суммы по категориям для **{self.month_name.capitalize()} {self.current_year}** года."
            )
            # return "Отчет не сформирован из-за отсутствия сумм."

        # Формирование ответа
        self.report_text = (
            f"Ваш отчет за {self.month_name.capitalize()} {self.current_year} года по категориям:\n\n"
        )
        total_report_summ = 0.0

        # Сортируем категории по сумме (от большей к меньшей)
        sorted_sums = sorted(self.category_sums.items(), key=lambda item: item[1], reverse=True)

        for category, summ in sorted_sums:
            sum_as_int = int(summ)
            self.report_text += f"🏷️ {category.capitalize()}: {sum_as_int} руб.\n"
            total_report_summ += summ

        total_report_summ_int = int(total_report_summ)
        self.report_text += f"\nОбщая сумма по всем категориям: {total_report_summ_int} руб."
        # self.report_text += f"\n{'Общая сумма по всем категориям:'} {f'{total_report_summ:.2f}'} руб."

        # Отправляем сообщение пользователю
        await self.message.reply(self.report_text)

        # return self.report_text  # Возвращаем текст для возможного логирования или дальнейшего использования
