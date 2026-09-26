# Garage Management & Analytics System

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLModel-ORM-black" alt="SQLModel" />
  <img src="https://img.shields.io/badge/Gradio-UI-FF7C00?logo=gradio&logoColor=white" alt="Gradio" />
  <img src="https://img.shields.io/badge/Plotly-charts-3F4F75?logo=plotly&logoColor=white" alt="Plotly" />
</p>

A full-stack fleet service and analytics platform for a garage: car and repair tracking, service
bay management, EV battery health monitoring, automated maintenance alerts, and an interactive
dashboard — built solo, from a provided dataset, in a **4-hour timed exam**.

## About this project

This was a graded exam for my Applied Computer Science program: I was given a project brief and a fixed set of raw data (`data/*.csv`, `data/*.json` — car records,
repair history, service bay status, EV charge cycles and battery logs), and had **4 hours** to
design the database schema, build a working REST API, wire it up to PostgreSQL, and produce an
analytics-capable frontend on top of it — no prior access to the data or requirements beforehand.

Everything under `backend/`, `frontend/`, `seed.py`, and the schema design is my own work written
during the exam window. `important-code-snippets.md` was provided as an exam reference sheet (small
`os.getenv`/config patterns), not code I wrote — it's included here for context, not as something to
present as mine.

## What it does

- **Car management** — CRUD on the fleet, with automatic maintenance warnings once a car's
  kilometrage crosses its configured threshold
- **Repair workflow** — tracks each repair through `Warning → Pending → In Progress → Completed`,
  with cost estimates vs. final cost and mechanic assignment
- **Service bay tracking** — assign/release cars to bays, monitor availability and bay type
  (General, EV, Heavy, Inspection)
- **EV battery health** — tracks battery capacity, health percentage, and charge cycles per EV;
  logs every health change with an old/new value and a reason
- **Audit logging** — every change across the system is logged with old/new JSON values
- **Analytics dashboard** — a Gradio UI with data tables and Plotly charts: repairs per day, repair
  status distribution, average repair cost, EV charging volume (kWh) by location

## Architecture

```
data/ (provided CSV/JSON)  →  seed.py  →  PostgreSQL 18
                                              │
                                       backend/ (FastAPI + SQLModel)
                                       ├── models/       ORM models & schemas
                                       ├── repositories/ data-access layer per entity
                                       └── routers/      REST endpoints (cars, repairs,
                                                          service bays, EV, logs)
                                              │
                                       frontend/ (Gradio + Plotly)
                                       talks to the API over HTTP
```

## Tech stack

- **Backend:** FastAPI, SQLModel (ORM), PostgreSQL 18, `psycopg2`
- **Frontend:** Gradio, Plotly, pandas
- **Infra:** Docker Compose (PostgreSQL + Adminer)

## Running it

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment (pre-filled example provided)
cp .env.example .env

# 3. Start everything — Postgres (via Docker), FastAPI backend, Gradio frontend
python launch_app.py

# 4. In a separate terminal, seed the database from the provided data files
python seed.py
```

| Service | URL |
|---|---|
| Frontend (Gradio) | http://127.0.0.1:7860 |
| API docs (Swagger) | http://127.0.0.1:8000/docs |
| Adminer (DB admin) | http://127.0.0.1:8080 |

## Project structure

```
backend/
├── main.py              # FastAPI app entrypoint
├── database.py           # DB engine & session
├── compose.yaml           # PostgreSQL 18 + Adminer via Docker Compose
├── models/                # SQLModel ORM models & Pydantic schemas
├── repositories/          # Data-access layer, one per entity
└── routers/                # REST endpoints: cars, repairs, service_bays, ev, logs
frontend/
└── main.py                # Gradio dashboard
data/                       # Provided seed data (CSV/JSON)
seed.py                     # Loads the provided data into PostgreSQL
launch_app.py                # Starts DB + backend + frontend together
```
