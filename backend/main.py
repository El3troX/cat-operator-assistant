from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from schemas import (
    AlertResponse,
    AnomalyResponse,
    HealthCheckResponse,
    IncidentCreateRequest,
    IncidentResponse,
    PredictTaskTimeRequest,
    PredictTaskTimeResponse,
    ProximityRequest,
    ProximityResponse,
    SafetyCheckRequest,
    TaskPatchRequest,
    TaskResponse,
    TrainingModulePatchRequest,
    TrainingModuleResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart Operator Assistant for CAT Machinery",
    description="Backend API for CAT Machinery Smart Operator Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# General Endpoints
# ==========================================


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Smart Operator Assistant for CAT Machinery API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["General"])
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        "operation_log",
        "task_time_data",
        "tasks",
        "incidents",
        "alerts",
        "training_modules",
    }
    all_present = required_tables.issubset(existing_tables)

    return HealthCheckResponse(
        status="ok",
        database="connected",
        tables_ready=all_present,
    )


# ==========================================
# Dashboard Endpoints
# ==========================================


@app.get("/tasks/today", response_model=List[TaskResponse], tags=["Dashboard"])
def get_tasks_today(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).order_by(models.Task.id.asc()).all()
    return tasks


@app.patch("/tasks/{id}", response_model=TaskResponse, tags=["Dashboard"])
def patch_task(id: int, payload: TaskPatchRequest, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.status is not None:
        task.status = payload.status
    if payload.actual_time_min is not None:
        task.actual_time_min = payload.actual_time_min

    db.commit()
    db.refresh(task)
    return task


# ==========================================
# Safety Endpoints
# ==========================================


@app.get("/safety/alerts", response_model=List[AlertResponse], tags=["Safety"])
def get_safety_alerts(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Alert)
    if machine_id:
        query = query.filter(models.Alert.machine_id == machine_id)
    alerts = query.order_by(models.Alert.timestamp.desc(), models.Alert.id.desc()).all()
    return alerts


@app.post("/safety/check", response_model=List[AlertResponse], tags=["Safety"])
def safety_check(payload: SafetyCheckRequest, db: Session = Depends(get_db)):
    generated_alerts = []

    # Rule 1: Seatbelt check
    if payload.seatbelt_status and payload.seatbelt_status.strip().lower() == "unfastened":
        alert_seatbelt = models.Alert(
            machine_id=payload.machine_id,
            operator_id=payload.operator_id,
            type="Seatbelt",
            severity="High",
            message="Seatbelt unfastened during operation",
            timestamp=payload.timestamp,
        )
        db.add(alert_seatbelt)
        generated_alerts.append(alert_seatbelt)

    # Rule 2: Excessive Idling (> 45 min)
    if payload.idling_time_min is not None and payload.idling_time_min > 45:
        alert_idling = models.Alert(
            machine_id=payload.machine_id,
            operator_id=payload.operator_id,
            type="Idling",
            severity="Medium",
            message=f"Idling time {payload.idling_time_min}min exceeds threshold (45min)",
            timestamp=payload.timestamp,
        )
        db.add(alert_idling)
        generated_alerts.append(alert_idling)

    if generated_alerts:
        db.commit()
        for a in generated_alerts:
            db.refresh(a)

    return generated_alerts


@app.post("/safety/proximity", response_model=ProximityResponse, tags=["Safety"])
def safety_proximity(payload: ProximityRequest, db: Session = Depends(get_db)):
    # Proximity threshold: 2.0 meters
    if payload.distance_m <= 2.0:
        alert = models.Alert(
            machine_id=payload.machine_id,
            operator_id="SYSTEM",
            type="Proximity",
            severity="High",
            message="Object within 2m of machine",
            timestamp=payload.timestamp,
        )
        db.add(alert)
        db.commit()
        return ProximityResponse(
            triggered=True,
            severity="High",
            message="Object within 2m of machine",
        )

    return ProximityResponse(
        triggered=False,
        severity="Low",
        message="Safe distance maintained",
    )


# ==========================================
# Incidents Endpoints
# ==========================================


@app.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED, tags=["Incidents"])
def create_incident(payload: IncidentCreateRequest, db: Session = Depends(get_db)):
    incident = models.Incident(
        machine_id=payload.machine_id,
        operator_id=payload.operator_id,
        description=payload.description,
        severity=payload.severity,
        timestamp=payload.timestamp,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
def get_incidents(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Incident)
    if machine_id:
        query = query.filter(models.Incident.machine_id == machine_id)
    incidents = query.order_by(models.Incident.timestamp.desc(), models.Incident.id.desc()).all()
    return incidents


# ==========================================
# Anomaly Detection Endpoints
# ==========================================


@app.get("/anomalies", response_model=List[AnomalyResponse], tags=["Anomaly Detection"])
def get_anomalies(
    machine_id: Optional[str] = Query(default=None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    query = db.query(models.OperationLog)
    if machine_id:
        query = query.filter(models.OperationLog.machine_id == machine_id)

    # Filter operations where idling > 45 or seatbelt unfastened or alert triggered
    logs = (
        query.filter(
            (models.OperationLog.idling_time_min > 45)
            | (models.OperationLog.seatbelt_status == "Unfastened")
            | (models.OperationLog.safety_alert_triggered == 1)
        )
        .order_by(models.OperationLog.timestamp.desc(), models.OperationLog.id.desc())
        .limit(100)
        .all()
    )

    anomalies = []
    for log in logs:
        if log.idling_time_min and log.idling_time_min > 45:
            anomalies.append(
                AnomalyResponse(
                    machine_id=log.machine_id,
                    operator_id=log.operator_id,
                    type="Idling",
                    detail=f"Idling time {log.idling_time_min}min exceeds threshold (45min)",
                    timestamp=log.timestamp,
                )
            )
        elif log.seatbelt_status == "Unfastened":
            anomalies.append(
                AnomalyResponse(
                    machine_id=log.machine_id,
                    operator_id=log.operator_id,
                    type="Seatbelt",
                    detail="Seatbelt unfastened during operation",
                    timestamp=log.timestamp,
                )
            )
        elif log.safety_alert_triggered == 1:
            anomalies.append(
                AnomalyResponse(
                    machine_id=log.machine_id,
                    operator_id=log.operator_id,
                    type="Safety",
                    detail="Safety alert triggered on machine",
                    timestamp=log.timestamp,
                )
            )

    return anomalies


# ==========================================
# Task Time Prediction Endpoints
# ==========================================


@app.post("/predict/task-time", response_model=PredictTaskTimeResponse, tags=["Task Time Prediction"])
def predict_task_time(payload: PredictTaskTimeRequest, db: Session = Depends(get_db)):
    # 1. Look for matching records in task_time_data
    exact_matches = (
        db.query(models.TaskTimeData)
        .filter(
            models.TaskTimeData.task_type == payload.task_type,
            models.TaskTimeData.weather == payload.weather,
            models.TaskTimeData.operator_skill == payload.operator_skill,
        )
        .all()
    )

    if exact_matches:
        # Distance-weighted average based on machine age
        weights = [1.0 / (1.0 + abs((r.machine_age_yrs or 0) - payload.machine_age_yrs)) for r in exact_matches]
        total_weight = sum(weights)
        if total_weight > 0:
            predicted = sum((r.actual_time_min or r.estimated_time_min or 50) * w for r, w in zip(exact_matches, weights)) / total_weight
            return PredictTaskTimeResponse(predicted_minutes=int(round(predicted)))

    # 2. Broader match on task_type with heuristic coefficients
    type_matches = db.query(models.TaskTimeData).filter(models.TaskTimeData.task_type == payload.task_type).all()
    if type_matches:
        base_time = sum(r.actual_time_min or r.estimated_time_min or 50 for r in type_matches) / len(type_matches)
    else:
        # Default baselines per TaskType
        baselines = {
            "Earth Excavation": 60,
            "Trenching": 45,
            "Material Loading": 30,
            "Grading": 35,
            "Demolition": 90,
        }
        base_time = baselines.get(payload.task_type, 45)

    weather_multipliers = {
        "Sunny": 0.95,
        "Cloudy": 1.0,
        "Windy": 1.05,
        "Rainy": 1.18,
    }
    skill_multipliers = {
        "Expert": 0.85,
        "Intermediate": 1.0,
        "Beginner": 1.25,
    }

    w_mult = weather_multipliers.get(payload.weather, 1.0)
    s_mult = skill_multipliers.get(payload.operator_skill, 1.0)
    age_mult = 1.0 + (payload.machine_age_yrs * 0.015)

    predicted = base_time * w_mult * s_mult * age_mult
    return PredictTaskTimeResponse(predicted_minutes=int(round(predicted)))


# ==========================================
# Training Hub Endpoints
# ==========================================


@app.get("/training/modules", response_model=List[TrainingModuleResponse], tags=["Training Hub"])
def get_training_modules(db: Session = Depends(get_db)):
    modules = db.query(models.TrainingModule).order_by(models.TrainingModule.id.asc()).all()
    return modules


@app.patch("/training/modules/{id}", response_model=TrainingModuleResponse, tags=["Training Hub"])
def patch_training_module(id: int, payload: TrainingModulePatchRequest, db: Session = Depends(get_db)):
    module = db.query(models.TrainingModule).filter(models.TrainingModule.id == id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    module.completed = payload.completed
    db.commit()
    db.refresh(module)
    return module
