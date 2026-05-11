from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from backend.models import Log, Repair


class RepairRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Repair]:
        return self.session.exec(select(Repair)).all()

    def get_by_id(self, repair_id: int) -> Optional[Repair]:
        return self.session.get(Repair, repair_id)

    def get_warnings(self) -> List[Repair]:
        return self.session.exec(select(Repair).where(Repair.status == "Warning")).all()

    def get_by_car(self, car_id: int) -> List[Repair]:
        return self.session.exec(select(Repair).where(Repair.car_id == car_id)).all()

    def create(self, repair: Repair) -> Repair:
        self.session.add(repair)
        self.session.flush()
        return repair

    def update(self, repair: Repair) -> Repair:
        self.session.add(repair)
        self.session.flush()
        return repair

    def delete(self, repair: Repair) -> None:
        self.session.delete(repair)
        self.session.flush()

    def log(self, entity_type: str, entity_id: int, action: str,
            old_val=None, new_val=None) -> None:
        log = Log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=json.dumps(old_val) if old_val is not None else None,
            new_value=json.dumps(new_val) if new_val is not None else None,
        )
        self.session.add(log)
