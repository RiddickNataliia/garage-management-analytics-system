from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from backend.models import BatteryLog, ChargeCycle, EVProfile, Log


class EVRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_profiles(self) -> List[EVProfile]:
        return self.session.exec(select(EVProfile)).all()

    def get_profile_by_car(self, car_id: int) -> Optional[EVProfile]:
        return self.session.exec(select(EVProfile).where(EVProfile.car_id == car_id)).first()

    def create_profile(self, profile: EVProfile) -> EVProfile:
        self.session.add(profile)
        self.session.flush()
        return profile

    def update_profile(self, profile: EVProfile) -> EVProfile:
        self.session.add(profile)
        self.session.flush()
        return profile

    # ── Charge cycles ─────────────────────────────────────────────────────────

    def get_cycles_by_car(self, car_id: int) -> List[ChargeCycle]:
        return self.session.exec(select(ChargeCycle).where(ChargeCycle.car_id == car_id)).all()

    def get_cycle_by_id(self, cycle_id: int) -> Optional[ChargeCycle]:
        return self.session.get(ChargeCycle, cycle_id)

    def create_cycle(self, cycle: ChargeCycle) -> ChargeCycle:
        self.session.add(cycle)
        self.session.flush()
        return cycle

    def delete_cycle(self, cycle: ChargeCycle) -> None:
        self.session.delete(cycle)
        self.session.flush()

    # ── Battery logs ──────────────────────────────────────────────────────────

    def get_battery_logs_by_car(self, car_id: int) -> List[BatteryLog]:
        return self.session.exec(select(BatteryLog).where(BatteryLog.car_id == car_id)).all()

    def create_battery_log(self, log: BatteryLog) -> BatteryLog:
        self.session.add(log)
        self.session.flush()
        return log

    # ── General log ───────────────────────────────────────────────────────────

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
