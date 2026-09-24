import logging
import os
from datetime import datetime

from config import get_settings
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.orm import Session

from services import copilot_offline
from services.copilot_tools import CopilotTools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the in-cab voice co-pilot for a CAT excavator operator. Your replies are read aloud in a noisy cab, so answer in one to three short spoken sentences: plain words, no lists, no markdown, lead with the answer. Latency-sensitive; begin your visible answer immediately.

Use the tools for anything about the operator's tasks, machine safety, training, or job-time estimates rather than guessing. When the operator describes an incident, call draft_incident, then read the draft back in one sentence and ask them to confirm it on screen; it is not saved until they do. Change a task's status only when the operator clearly asks. If someone is inside 2 metres of the machine, tell the operator to stop before anything else."""


def _credentials_available(settings) -> bool:
    return bool(
        settings.gemini_api_key.get_secret_value()
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def _get_api_key(settings) -> str | None:
    return (
        settings.gemini_api_key.get_secret_value()
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or None
    )


def _run_gemini(tools: CopilotTools, history: list[dict]) -> str:
    settings = get_settings()
    api_key = _get_api_key(settings)
    client = genai.Client(api_key=api_key)

    session_note = f"Operator {tools.operator_id} is in machine {tools.machine_id}. Local time {datetime.now():%H:%M}."
    full_system_instruction = f"{SYSTEM_PROMPT}\n\nSession context: {session_note}"

    # Callable tools available to Gemini
    tools_list = [
        tools.get_my_tasks,
        tools.update_task_status,
        tools.draft_incident,
        tools.estimate_task_time,
        tools.get_safety_status,
        tools.get_my_training,
    ]

    config = types.GenerateContentConfig(
        system_instruction=full_system_instruction,
        tools=tools_list,
        temperature=0.2,
    )

    if not history:
        return "How can I help you today?"

    prior_messages = history[:-1]
    last_user_message = history[-1]["content"]

    gemini_history = []
    for msg in prior_messages:
        role = "model" if msg.get("role") in ("assistant", "model") else "user"
        content_text = msg.get("content", "")
        if content_text:
            gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=content_text)]))

    chat_session = client.chats.create(
        model=settings.copilot_model,
        config=config,
        history=gemini_history if gemini_history else None,
    )

    response = chat_session.send_message(last_user_message)
    return response.text.strip() if response.text else "Done."


def chat(db: Session, operator_id: str, machine_id: str, history: list[dict]) -> dict:
    """Answer the latest user message; falls back to the offline parser if Gemini isn't available."""
    tools = CopilotTools(db, operator_id, machine_id)
    settings = get_settings()

    if _credentials_available(settings):
        try:
            reply = _run_gemini(tools, history)
            return {"reply": reply, "source": "gemini", "draft_incident": tools.draft, "actions": tools.actions}
        except APIError as exc:
            logger.warning("Gemini API error (%s): %s; using offline commands", exc.code, exc.message)
        except Exception as exc:
            logger.warning("Gemini copilot error: %s; using offline commands", exc)

    reply = copilot_offline.respond(tools, history[-1]["content"])
    return {"reply": reply, "source": "offline", "draft_incident": tools.draft, "actions": tools.actions}
