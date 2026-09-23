import logging
import os
from datetime import datetime

import anthropic
from sqlalchemy.orm import Session

from config import get_settings
from services import copilot_offline
from services.copilot_tools import TOOL_DEFINITIONS, CopilotTools

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
MAX_TOKENS = 4096
# Server-side refusal fallback (beta) is available for these models.
FALLBACK_MODEL_PREFIXES = ("claude-opus-5", "claude-fable-5")

SYSTEM_PROMPT = """You are the in-cab voice co-pilot for a CAT excavator operator. Your replies are read aloud in a noisy cab, so answer in one to three short spoken sentences: plain words, no lists, no markdown, lead with the answer. Latency-sensitive; begin your visible answer immediately.

Use the tools for anything about the operator's tasks, machine safety, training, or job-time estimates rather than guessing. When the operator describes an incident, call draft_incident, then read the draft back in one sentence and ask them to confirm it on screen; it is not saved until they do. Change a task's status only when the operator clearly asks. If someone is inside 2 metres of the machine, tell the operator to stop before anything else."""


def _credentials_available(settings) -> bool:
    return bool(
        settings.anthropic_api_key.get_secret_value()
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def _request_options(settings) -> dict:
    model = settings.copilot_model
    options = {"model": model}
    if not model.startswith("claude-haiku"):
        options["output_config"] = {"effort": settings.copilot_effort}
    if model.startswith(FALLBACK_MODEL_PREFIXES):
        options.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    return options


def _run_claude(tools: CopilotTools, history: list[dict]) -> str:
    settings = get_settings()
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key.get_secret_value() or None,
        timeout=settings.copilot_timeout_s,
        max_retries=1,
    )
    session_note = f"Operator {tools.operator_id} is in machine {tools.machine_id}. Local time {datetime.now():%H:%M}."
    messages = list(history)

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.beta.messages.create(
            **_request_options(settings),
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": SYSTEM_PROMPT}, {"type": "text", "text": session_note}],
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            logger.warning("Co-pilot request refused (%s)", response.stop_details and response.stop_details.category)
            return "I can't help with that one. Try asking about your tasks, safety or training."
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            # All results go back in one user message so parallel tool calls keep working.
            messages.append(
                {"role": "user", "content": [tools.run_for_model(b) for b in response.content if b.type == "tool_use"]}
            )
            continue
        text = " ".join(block.text for block in response.content if block.type == "text").strip()
        if response.stop_reason == "max_tokens":
            logger.warning("Co-pilot reply hit max_tokens")
        return text or "Done."

    logger.warning("Co-pilot gave up after %d tool rounds", MAX_TOOL_ROUNDS)
    return "Sorry, that took too many steps. Please try asking a simpler way."


def chat(db: Session, operator_id: str, machine_id: str, history: list[dict]) -> dict:
    """Answer the latest user message; falls back to the offline parser if Claude isn't available."""
    tools = CopilotTools(db, operator_id, machine_id)
    settings = get_settings()

    if _credentials_available(settings):
        try:
            reply = _run_claude(tools, history)
            return {"reply": reply, "source": "claude", "draft_incident": tools.draft, "actions": tools.actions}
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
            logger.warning("Co-pilot credentials rejected; using offline commands")
        except anthropic.RateLimitError:
            logger.warning("Co-pilot rate limited; using offline commands")
        except anthropic.APIConnectionError:
            logger.warning("Claude unreachable; using offline commands")
        except anthropic.APIStatusError as exc:
            logger.error("Co-pilot API error %s: %s", exc.status_code, exc.message)
        # Tools commit as they run, so anything already done in the failed attempt stays in tools.actions.

    reply = copilot_offline.respond(tools, history[-1]["content"])
    return {"reply": reply, "source": "offline", "draft_incident": tools.draft, "actions": tools.actions}
