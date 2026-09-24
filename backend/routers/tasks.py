import logging

import models
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import TaskPatchRequest, TaskResponse
from services.events import publish_event
from sqlalchemy.orm import Session

router = APIRouter(tags=["Dashboard"])
logger = logging.getLogger(__name__)


@router.get("/tasks/today", response_model=list[TaskResponse])
def get_tasks_today(db: Session = Depends(get_db)):
    return db.query(models.Task).order_by(models.Task.id.asc()).all()


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, payload: TaskPatchRequest, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.status is not None:
        task.status = payload.status
    if "actual_time_min" in payload.model_fields_set:
        task.actual_time_min = payload.actual_time_min

    db.commit()
    db.refresh(task)
    logger.info("Task %s updated: %s", task_id, payload.model_dump(exclude_unset=True))
    response = TaskResponse.model_validate(task)
    publish_event("task.updated", response)
    return response
