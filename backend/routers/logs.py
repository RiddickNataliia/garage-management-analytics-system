from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.database import get_session
from backend.repositories import LogRepository

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=List[dict])
def list_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    session: Session = Depends(get_session),
):
    repo = LogRepository(session)
    logs = repo.get_all(entity_type=entity_type, entity_id=entity_id, action=action)
    return [log.model_dump() for log in logs]
