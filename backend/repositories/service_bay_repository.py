from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from backend.models import Car, Log, ServiceBay


class ServiceBayRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[ServiceBay]:
        return self.session.exec(select(ServiceBay)).all()

    def get_by_id(self, bay_id: int) -> Optional[ServiceBay]:
        return self.session.get(ServiceBay, bay_id)

    def get_cars_in_bay(self, bay_id: int) -> List[Car]:
        return self.session.exec(select(Car).where(Car.service_bay_id == bay_id)).all()

    def create(self, bay: ServiceBay) -> ServiceBay:
        self.session.add(bay)
        self.session.flush()
        return bay

    def update(self, bay: ServiceBay) -> ServiceBay:
        self.session.add(bay)
        self.session.flush()
        return bay

    def delete(self, bay: ServiceBay) -> None:
        self.session.delete(bay)
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
