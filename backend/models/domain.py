from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, unique=True, index=True)
    brand = Column(String)
    model = Column(String)
    owner_name = Column(String)
    kilometrage = Column(Integer)
    maintenance_threshold = Column(Integer)
    is_ev = Column(Boolean, default=False)

    repairs = relationship("Repair", back_populates="car", cascade="all, delete-orphan")
    ev_profile = relationship("EVProfile", back_populates="car", uselist=False, cascade="all, delete-orphan")
    charge_cycles = relationship("EVChargeCycle", back_populates="car", cascade="all, delete-orphan")
    battery_logs = relationship("BatteryLog", back_populates="car", cascade="all, delete-orphan")

class Repair(Base):
    __tablename__ = "repairs"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    repair_type = Column(String)
    mechanic = Column(String)
    status = Column(String)
    cost_estimate = Column(Float)
    final_cost = Column(Float, nullable=True)
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    service_bay_id = Column(Integer, ForeignKey("service_bays.id"), nullable=True)

    car = relationship("Car", back_populates="repairs")
    service_bay = relationship("ServiceBay", back_populates="repairs")

class ServiceBay(Base):
    __tablename__ = "service_bays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    bay_type = Column(String)
    is_available = Column(Boolean, default=True)
    notes = Column(String)

    repairs = relationship("Repair", back_populates="service_bay")

class EVProfile(Base):
    __tablename__ = "ev_profiles"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), unique=True)
    battery_capacity_kwh = Column(Float)
    battery_health_percent = Column(Float)
    charge_cycles_count = Column(Integer)

    car = relationship("Car", back_populates="ev_profile")

class EVChargeCycle(Base):
    __tablename__ = "ev_charge_cycles"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    date = Column(DateTime)
    start_percent = Column(Float)
    end_percent = Column(Float)
    kwh_charged = Column(Float)
    location = Column(String)

    car = relationship("Car", back_populates="charge_cycles")

class BatteryLog(Base):
    __tablename__ = "battery_logs"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    timestamp = Column(DateTime)
    old_health = Column(Float)
    new_health = Column(Float)
    reason = Column(String)

    car = relationship("Car", back_populates="battery_logs")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)