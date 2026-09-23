from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

# ==========================================
# Shared value sets (CONTRACT.md §1). Requests must use these exact strings.
# ==========================================

SeatbeltStatus = Literal["Fastened", "Unfastened"]
TaskType = Literal["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
Weather = Literal["Sunny", "Rainy", "Cloudy", "Windy"]
OperatorSkill = Literal["Beginner", "Intermediate", "Expert"]
TaskStatus = Literal["Pending", "In Progress", "Completed"]
AlertSeverity = Literal["Low", "Medium", "High"]
PredictionSource = Literal["model", "historical", "heuristic"]


def _normalize_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("must be an ISO 8601 date-time, e.g. 2025-05-01T10:00:00") from None
    # Stored timestamps are naive local time and sorted as strings, so every value must share one format.
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed.isoformat(timespec="seconds")


Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")]
Timestamp = Annotated[str, AfterValidator(_normalize_timestamp)]
Minutes = Annotated[int, Field(ge=0, le=1440)]


class RequestModel(BaseModel):
    # Unknown fields are almost always client typos (e.g. "actual_time"), which would otherwise be silently ignored.
    model_config = ConfigDict(extra="forbid")


# ==========================================
# General Schemas
# ==========================================


class HealthCheckResponse(BaseModel):
    status: str
    database: str
    tables_ready: bool


# ==========================================
# Dashboard Schemas
# ==========================================


class TaskResponse(BaseModel):
    id: int
    machine_id: str
    operator_id: str
    task_type: str
    status: str
    scheduled_time: Optional[str] = None
    estimated_time_min: Optional[int] = None
    actual_time_min: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TaskPatchRequest(RequestModel):
    status: Optional[TaskStatus] = None
    # Sending null explicitly clears a recorded time (e.g. when a task is reopened).
    actual_time_min: Optional[Minutes] = None


# ==========================================
# Safety Schemas
# ==========================================


class AlertResponse(BaseModel):
    id: int
    machine_id: str
    operator_id: str
    type: str
    severity: Optional[str] = None
    message: Optional[str] = None
    timestamp: str

    model_config = ConfigDict(from_attributes=True)


class SafetyCheckRequest(RequestModel):
    machine_id: Identifier
    operator_id: Identifier
    seatbelt_status: Optional[SeatbeltStatus] = None
    idling_time_min: Optional[Minutes] = None
    timestamp: Timestamp


class ProximityRequest(RequestModel):
    machine_id: Identifier
    distance_m: float = Field(ge=0, le=1000)
    timestamp: Timestamp


class ProximityResponse(BaseModel):
    triggered: bool
    severity: str
    message: str


# ==========================================
# Incidents Schemas
# ==========================================


class IncidentCreateRequest(RequestModel):
    machine_id: Identifier
    operator_id: Identifier
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=2000)]
    severity: Optional[AlertSeverity] = None
    timestamp: Timestamp


class IncidentResponse(BaseModel):
    id: int
    machine_id: str
    operator_id: str
    description: str
    severity: Optional[str] = None
    timestamp: str

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Anomaly Detection Schemas
# ==========================================


class AnomalyResponse(BaseModel):
    machine_id: str
    operator_id: str
    type: str
    detail: str
    timestamp: str


# ==========================================
# Prediction Schemas
# ==========================================


class PredictTaskTimeRequest(RequestModel):
    task_type: TaskType
    weather: Weather
    operator_skill: OperatorSkill
    machine_age_yrs: int = Field(ge=0, le=60)


class PredictTaskTimeResponse(BaseModel):
    predicted_minutes: int
    # "model" = trained regressor; the other two mean the model was unavailable.
    source: PredictionSource


# ==========================================
# Training Hub Schemas
# ==========================================


class TrainingModuleResponse(BaseModel):
    id: int
    title: str
    format: Optional[str] = None
    duration_min: Optional[int] = None
    completed: int

    model_config = ConfigDict(from_attributes=True)


class TrainingModulePatchRequest(RequestModel):
    completed: Literal[0, 1]
