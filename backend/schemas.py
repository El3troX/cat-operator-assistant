from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


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


class HealthCheckResponse(BaseModel):
    status: str
    database: str
    tables_ready: bool


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


class AlertResponse(BaseModel):
    id: int
    machine_id: str
    operator_id: str
    type: str
    severity: Optional[str] = None
    message: Optional[str] = None
    timestamp: str

    model_config = ConfigDict(from_attributes=True)
