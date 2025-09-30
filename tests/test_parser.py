import pytest

from app.parser import split_message

@pytest.mark.asyncio
async def test_split_message_sum_at_start_simple():
    # Ожидаемый результат: (сумма, категория, подкатегория, описание)
    expected = (100, "Еда", "Еда", "Еда")
    result = await split_message("100 Еда")
    assert result == expected

@pytest.mark.asyncio
async def test_split_message_sum_at_start():
    # Сумма в начале, категория, описание
    msg = "500 Еда Обед с коллегами"
    summ, cat, sub_cat, descr = await split_message(msg)
    assert summ == 500
    assert cat == "Еда"
    assert sub_cat == "Обед"
    assert descr == "Еда Обед с коллегами"

@pytest.mark.asyncio
async def test_split_message_sum_at_end():
    # Сумма в конце
    msg = "Кофе Завтрак 150"
    summ, cat, sub_cat, descr = await split_message(msg)
    assert summ == 150
    assert cat == "Кофе"
    assert sub_cat == "Завтрак"
    assert descr == "Кофе Завтрак"

@pytest.mark.asyncio
async def test_split_message_no_sum():
    # Нет суммы
    msg = "Просто текст"
    summ, _, _, _ = await split_message(msg)
    assert summ is None

