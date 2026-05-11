from __future__ import annotations

import os
import json
from datetime import datetime

import gradio as gr
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("GARAGE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
STUDENT_NAME = os.getenv("STUDENT_NAME", "Student").strip() or "Student"
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "7860"))

# --- Stricter CSS to force text colors and hide default borders ---
custom_css = """
.gradio-container {
    background-color: #f8fafc !important;
}
footer {visibility: hidden}

/* Force everything in the header to be white */
#header-markdown {
    text-align: center;
    padding: 24px;
    background: linear-gradient(90deg, #0f172a 0%, #334155 100%) !important;
    border-radius: 8px;
    margin-bottom: 20px;
    color: white !important;
    box-shadow: none !important;
    border: none !important;
}

/* Override ALL Gradio defaults inside header */
#header-markdown > * {
    background: transparent !important;
    border: none !important;
}

#header-markdown .group {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

#header-markdown h1, 
#header-markdown p, 
#header-markdown strong, 
#header-markdown code {
    color: white !important;
    background: transparent !important;
}
"""

# --- Build a strict custom theme using Gradio's built-in Slate colors ---
theme = gr.themes.Default(
    primary_hue=gr.themes.colors.slate,  
    secondary_hue=gr.themes.colors.gray,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    # Core Backgrounds
    body_background_fill="#f8fafc",
    block_background_fill="#ffffff",
    
    # Primary Buttons (The main actions)
    button_primary_background_fill="#1e293b",
    button_primary_background_fill_hover="#0f172a",
    button_primary_text_color="#ffffff",
    
    # Secondary Buttons (Refresh buttons)
    button_secondary_background_fill="#f1f5f9",
    button_secondary_background_fill_hover="#e2e8f0",
    button_secondary_text_color="#334155",
    
    # Input Labels 
    block_label_background_fill="#f1f5f9",
    block_label_text_color="#475569",
    block_label_text_weight="600",
    block_title_text_color="#1e293b",
)


# HTTP helpers 

def _get(path: str, params: dict = None):
    try:
        r = httpx.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def _post(path: str, data: dict = None, params: dict = None):
    try:
        r = httpx.post(f"{API_BASE_URL}{path}", json=data, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def _put(path: str, data: dict):
    try:
        r = httpx.put(f"{API_BASE_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def _patch(path: str, data: dict = None, params: dict = None):
    try:
        r = httpx.patch(f"{API_BASE_URL}{path}", json=data, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def _delete(path: str):
    try:
        r = httpx.delete(f"{API_BASE_URL}{path}", timeout=10)
        r.raise_for_status()
        return True, None
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return False, detail
    except Exception as e:
        return False, str(e)


# Data helpers

def _cars_df():
    data, err = _get("/cars/")
    if err:
        return pd.DataFrame(), err
    if not data:
        return pd.DataFrame(), None
    df = pd.DataFrame(data)
    cols = ["id", "license_plate", "brand", "model", "owner_name",
            "kilometrage", "maintenance_threshold", "is_ev", "service_bay_id", "warning"]
    df = df.reindex(columns=[c for c in cols if c in df.columns])
    return df, None


def _repairs_df():
    data, err = _get("/repairs/")
    if err:
        return pd.DataFrame(), err
    if not data:
        return pd.DataFrame(), None
    df = pd.DataFrame(data)
    cols = ["id", "car_id", "repair_type", "mechanic", "status",
            "cost_estimate", "final_cost", "created_at", "started_at", "completed_at", "service_bay_id"]
    df = df.reindex(columns=[c for c in cols if c in df.columns])
    return df, None


def _bays_df():
    data, err = _get("/service-bays/")
    if err:
        return pd.DataFrame(), err
    if not data:
        return pd.DataFrame(), None
    df = pd.DataFrame(data)
    if "id" in df.columns:
        df = df.sort_values("id", ascending=False)
    return df.reset_index(drop=True), None


def _logs_df(entity_type=None, action=None):
    params = {}
    if entity_type:
        params["entity_type"] = entity_type
    if action:
        params["action"] = action
    data, err = _get("/logs/", params=params)
    if err:
        return pd.DataFrame(), err
    if not data:
        return pd.DataFrame(), None
    return pd.DataFrame(data), None


def _car_choices():
    data, _ = _get("/cars/")
    if not data:
        return []
    return [f"{c['id']} - {c['license_plate']} ({c['brand']} {c['model']})" for c in data]


def _ev_car_choices():
    data, _ = _get("/cars/")
    if not data:
        return []
    return [f"{c['id']} - {c['license_plate']} ({c['brand']} {c['model']})"
            for c in data if c.get("is_ev")]


def _bay_choices():
    data, _ = _get("/service-bays/")
    if not data:
        return []
    data = sorted(data, key=lambda b: b.get("id", 0), reverse=True)
    return [f"{b['id']} - {b['name']} ({b['bay_type']})" for b in data]


def _bay_choice_bundle():
    choices = _bay_choices()
    return choices, choices, choices, choices, choices, choices


def _repair_choices():
    data, _ = _get("/repairs/")
    if not data:
        return []
    return [f"{r['id']} - Car {r['car_id']}: {r['repair_type']} [{r['status']}]" for r in data]


def _parse_id(choice: str) -> int:
    return int(choice.split(" - ")[0])

# CARS TAB
def refresh_cars():
    df, err = _cars_df()
    if err:
        gr.Warning(f"Failed to load cars: {err}")
    return df


def add_car(plate, brand, model, owner, km, threshold, is_ev):
    if not plate or not brand or not model or not owner:
        gr.Warning("Please fill in all required fields (plate, brand, model, owner).")
        return refresh_cars(), _car_choices(), _car_choices(), _car_choices(), _car_choices()
    km_val = float(km or 0)
    threshold_val = float(threshold or 150000)
    if km_val < 0:
        gr.Warning("Kilometrage cannot be negative.")
        return refresh_cars(), _car_choices(), _car_choices(), _car_choices(), _car_choices()
    if threshold_val < 0:
        gr.Warning("Maintenance threshold cannot be negative.")
        return refresh_cars(), _car_choices(), _car_choices(), _car_choices(), _car_choices()
    payload = {
        "license_plate": plate.strip(),
        "brand": brand.strip(),
        "model": model.strip(),
        "owner_name": owner.strip(),
        "kilometrage": km_val,
        "maintenance_threshold": threshold_val,
        "is_ev": bool(is_ev),
    }
    data, err = _post("/cars/", payload)
    if err:
        gr.Warning(f"Failed to add car: {err}")
    else:
        gr.Info(f"Car '{brand} {model}' added successfully (ID {data['id']}).")
    df, _ = _cars_df()
    choices = _car_choices()
    return df, choices, choices, choices, choices


def update_kilometrage(car_choice, new_km):
    if not car_choice:
        gr.Warning("Please select a car.")
        return refresh_cars()
    new_km_val = float(new_km or 0)
    if new_km_val < 0:
        gr.Warning("Kilometrage cannot be negative.")
        return refresh_cars()
    car_id = _parse_id(car_choice)
    data, err = _patch(f"/cars/{car_id}/kilometrage", {"kilometrage": new_km_val})
    if err:
        gr.Warning(f"Failed to update kilometrage: {err}")
    else:
        msg = f"Kilometrage updated to {new_km_val} km."
        if data.get("warning"):
            msg += " ⚠️ Maintenance threshold exceeded — a Warning repair has been created."
        gr.Info(msg)
    df, _ = _cars_df()
    return df


def assign_bay_to_car(car_choice, bay_choice):
    if not car_choice or not bay_choice:
        gr.Warning("Please select both a car and a bay.")
        return refresh_cars()
    car_id = _parse_id(car_choice)
    bay_id = _parse_id(bay_choice)
    _, err = _post(f"/service-bays/{bay_id}/assign-car", params={"car_id": car_id})
    if err:
        gr.Warning(f"Failed to assign bay: {err}")
    else:
        gr.Info("Car assigned to service bay successfully.")
    df, _ = _cars_df()
    return df


def delete_car(car_choice):
    if not car_choice:
        gr.Warning("Please select a car.")
        return refresh_cars(), _car_choices(), _car_choices(), _car_choices(), _car_choices()
    car_id = _parse_id(car_choice)
    ok, err = _delete(f"/cars/{car_id}")
    if err:
        gr.Warning(f"Failed to delete car: {err}")
    else:
        gr.Info("Car deleted successfully.")
    df, _ = _cars_df()
    choices = _car_choices()
    return df, choices, choices, choices, choices


# REPAIRS TAB

def refresh_repairs():
    df, err = _repairs_df()
    if err:
        gr.Warning(f"Failed to load repairs: {err}")
    return df


def add_repair(car_choice, repair_type, mechanic, status, cost_est, bay_choice):
    if not car_choice or not repair_type or not mechanic:
        gr.Warning("Please fill in car, repair type, and mechanic.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    car_id = _parse_id(car_choice)
    payload = {
        "car_id": car_id,
        "repair_type": repair_type.strip(),
        "mechanic": mechanic.strip(),
        "status": status or "Pending",
        "cost_estimate": float(cost_est) if cost_est else None,
        "service_bay_id": _parse_id(bay_choice) if bay_choice else None,
    }
    data, err = _post("/repairs/", payload)
    if err:
        gr.Warning(f"Failed to add repair: {err}")
    else:
        gr.Info(f"Repair created successfully (ID {data['id']}).")
    df, _ = _repairs_df()
    choices = _repair_choices()
    return df, choices, choices, choices


def start_repair(repair_choice, bay_choice):
    if not repair_choice:
        gr.Warning("Please select a repair.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    repair_id = _parse_id(repair_choice)
    params = {"bay_id": _parse_id(bay_choice)} if bay_choice else {}
    _, err = _post(f"/repairs/{repair_id}/start", params=params)
    if err:
        gr.Warning(f"Failed to start repair: {err}")
    else:
        gr.Info("Repair started — status set to 'In Progress'.")
    df, _ = _repairs_df()
    choices = _repair_choices()
    return df, choices, choices, choices


def complete_repair(repair_choice, final_cost):
    if not repair_choice:
        gr.Warning("Please select a repair.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    repair_id = _parse_id(repair_choice)
    params = {"final_cost": float(final_cost)} if final_cost else {}
    _, err = _post(f"/repairs/{repair_id}/complete", params=params)
    if err:
        gr.Warning(f"Failed to complete repair: {err}")
    else:
        gr.Info("Repair marked as Completed.")
    df, _ = _repairs_df()
    choices = _repair_choices()
    return df, choices, choices, choices


def update_repair(repair_choice, mechanic, status, cost_est, final_cost):
    if not repair_choice:
        gr.Warning("Please select a repair.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    repair_id = _parse_id(repair_choice)
    payload = {}
    if mechanic:
        payload["mechanic"] = mechanic.strip()
    if status:
        payload["status"] = status
    if cost_est:
        payload["cost_estimate"] = float(cost_est)
    if final_cost:
        payload["final_cost"] = float(final_cost)
    if not payload:
        gr.Warning("No fields to update.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    _, err = _put(f"/repairs/{repair_id}", payload)
    if err:
        gr.Warning(f"Failed to update repair: {err}")
    else:
        gr.Info("Repair updated successfully.")
    df, _ = _repairs_df()
    choices = _repair_choices()
    return df, choices, choices, choices


def delete_repair(repair_choice):
    if not repair_choice:
        gr.Warning("Please select a repair.")
        choices = _repair_choices()
        return refresh_repairs(), choices, choices, choices
    repair_id = _parse_id(repair_choice)
    ok, err = _delete(f"/repairs/{repair_id}")
    if err:
        gr.Warning(f"Failed to delete repair: {err}")
    else:
        gr.Info("Repair deleted.")
    df, _ = _repairs_df()
    choices = _repair_choices()
    return df, choices, choices, choices


def refresh_warnings():
    data, err = _get("/repairs/warnings")
    if err:
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)



# SERVICE BAYS TAB

def refresh_bays():
    df, err = _bays_df()
    if err:
        return df
    return df


def add_bay(name, bay_type, notes):
    if not name:
        gr.Warning("Bay name is required.")
        return refresh_bays(), *_bay_choice_bundle()
    payload = {"name": name.strip(), "bay_type": bay_type or "General",
               "is_available": True, "notes": notes or None}
    data, err = _post("/service-bays/", payload)
    if err:
        gr.Warning(f"Failed to add bay: {err}")
    else:
        gr.Info(f"Service bay '{name}' added (ID {data['id']}).")
    return refresh_bays(), *_bay_choice_bundle()


def release_bay(bay_choice):
    if not bay_choice:
        gr.Warning("Please select a bay.")
        return refresh_bays(), *_bay_choice_bundle()
    bay_id = _parse_id(bay_choice)
    _, err = _post(f"/service-bays/{bay_id}/release-car")
    if err:
        gr.Warning(f"Failed to release bay: {err}")
    else:
        gr.Info("Bay released and car unassigned.")
    return refresh_bays(), *_bay_choice_bundle()


def delete_bay(bay_choice):
    if not bay_choice:
        gr.Warning("Please select a bay.")
        return refresh_bays(), *_bay_choice_bundle()
    bay_id = _parse_id(bay_choice)
    ok, err = _delete(f"/service-bays/{bay_id}")
    if err:
        gr.Warning(f"Failed to delete bay: {err}")
    else:
        gr.Info("Service bay deleted.")
    return refresh_bays(), *_bay_choice_bundle()


# EV TAB

def refresh_ev_profiles():
    data, err = _get("/ev/")
    if err:
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def get_charge_cycles(car_choice):
    if not car_choice:
        return pd.DataFrame()
    car_id = _parse_id(car_choice)
    data, err = _get(f"/ev/{car_id}/charge-cycles")
    if err:
        gr.Warning(f"Failed to load charge cycles: {err}")
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def add_charge_cycle(car_choice, date_str, start_pct, end_pct, kwh, location):
    if not car_choice:
        gr.Warning("Please select an EV.")
        return get_charge_cycles(car_choice)
    if not date_str:
        gr.Warning("Please enter a date.")
        return get_charge_cycles(car_choice)
    car_id = _parse_id(car_choice)
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").isoformat()
    except ValueError:
        gr.Warning("Date must be in YYYY-MM-DD format.")
        return get_charge_cycles(car_choice)

    payload = {
        "date": dt,
        "start_percent": float(start_pct),
        "end_percent": float(end_pct),
        "kwh_charged": float(kwh),
        "location": location.strip() if location else "Unknown",
    }
    _, err = _post(f"/ev/{car_id}/charge-cycles", payload)
    if err:
        gr.Warning(f"Failed to add charge cycle: {err}")
    else:
        gr.Info("Charge cycle recorded successfully.")
    return get_charge_cycles(car_choice)


def get_battery_logs(car_choice):
    if not car_choice:
        return pd.DataFrame()
    car_id = _parse_id(car_choice)
    data, err = _get(f"/ev/{car_id}/battery-logs")
    if err:
        gr.Warning(f"Failed to load battery logs: {err}")
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def update_battery_health(car_choice, new_health, reason):
    if not car_choice:
        gr.Warning("Please select an EV.")
        return get_battery_logs(car_choice)
    car_id = _parse_id(car_choice)
    if not reason:
        gr.Warning("Please provide a reason.")
        return get_battery_logs(car_choice)
    _, err = _patch(f"/ev/{car_id}/battery-health",
                    {"new_health": float(new_health), "reason": reason.strip()})
    if err:
        gr.Warning(f"Failed to update battery health: {err}")
    else:
        gr.Info("Battery health updated.")
    return get_battery_logs(car_choice)


def ev_battery_health_plot(car_choice):
    if not car_choice:
        return go.Figure()
    car_id = _parse_id(car_choice)
    data, err = _get(f"/ev/{car_id}/battery-logs")
    if err or not data:
        return go.Figure().update_layout(title="No battery log data available.")
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    fig = px.line(df, x="timestamp", y="new_health",
                  title=f"Battery Health Over Time — {car_choice.split(' - ')[1].split(' (')[0]}",
                  labels={"new_health": "Health (%)", "timestamp": "Date"},
                  markers=True,
                  template="plotly_white")
    fig.update_traces(line_color="#334155", marker_color="#1e293b")
    fig.update_layout(yaxis_range=[0, 100])
    return fig


def ev_charge_cycles_plot(car_choice):
    if not car_choice:
        return go.Figure()
    car_id = _parse_id(car_choice)
    data, err = _get(f"/ev/{car_id}/charge-cycles")
    if err or not data:
        return go.Figure().update_layout(title="No charge cycle data available.")
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").size().reset_index(name="cycles")
    fig = px.bar(monthly, x="month", y="cycles",
                 title=f"Charge Cycles per Month — {car_choice.split(' - ')[1].split(' (')[0]}",
                 labels={"month": "Month", "cycles": "Number of Cycles"},
                 template="plotly_white",
                 color_discrete_sequence=["#334155"])
    return fig



# LOGS TAB

def refresh_logs(entity_type, action):
    df, err = _logs_df(
        entity_type=entity_type if entity_type != "All" else None,
        action=action if action else None,
    )
    if err:
        gr.Warning(f"Failed to load logs: {err}")
        return pd.DataFrame()
    return df


# VISUALISATION TAB

def plot_repairs_per_day():
    data, err = _get("/repairs/")
    if err or not data:
        return go.Figure().update_layout(title="No repair data.")
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    daily = df.groupby("date").size().reset_index(name="count")
    fig = px.bar(daily, x="date", y="count",
                 title="Repairs per Day",
                 labels={"date": "Date", "count": "Number of Repairs"},
                 template="plotly_white",
                 color_discrete_sequence=["#334155"])
    return fig


def plot_status_distribution():
    data, err = _get("/repairs/")
    if err or not data:
        return go.Figure().update_layout(title="No repair data.")
    df = pd.DataFrame(data)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    colors = {"Warning": "#f59e0b", "Pending": "#6366f1",
               "In Progress": "#3b82f6", "Completed": "#22c55e"}
    fig = px.pie(status_counts, names="status", values="count",
                 title="Repair Status Distribution",
                 color="status", color_discrete_map=colors,
                 template="plotly_white")
    return fig


def plot_avg_repair_cost():
    data, err = _get("/repairs/")
    if err or not data:
        return go.Figure().update_layout(title="No repair data.")
    df = pd.DataFrame(data)
    df = df[df["cost_estimate"].notna()]
    if df.empty:
        return go.Figure().update_layout(title="No cost data available.")
    avg = df.groupby("status")["cost_estimate"].mean().reset_index()
    avg.columns = ["status", "avg_cost"]
    fig = px.bar(avg, x="status", y="avg_cost",
                 title="Average Cost Estimate by Repair Status",
                 labels={"status": "Status", "avg_cost": "Avg Cost Estimate (€)"},
                 template="plotly_white",
                 color_discrete_sequence=["#334155"])
    return fig


def plot_ev_kwh_by_location():
    """Custom EV plot: kWh charged per location across all EVs."""
    data, err = _get("/cars/")
    if err or not data:
        return go.Figure().update_layout(title="No EV data.")
    ev_ids = [c["id"] for c in data if c.get("is_ev")]
    all_cycles = []
    for car_id in ev_ids:
        cycles, _ = _get(f"/ev/{car_id}/charge-cycles")
        if cycles:
            for c in cycles:
                c["car_id"] = car_id
            all_cycles.extend(cycles)
    if not all_cycles:
        return go.Figure().update_layout(title="No charge cycle data available.")
    df = pd.DataFrame(all_cycles)
    by_loc = df.groupby("location")["kwh_charged"].sum().reset_index()
    by_loc.columns = ["location", "total_kwh"]
    by_loc = by_loc.sort_values("total_kwh", ascending=False)
    fig = px.bar(by_loc, x="location", y="total_kwh",
                 title="Total kWh Charged by Location (All EVs)",
                 labels={"location": "Charging Location", "total_kwh": "Total kWh Charged"},
                 template="plotly_white",
                 color_discrete_sequence=["#334155"])
    return fig


def load_all_plots():
    return (
        plot_repairs_per_day(),
        plot_status_distribution(),
        plot_avg_repair_cost(),
        plot_ev_kwh_by_location(),
    )


# GRADIO APP

with gr.Blocks(title=f"Garage OS — {STUDENT_NAME}") as demo:

    with gr.Group(elem_id="header-markdown"):
        gr.Markdown(f"# 🏎️ GARAGE MANAGEMENT OS")
        gr.Markdown(f"OPERATOR: **{STUDENT_NAME.upper()}** &nbsp;|&nbsp; SYSTEM STATUS: ONLINE &nbsp;|&nbsp; BACKEND: `{API_BASE_URL}`")

    # CARS
    with gr.Tab("🚗 Cars"):
        gr.Markdown("## Car Management")

        with gr.Row():
            car_table = gr.DataFrame(label="All Cars", interactive=False)

        with gr.Row():
            refresh_cars_btn = gr.Button("🔄 Refresh Cars", variant="secondary")

        gr.Markdown("### ➕ Add Car")
        with gr.Row():
            c_plate = gr.Textbox(label="License Plate *")
            c_brand = gr.Textbox(label="Brand *")
            c_model = gr.Textbox(label="Model *")
            c_owner = gr.Textbox(label="Owner Name *")
        with gr.Row():
            c_km = gr.Number(label="Kilometrage", value=0)
            c_threshold = gr.Number(label="Maintenance Threshold (km)", value=150000)
            c_is_ev = gr.Checkbox(label="Is EV?")
        add_car_btn = gr.Button("Add Car", variant="primary")

        gr.Markdown("### 📏 Update Kilometrage")
        with gr.Row():
            km_car_dd = gr.Dropdown(label="Select Car", choices=_car_choices())
            km_new = gr.Number(label="New Kilometrage (km)", value=0)
        update_km_btn = gr.Button("Update Kilometrage", variant="primary")

        gr.Markdown("### 🅿️ Assign Service Bay")
        with gr.Row():
            bay_car_dd = gr.Dropdown(label="Select Car", choices=_car_choices())
            bay_dd = gr.Dropdown(label="Select Bay", choices=_bay_choices())
        assign_bay_btn = gr.Button("Assign Bay", variant="primary")

        gr.Markdown("### 🗑️ Delete Car")
        del_car_dd = gr.Dropdown(label="Select Car to Delete", choices=_car_choices())
        del_car_btn = gr.Button("Delete Car", variant="stop")

        refresh_cars_btn.click(refresh_cars, outputs=[car_table])
        demo.load(refresh_cars, outputs=[car_table])

    # REPAIRS 
    with gr.Tab("🔧 Repairs"):
        gr.Markdown("## Repair Management")

        with gr.Row():
            repair_table = gr.DataFrame(label="All Repairs", interactive=False)
        refresh_repairs_btn = gr.Button("🔄 Refresh Repairs", variant="secondary")

        gr.Markdown("### ⚠️ Warning Repairs")
        warning_table = gr.DataFrame(label="Warning Repairs", interactive=False)
        refresh_warnings_btn = gr.Button("🔄 Refresh Warnings", variant="secondary")

        gr.Markdown("### ➕ Add Repair")
        with gr.Row():
            r_car_dd = gr.Dropdown(label="Car *", choices=_car_choices())
            r_type = gr.Textbox(label="Repair Type *")
            r_mechanic = gr.Textbox(label="Mechanic *")
        with gr.Row():
            r_status = gr.Dropdown(label="Status", choices=["Pending", "Warning", "In Progress", "Completed"],
                                   value="Pending")
            r_cost = gr.Number(label="Cost Estimate (€)", value=None)
            r_bay_dd = gr.Dropdown(label="Service Bay (optional)", choices=[""] + _bay_choices())
        add_repair_btn = gr.Button("Add Repair", variant="primary")

        gr.Markdown("### ▶️ Start / ✅ Complete Repair")
        with gr.Row():
            action_repair_dd = gr.Dropdown(label="Select Repair", choices=_repair_choices())
            action_bay_dd = gr.Dropdown(label="Bay for Start (optional)", choices=[""] + _bay_choices())
            action_final_cost = gr.Number(label="Final Cost for Complete (€)", value=None)
        with gr.Row():
            start_repair_btn = gr.Button("▶️ Start Repair", variant="primary")
            complete_repair_btn = gr.Button("✅ Complete Repair", variant="primary")

        gr.Markdown("### ✏️ Update Repair")
        with gr.Row():
            upd_repair_dd = gr.Dropdown(label="Select Repair", choices=_repair_choices())
            upd_mechanic = gr.Textbox(label="New Mechanic")
            upd_status = gr.Dropdown(label="New Status",
                                     choices=["", "Pending", "Warning", "In Progress", "Completed"])
        with gr.Row():
            upd_cost = gr.Number(label="New Cost Estimate (€)", value=None)
            upd_final = gr.Number(label="New Final Cost (€)", value=None)
        update_repair_btn = gr.Button("Update Repair", variant="primary")

        gr.Markdown("### 🗑️ Delete Repair")
        with gr.Row():
            del_repair_dd = gr.Dropdown(label="Select Repair", choices=_repair_choices())
        del_repair_btn = gr.Button("Delete Repair", variant="stop")

        refresh_repairs_btn.click(refresh_repairs, outputs=[repair_table])
        refresh_warnings_btn.click(refresh_warnings, outputs=[warning_table])
        add_repair_btn.click(add_repair,
                             inputs=[r_car_dd, r_type, r_mechanic, r_status, r_cost, r_bay_dd],
                             outputs=[repair_table, action_repair_dd, upd_repair_dd, del_repair_dd])
        start_repair_btn.click(start_repair, inputs=[action_repair_dd, action_bay_dd], outputs=[repair_table, action_repair_dd, upd_repair_dd, del_repair_dd])
        complete_repair_btn.click(complete_repair, inputs=[action_repair_dd, action_final_cost], outputs=[repair_table, action_repair_dd, upd_repair_dd, del_repair_dd])
        update_repair_btn.click(update_repair,
                                inputs=[upd_repair_dd, upd_mechanic, upd_status, upd_cost, upd_final],
                                outputs=[repair_table, action_repair_dd, upd_repair_dd, del_repair_dd])
        del_repair_btn.click(delete_repair, inputs=[del_repair_dd], outputs=[repair_table, action_repair_dd, upd_repair_dd, del_repair_dd])
        demo.load(refresh_repairs, outputs=[repair_table])
        demo.load(refresh_warnings, outputs=[warning_table])

        add_car_btn.click(
            add_car,
            inputs=[c_plate, c_brand, c_model, c_owner, c_km, c_threshold, c_is_ev],
            outputs=[car_table, km_car_dd, bay_car_dd, r_car_dd, del_car_dd],
        )
        update_km_btn.click(update_kilometrage, inputs=[km_car_dd, km_new], outputs=[car_table])
        assign_bay_btn.click(assign_bay_to_car, inputs=[bay_car_dd, bay_dd], outputs=[car_table])
        del_car_btn.click(delete_car, inputs=[del_car_dd], outputs=[car_table, km_car_dd, bay_car_dd, r_car_dd, del_car_dd])

    # SERVICE BAYS
    with gr.Tab("Service Bays"):
        gr.Markdown("## Service Bay Management")

        bay_table = gr.DataFrame(label="Service Bays", interactive=False)
        refresh_bays_btn = gr.Button("🔄 Refresh Bays", variant="secondary")

        gr.Markdown("### ➕ Add Bay")
        with gr.Row():
            b_name = gr.Textbox(label="Bay Name *")
            b_type = gr.Dropdown(label="Bay Type", choices=["General", "EV", "Heavy", "Inspection"],
                                 value="General")
            b_notes = gr.Textbox(label="Notes")
        add_bay_btn = gr.Button("Add Bay", variant="primary")

        gr.Markdown("### 🚗 Assign Car to Bay")
        with gr.Row():
            assign_bay_dd = gr.Dropdown(label="Select Bay", choices=_bay_choices())
            assign_car_dd = gr.Dropdown(label="Select Car", choices=_car_choices())
        assign_car_bay_btn = gr.Button("Assign Car to Bay", variant="primary")

        gr.Markdown("### 🔓 Release Car from Bay")
        release_bay_dd = gr.Dropdown(label="Select Bay to Release", choices=_bay_choices())
        release_bay_btn = gr.Button("Release Car from Bay", variant="secondary")

        gr.Markdown("### 🗑️ Delete Bay")
        del_bay_dd = gr.Dropdown(label="Select Bay to Delete", choices=_bay_choices())
        del_bay_btn = gr.Button("Delete Bay", variant="stop")

        refresh_bays_btn.click(refresh_bays, outputs=[bay_table])
        add_bay_btn.click(
            add_bay,
            inputs=[b_name, b_type, b_notes],
            outputs=[bay_table, assign_bay_dd, release_bay_dd, del_bay_dd, bay_dd, r_bay_dd, action_bay_dd],
        )
        assign_car_bay_btn.click(assign_bay_to_car, inputs=[assign_car_dd, assign_bay_dd], outputs=[bay_table])
        release_bay_btn.click(
            release_bay,
            inputs=[release_bay_dd],
            outputs=[bay_table, assign_bay_dd, release_bay_dd, del_bay_dd, bay_dd, r_bay_dd, action_bay_dd],
        )
        del_bay_btn.click(
            delete_bay,
            inputs=[del_bay_dd],
            outputs=[bay_table, assign_bay_dd, release_bay_dd, del_bay_dd, bay_dd, r_bay_dd, action_bay_dd],
        )
        demo.load(refresh_bays, outputs=[bay_table])

    # EV
    with gr.Tab("⚡ EV Management"):
        gr.Markdown("## EV Data & Battery Management")

        ev_profiles_table = gr.DataFrame(label="EV Profiles", interactive=False)
        refresh_ev_btn = gr.Button("🔄 Refresh EV Profiles", variant="secondary")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🔋 Charge Cycles")
                ev_car_dd = gr.Dropdown(label="Select EV", choices=_ev_car_choices())
                cycles_table = gr.DataFrame(label="Charge Cycles", interactive=False)
                load_cycles_btn = gr.Button("Load Cycles", variant="secondary")

                gr.Markdown("#### ➕ Add Charge Cycle")
                with gr.Row():
                    cc_date = gr.Textbox(label="Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
                    cc_start = gr.Number(label="Start %", value=20, minimum=0, maximum=100)
                    cc_end = gr.Number(label="End %", value=80, minimum=0, maximum=100)
                with gr.Row():
                    cc_kwh = gr.Number(label="kWh Charged", value=30)
                    cc_location = gr.Textbox(label="Location", value="Garage EV Bay")
                add_cycle_btn = gr.Button("Add Charge Cycle", variant="primary")

            with gr.Column():
                gr.Markdown("### 🩺 Battery Health")
                ev_car_dd2 = gr.Dropdown(label="Select EV", choices=_ev_car_choices())
                battery_log_table = gr.DataFrame(label="Battery Logs", interactive=False)
                load_battery_btn = gr.Button("Load Battery Logs", variant="secondary")

                gr.Markdown("#### ✏️ Update Battery Health")
                with gr.Row():
                    bh_new = gr.Number(label="New Health (%)", value=90, minimum=0, maximum=100)
                    bh_reason = gr.Textbox(label="Reason")
                update_bh_btn = gr.Button("Update Battery Health", variant="primary")

        refresh_ev_btn.click(refresh_ev_profiles, outputs=[ev_profiles_table])
        load_cycles_btn.click(get_charge_cycles, inputs=[ev_car_dd], outputs=[cycles_table])
        add_cycle_btn.click(add_charge_cycle,
                            inputs=[ev_car_dd, cc_date, cc_start, cc_end, cc_kwh, cc_location],
                            outputs=[cycles_table])
        load_battery_btn.click(get_battery_logs, inputs=[ev_car_dd2], outputs=[battery_log_table])
        update_bh_btn.click(update_battery_health,
                            inputs=[ev_car_dd2, bh_new, bh_reason],
                            outputs=[battery_log_table])
        demo.load(refresh_ev_profiles, outputs=[ev_profiles_table])

    # LOGS
    with gr.Tab("📋 Logs"):
        gr.Markdown("## System Logs")

        with gr.Row():
            log_entity_filter = gr.Dropdown(
                label="Filter by Entity Type",
                choices=["All", "car", "repair", "service_bay", "ev", "charge_cycle"],
                value="All",
            )
            log_action_filter = gr.Textbox(label="Filter by Action (partial match)")
        refresh_logs_btn = gr.Button("🔄 Load / Refresh Logs", variant="primary")
        logs_table = gr.DataFrame(label="System Logs", interactive=False)

        refresh_logs_btn.click(refresh_logs, inputs=[log_entity_filter, log_action_filter], outputs=[logs_table])
        demo.load(lambda: refresh_logs("All", ""), outputs=[logs_table])

    # VISUALISATIONS
    with gr.Tab("📊 Visualisations"):
        gr.Markdown("## Garage Analytics")
        load_plots_btn = gr.Button("🔄 Load All Plots", variant="primary")

        with gr.Row():
            plot_rpd = gr.Plot(label="Repairs per Day")
            plot_sd = gr.Plot(label="Status Distribution")
        with gr.Row():
            plot_arc = gr.Plot(label="Avg Repair Cost by Status")
            plot_ev_loc = gr.Plot(label="EV: kWh by Charging Location")

        gr.Markdown("### ⚡ EV Plots per Vehicle")
        with gr.Row():
            ev_plot_dd = gr.Dropdown(label="Select EV for Plots", choices=_ev_car_choices())
        with gr.Row():
            plot_bh_btn = gr.Button("Battery Health Over Time", variant="primary")
            plot_cc_btn = gr.Button("Charge Cycles per Month", variant="primary")
        with gr.Row():
            ev_plot1 = gr.Plot(label="Battery Health")
            ev_plot2 = gr.Plot(label="Charge Cycles")

        plot_bh_btn.click(ev_battery_health_plot, inputs=[ev_plot_dd], outputs=[ev_plot1])
        plot_cc_btn.click(ev_charge_cycles_plot, inputs=[ev_plot_dd], outputs=[ev_plot2])

        load_plots_btn.click(load_all_plots, outputs=[plot_rpd, plot_sd, plot_arc, plot_ev_loc])
        demo.load(load_all_plots, outputs=[plot_rpd, plot_sd, plot_arc, plot_ev_loc])


if __name__ == "__main__":
    demo.launch(server_name=FRONTEND_HOST, server_port=FRONTEND_PORT, theme=theme, css=custom_css)
