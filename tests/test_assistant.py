import pytest
from agents import MaxTurnsExceeded
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assistant import AssistantAnswer
from app.services import assistant

client = TestClient(app)

ANSWER = AssistantAnswer(intent="early_repayment", answer="Новый платеж 49 477,38 ₽", confidence=0.9)
TOOL_OUTPUT = {
    "type": "function_call_output",
    "call_id": "call_1",
    "output": "{'mode': 'payment', 'new_payment': '49 477,38 ₽', 'saved_on_interest': '771 538,25 ₽'}",
}


class FakeResult:
    """Как RunResult: to_input_list() – вход прогона плюс новые элементы (здесь – результат инструмента)."""

    def __init__(self, run_input, final_output, items):
        self.final_output = final_output
        history = [{"role": "user", "content": run_input}] if isinstance(run_input, str) else list(run_input)
        self._items = history + items

    def to_input_list(self):
        return self._items


def fake_run(monkeypatch, *outputs):
    """Подменяет агента: первый прогон вызывает инструмент, повторы отвечают по истории."""
    calls = []

    async def run(agent, run_input, context=None):
        calls.append((run_input, context))
        items = [TOOL_OUTPUT] if len(calls) == 1 else []
        return FakeResult(run_input, outputs[min(len(calls), len(outputs)) - 1], items)

    monkeypatch.setattr(assistant, "run_agent", run)
    return calls


@pytest.fixture(autouse=True)
def confidence_threshold(monkeypatch):
    monkeypatch.setattr(assistant.settings, "agent_min_confidence", 0.7)


@pytest.fixture
def no_db(monkeypatch):
    monkeypatch.setattr(assistant.loans, "get_loan", lambda loan_id: object())


@pytest.fixture
def fake_agent(monkeypatch):
    return fake_run(monkeypatch, ANSWER.model_dump_json())


def test_ask_passes_loan_in_context(fake_agent):
    resp = client.post("/ask", json={"loan_id": 1, "question": "Какой будет платеж после досрочки?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == ANSWER.answer
    assert fake_agent[0][1].loan_id == 1


def test_ask_unknown_loan(fake_agent):
    assert client.post("/ask", json={"loan_id": 999999, "question": "?"}).status_code == 404
    assert fake_agent == []


def test_turn_budget_goes_to_human(monkeypatch):
    async def run(agent, prompt, context=None):
        raise MaxTurnsExceeded("6 ходов")

    monkeypatch.setattr(assistant, "run_agent", run)
    body = client.post("/ask", json={"loan_id": 1, "question": "..."}).json()
    assert body["needs_human"] is True


def test_answer_not_in_format_goes_to_human(monkeypatch):
    calls = fake_run(monkeypatch, "Новый платеж составит **49 477,38 ₽**.")
    body = client.post("/ask", json={"loan_id": 1, "question": "..."}).json()
    assert body == assistant.HANDOFF.model_dump()
    assert len(calls) == 3


def test_fenced_answer_is_accepted(monkeypatch):
    fake_run(monkeypatch, "```json\n" + ANSWER.model_dump_json() + "\n```")
    assert client.post("/ask", json={"loan_id": 1, "question": "..."}).json()["answer"] == ANSWER.answer


def test_answer_with_text_around_is_accepted(monkeypatch):
    fake_run(monkeypatch, "Конечно! " + ANSWER.model_dump_json() + "\nНадеюсь, помог")
    resp = client.post("/ask", json={"loan_id": 1, "question": "..."})
    assert resp.status_code == 200
    assert resp.json()["answer"] == ANSWER.answer


@pytest.mark.asyncio
async def test_garbage_answer_is_repaired_with_clear_error(monkeypatch, no_db):
    calls = fake_run(monkeypatch, '{"answer": "...",,', ANSWER.model_dump_json())
    assert await assistant.ask(1, "...") == ANSWER
    repair = calls[1][0]
    assert TOOL_OUTPUT in repair
    assert "битый JSON" in repair[-1]["content"]


@pytest.mark.asyncio
async def test_invented_amount_is_repaired(monkeypatch, no_db):
    wrong = ANSWER.model_copy(update={"answer": "Новый платеж около 49 500 ₽"})
    calls = fake_run(monkeypatch, wrong.model_dump_json(), ANSWER.model_dump_json())
    assert await assistant.ask(1, "Внесу 500 000 после 12-го платежа") == ANSWER
    assert "«49 500 ₽»" in calls[1][0][-1]["content"]


@pytest.mark.asyncio
async def test_amount_from_question_is_allowed(monkeypatch, no_db):
    ok = ANSWER.model_copy(update={"answer": "После взноса 500 000 ₽ платеж будет 49 477,38 ₽"})
    calls = fake_run(monkeypatch, ok.model_dump_json())
    assert await assistant.ask(1, "Внесу 500000 рублей после 12-го платежа") == ok
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_invented_amount_twice_goes_to_human(monkeypatch, no_db):
    wrong = ANSWER.model_copy(update={"answer": "Сэкономите 1 000 000 ₽"})
    calls = fake_run(monkeypatch, wrong.model_dump_json())
    assert await assistant.ask(1, "...") == assistant.HANDOFF
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_low_confidence_goes_to_human(monkeypatch, no_db):
    low = ANSWER.model_copy(update={"confidence": 0.3})
    calls = fake_run(monkeypatch, low.model_dump_json())
    assert await assistant.ask(1, "...") == low.model_copy(update={"needs_human": True})
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_confidence_at_threshold_is_trusted(monkeypatch, no_db):
    edge = ANSWER.model_copy(update={"confidence": 0.7})
    fake_run(monkeypatch, edge.model_dump_json())
    assert (await assistant.ask(1, "...")).needs_human is False
