import logging
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

import models
from schemas import PredictTaskTimeRequest, PredictTaskTimeResponse

# The ml package lives at the repo root, beside backend/.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

BASELINE_MIN = {
    "Earth Excavation": 60,
    "Trenching": 45,
    "Material Loading": 30,
    "Grading": 35,
    "Demolition": 90,
}
WEATHER_FACTOR = {"Sunny": 0.95, "Cloudy": 1.0, "Windy": 1.05, "Rainy": 1.18}
SKILL_FACTOR = {"Expert": 0.85, "Intermediate": 1.0, "Beginner": 1.25}
AGE_FACTOR_PER_YEAR = 0.015
DEFAULT_TASK_MIN = 50


def warm_up() -> None:
    """Load the model and its error bands at startup; otherwise the first prediction pays several seconds."""
    try:
        from ml.predict import get_model, get_residual_band

        get_model()
        low, high = get_residual_band()
        logger.info("Task-time model loaded (likely range %+.1f to %+.1f min around each estimate)", low, high)
    except Exception as exc:
        logger.warning("Task-time model unavailable, predictions will use fallback estimates: %s", exc)


def estimate_task_time(req: PredictTaskTimeRequest, db: Session) -> PredictTaskTimeResponse:
    """Prediction with the method that produced it: "model", "historical" or "heuristic"."""
    try:
        from ml.predict import explain

        result = explain(
            task_type=req.task_type,
            weather=req.weather,
            operator_skill=req.operator_skill,
            machine_age_yrs=req.machine_age_yrs,
        )
        return PredictTaskTimeResponse(
            predicted_minutes=round(result["minutes"]),
            source="model",
            p10=round(result["p10"]),
            p90=round(result["p90"]),
            drivers=result["drivers"],
        )
    except Exception as exc:
        logger.warning("Task-time model unavailable, using fallback estimate: %s", exc)

    historical = _historical_estimate(req, db)
    if historical is not None:
        return PredictTaskTimeResponse(predicted_minutes=round(historical), source="historical")
    return PredictTaskTimeResponse(predicted_minutes=round(_heuristic_estimate(req, db)), source="heuristic")


def _recorded_minutes(row: models.TaskTimeData) -> int:
    return row.actual_time_min or row.estimated_time_min or DEFAULT_TASK_MIN


def _historical_estimate(req: PredictTaskTimeRequest, db: Session) -> Optional[float]:
    """Average of past jobs with the same task, weather and skill, weighted toward similar machine ages."""
    matches = (
        db.query(models.TaskTimeData)
        .filter(
            models.TaskTimeData.task_type == req.task_type,
            models.TaskTimeData.weather == req.weather,
            models.TaskTimeData.operator_skill == req.operator_skill,
        )
        .all()
    )
    if not matches:
        return None
    weights = [1.0 / (1.0 + abs((row.machine_age_yrs or 0) - req.machine_age_yrs)) for row in matches]
    return sum(_recorded_minutes(row) * w for row, w in zip(matches, weights)) / sum(weights)


def _heuristic_estimate(req: PredictTaskTimeRequest, db: Session) -> float:
    same_type = db.query(models.TaskTimeData).filter(models.TaskTimeData.task_type == req.task_type).all()
    if same_type:
        base = sum(_recorded_minutes(row) for row in same_type) / len(same_type)
    else:
        base = BASELINE_MIN.get(req.task_type, 45)
    return (
        base
        * WEATHER_FACTOR.get(req.weather, 1.0)
        * SKILL_FACTOR.get(req.operator_skill, 1.0)
        * (1.0 + req.machine_age_yrs * AGE_FACTOR_PER_YEAR)
    )
