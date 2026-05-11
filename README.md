# Garage Management System
**Student:** Nataliia Riddick

## Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
The `.env` file is pre-filled and ready. Edit it if needed:
```
STUDENT_NAME=Nataliia Riddick
BACKEND_PORT=8000
FRONTEND_PORT=7860
LAUNCH_POSTGRES_DOCKER=true   # set to false if you have your own PostgreSQL
```

### 3. Start everything
```bash
python launch_app.py
```

This will:
- Start PostgreSQL 18 via Docker Compose (if `LAUNCH_POSTGRES_DOCKER=true`)
- Start the FastAPI backend with hot-reload
- Start the Gradio frontend with hot-reload

### 4. Seed demo data (first time)
In a separate terminal, after the backend is running:
```bash
python seed.py
```

### URLs
| Service    | URL                            |
|------------|--------------------------------|
| Frontend   | http://127.0.0.1:7860          |
| API Docs   | http://127.0.0.1:8000/docs     |
| Adminer DB | http://127.0.0.1:8080          |

## Project Structure
```
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # DB engine & session
│   ├── compose.yaml         # PostgreSQL 18 + Adminer Docker Compose
│   ├── models/
│   │   └── models.py        # SQLModel ORM models
│   └── routers/
│       ├── cars.py
│       ├── repairs.py
│       ├── service_bays.py
│       ├── ev.py
│       └── logs.py
├── frontend/
│   └── main.py              # Gradio UI
├── data/                    # Original seed CSV/JSON files
├── seed.py                  # Database seeder
├── launch_app.py            # Full stack launcher
├── requirements.txt
├── .env                     # Pre-filled environment config
└── .env.example             # Environment template
```

## Features
- **Car CRUD** with automatic maintenance warnings when kilometrage > threshold
- **Repair management**: Warning → Pending → In Progress → Completed flow
- **Service Bay management**: assign/release cars, track availability
- **EV support**: battery health, charge cycles, degradation tracking
- **Comprehensive logging** of all changes with old/new JSON values
- **Gradio UI** with DataFrames, Plotly charts, alert messages
- **Visualisations**: repairs per day, status distribution, avg cost, EV kWh by location
