from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from backend.database import get_session
from backend.models import BatteryLog, Car, ChargeCycle, EVProfile
from backend.repositories import EVRepository

router = APIRouter(prefix="/ev", tags=["EV"])


class EVProfileUpdate(BaseModel):
    battery_capacity_kwh: Optional[float] = None
    battery_health_percent: Optional[float] = None


class ChargeCycleCreate(BaseModel):
    date: datetime
    start_percent: float
    end_percent: float
    kwh_charged: float
    location: str


class BatteryHealthUpdate(BaseModel):
    new_health: float
    reason: str


def _get_ev(car_id: int, session: Session):
    car = session.get(Car, car_id)
    if not car:
        raise HTTPException(404, "Car not found.")
    if not car.is_ev:
        raise HTTPException(400, "This car is not an EV.")
    repo = EVRepository(session)
    ev = repo.get_profile_by_car(car_id)
    if not ev:
        raise HTTPException(404, "EV profile not found for this car.")
    return car, ev, repo


@router.get("/", response_model=List[dict])
def list_ev_profiles(session: Session = Depends(get_session)):
    repo = EVRepository(session)
    return [p.model_dump() for p in repo.get_all_profiles()]


@router.get("/{car_id}", response_model=dict)
def get_ev_profile(car_id: int, session: Session = Depends(get_session)):
    _, ev, _ = _get_ev(car_id, session)
    return ev.model_dump()


@router.put("/{car_id}", response_model=dict)
def update_ev_profile(car_id: int, data: EVProfileUpdate,
                      session: Session = Depends(get_session)):
    _, ev, repo = _get_ev(car_id, session)
    old = ev.model_dump()
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(ev, k, v)
    repo.log("ev", car_id, "profile_updated", old_val=old, new_val=ev.model_dump())
    repo.update_profile(ev)
    session.commit()
    session.refresh(ev)
    return ev.model_dump()


@router.post("/{car_id}/charge-cycles", response_model=dict, status_code=201)
def add_charge_cycle(car_id: int, data: ChargeCycleCreate,
                     session: Session = Depends(get_session)):
    _, ev, repo = _get_ev(car_id, session)

    if not (0 <= data.start_percent <= 100):
        raise HTTPException(400, "start_percent must be between 0 and 100.")
    if not (0 <= data.end_percent <= 100):
        raise HTTPException(400, "end_percent must be between 0 and 100.")
    if data.end_percent <= data.start_percent:
        raise HTTPException(400, "end_percent must be greater than start_percent.")
    if data.kwh_charged <= 0:
        raise HTTPException(400, "kwh_charged must be positive.")

    cycle = ChargeCycle(car_id=car_id, **data.model_dump())
    repo.create_cycle(cycle)

    ev.charge_cycles += 1
    old_health = ev.battery_health_percent
    degradation = 0.05 if data.end_percent >= 90 else 0.02
    ev.battery_health_percent = max(0.0, round(ev.battery_health_percent - degradation, 2))

    battery_log = BatteryLog(car_id=car_id, old_health=old_health,
                             new_health=ev.battery_health_percent,
                             reason="Charge cycle recorded")
    repo.create_battery_log(battery_log)
    repo.update_profile(ev)
    repo.log("charge_cycle", cycle.id, "created",
             new_val={"car_id": car_id, "kwh_charged": data.kwh_charged,
                      "location": data.location})
    session.commit()
    session.refresh(cycle)
    return cycle.model_dump()


@router.get("/{car_id}/charge-cycles", response_model=List[dict])
def get_charge_cycles(car_id: int, session: Session = Depends(get_session)):
    _get_ev(car_id, session)
    repo = EVRepository(session)
    return [c.model_dump() for c in repo.get_cycles_by_car(car_id)]


@router.delete("/{car_id}/charge-cycles/{cycle_id}", status_code=204)
def delete_charge_cycle(car_id: int, cycle_id: int,
                        session: Session = Depends(get_session)):
    _get_ev(car_id, session)
    repo = EVRepository(session)
    cycle = repo.get_cycle_by_id(cycle_id)
    if not cycle or cycle.car_id != car_id:
        raise HTTPException(404, "Charge cycle not found.")
    repo.log("charge_cycle", cycle_id, "deleted", old_val=cycle.model_dump())
    repo.delete_cycle(cycle)
    session.commit()


@router.patch("/{car_id}/battery-health", response_model=dict)
def update_battery_health(car_id: int, data: BatteryHealthUpdate,
                          session: Session = Depends(get_session)):
    _, ev, repo = _get_ev(car_id, session)

    if not (0 <= data.new_health <= 100):
        raise HTTPException(400, "Battery health must be between 0 and 100.")

    old_health = ev.battery_health_percent
    ev.battery_health_percent = data.new_health

    battery_log = BatteryLog(car_id=car_id, old_health=old_health,
                             new_health=data.new_health, reason=data.reason)
    repo.create_battery_log(battery_log)
    repo.update_profile(ev)
    repo.log("ev", car_id, "battery_health_updated",
             old_val={"battery_health_percent": old_health},
             new_val={"battery_health_percent": data.new_health, "reason": data.reason})
    session.commit()
    session.refresh(ev)
    return ev.model_dump()


@router.get("/{car_id}/battery-logs", response_model=List[dict])
def get_battery_logs(car_id: int, session: Session = Depends(get_session)):
    _get_ev(car_id, session)
    repo = EVRepository(session)
    return [l.model_dump() for l in repo.get_battery_logs_by_car(car_id)]
