from __future__ import annotations

import os

from sqlmodel import Session, SQLModel, create_engine

from backend.models.models import (  # noqa: F401 – imported so SQLModel registers tables
    BatteryLog,
    Car,
    ChargeCycle,
    EVProfile,
    Log,
    Repair,
    ServiceBay,
)


def _build_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "garage_management")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = _build_database_url()
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
