from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import PredictTaskTimeRequest, PredictTaskTimeResponse
from services.task_time import estimate_task_time

router = APIRouter(tags=["Task Time Prediction"])


@router.post("/predict/task-time", response_model=PredictTaskTimeResponse)
def predict_task_time(payload: PredictTaskTimeRequest, db: Session = Depends(get_db)):
    minutes, source = estimate_task_time(payload, db)
    return PredictTaskTimeResponse(predicted_minutes=minutes, source=source)
