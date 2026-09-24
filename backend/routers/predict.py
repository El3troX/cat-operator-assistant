from database import get_db
from fastapi import APIRouter, Depends
from schemas import PredictTaskTimeRequest, PredictTaskTimeResponse
from services.task_time import estimate_task_time
from sqlalchemy.orm import Session

router = APIRouter(tags=["Task Time Prediction"])


@router.post("/predict/task-time", response_model=PredictTaskTimeResponse)
def predict_task_time(payload: PredictTaskTimeRequest, db: Session = Depends(get_db)):
    return estimate_task_time(payload, db)
