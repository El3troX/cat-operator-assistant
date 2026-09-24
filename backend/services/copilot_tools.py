import json
import logging
from typing import Any, Optional

import models
from pydantic import ValidationError
from schemas import PredictTaskTimeRequest, TaskResponse
from sqlalchemy.orm import Session

from services import simulator
from services.events import publish_event
from services.rules import PROXIMITY_ALERT_M
from services.scoring import operator_scores
from services.task_time import estimate_task_time

logger = logging.getLogger(__name__)

SEVERITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Completed"]
TASK_TYPES = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
WEATHERS = ["Sunny", "Rainy", "Cloudy", "Windy"]
SKILLS = ["Beginner", "Intermediate", "Expert"]


def _schema(properties: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


# Identity (operator, machine) comes from the cab session, never from the model's arguments.
TOOL_DEFINITIONS = [
    {
        "name": "get_my_tasks",
        "description": "Today's tasks assigned to this operator: id, task type, machine, status, scheduled time and estimate.",
        "input_schema": _schema({}, []),
        "strict": True,
    },
    {
        "name": "update_task_status",
        "description": "Start or complete one of this operator's tasks. Use only when the operator clearly asks.",
        "input_schema": _schema(
            {"task_id": {"type": "integer"}, "status": {"type": "string", "enum": STATUSES}}, ["task_id", "status"]
        ),
        "strict": True,
    },
    {
        "name": "draft_incident",
        "description": (
            "Prepare an incident report from what the operator described. It is NOT saved: "
            "the operator confirms it on screen. Afterwards, read the draft back briefly."
        ),
        "input_schema": _schema(
            {
                "description": {
                    "type": "string",
                    "description": "One or two clear sentences of what happened, where, and whether anyone was hurt.",
                },
                "severity": {
                    "type": "string",
                    "enum": SEVERITIES,
                    "description": "High if anyone is hurt or at serious risk; Medium for collisions or damage; Low for near misses.",
                },
            },
            ["description", "severity"],
        ),
        "strict": True,
    },
    {
        "name": "estimate_task_time",
        "description": "Predict how long a job takes, with a likely range and what drives it. Use the operator's task and stated conditions.",
        "input_schema": _schema(
            {
                "task_type": {"type": "string", "enum": TASK_TYPES},
                "weather": {"type": "string", "enum": WEATHERS},
                "operator_skill": {"type": "string", "enum": SKILLS},
                "machine_age_yrs": {"type": "integer"},
            },
            ["task_type", "weather", "operator_skill", "machine_age_yrs"],
        ),
        "strict": True,
    },
    {
        "name": "get_safety_status",
        "description": "Live readings for the operator's machine (seatbelt, idling, nearest person) and its latest alerts.",
        "input_schema": _schema({}, []),
        "strict": True,
    },
    {
        "name": "get_my_training",
        "description": "The operator's safety score, the factors behind it, and the training assigned to them.",
        "input_schema": _schema({}, []),
        "strict": True,
    },
]


class ToolError(Exception):
    """A tool failed in a way the model (or the operator) should hear about."""


class CopilotTools:
    """Executes co-pilot tools as the cab's operator and records what changed for the response."""

    def __init__(self, db: Session, operator_id: str, machine_id: str) -> None:
        self.db = db
        self.operator_id = operator_id
        self.machine_id = machine_id
        self.draft: Optional[dict] = None
        self.actions: list[dict] = []

    def run(self, name: str, arguments: dict) -> dict:
        handler = getattr(self, name, None)
        if name not in {tool["name"] for tool in TOOL_DEFINITIONS} or handler is None:
            raise ToolError(f"Unknown tool {name}")
        return handler(**arguments)

    def run_for_model(self, block: Any) -> dict:
        """tool_result block for a tool_use block; failures go back to the model as is_error results."""
        try:
            content, is_error = json.dumps(self.run(block.name, dict(block.input))), False
        except ToolError as exc:
            content, is_error = str(exc), True
        except (TypeError, ValidationError) as exc:
            content, is_error = f"Invalid arguments: {exc}", True
        return {"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error}

    # --- tools ---

    def get_my_tasks(self) -> dict:
        """Get today's tasks assigned to this operator including id, task type, machine, status, scheduled time and estimate."""
        tasks = (
            self.db.query(models.Task)
            .filter(models.Task.operator_id == self.operator_id)
            .order_by(models.Task.scheduled_time)
            .all()
        )
        return {
            "operator_id": self.operator_id,
            "tasks": [
                {
                    "id": t.id,
                    "task_type": t.task_type,
                    "machine_id": t.machine_id,
                    "status": t.status,
                    "scheduled": (t.scheduled_time or "")[11:16],
                    "estimated_min": t.estimated_time_min,
                }
                for t in tasks
            ],
        }

    def update_task_status(self, task_id: int, status: str) -> dict:
        """Start or complete one of this operator's tasks. Status must be 'Pending', 'In Progress', or 'Completed'.

        Args:
            task_id: ID of the task to update.
            status: New status ('Pending', 'In Progress', or 'Completed').
        """
        if status not in STATUSES:
            raise ToolError(f"Status must be one of {STATUSES}")
        task = self.db.get(models.Task, task_id)
        if task is None or task.operator_id != self.operator_id:
            raise ToolError(f"Task {task_id} is not assigned to {self.operator_id}")
        task.status = status
        if status == "Completed" and task.actual_time_min is None:
            task.actual_time_min = task.estimated_time_min
        elif status != "Completed":
            task.actual_time_min = None
        self.db.commit()
        self.db.refresh(task)
        publish_event("task.updated", TaskResponse.model_validate(task))
        self.actions.append({"tool": "update_task_status", "summary": f"{task.task_type} marked {status}"})
        logger.info("Co-pilot set task %s to %s for %s", task_id, status, self.operator_id)
        return {"task_id": task.id, "task_type": task.task_type, "status": task.status}

    def draft_incident(self, description: str, severity: str) -> dict:
        """Prepare an incident report from what the operator described. It is NOT saved: the operator confirms it on screen.

        Args:
            description: One or two clear sentences of what happened, where, and whether anyone was hurt.
            severity: Severity level: 'High' if injured/hazard, 'Medium' for collisions/damage, 'Low' for near misses.
        """
        description = description.strip()
        if severity not in SEVERITIES:
            raise ToolError(f"Severity must be one of {SEVERITIES}")
        if not 5 <= len(description) <= 2000:
            raise ToolError("Description must be 5 to 2000 characters")
        self.draft = {
            "machine_id": self.machine_id,
            "operator_id": self.operator_id,
            "description": description,
            "severity": severity,
        }
        self.actions.append(
            {"tool": "draft_incident", "summary": f"{severity} incident drafted, awaiting confirmation"}
        )
        return {"status": "awaiting operator confirmation on screen", **self.draft}

    def estimate_task_time(self, task_type: str, weather: str, operator_skill: str, machine_age_yrs: int) -> dict:
        """Predict how long a job takes, with a likely range and what drives it.

        Args:
            task_type: Type of task ('Earth Excavation', 'Trenching', 'Material Loading', 'Grading', 'Demolition').
            weather: Weather condition ('Sunny', 'Rainy', 'Cloudy', 'Windy').
            operator_skill: Skill level of operator ('Beginner', 'Intermediate', 'Expert').
            machine_age_yrs: Machine age in years.
        """
        request = PredictTaskTimeRequest(
            task_type=task_type, weather=weather, operator_skill=operator_skill, machine_age_yrs=machine_age_yrs
        )
        return estimate_task_time(request, self.db).model_dump()

    def get_safety_status(self) -> dict:
        """Get live readings for the operator's machine (seatbelt, idling, nearest person) and its latest alerts."""
        frame = simulator.current.latest if simulator.current else None
        reading = next((m for m in (frame or {}).get("machines", []) if m["machine_id"] == self.machine_id), None)
        alerts = (
            self.db.query(models.Alert)
            .filter(models.Alert.machine_id == self.machine_id)
            .order_by(models.Alert.timestamp.desc(), models.Alert.id.desc())
            .limit(3)
            .all()
        )
        return {
            "machine_id": self.machine_id,
            "live": reading is not None,
            "seatbelt_status": reading and reading["seatbelt_status"],
            "idling_time_min": reading and reading["idling_time_min"],
            "nearest_person_m": reading and reading["nearest_m"],
            "person_in_danger_zone": bool(reading and reading["nearest_m"] <= PROXIMITY_ALERT_M),
            "recent_alerts": [
                {"type": a.type, "severity": a.severity, "message": a.message, "time": a.timestamp[11:16]}
                for a in alerts
            ],
        }

    def get_my_training(self) -> dict:
        """Get the operator's safety score, the factors behind it, and the training assigned to them."""
        scores = operator_scores(self.db, self.operator_id)

        if not scores:
            return {"operator_id": self.operator_id, "score": None, "assigned_training": []}
        entry = scores[0]
        return {
            "operator_id": self.operator_id,
            "score": entry.score,
            "band": entry.band,
            "factors": [
                {"factor": f.factor, "penalty": f.penalty, "detail": f.detail} for f in entry.factors if f.penalty
            ],
            "assigned_training": [
                {"title": m["title"], "reason": m["reason"], "completed": bool(m["completed"])}
                for m in entry.recommended_modules
            ],
        }
