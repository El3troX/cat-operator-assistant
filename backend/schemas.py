from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ==========================================
# Shared Enums (from CONTRACT.md Section 1)
# ==========================================


class SeatbeltStatus(str, Enum):
    FASTENED = "Fastened"
    UNFASTENED = "Unfastened"


class TaskType(str, Enum):
    EARTH_EXCAVATION = "Earth Excavation"
    TRENCHING = "Trenching"
    MATERIAL_LOADING = "Material Loading"
    GRADING = "Grading"
    DEMOLITION = "Demolition"


class Weather(str, Enum):
    SUNNY = "Sunny"
    RAINY = "Rainy"
    CLOUDY = "Cloudy"
    WINDY = "Windy"


class OperatorSkill(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    EXPERT = "Expert"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class AlertType(str, Enum):
    SEATBELT = "Seatbelt"
    PROXIMITY = "Proximity"
    IDLING = "Idling"
    ANOMALY = "Anomaly"


class AlertSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


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


class TaskPatchRequest(BaseModel):
    status: Optional[str] = None
    actual_time_min: Optional[int] = None


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


class SafetyCheckRequest(BaseModel):
    machine_id: str
    operator_id: str
    seatbelt_status: Optional[str] = None
    idling_time_min: Optional[int] = None
    timestamp: str


class ProximityRequest(BaseModel):
    machine_id: str
    distance_m: float
    timestamp: str


class ProximityResponse(BaseModel):
    triggered: bool
    severity: str
    message: str


# ==========================================
# Incidents Schemas
# ==========================================


class IncidentCreateRequest(BaseModel):
    machine_id: str
    operator_id: str
    description: str
    severity: Optional[str] = None
    timestamp: str


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


class PredictTaskTimeRequest(BaseModel):
    task_type: str
    weather: str
    operator_skill: str
    machine_age_yrs: int


class PredictTaskTimeResponse(BaseModel):
    predicted_minutes: int


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


class TrainingModulePatchRequest(BaseModel):
    completed: int
