import pytest

from app.services.json_utils import ModelOutputError, extract_json

EXPECTED = {"answer": "Новый платеж 49 477,38 ₽"}
RAW = '{"answer": "Новый платеж 49 477,38 ₽"}'


def test_clean_json():
    assert extract_json(RAW) == EXPECTED


def test_fenced_json():
    assert extract_json("```json\n" + RAW + "\n```") == EXPECTED


def test_text_around_json():
    assert extract_json("Конечно! " + RAW + "\nНадеюсь, помог") == EXPECTED


def test_braces_inside_string_value():
    assert extract_json('Вот: {"answer": "скобка } внутри"} и всё') == {"answer": "скобка } внутри"}


def test_garbage_json():
    with pytest.raises(ModelOutputError, match="битый JSON"):
        extract_json('{"answer": "...",,')


def test_garbage_does_not_fall_back_to_nested_object():
    with pytest.raises(ModelOutputError, match="битый JSON"):
        extract_json('{"a": {"b": 1},,')


def test_no_json_at_all():
    with pytest.raises(ModelOutputError, match="нет JSON"):
        extract_json("Новый платеж составит **49 477,38 ₽**.")
