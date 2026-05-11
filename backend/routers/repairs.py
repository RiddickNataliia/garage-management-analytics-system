from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from backend.database import get_session
from backend.models import Car, Repair, ServiceBay
from backend.repositories import RepairRepository, ServiceBayRepository

router = APIRouter(prefix="/repairs", tags=["Repairs"])

VALID_STATUSES = {"Warning", "Pending", "In Progress", "Completed"}


class RepairCreate(BaseModel):
    car_id: int
    repair_type: str
    mechanic: str
    status: str = "Pending"
    cost_estimate: Optional[float] = None
    service_bay_id: Optional[int] = None


class RepairUpdate(BaseModel):
    repair_type: Optional[str] = None
    mechanic: Optional[str] = None
    status: Optional[str] = None
    cost_estimate: Optional[float] = None
    final_cost: Optional[float] = None
    service_bay_id: Optional[int] = None


@router.get("/", response_model=List[dict])
def list_repairs(session: Session = Depends(get_session)):
    repo = RepairRepository(session)
    return [r.model_dump() for r in repo.get_all()]


@router.get("/warnings", response_model=List[dict])
def list_warnings(session: Session = Depends(get_session)):
    repo = RepairRepository(session)
    return [r.model_dump() for r in repo.get_warnings()]


@router.post("/", response_model=dict, status_code=201)
def create_repair(data: RepairCreate, session: Session = Depends(get_session)):
    repo = RepairRepository(session)

    if data.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
    if not session.get(Car, data.car_id):
        raise HTTPException(404, f"Car {data.car_id} not found.")
    if data.service_bay_id and not session.get(ServiceBay, data.service_bay_id):
        raise HTTPException(404, f"Service bay {data.service_bay_id} not found.")

    repair = Repair(**data.model_dump(), created_at=datetime.utcnow())
    repo.create(repair)
    repo.log("repair", repair.id, "created",
             new_val={"car_id": data.car_id, "repair_type": data.repair_type, "status": data.status})
    session.commit()
    session.refresh(repair)
    return repair.model_dump()


@router.get("/{repair_id}", response_model=dict)
def get_repair(repair_id: int, session: Session = Depends(get_session)):
    repo = RepairRepository(session)
    repair = repo.get_by_id(repair_id)
    if not repair:
        raise HTTPException(404, "Repair not found.")
    return repair.model_dump()


@router.put("/{repair_id}", response_model=dict)
def update_repair(repair_id: int, data: RepairUpdate, session: Session = Depends(get_session)):
    repo = RepairRepository(session)
    repair = repo.get_by_id(repair_id)
    if not repair:
        raise HTTPException(404, "Repair not found.")
    if data.status and data.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")

    old = repair.model_dump()
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(repair, k, v)

    repo.log("repair", repair_id, "updated", old_val=old, new_val=repair.model_dump())
    repo.update(repair)
    session.commit()
    session.refresh(repair)
    return repair.model_dump()


@router.post("/{repair_id}/start", response_model=dict)
def start_repair(repair_id: int, bay_id: Optional[int] = None,
                 session: Session = Depends(get_session)):
    repair_repo = RepairRepository(session)
    bay_repo = ServiceBayRepository(session)

    repair = repair_repo.get_by_id(repair_id)
    if not repair:
        raise HTTPException(404, "Repair not found.")
    if repair.status == "Completed":
        raise HTTPException(400, "Cannot start a completed repair.")
    if repair.status == "In Progress":
        raise HTTPException(400, "Repair is already in progress.")

    old_status = repair.status

    if bay_id is not None:
        bay = bay_repo.get_by_id(bay_id)
        if not bay:
            raise HTTPException(404, f"Service bay {bay_id} not found.")
        repair.service_bay_id = bay_id
        bay.is_available = False
        bay_repo.update(bay)

    repair.status = "In Progress"
    repair.started_at = datetime.utcnow()

    repair_repo.log("repair", repair_id, "status_changed",
                    old_val={"status": old_status},
                    new_val={"status": "In Progress", "service_bay_id": repair.service_bay_id})
    repair_repo.update(repair)
    session.commit()
    session.refresh(repair)
    return repair.model_dump()


@router.post("/{repair_id}/complete", response_model=dict)
def complete_repair(repair_id: int, final_cost: Optional[float] = None,
                    session: Session = Depends(get_session)):
    repair_repo = RepairRepository(session)
    bay_repo = ServiceBayRepository(session)

    repair = repair_repo.get_by_id(repair_id)
    if not repair:
        raise HTTPException(404, "Repair not found.")
    if repair.status == "Completed":
        raise HTTPException(400, "Repair is already completed.")

    old = {"status": repair.status, "final_cost": repair.final_cost}
    repair.status = "Completed"
    repair.completed_at = datetime.utcnow()
    if final_cost is not None:
        repair.final_cost = final_cost

    if repair.service_bay_id:
        bay = bay_repo.get_by_id(repair.service_bay_id)
        if bay:
            bay.is_available = True
            bay_repo.update(bay)

    repair_repo.log("repair", repair_id, "completed",
                    old_val=old,
                    new_val={"status": "Completed", "final_cost": repair.final_cost})
    repair_repo.update(repair)
    session.commit()
    session.refresh(repair)
    return repair.model_dump()


@router.delete("/{repair_id}", status_code=204)
def delete_repair(repair_id: int, session: Session = Depends(get_session)):
    repo = RepairRepository(session)
    repair = repo.get_by_id(repair_id)
    if not repair:
        raise HTTPException(404, "Repair not found.")

    # Release service bay if repair was assigned to one
    if repair.service_bay_id:
        bay = session.get(ServiceBay, repair.service_bay_id)
        if bay:
            bay.is_available = True
            bay_repo = ServiceBayRepository(session)
            bay_repo.update(bay)

    # Log deletion with serializable data (exclude datetime objects)
    old_data = {
        "car_id": repair.car_id,
        "repair_type": repair.repair_type,
        "mechanic": repair.mechanic,
        "status": repair.status,
        "cost_estimate": repair.cost_estimate,
        "final_cost": repair.final_cost,
        "service_bay_id": repair.service_bay_id,
    }
    repo.log("repair", repair_id, "deleted", old_val=old_data)
    repo.delete(repair)
    session.commit()
