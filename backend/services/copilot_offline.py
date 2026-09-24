"""Keyword fallback for the co-pilot when Claude is unreachable or unconfigured.

Covers the core cab commands only; replies are short because they are read aloud.
"""

import re

from services.copilot_tools import CopilotTools, ToolError

_INJURY = re.compile(r"\b(hurt|injur\w*|bleed\w*|ambulance|unconscious)\b")
_NO_INJURY = re.compile(r"\b(no ?one|nobody|not|no)\s+(was\s+|is\s+|got\s+)?(hurt|injured)\b")
_DAMAGE = re.compile(r"\b(clip\w*|hit|struck|collid\w*|collision|crash\w*|damag\w*|dent\w*|leak\w*|broke\w*)\b")
_INCIDENT = re.compile(r"\b(log|report|record)\b|near miss|" + _DAMAGE.pattern)
_ESTIMATE = re.compile(r"\bhow long\b|\bestimate\b|\bhow much time\b")
_START = re.compile(r"\b(start|begin)\b")
_COMPLETE = re.compile(r"\b(done|complete\w*|finish\w*)\b")
_SAFETY = re.compile(r"\b(safe|safety|seatbelt|near me|near my|anyone|proximity)\b")
_TRAINING = re.compile(r"\b(training|score|coaching)\b")
_TASKS = re.compile(r"\b(next|task|tasks|job|jobs|schedule)\b")
_LEAD_IN = re.compile(r"^\s*(please\s+)?(log|report|record)( it| an? incident| incident| that)?[:,.\s-]*", re.I)

_TASK_WORDS = {
    "excavat": "Earth Excavation",
    "trench": "Trenching",
    "load": "Material Loading",
    "grad": "Grading",
    "demoli": "Demolition",
}
_WEATHER_WORDS = {"rain": "Rainy", "wind": "Windy", "cloud": "Cloudy", "sun": "Sunny", "clear": "Sunny"}

HELP = "I can tell you your next task, log an incident, estimate a job's time, check safety around your machine, or show your training."


def _severity(text: str) -> str:
    if _INJURY.search(text) and not _NO_INJURY.search(text):
        return "High"
    if _DAMAGE.search(text):
        return "Medium"
    return "Low"


def _first_match(text: str, words: dict) -> str | None:
    return next((value for key, value in words.items() if key in text), None)


def _minutes(n: int) -> str:
    return f"{n} minute{'s' if n != 1 else ''}"


def respond(tools: CopilotTools, message: str) -> str:
    text = message.lower()
    try:
        if _INCIDENT.search(text):
            description = _LEAD_IN.sub("", message).strip().rstrip(".") or message.strip()
            draft = tools.draft_incident(description[:1].upper() + description[1:], _severity(text))
            return f"I've drafted a {draft['severity'].lower()} severity incident: {draft['description']}. Please confirm it on screen."

        tasks = tools.get_my_tasks()["tasks"]
        open_tasks = [t for t in tasks if t["status"] != "Completed"]

        if _ESTIMATE.search(text):
            task_type = _first_match(text, _TASK_WORDS) or (
                open_tasks[0]["task_type"] if open_tasks else "Earth Excavation"
            )
            weather = _first_match(text, _WEATHER_WORDS) or "Sunny"
            estimate = tools.estimate_task_time(task_type, weather, "Intermediate", 4)
            reply = f"{task_type} in {weather.lower()} weather: about {_minutes(estimate['predicted_minutes'])}"
            if estimate["p10"] is not None:
                reply += f", likely {estimate['p10']} to {estimate['p90']}"
            reply += "."
            if estimate["drivers"]:
                top = estimate["drivers"][0]
                reply += f" {top['label']} adds about {_minutes(top['minutes'])}." if top["minutes"] > 0 else ""
            return reply

        if _START.search(text):
            pending = next((t for t in open_tasks if t["status"] == "Pending"), None)
            if not pending:
                return "You have no pending tasks to start."
            tools.update_task_status(pending["id"], "In Progress")
            return f"Started {pending['task_type']} on {pending['machine_id']}."

        if _COMPLETE.search(text):
            running = next((t for t in open_tasks if t["status"] == "In Progress"), None)
            if not running:
                return "Nothing is in progress right now."
            tools.update_task_status(running["id"], "Completed")
            return f"{running['task_type']} marked complete."

        # Before the safety check: "what's my safety score" is about training, not the machine's surroundings.
        if _TRAINING.search(text):
            training = tools.get_my_training()
            if training["score"] is None:
                return "I don't have a safety score for you yet."
            open_modules = [m["title"] for m in training["assigned_training"] if not m["completed"]]
            reply = f"Your safety score is {training['score']}, {training['band'].lower()}."
            return reply + (
                f" Assigned training: {', '.join(open_modules)}." if open_modules else " No training assigned."
            )

        if _SAFETY.search(text):
            status = tools.get_safety_status()
            if not status["live"]:
                return "Live readings aren't available right now."
            if status["person_in_danger_zone"]:
                return f"Stop. Someone is {status['nearest_person_m']} metres from your machine."
            belt = "fastened" if status["seatbelt_status"] == "Fastened" else "unfastened. Please buckle up"
            return f"Nearest person is {status['nearest_person_m']} metres away. Your seatbelt is {belt}."

        if _TASKS.search(text):
            if not open_tasks:
                return "All your tasks are done for today."
            nxt = next((t for t in open_tasks if t["status"] == "In Progress"), open_tasks[0])
            verb = "You're on" if nxt["status"] == "In Progress" else "Next up is"
            reply = f"{verb} {nxt['task_type']} on {nxt['machine_id']} at {nxt['scheduled']}, about {_minutes(nxt['estimated_min'] or 0)}."
            if len(open_tasks) > 1:
                reply += f" {len(open_tasks) - 1} more after that."
            return reply
    except ToolError as exc:
        return f"Sorry, {exc}."

    return HELP
