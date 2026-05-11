from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_db_and_tables
from backend.routers import cars, ev, logs, repairs, service_bays

STUDENT_NAME = os.getenv("STUDENT_NAME", "Student")

app = FastAPI(
    title=f"Garage Management API - {STUDENT_NAME}",
    description="Garage management system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cars.router)
app.include_router(repairs.router)
app.include_router(service_bays.router)
app.include_router(ev.router)
app.include_router(logs.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {
        "message": "Garage Management API is running.",
        "student_name": STUDENT_NAME,
    }
