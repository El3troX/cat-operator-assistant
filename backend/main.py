from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from schemas import AlertResponse, HealthCheckResponse, TaskResponse


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


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Smart Operator Assistant for CAT Machinery API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["General"])
def health_check(db: Session = Depends(get_db)):
    # Verify DB connectivity
    db.execute(text("SELECT 1"))

    # Verify table creation
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
