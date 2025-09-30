import pytest
# Предполагаем, что split_message находится в вашем модуле parser
from parser import split_message

@pytest.mark.asyncio
async def test_split_message_sum_at_start_simple():
    # Ожидаемый результат: (сумма, категория, подкатегория, описание)
    expected = ("100", "Еда", "Еда", "Еда")
    result = await split_message("100 Еда")
    assert result == expected
