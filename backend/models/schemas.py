import os
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class CarBase(BaseModel):
    license_plate: str
    brand: str
    model: str
    owner_name: str
    kilometrage: int
    maintenance_threshold: int
    is_ev: bool

class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    kilometrage: Optional[int] = None
    maintenance_threshold: Optional[int] = None

class CarResponse(CarBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RepairBase(BaseModel):
    car_id: int
    repair_type: str
    mechanic: str
    status: str
    cost_estimate: Optional[float] = None
    service_bay_id: Optional[int] = None

class RepairCreate(RepairBase):
    pass

class RepairUpdate(BaseModel):
    status: Optional[str] = None
    mechanic: Optional[str] = None
    final_cost: Optional[float] = None
    service_bay_id: Optional[int] = None

class RepairResponse(RepairBase):
    id: int
    final_cost: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ServiceBayBase(BaseModel):
    name: str
    bay_type: str
    is_available: bool
    notes: Optional[str] = None

class ServiceBayResponse(ServiceBayBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    entity_type: str
    entity_id: int
    action: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)