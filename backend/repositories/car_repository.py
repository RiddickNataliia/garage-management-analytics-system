from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from backend.models import Car, EVProfile, Log, Repair, ServiceBay


class CarRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Car]:
        return self.session.exec(select(Car)).all()

    def get_by_id(self, car_id: int) -> Optional[Car]:
        return self.session.get(Car, car_id)

    def get_by_plate(self, plate: str) -> Optional[Car]:
        return self.session.exec(select(Car).where(Car.license_plate == plate)).first()

    def create(self, car: Car) -> Car:
        self.session.add(car)
        self.session.flush()
        return car

    def update(self, car: Car) -> Car:
        self.session.add(car)
        self.session.flush()
        return car

    def delete(self, car: Car) -> None:
        self.session.delete(car)
        self.session.flush()

    def get_warning_exists(self, car_id: int) -> bool:
        existing = self.session.exec(
            select(Repair).where(
                Repair.car_id == car_id,
                Repair.status == "Warning",
                Repair.repair_type == "Maintenance threshold exceeded",
            )
        ).first()
        return existing is not None

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
