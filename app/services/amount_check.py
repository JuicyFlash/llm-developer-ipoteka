import re

from app.services.json_utils import ModelOutputError

# Пробел-разделитель тысяч: модель пишет и обычный, и неразрывный, и узкий неразрывный.
_SPACE = r"[   ]"
_NUMBER = rf"(?<![\d.,])(\d{{1,3}}(?:{_SPACE}\d{{3}})+|\d+)(?:[.,](\d{{1,2}}))?(?![\d])"
_SCALE = rf"(?:{_SPACE}*(тыс\w*\.?|млн\w*\.?))?"
_RUB = rf"{_SPACE}*(?:₽|руб\w*\.?|р\.)"

NUMBER = re.compile(_NUMBER + _SCALE, re.IGNORECASE)
RUB_AMOUNT = re.compile(_NUMBER + _SCALE + _RUB, re.IGNORECASE)

SCALES = {"тыс": 1_000, "млн": 1_000_000}


class UnknownAmountError(ModelOutputError):
    """В ответе есть сумма, которой нет ни в результатах инструментов, ни в вопросе клиента."""


def _kopecks(whole: str, frac: str | None, scale: str | None) -> int:
    kopecks = int(re.sub(_SPACE, "", whole)) * 100 + int((frac or "0").ljust(2, "0"))
    if scale:
        kopecks *= SCALES[scale.lower()[:3]]
    return kopecks


def rub_amounts(text: str) -> list[tuple[str, int]]:
    """Суммы в рублях из текста ответа: (как написано, копейки)."""
    return [(m.group(0), _kopecks(*m.groups())) for m in RUB_AMOUNT.finditer(text)]


def known_amounts(text: str) -> set[int]:
    """Все числа источника как копейки: клиент может написать «500000» или «500 тыс.» без «₽»."""
    return {_kopecks(*m.groups()) for m in NUMBER.finditer(text)}


def tool_outputs(items: list) -> list[str]:
    return [str(i["output"]) for i in items if isinstance(i, dict) and i.get("type") == "function_call_output"]


def check_amounts(answer: str, sources: list[str]) -> None:
    known = set().union(*(known_amounts(s) for s in sources))
    unknown = [raw for raw, kopecks in rub_amounts(answer) if kopecks not in known]
    if unknown:
        raise UnknownAmountError(
            "суммы " + ", ".join(f"«{raw}»" for raw in unknown)
            + " нет в результатах инструментов и в вопросе клиента — бери суммы только оттуда, без изменений"
        )
