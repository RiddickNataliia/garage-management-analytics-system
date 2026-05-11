from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ServiceBay(SQLModel, table=True):
    __tablename__ = "service_bays"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    bay_type: str  # General, EV, Heavy, Inspection
    is_available: bool = Field(default=True)
    notes: Optional[str] = None


class Car(SQLModel, table=True):
    __tablename__ = "cars"

    id: Optional[int] = Field(default=None, primary_key=True)
    license_plate: str = Field(unique=True, index=True)
    brand: str
    model: str
    owner_name: str
    kilometrage: float = Field(default=0.0)
    maintenance_threshold: float = Field(default=150000.0)
    is_ev: bool = Field(default=False)
    service_bay_id: Optional[int] = Field(default=None, foreign_key="service_bays.id")


class EVProfile(SQLModel, table=True):
    __tablename__ = "ev_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="cars.id", unique=True, index=True)
    battery_capacity_kwh: float
    battery_health_percent: float = Field(default=100.0)
    charge_cycles: int = Field(default=0)


class Repair(SQLModel, table=True):
    __tablename__ = "repairs"

    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="cars.id", index=True)
    repair_type: str
    mechanic: str
    status: str = Field(default="Pending")  # Warning, Pending, In Progress, Completed
    cost_estimate: Optional[float] = None
    final_cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    service_bay_id: Optional[int] = Field(default=None, foreign_key="service_bays.id")


class ChargeCycle(SQLModel, table=True):
    __tablename__ = "charge_cycles"

    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="cars.id", index=True)
    date: datetime
    start_percent: float
    end_percent: float
    kwh_charged: float
    location: str


class BatteryLog(SQLModel, table=True):
    __tablename__ = "battery_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="cars.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    old_health: float
    new_health: float
    reason: str


class Log(SQLModel, table=True):
    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entity_type: str  # car, repair, service_bay, ev, charge_cycle
    entity_id: int
    action: str
    old_value: Optional[str] = None  # JSON string
    new_value: Optional[str] = None  # JSON string

    def set_old_value(self, val):
        self.old_value = json.dumps(val) if val is not None else None

    def set_new_value(self, val):
        self.new_value = json.dumps(val) if val is not None else None
