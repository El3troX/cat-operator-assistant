from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import OperatorScoreResponse
from services.scoring import operator_scores

router = APIRouter(tags=["Coaching"])


@router.get("/scores/operators", response_model=list[OperatorScoreResponse])
def get_operator_scores(
    operator_id: Optional[str] = Query(default=None, description="Optional operator ID filter"),
    db: Session = Depends(get_db),
):
    """Safety score per operator (lowest first), with the factors behind it and training it assigns."""
    return operator_scores(db, operator_id)
