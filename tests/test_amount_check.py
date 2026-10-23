import pytest

from app.services.amount_check import UnknownAmountError, check_amounts, rub_amounts, tool_outputs

TOOL_OUTPUT = "{'mode': 'payment', 'new_payment': '49 477,38 ₽', 'saved_on_interest': '771 538,25 ₽'}"


def test_rub_amounts_formats():
    text = "Платеж 49 477,38 ₽, экономия 771 538.25 руб., внесете 500 тыс. рублей, комиссия 300 р."
    assert [k for _, k in rub_amounts(text)] == [4_947_738, 77_153_825, 50_000_000, 30_000]


def test_numbers_without_rubles_are_not_amounts():
    assert rub_amounts("Срок 228 месяцев, ставка 12,5%, платеж №13") == []


def test_tool_outputs_from_history():
    items = [
        {"role": "user", "content": "500 000 ₽"},
        {"type": "function_call", "name": "get_loan", "arguments": "{}"},
        {"type": "function_call_output", "call_id": "c1", "output": TOOL_OUTPUT},
    ]
    assert tool_outputs(items) == [TOOL_OUTPUT]


def test_amount_from_tool_passes():
    check_amounts("Новый платеж 49 477,38 ₽, экономия 771 538,25 ₽.", [TOOL_OUTPUT, "вопрос"])


def test_amount_from_question_passes():
    check_amounts("Если внести 500 000 ₽, платеж будет 49 477,38 ₽.", [TOOL_OUTPUT, "Внесу 500000 после 12-го"])
    check_amounts("После взноса 500 000 ₽ платеж 49 477,38 ₽.", [TOOL_OUTPUT, "Хочу внести 500 тыс."])


def test_rounded_amount_fails():
    with pytest.raises(UnknownAmountError, match="«49 477 ₽»"):
        check_amounts("Новый платеж 49 477 ₽.", [TOOL_OUTPUT, "вопрос"])


def test_invented_amount_fails():
    with pytest.raises(UnknownAmountError, match="«1 000 000 ₽»"):
        check_amounts("Платеж 49 477,38 ₽, а всего сэкономите 1 000 000 ₽.", [TOOL_OUTPUT, "вопрос"])
