import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import IncidentCreateRequest, IncidentResponse

router = APIRouter(tags=["Incidents"])
logger = logging.getLogger(__name__)


@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreateRequest, db: Session = Depends(get_db)):
    incident = models.Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Incident %s logged on %s (%s)", incident.id, incident.machine_id, incident.severity)
    return incident


@router.get("/incidents", response_model=list[IncidentResponse])
def get_incidents(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Incident)
    if machine_id:
        query = query.filter(models.Incident.machine_id == machine_id)
    return query.order_by(models.Incident.timestamp.desc(), models.Incident.id.desc()).all()
