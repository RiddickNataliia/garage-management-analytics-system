from __future__ import annotations

from typing import List, Optional

from sqlmodel import Session, select

from backend.models import Log


class LogRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self, entity_type: Optional[str] = None,
                entity_id: Optional[int] = None,
                action: Optional[str] = None) -> List[Log]:
        logs = self.session.exec(select(Log).order_by(Log.timestamp.desc())).all()
        result = []
        for log in logs:
            if entity_type and log.entity_type != entity_type:
                continue
            if entity_id and log.entity_id != entity_id:
                continue
            if action and action.lower() not in log.action.lower():
                continue
            result.append(log)
        return result
