from agents import MaxTurnsExceeded
from pydantic import ValidationError

from app.agents.prompts import assistant_agent
from app.agents.tools import ClientContext
from app.core.config import settings
from app.core.logging import get_logger
from app.llm.client import run_agent
from app.schemas.assistant import AssistantAnswer
from app.services import loans
from app.services.json_utils import ModelOutputError, extract_json

log = get_logger(__name__)

HANDOFF = AssistantAnswer(
    intent="other",
    answer="Не смог разобраться с вопросом, передаю его сотруднику банка.",
    needs_human=True,
    confidence=0,
)

REPAIR = (
    "Твой ответ не по формату: {error}. Исправь его и верни только JSON-объект по схеме, "
    "без текста вокруг. Инструменты заново не вызывай — их результаты выше."
)


def _parse(output: str) -> AssistantAnswer:
    return AssistantAnswer.model_validate(extract_json(output))


def _describe(err: ModelOutputError | ValidationError) -> str:
    if isinstance(err, ValidationError):
        return "; ".join(f"{'.'.join(map(str, e['loc'])) or 'ответ'}: {e['msg']}" for e in err.errors())
    return str(err)


async def ask(loan_id: int, question: str) -> AssistantAnswer | None:
    if loans.get_loan(loan_id) is None:
        return None
    context = ClientContext(loan_id)
    run_input: str | list = question
    try:
        # Лечим кривой ответ в том же диалоге: история с результатами инструментов уходит модели как есть.
        for attempt in range(settings.agent_max_repairs + 1):
            result = await run_agent(assistant_agent, run_input, context)
            try:
                return _parse(result.final_output)
            except (ModelOutputError, ValidationError) as err:
                error = _describe(err)
                log.warning("answer_repair", attempt=attempt, error=error)
                run_input = result.to_input_list() + [{"role": "user", "content": REPAIR.format(error=error)}]
    except MaxTurnsExceeded:
        return HANDOFF
    return HANDOFF
