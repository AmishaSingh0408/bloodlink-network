"""
BloodLink Network - synthetic hospital blood inventory generator.

Generates 90 days of daily blood inventory data (opening stock, demand,
received, closing stock) for a network of fake hospitals, one row per
hospital/blood-type/day.

Run: python data_sim/generate_data.py
Output: data/hospital_blood_data.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime

NUM_DAYS = 90

BLOOD_TYPE_WEIGHTS = {
    "O+": 0.35, "O-": 0.07,
    "A+": 0.30, "A-": 0.06,
    "B+": 0.10, "B-": 0.03,
    "AB+": 0.06, "AB-": 0.03,
}

# name, city, lat, lon, hospital_type, bed_capacity, avg_daily_demand
HOSPITALS = [
    ("City General Hospital",      "Hyderabad",  17.3850, 78.4867, "General",        400, 25),
    ("Sunrise Multispecialty",     "Hyderabad",  17.4239, 78.4738, "Multispecialty", 300, 15),
    ("Care Trust Hospital",        "Vijayawada", 16.5062, 80.6480, "General",        350, 18),
    ("Apex Medical Center",        "Vijayawada", 16.5193, 80.6305, "Multispecialty", 250, 12),
    ("Lifeline Hospital",          "Guntur",     16.3067, 80.4365, "General",        200, 10),
    ("Metro Health Institute",     "Hyderabad",  17.4483, 78.3915, "Multispecialty", 450, 20),
    ("St. Mary's Medical College", "Vijayawada", 16.4900, 80.6100, "Teaching",       500, 22),
    ("Regional Trauma Center",     "Guntur",     16.3150, 80.4500, "Trauma",         600, 14),
]

HOSPITAL_TYPE_MULTIPLIER = {"General": 1.0, "Multispecialty": 1.05, "Teaching": 1.10, "Trauma": 1.20}


def generate_blood_type_series(avg_demand, blood_weight, hospital_type, seed):
    """Generate 90 days of opening/demand/received/closing stock for one
    hospital + one blood type."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(end=datetime.today(), periods=NUM_DAYS, freq="D")
    type_mult = HOSPITAL_TYPE_MULTIPLIER[hospital_type]

    opening = np.zeros(NUM_DAYS)
    demand = np.zeros(NUM_DAYS)
    received = np.zeros(NUM_DAYS)
    closing = np.zeros(NUM_DAYS)
    emergency = np.zeros(NUM_DAYS, dtype=int)

    opening[0] = avg_demand * 14 * blood_weight  # ~2 weeks of stock to start

    for i, day in enumerate(days):
        if i > 0:
            opening[i] = closing[i - 1]

        weekday_factor = 1.15 if day.weekday() < 5 else 0.80
        emergency[i] = int(rng.random() < 0.04)
        surge_factor = 2.5 if emergency[i] else 1.0

        expected_demand = avg_demand * type_mult * blood_weight * weekday_factor * surge_factor
        demand[i] = max(0, round(rng.normal(expected_demand, max(1, expected_demand * 0.20))))

        expected_supply = avg_demand * blood_weight * 1.05
        received[i] = max(0, round(rng.normal(expected_supply, max(1, expected_supply * 0.25))))

        closing[i] = max(0, opening[i] - demand[i] + received[i])

    return days, opening.round().astype(int), demand.astype(int), received.astype(int), closing.round().astype(int), emergency


def main():
    rows = []
    for h_idx, (name, city, lat, lon, htype, beds, avg_demand) in enumerate(HOSPITALS):
        for b_idx, (blood_type, weight) in enumerate(BLOOD_TYPE_WEIGHTS.items()):
            seed = h_idx * 100 + b_idx
            days, opening, demand, received, closing, emergency = generate_blood_type_series(
                avg_demand, weight, htype, seed
            )
            for i, day in enumerate(days):
                rows.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "hospital": name,
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "hospital_type": htype,
                    "bed_capacity": beds,
                    "blood_type": blood_type,
                    "opening_stock": int(opening[i]),
                    "units_demanded": int(demand[i]),
                    "units_received": int(received[i]),
                    "closing_stock": int(closing[i]),
                    "emergency_event": int(emergency[i]),
                })

    df = pd.DataFrame(rows)
    df.to_csv("data/hospital_blood_data.csv", index=False)

    print(f"Generated {len(df)} rows across {len(HOSPITALS)} hospitals -> data/hospital_blood_data.csv")
    print(df.head(10))
    print("\nShape:", df.shape)
    print("Emergency days flagged:", df["emergency_event"].sum())


if __name__ == "__main__":
    main()