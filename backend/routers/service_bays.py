from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import Car, Repair, ServiceBay
from backend.repositories import CarRepository, ServiceBayRepository

router = APIRouter(prefix="/service-bays", tags=["Service Bays"])

VALID_BAY_TYPES = {"General", "EV", "Heavy", "Inspection"}


class BayCreate(BaseModel):
    name: str
    bay_type: str = "General"
    is_available: bool = True
    notes: Optional[str] = None


class BayUpdate(BaseModel):
    name: Optional[str] = None
    bay_type: Optional[str] = None
    is_available: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/", response_model=List[dict])
def list_bays(session: Session = Depends(get_session)):
    repo = ServiceBayRepository(session)
    return [b.model_dump() for b in repo.get_all()]


@router.post("/", response_model=dict, status_code=201)
def create_bay(data: BayCreate, session: Session = Depends(get_session)):
    repo = ServiceBayRepository(session)
    if data.bay_type not in VALID_BAY_TYPES:
        raise HTTPException(400, f"Invalid bay type. Must be one of: {', '.join(VALID_BAY_TYPES)}")

    bay = ServiceBay(**data.model_dump())
    repo.create(bay)
    repo.log("service_bay", bay.id, "created", new_val=data.model_dump())
    session.commit()
    session.refresh(bay)
    return bay.model_dump()


@router.get("/{bay_id}", response_model=dict)
def get_bay(bay_id: int, session: Session = Depends(get_session)):
    repo = ServiceBayRepository(session)
    bay = repo.get_by_id(bay_id)
    if not bay:
        raise HTTPException(404, "Service bay not found.")
    return bay.model_dump()


@router.put("/{bay_id}", response_model=dict)
def update_bay(bay_id: int, data: BayUpdate, session: Session = Depends(get_session)):
    repo = ServiceBayRepository(session)
    bay = repo.get_by_id(bay_id)
    if not bay:
        raise HTTPException(404, "Service bay not found.")
    if data.bay_type and data.bay_type not in VALID_BAY_TYPES:
        raise HTTPException(400, f"Invalid bay type. Must be one of: {', '.join(VALID_BAY_TYPES)}")

    old = bay.model_dump()
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(bay, k, v)

    repo.log("service_bay", bay_id, "updated", old_val=old, new_val=bay.model_dump())
    repo.update(bay)
    session.commit()
    session.refresh(bay)
    return bay.model_dump()


@router.post("/{bay_id}/assign-car", response_model=dict)
def assign_car_to_bay(bay_id: int, car_id: int, session: Session = Depends(get_session)):
    bay_repo = ServiceBayRepository(session)
    car_repo = CarRepository(session)

    bay = bay_repo.get_by_id(bay_id)
    if not bay:
        raise HTTPException(404, "Service bay not found.")
    car = car_repo.get_by_id(car_id)
    if not car:
        raise HTTPException(404, "Car not found.")

    old_bay_available = bay.is_available
    old_car_bay = car.service_bay_id

    bay.is_available = False
    car.service_bay_id = bay_id

    bay_repo.log("service_bay", bay_id, "assigned",
                 old_val={"car_id": None, "is_available": old_bay_available},
                 new_val={"car_id": car_id, "is_available": False})
    car_repo.log("car", car_id, "bay_assigned",
                 old_val={"service_bay_id": old_car_bay},
                 new_val={"service_bay_id": bay_id})

    bay_repo.update(bay)
    car_repo.update(car)
    session.commit()
    session.refresh(bay)
    return bay.model_dump()


@router.post("/{bay_id}/release-car", response_model=dict)
def release_car_from_bay(bay_id: int, session: Session = Depends(get_session)):
    bay_repo = ServiceBayRepository(session)
    car_repo = CarRepository(session)

    bay = bay_repo.get_by_id(bay_id)
    if not bay:
        raise HTTPException(404, "Service bay not found.")

    for car in bay_repo.get_cars_in_bay(bay_id):
        car.service_bay_id = None
        car_repo.update(car)

    bay.is_available = True
    bay_repo.log("service_bay", bay_id, "released",
                 old_val={"is_available": False}, new_val={"is_available": True})
    bay_repo.update(bay)
    session.commit()
    session.refresh(bay)
    return bay.model_dump()


@router.delete("/{bay_id}", status_code=204)
def delete_bay(bay_id: int, session: Session = Depends(get_session)):
    bay_repo = ServiceBayRepository(session)
    car_repo = CarRepository(session)

    bay = bay_repo.get_by_id(bay_id)
    if not bay:
        raise HTTPException(404, "Service bay not found.")

    for car in bay_repo.get_cars_in_bay(bay_id):
        car.service_bay_id = None
        car_repo.update(car)

    for repair in session.exec(select(Repair).where(Repair.service_bay_id == bay_id)).all():
        repair.service_bay_id = None
        session.add(repair)

    bay_repo.log("service_bay", bay_id, "deleted", old_val=bay.model_dump())
    bay_repo.delete(bay)
    session.commit()
