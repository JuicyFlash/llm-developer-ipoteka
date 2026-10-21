import re

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def strip_fence(text: str) -> str:
    fenced = FENCE.search(text)
    return fenced.group(1).strip() if fenced else text.strip()
