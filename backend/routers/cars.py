from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from backend.database import get_session
from backend.models import Car, EVProfile, Repair, ServiceBay, BatteryLog, ChargeCycle
from backend.repositories import CarRepository

router = APIRouter(prefix="/cars", tags=["Cars"])


class CarCreate(BaseModel):
    license_plate: str
    brand: str
    model: str
    owner_name: str
    kilometrage: float = 0.0
    maintenance_threshold: float = 150000.0
    is_ev: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        if self.kilometrage < 0:
            raise ValueError("Kilometrage cannot be negative.")
        if self.maintenance_threshold < 0:
            raise ValueError("Maintenance threshold cannot be negative.")


class CarUpdate(BaseModel):
    license_plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    owner_name: Optional[str] = None
    kilometrage: Optional[float] = None
    maintenance_threshold: Optional[float] = None
    is_ev: Optional[bool] = None
    service_bay_id: Optional[int] = None


class KilometrageUpdate(BaseModel):
    kilometrage: float


def _check_maintenance(car: Car, repo: CarRepository):
    """Create a Warning repair if kilometrage exceeds threshold and none exists yet."""
    if car.kilometrage <= car.maintenance_threshold:
        return
    if repo.get_warning_exists(car.id):
        return

    repair = Repair(
        car_id=car.id,
        repair_type="Maintenance threshold exceeded",
        mechanic="System",
        status="Warning",
        created_at=datetime.utcnow(),
    )
    repo.session.add(repair)
    repo.session.flush()

    repo.log("car", car.id, "maintenance_warning_created",
             old_val={"kilometrage": car.kilometrage,
                      "maintenance_threshold": car.maintenance_threshold},
             new_val={"kilometrage": car.kilometrage,
                      "repair_id": repair.id, "status": "Warning"})


@router.get("/", response_model=List[dict])
def list_cars(session: Session = Depends(get_session)):
    repo = CarRepository(session)
    cars = repo.get_all()
    result = []
    for car in cars:
        d = car.model_dump()
        d["warning"] = car.kilometrage > car.maintenance_threshold
        result.append(d)
    return result


@router.post("/", response_model=dict, status_code=201)
def create_car(data: CarCreate, session: Session = Depends(get_session)):
    repo = CarRepository(session)

    if repo.get_by_plate(data.license_plate):
        raise HTTPException(400, f"License plate '{data.license_plate}' already exists.")

    car = Car(**data.model_dump())
    repo.create(car)
    repo.log("car", car.id, "created", new_val=data.model_dump())

    if data.is_ev:
        ev = EVProfile(car_id=car.id, battery_capacity_kwh=60.0,
                       battery_health_percent=100.0, charge_cycles=0)
        session.add(ev)

    _check_maintenance(car, repo)
    session.commit()
    session.refresh(car)
    return car.model_dump()


@router.get("/{car_id}", response_model=dict)
def get_car(car_id: int, session: Session = Depends(get_session)):
    repo = CarRepository(session)
    car = repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")
    return car.model_dump()


@router.put("/{car_id}", response_model=dict)
def update_car(car_id: int, data: CarUpdate, session: Session = Depends(get_session)):
    repo = CarRepository(session)
    car = repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")

    old = car.model_dump()
    update_data = data.model_dump(exclude_none=True)

    if "license_plate" in update_data:
        existing = repo.get_by_plate(update_data["license_plate"])
        if existing and existing.id != car_id:
            raise HTTPException(400, f"License plate '{update_data['license_plate']}' already in use.")

    for k, v in update_data.items():
        setattr(car, k, v)

    repo.log("car", car_id, "updated", old_val=old, new_val=car.model_dump())
    _check_maintenance(car, repo)
    repo.update(car)
    session.commit()
    session.refresh(car)
    return car.model_dump()


@router.patch("/{car_id}/kilometrage", response_model=dict)
def update_kilometrage(car_id: int, data: KilometrageUpdate,
                       session: Session = Depends(get_session)):
    repo = CarRepository(session)
    car = repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")
    if data.kilometrage < 0:
        raise HTTPException(400, "Kilometrage cannot be negative.")
    if data.kilometrage < car.kilometrage:
        raise HTTPException(400, "New kilometrage cannot be less than current kilometrage.")

    old_km = car.kilometrage
    car.kilometrage = data.kilometrage

    repo.log("car", car_id, "kilometrage_updated",
             old_val={"kilometrage": old_km},
             new_val={"kilometrage": data.kilometrage})

    _check_maintenance(car, repo)
    repo.update(car)
    session.commit()
    session.refresh(car)
    result = car.model_dump()
    result["warning"] = car.kilometrage > car.maintenance_threshold
    return result


@router.patch("/{car_id}/assign-bay", response_model=dict)
def assign_bay(car_id: int, bay_id: Optional[int] = None,
               session: Session = Depends(get_session)):
    repo = CarRepository(session)
    car = repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")

    if bay_id is not None and not session.get(ServiceBay, bay_id):
        raise HTTPException(404, "Service bay not found.")

    old_bay = car.service_bay_id
    car.service_bay_id = bay_id
    repo.log("car", car_id, "bay_assigned",
             old_val={"service_bay_id": old_bay},
             new_val={"service_bay_id": bay_id})
    repo.update(car)
    session.commit()
    session.refresh(car)
    return car.model_dump()


@router.delete("/{car_id}", status_code=204)
def delete_car(car_id: int, session: Session = Depends(get_session)):
    repo = CarRepository(session)
    car = repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")

    # Delete related records first (cascade delete)
    from sqlmodel import delete as sql_delete
    
    # Delete battery logs
    session.exec(sql_delete(BatteryLog).where(BatteryLog.car_id == car_id))
    
    # Delete charge cycles
    session.exec(sql_delete(ChargeCycle).where(ChargeCycle.car_id == car_id))
    
    # Delete EV profile
    session.exec(sql_delete(EVProfile).where(EVProfile.car_id == car_id))
    
    # Delete repairs
    session.exec(sql_delete(Repair).where(Repair.car_id == car_id))
    
    # Log and delete the car
    repo.log("car", car_id, "deleted", old_val=car.model_dump())
    repo.delete(car)
    session.commit()
