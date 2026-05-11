from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from sqlmodel import Session

from backend.database import create_db_and_tables, engine
from backend.models import (
    BatteryLog,
    Car,
    ChargeCycle,
    EVProfile,
    Log,
    Repair,
    ServiceBay,
)

DATA_DIR = ROOT_DIR / "data"
STUDENT_NAME = os.getenv("STUDENT_NAME", "Nataliia Riddick").strip() or "Nataliia Riddick"


def _sync_postgres_sequences(session: Session):
    if engine.dialect.name != "postgresql":
        return
    for table_name in ("service_bays", "cars", "repairs", "charge_cycles", "battery_logs", "logs", "ev_profiles"):
        session.exec(
            text(
                "SELECT setval("
                "pg_get_serial_sequence(:table_name, 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
                "true)"
            ).bindparams(table_name=table_name)
        )
    session.commit()


def seed():
    print("Creating tables...")
    create_db_and_tables()

    with Session(engine) as session:
        # ── Check if already seeded ───────────────────────────────────────────
        from sqlmodel import select
        existing = session.exec(select(Car)).first()
        if existing:
            print("Database already has data. Skipping seed.")
            return

        print(f"Seeding demo data for student: {STUDENT_NAME}")

        # ── Service Bays ─────────────────────────────────────────────────────
        bays = [
            ServiceBay(id=1, name="Bay 1", bay_type="General", is_available=True,
                       notes="Standard lift for compact cars"),
            ServiceBay(id=2, name="Bay 2", bay_type="General", is_available=False,
                       notes="Occupied by brake inspection"),
            ServiceBay(id=3, name="EV Bay", bay_type="EV", is_available=False,
                       notes="High-voltage certified bay with charger"),
            ServiceBay(id=4, name="Van Bay", bay_type="Heavy", is_available=False,
                       notes="Large bay for vans and fleet vehicles"),
            ServiceBay(id=5, name="Inspection Lane", bay_type="Inspection", is_available=True,
                       notes="Quick diagnostics and intake checks"),
        ]
        for b in bays:
            session.add(b)
        session.flush()

        # ── Cars ──────────────────────────────────────────────────────────────
        cars = [
            Car(id=1, license_plate="1-ABC-234", brand="Toyota", model="Corolla",
                owner_name="Nina Peeters", kilometrage=158200, maintenance_threshold=160000, is_ev=False),
            Car(id=2, license_plate="2-DEF-987", brand="Volkswagen", model="Golf",
                owner_name="Samira El Idrissi", kilometrage=182450, maintenance_threshold=175000, is_ev=False),
            Car(id=3, license_plate="1-EVQ-442", brand="Tesla", model="Model 3",
                owner_name="Jonas Vermeulen", kilometrage=64200, maintenance_threshold=70000, is_ev=True,
                service_bay_id=2),
            Car(id=4, license_plate="2-HJK-615", brand="Renault", model="Clio",
                owner_name="Kamiel De Graef", kilometrage=118900, maintenance_threshold=120000, is_ev=False),
            Car(id=5, license_plate="1-PLG-808", brand="Kia", model="Niro EV",
                owner_name="Elias Pieters", kilometrage=93400, maintenance_threshold=90000, is_ev=True,
                service_bay_id=3),
            Car(id=6, license_plate="2-MNO-331", brand="Ford", model="Transit",
                owner_name=f"Garage Demo Fleet — {STUDENT_NAME}", kilometrage=221000,
                maintenance_threshold=220000, is_ev=False, service_bay_id=4),
        ]
        for c in cars:
            session.add(c)
        session.flush()

        # ── EV Profiles ───────────────────────────────────────────────────────
        ev_profiles = [
            EVProfile(id=1, car_id=3, battery_capacity_kwh=75.0, battery_health_percent=94.6, charge_cycles=2),
            EVProfile(id=2, car_id=5, battery_capacity_kwh=64.8, battery_health_percent=91.1, charge_cycles=3),
        ]
        for ev in ev_profiles:
            session.add(ev)
        session.flush()

        # ── Repairs ───────────────────────────────────────────────────────────
        repairs = [
            Repair(id=1, car_id=2, repair_type="Maintenance threshold exceeded",
                   mechanic="Robin Maes", status="Warning", cost_estimate=180.00,
                   created_at=datetime(2026, 5, 6, 8, 15)),
            Repair(id=2, car_id=3, repair_type="Brake inspection",
                   mechanic="Elise De Smet", status="In Progress", cost_estimate=420.00,
                   created_at=datetime(2026, 5, 6, 9, 20), started_at=datetime(2026, 5, 6, 10, 0),
                   service_bay_id=2),
            Repair(id=3, car_id=4, repair_type="Oil service and filter",
                   mechanic="Nora Janssens", status="Completed", cost_estimate=160.00,
                   final_cost=148.50, created_at=datetime(2026, 5, 5, 13, 10),
                   started_at=datetime(2026, 5, 5, 13, 35), completed_at=datetime(2026, 5, 5, 15, 5),
                   service_bay_id=1),
            Repair(id=4, car_id=5, repair_type="Maintenance threshold exceeded",
                   mechanic="Robin Maes", status="Warning", cost_estimate=220.00,
                   created_at=datetime(2026, 5, 7, 11, 45), service_bay_id=3),
            Repair(id=5, car_id=6, repair_type="Front suspension noise",
                   mechanic="Milan Peeters", status="Pending", cost_estimate=650.00,
                   created_at=datetime(2026, 5, 7, 14, 25), service_bay_id=4),
        ]
        for r in repairs:
            session.add(r)
        session.flush()

        # ── Charge Cycles ─────────────────────────────────────────────────────
        charge_cycles = [
            ChargeCycle(id=1, car_id=3, date=datetime(2026, 4, 18), start_percent=22, end_percent=86,
                        kwh_charged=47.8, location="Garage EV Bay"),
            ChargeCycle(id=2, car_id=3, date=datetime(2026, 4, 29), start_percent=35, end_percent=80,
                        kwh_charged=33.2, location="Public fast charger Antwerp"),
            ChargeCycle(id=3, car_id=5, date=datetime(2026, 4, 12), start_percent=18, end_percent=92,
                        kwh_charged=54.6, location="Owner home charger"),
            ChargeCycle(id=4, car_id=5, date=datetime(2026, 5, 2), start_percent=41, end_percent=88,
                        kwh_charged=36.4, location="Garage EV Bay"),
            ChargeCycle(id=5, car_id=5, date=datetime(2026, 5, 7), start_percent=27, end_percent=75,
                        kwh_charged=38.1, location="Public charger Mechelen"),
        ]
        for cc in charge_cycles:
            session.add(cc)
        session.flush()

        # ── Battery Logs ──────────────────────────────────────────────────────
        battery_logs = [
            BatteryLog(id=1, car_id=3, timestamp=datetime(2026, 4, 18, 17, 30),
                       old_health=94.8, new_health=94.7, reason="Charge cycle recorded"),
            BatteryLog(id=2, car_id=3, timestamp=datetime(2026, 4, 29, 19, 10),
                       old_health=94.7, new_health=94.6, reason="Fast charge cycle recorded"),
            BatteryLog(id=3, car_id=5, timestamp=datetime(2026, 4, 12, 8, 45),
                       old_health=91.5, new_health=91.4, reason="Charge cycle recorded"),
            BatteryLog(id=4, car_id=5, timestamp=datetime(2026, 5, 2, 16, 20),
                       old_health=91.4, new_health=91.2, reason="Garage diagnostic update"),
            BatteryLog(id=5, car_id=5, timestamp=datetime(2026, 5, 7, 18, 5),
                       old_health=91.2, new_health=91.1, reason="Charge cycle recorded"),
        ]
        for bl in battery_logs:
            session.add(bl)
        session.flush()

        # ── Logs ──────────────────────────────────────────────────────────────
        logs_data = [
            Log(id=1, timestamp=datetime(2026, 5, 5, 13, 10), entity_type="repair", entity_id=3,
                action="created", old_value=None,
                new_value=json.dumps({"car_id": 4, "repair_type": "Oil service and filter", "status": "Pending"})),
            Log(id=2, timestamp=datetime(2026, 5, 5, 15, 5), entity_type="repair", entity_id=3,
                action="completed",
                old_value=json.dumps({"status": "In Progress", "final_cost": None}),
                new_value=json.dumps({"status": "Completed", "final_cost": 148.5})),
            Log(id=3, timestamp=datetime(2026, 5, 6, 8, 15), entity_type="car", entity_id=2,
                action="maintenance_warning_created",
                old_value=json.dumps({"kilometrage": 174900, "maintenance_threshold": 175000}),
                new_value=json.dumps({"kilometrage": 182450, "repair_id": 1, "status": "Warning"})),
            Log(id=4, timestamp=datetime(2026, 5, 6, 10, 0), entity_type="repair", entity_id=2,
                action="status_changed",
                old_value=json.dumps({"status": "Pending"}),
                new_value=json.dumps({"status": "In Progress", "service_bay_id": 2})),
            Log(id=5, timestamp=datetime(2026, 5, 7, 11, 45), entity_type="car", entity_id=5,
                action="maintenance_warning_created",
                old_value=json.dumps({"kilometrage": 89950, "maintenance_threshold": 90000}),
                new_value=json.dumps({"kilometrage": 93400, "repair_id": 4, "status": "Warning"})),
            Log(id=6, timestamp=datetime(2026, 5, 7, 14, 25), entity_type="service_bay", entity_id=4,
                action="assigned",
                old_value=json.dumps({"car_id": None, "is_available": True}),
                new_value=json.dumps({"car_id": 6, "repair_id": 5, "is_available": False})),
        ]
        for log in logs_data:
            session.add(log)

        session.commit()
        _sync_postgres_sequences(session)

    print(f"✅ Seed complete! Demo data loaded for {STUDENT_NAME}.")


if __name__ == "__main__":
    seed()
