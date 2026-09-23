from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import CopilotChatRequest, CopilotChatResponse
from services.copilot import chat

router = APIRouter(tags=["Co-pilot"])


@router.post("/copilot/chat", response_model=CopilotChatResponse)
def copilot_chat(payload: CopilotChatRequest, db: Session = Depends(get_db)):
    """One co-pilot turn. Incidents come back as a draft; the client saves them via POST /incidents once confirmed."""
    history = [message.model_dump() for message in payload.messages]
    return chat(db, payload.operator_id, payload.machine_id, history)
