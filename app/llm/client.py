import asyncio
import time

from agents import (
    Agent,
    OpenAIProvider,
    RunConfig,
    Runner,
    RunResult,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_run_config: RunConfig | None = None


def setup_llm() -> RunConfig:
    global _run_config
    if _run_config is not None:
        return _run_config
    client = AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=settings.llm_timeout_s,
        max_retries=settings.llm_max_retries,
    )
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    # Стандартный MultiProvider считает «qwen/» в «qwen/qwen3.6-27b» префиксом провайдера и падает;
    # OpenAIProvider передаёт имя модели в LM Studio как есть.
    _run_config = RunConfig(model_provider=OpenAIProvider(openai_client=client, use_responses=False))
    return _run_config


async def run_agent(agent: Agent, prompt: str, context=None) -> RunResult:
    run_config = setup_llm()
    started = time.monotonic()
    result = await asyncio.wait_for(
        Runner.run(agent, prompt, context=context, max_turns=settings.agent_max_turns, run_config=run_config),
        timeout=settings.agent_timeout_s,
    )
    tools = [i.raw_item.name for i in result.new_items if i.type == "tool_call_item"]
    log.info("agent_run", agent=agent.name, tools=tools, latency_ms=int((time.monotonic() - started) * 1000))
    return result
