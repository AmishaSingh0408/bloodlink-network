
from fastapi import FastAPI
from functools import lru_cache
import pandas as pd
from pathlib import Path
import sys
import numpy as np
from fastapi.encoders import jsonable_encoder
from services.email_service import send_email, send_transfer_notification
from services.whatsapp_service import send_transfer_whatsapp_notification

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "agents"))
from matching_agent import generate_matching_results


app = FastAPI(
    title="BloodLink Network API",
    description="AI-powered hospital blood inventory coordination system",
    version="1.0.0"
)

def convert_numpy(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy(value) for key, value in obj.items()}

    elif isinstance(obj, list):
        return [convert_numpy(value) for value in obj]

    elif isinstance(obj, tuple):
        return [convert_numpy(value) for value in obj]

    elif isinstance(obj, np.integer):
        return int(obj)

    elif isinstance(obj, np.floating):
        return float(obj)

    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, np.bool_):
        return bool(obj)

    return obj
  
@lru_cache(maxsize=1)
def get_cached_matching_results():
    return generate_matching_results()
  
   
@app.get("/")
def home():
    return {
        "message": "Welcome to BloodLink Network API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }



from forecast_agent import (
    prepare_ml_data,
    split_data,
    train_random_forest,
    evaluate_model,
    forecast_next_7_days,
    calculate_safety_stock
)

DATA_PATH = BASE_DIR / "data" / "hospital_blood_data.csv"


@app.get("/inventory")
def get_inventory():

    df = pd.read_csv(DATA_PATH)

    latest_date = df["date"].max()

    latest_inventory = df[
        df["date"] == latest_date
    ]

    return latest_inventory.to_dict(
        orient="records"
    )
    

@app.get("/inventory/{hospital_name}")
def get_hospital_inventory(hospital_name: str):

    df = pd.read_csv(DATA_PATH)

    latest_date = df["date"].max()

    latest_inventory = df[
        (df["date"] == latest_date) &
        (df["hospital"].str.lower() == hospital_name.lower())
    ]

    if latest_inventory.empty:
        return {
            "message": "Hospital not found",
            "hospital": hospital_name
        }

    return latest_inventory.to_dict(
        orient="records"
    )


@app.get("/shortages")
def get_shortages():

    df = pd.read_csv(DATA_PATH)

    latest_date = df["date"].max()

    latest_inventory = df[
        df["date"] == latest_date
    ].copy()

    # Calculate average daily demand
    average_demand = (
        df.groupby(["hospital", "blood_type"])["units_demanded"]
        .mean()
        .reset_index(name="average_daily_demand")
    )

    latest_inventory = latest_inventory.merge(
        average_demand,
        on=["hospital", "blood_type"]
    )

    # Safety stock = 3 days of average demand
    latest_inventory["safety_stock"] = (
        latest_inventory["average_daily_demand"] * 3
    )

    shortages = latest_inventory[
        latest_inventory["closing_stock"]
        < latest_inventory["safety_stock"]
    ]

    return shortages.to_dict(orient="records")


@app.get("/forecast/{hospital_name}/{blood_type}")
def get_hospital_forecast(
    hospital_name: str,
    blood_type: str
):
    # Load historical data
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    # Check whether hospital and blood type exist
    hospital_data = df[
        (df["hospital"].str.lower() == hospital_name.lower()) &
        (df["blood_type"].str.upper() == blood_type.upper())
    ]

    if hospital_data.empty:
        return {
            "error": "Hospital or blood type not found"
        }

    # Prepare ML data
    ml_data = prepare_ml_data(df)

    train_data, test_data = split_data(
        ml_data,
        test_size=0.2
    )

    # Train model
    model, feature_columns = train_random_forest(
        train_data
    )

    # Generate 7-day forecast
    forecast = forecast_next_7_days(
        model,
        df,
        hospital_data["hospital"].iloc[0],
        blood_type.upper(),
        feature_columns
    )

    # Calculate safety stock
    safety_stock = calculate_safety_stock(
        df,
        hospital_data["hospital"].iloc[0],
        blood_type.upper(),
        buffer_days=3
    )

    # Convert forecast dates to JSON-compatible strings
    forecast["date"] = forecast["date"].dt.strftime(
        "%Y-%m-%d"
    )

    return {
        "hospital": hospital_data["hospital"].iloc[0],
        "blood_type": blood_type.upper(),
        "safety_stock": round(float(safety_stock), 2),
        "forecast": forecast.to_dict(orient="records")
    }

@app.get("/matching-recommendations")
def matching_recommendations():
    result = get_cached_matching_results()

    response = {
        "mae": float(result["mae"]),
        "total_shortages": int(len(result["shortages"])),
        "matching_results": result["matching_results"]
    }

    return jsonable_encoder(convert_numpy(response))

# ------------------------------------------------------------
# SIMULATED HOSPITAL COORDINATION
# ------------------------------------------------------------

from coordination_agent import (
    build_transfer_requests,
    list_transfer_requests,
    decide_transfer_request,
)


@app.get("/coordination/requests")
def get_coordination_requests():
    """Return simulated transfer requests awaiting human review."""

    # Snapshot existing IDs before building requests
    existing_requests = list_transfer_requests()
    existing_ids = {
        request["request_id"]
        for request in existing_requests
    }

    matching = get_cached_matching_results()

    requests = build_transfer_requests(
        matching["matching_results"]
    )

    # Identify requests newly created during this call
    new_requests = [
        request
        for request in requests
        if request["request_id"] not in existing_ids
    ]

    # Send one summary email only when new requests are created
    if new_requests:
        try:
            summary_lines = [
                f"- {request['shortage_hospital']} needs "
                f"{request['recommended_units']} units of "
                f"{request['blood_type']} from "
                f"{request['supplier_hospital']} "
                f"(Priority: {request['priority']})"
                for request in new_requests
            ]

            email_body = (
                "BloodLink Network - New Simulated Transfer Requests\\n\\n"
                f"New requests created: {len(new_requests)}\\n\\n"
                + "\\n".join(summary_lines)
                + "\\n\\nThese are simulated recommendations. "
                "No actual blood transfer has been initiated."
            )

            send_email(
                subject="BloodLink: New Transfer Requests Generated",
                body=email_body,
            )

        except Exception:
            # Notification failure must never interrupt the API
            import logging
            logging.exception(
                "Failed to send new transfer request notification"
            )

    return jsonable_encoder(convert_numpy(requests))


@app.post("/coordination/requests/{request_id}/decision")
def review_coordination_request(request_id: str, payload: dict):
    """
    Record an approval or rejection for a simulated request.
    Approval is a workflow status only; no real transfer is initiated.
    """

    decision = payload.get("decision", "")
    note = payload.get("note")

    try:
        result = decide_transfer_request(
            request_id,
            decision,
            note,
        )

    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if result is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Transfer request not found",
        )

    # Send email notification
    try:
        send_transfer_notification(
            request_id=result["request_id"],
            shortage_hospital=result["shortage_hospital"],
            supplier_hospital=result["supplier_hospital"],
            blood_type=result["blood_type"],
            units=result["recommended_units"],
            status=result["status"],
        )

    except Exception:
        import logging
        logging.exception(
            "Failed to send email notification for request %s",
            request_id,
        )

    # Send WhatsApp notification
    try:
        send_transfer_whatsapp_notification(
            request_id=result["request_id"],
            shortage_hospital=result["shortage_hospital"],
            supplier_hospital=result["supplier_hospital"],
            blood_type=result["blood_type"],
            units=result["recommended_units"],
            status=result["status"],
        )

    except Exception:
        import logging
        logging.exception(
            "Failed to send WhatsApp notification for request %s",
            request_id,
        )

    return jsonable_encoder(convert_numpy(result))
