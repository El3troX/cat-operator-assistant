import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import AlertResponse, ProximityRequest, ProximityResponse, SafetyCheckRequest
from services.rules import evaluate_cab_reading, evaluate_proximity

router = APIRouter(tags=["Safety"])
logger = logging.getLogger(__name__)


@router.get("/safety/alerts", response_model=list[AlertResponse])
def get_safety_alerts(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Alert)
    if machine_id:
        query = query.filter(models.Alert.machine_id == machine_id)
    return query.order_by(models.Alert.timestamp.desc(), models.Alert.id.desc()).all()


@router.post("/safety/check", response_model=list[AlertResponse])
def safety_check(payload: SafetyCheckRequest, db: Session = Depends(get_db)):
    alerts = [
        models.Alert(
            machine_id=payload.machine_id,
            operator_id=payload.operator_id,
            type=violation.type,
            severity=violation.severity,
            message=violation.message,
            timestamp=payload.timestamp,
        )
        for violation in evaluate_cab_reading(payload.seatbelt_status, payload.idling_time_min)
    ]
    if alerts:
        db.add_all(alerts)
        db.commit()
        for alert in alerts:
            db.refresh(alert)
        logger.info(
            "Safety check on %s/%s raised: %s",
            payload.machine_id,
            payload.operator_id,
            ", ".join(alert.type for alert in alerts),
        )
    return alerts


@router.post("/safety/proximity", response_model=ProximityResponse)
def safety_proximity(payload: ProximityRequest, db: Session = Depends(get_db)):
    violation = evaluate_proximity(payload.distance_m)
    if violation is None:
        return ProximityResponse(triggered=False, severity="Low", message="Safe distance maintained")

    db.add(
        models.Alert(
            machine_id=payload.machine_id,
            operator_id="SYSTEM",
            type=violation.type,
            severity=violation.severity,
            message=violation.message,
            timestamp=payload.timestamp,
        )
    )
    db.commit()
    logger.info("Proximity alert on %s: object at %.1f m", payload.machine_id, payload.distance_m)
    return ProximityResponse(triggered=True, severity=violation.severity, message=violation.message)
