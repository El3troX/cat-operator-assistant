import models
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import TrainingModulePatchRequest, TrainingModuleResponse
from services.events import publish_event
from sqlalchemy.orm import Session

router = APIRouter(tags=["Training Hub"])


@router.get("/training/modules", response_model=list[TrainingModuleResponse])
def get_training_modules(db: Session = Depends(get_db)):
    return db.query(models.TrainingModule).order_by(models.TrainingModule.id.asc()).all()


@router.patch("/training/modules/{module_id}", response_model=TrainingModuleResponse)
def patch_training_module(module_id: int, payload: TrainingModulePatchRequest, db: Session = Depends(get_db)):
    module = db.get(models.TrainingModule, module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    module.completed = payload.completed
    db.commit()
    db.refresh(module)
    response = TrainingModuleResponse.model_validate(module)
    publish_event("training.updated", response)
    return response
