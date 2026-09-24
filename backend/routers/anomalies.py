from typing import Optional

import models
from database import get_db
from fastapi import APIRouter, Depends, Query
from schemas import AnomalyResponse
from services.rules import IDLE_THRESHOLD_MIN, summarize_log_reading
from sqlalchemy.orm import Session

router = APIRouter(tags=["Anomaly Detection"])

ANOMALY_LIMIT = 100


@router.get("/anomalies", response_model=list[AnomalyResponse])
def get_anomalies(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    log = models.OperationLog
    query = db.query(log)
    if machine_id:
        query = query.filter(log.machine_id == machine_id)

    flagged = (
        query.filter(
            (log.idling_time_min > IDLE_THRESHOLD_MIN)
            | (log.seatbelt_status == "Unfastened")
            | (log.safety_alert_triggered == 1)
        )
        .order_by(log.timestamp.desc(), log.id.desc())
        .limit(ANOMALY_LIMIT)
        .all()
    )

    anomalies = []
    for reading in flagged:
        violation = summarize_log_reading(
            reading.seatbelt_status, reading.idling_time_min, reading.safety_alert_triggered == 1
        )
        if violation:
            anomalies.append(
                AnomalyResponse(
                    machine_id=reading.machine_id,
                    operator_id=reading.operator_id,
                    type=violation.type,
                    detail=violation.message,
                    timestamp=reading.timestamp,
                )
            )
    return anomalies
