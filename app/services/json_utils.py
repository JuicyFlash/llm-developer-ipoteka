import json
import re

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class ModelOutputError(ValueError):
    """Ответ модели не удалось разобрать как JSON."""


def strip_fence(text: str) -> str:
    fenced = FENCE.search(text)
    return fenced.group(1).strip() if fenced else text.strip()


def extract_json(text: str) -> dict:
    # Разбираем с первой «{»: перебор всех скобок выдал бы вложенный объект из битого JSON за ответ.
    text = strip_fence(text)
    start = text.find("{")
    if start == -1:
        raise ModelOutputError("в ответе модели нет JSON-объекта")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError as err:
        raise ModelOutputError(
            f"ответ модели — битый JSON: {err.msg} (строка {err.lineno}, столбец {err.colno})"
        ) from err
    return obj
