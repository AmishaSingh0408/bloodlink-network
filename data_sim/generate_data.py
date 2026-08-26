"""
Simulated hospital data generator.

Generates 90 days of daily blood-unit inventory and demand data for a
network of fake hospitals. This stands in for real hospital data until
you get access to the real thing (or as your permanent demo dataset).

Run: python data_sim/generate_data.py
Output: data/hospital_blood_data.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---- Config ----
NUM_DAYS = 90
BLOOD_TYPES = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]

# Each hospital: (name, city, lat, lon, avg_daily_demand, base_stock)
# Coordinates are real approximate locations so distance calcs later are meaningful.
HOSPITALS = [
    ("City General Hospital",     "Hyderabad",  17.3850, 78.4867, 25, 400),
    ("Sunrise Multispecialty",    "Hyderabad",  17.4239, 78.4738, 15, 250),
    ("Care Trust Hospital",       "Vijayawada", 16.5062, 80.6480, 18, 280),
    ("Apex Medical Center",       "Vijayawada", 16.5193, 80.6305, 12, 200),
    ("Lifeline Hospital",         "Guntur",     16.3067, 80.4365, 10, 180),
    ("Metro Health Institute",    "Hyderabad",  17.4483, 78.3915, 20, 320),
    ("St. Mary's Medical College","Vijayawada", 16.4900, 80.6100, 22, 350),
    ("Regional Trauma Center",    "Guntur",     16.3150, 80.4500, 14, 220),
]


def generate_hospital_series(base_stock, avg_demand, seed):
    """Generate one hospital's daily stock + demand with seasonality,
    weekend dips, and occasional shortage/surge events."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(end=datetime.today(), periods=NUM_DAYS, freq="D")

    stock = np.zeros(NUM_DAYS)
    demand = np.zeros(NUM_DAYS)
    stock[0] = base_stock

    for i, day in enumerate(days):
        # Weekly seasonality: more demand mid-week, less on weekends
        weekday_factor = 1.15 if day.weekday() < 5 else 0.8

        # Occasional surge event (accident cluster, outbreak) - 4% chance/day
        surge = 2.5 if rng.random() < 0.04 else 1.0

        daily_demand = max(0, rng.normal(avg_demand * weekday_factor * surge, avg_demand * 0.2))
        daily_supply = max(0, rng.normal(avg_demand * 1.05, avg_demand * 0.25))  # donations/restock

        demand[i] = round(daily_demand)
        if i > 0:
            stock[i] = max(0, stock[i - 1] - demand[i] + daily_supply)

    return days, stock.round().astype(int), demand.astype(int)


def main():
    rows = []
    for idx, (name, city, lat, lon, avg_demand, base_stock) in enumerate(HOSPITALS):
        days, stock, demand = generate_hospital_series(base_stock, avg_demand, seed=idx)
        for i, day in enumerate(days):
            # Split total stock/demand across blood types (not equal - O+ and A+ dominate)
            weights = np.array([0.35, 0.07, 0.30, 0.06, 0.10, 0.03, 0.06, 0.03])
            for bt, w in zip(BLOOD_TYPES, weights):
                rows.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "hospital": name,
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "blood_type": bt,
                    "units_available": int(round(stock[i] * w)),
                    "units_demanded": int(round(demand[i] * w)),
                })

    df = pd.DataFrame(rows)
    df.to_csv("data/hospital_blood_data.csv", index=False)
    print(f"Generated {len(df)} rows across {len(HOSPITALS)} hospitals -> data/hospital_blood_data.csv")
    print(df.head(10))


if __name__ == "__main__":
    main()