from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import engine, get_db
from schemas import HealthCheckResponse

router = APIRouter(tags=["General"])

REQUIRED_TABLES = {"operation_log", "task_time_data", "tasks", "incidents", "alerts", "training_modules"}


@router.get("/")
def root():
    return {
        "message": "Smart Operator Assistant for CAT Machinery API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    existing_tables = set(inspect(engine).get_table_names())
    return HealthCheckResponse(status="ok", database="connected", tables_ready=REQUIRED_TABLES <= existing_tables)
