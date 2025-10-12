from datetime import datetime

from aiogram import types

from config import MONTH_MAP


class ReportHandler:
    def __init__(self, message: types.Message):
        self.message = message
        self.month_name = None
        self.month_number = None


    async def get_month_report(self):
        # Получим месяц
        await self._get_month()
        print(f"Ваш отчет за {self.month_name.capitalize()}")
        return f"Ваш отчет за {self.month_name.capitalize()}"


    async def _get_month(self):
        args = self.message.text.split(maxsplit=1)  # Разделить только по первому пробелу
        # TODO тут идет всегда текущий год
        current_year = datetime.now().year  # Всегда получаем текущий год по умолчанию

        if len(args) < 2:
            # Если месяц не указан, используем текущий
            self.month_number = datetime.now().month
            # Получим название месяца для ответа
            self.month_name = list(MONTH_MAP.keys())[list(MONTH_MAP.values()).index(self.month_number)]
            await self.message.reply(f"Месяц не указан. Формирую отчет за {self.month_name.capitalize()} {current_year} года.")
        else:
            # Если месяц указан, обрабатываем его как раньше
            self.month_name = args[1].lower()
            self.month_number = MONTH_MAP.get(self.month_name)

            if self.month_number is None:
                await self.message.reply(
                    "Не удалось распознать месяц. Пожалуйста, используйте полное название месяца (например, 'июль')."
                )
                return


