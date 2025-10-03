
# Парсер основного сообщения.
async def split_message(msg: str) -> tuple[int | None, str, str, str | None]:
    """
    Парсит сообщение пользователя в сумму, категорию, подкатегорию и описание.
    Возвращает (summ, cat, sub_cat, descr) или None, если парсинг не удался.
    """
    msg_list = msg.split()
    if not msg_list:
        return None, "", "", ""

    summ = None
    # 1. Поиск суммы
    if msg_list[0].isdigit():
        summ = int(msg_list[0])
        data_list = msg_list[1:]
    elif msg_list[-1].isdigit():
        summ = int(msg_list[-1])
        data_list = msg_list[:-1]
    else:
        return None, "", "", ""  # Сумма не найдена

    if summ < 0:
        # TODO: Добавить проверку на отрицательные числа или игнорирование
        return None, "", "", ""

    # 2. Определение категории, подкатегории и описания
    if not data_list:
        # Сообщение состояло только из суммы
        return None, "", "", ""

    category = data_list[0].capitalize()

    if len(data_list) > 1:
        sub_category = data_list[1].capitalize()
        description = " ".join(data_list)
    else:
        sub_category = category  # Если подкатегории нет, берем категорию
        description = category

    # Небольшая очистка
    if not category or not description:
        return None, "", "", ""

    # print(summ, category, sub_category, description)
    return summ, category, sub_category, description
