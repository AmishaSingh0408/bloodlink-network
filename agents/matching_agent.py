import pandas as pd
from math import radians, sin, cos, sqrt, atan2, ceil

from agents.forecast_agent import (
    calculate_safety_stock,
    create_features,
    prepare_ml_data,
    split_data,
    train_random_forest,
    evaluate_model,
    forecast_next_7_days
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "data/hospital_blood_data.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load the latest hospital blood inventory data."""

    df = pd.read_csv(DATA_PATH)

    # Convert date column to pandas datetime.
    df["date"] = pd.to_datetime(df["date"])

    return df


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two geographic coordinates
    using the Haversine formula.

    Returns distance in kilometers.
    """

    R = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# ============================================================
# FIND SUPPLIER HOSPITALS
# ============================================================

def get_surplus_hospitals(
    df,
    blood_type,
    shortage_hospital,
    inventory_state,
    model,
    feature_columns
):
    """
    Find hospitals that are predicted to have surplus blood
    during the shortage period.
    """

    suppliers = []

    # Get all hospitals except the shortage hospital.
    hospitals = df["hospital"].unique()

    for hospital in hospitals:

        if hospital == shortage_hospital:
            continue

        # Calculate projected inventory for this hospital.
        projected = calculate_projected_inventory(
            df,
            model,
            feature_columns,
            hospital,
            blood_type
        )

        if projected.empty:
            continue

        # ----------------------------------------------------
        # Use the final day of the 7-day forecast
        # ----------------------------------------------------

        future = projected.iloc[-1]

        projected_stock = future["projected_stock"]
        safety_stock = future["safety_stock"]

        future_surplus = (
            projected_stock - safety_stock
        )

        if future_surplus <= 0:
            continue

        # ----------------------------------------------------
        # Find hospital coordinates
        # ----------------------------------------------------

        hospital_data = df[
            df["hospital"] == hospital
        ].iloc[-1]

        shortage_data = df[
            df["hospital"] == shortage_hospital
        ].iloc[-1]

        # ----------------------------------------------------
        # Calculate distance
        # ----------------------------------------------------

        distance = haversine_distance(
            shortage_data["lat"],
            shortage_data["lon"],
            hospital_data["lat"],
            hospital_data["lon"]
        )

        suppliers.append({
            "hospital": hospital,
            "city": hospital_data["city"],
            "lat": hospital_data["lat"],
            "lon": hospital_data["lon"],
            "projected_stock": projected_stock,
            "safety_stock": safety_stock,
            "surplus": future_surplus,
            "distance_km": distance
        })

    if not suppliers:
        return pd.DataFrame()

    return pd.DataFrame(suppliers)

# ============================================================
# RANK SUPPLIERS
# ============================================================

def rank_suppliers(suppliers):
    """
    Rank suppliers by geographic distance.

    Closest hospital gets highest priority.
    """

    if suppliers.empty:
        return suppliers

    return suppliers.sort_values(
        "distance_km",
        ascending=True
    ).reset_index(drop=True)


# ============================================================
# CALCULATE REQUIRED UNITS
# ============================================================

def calculate_required_units(
    projected_stock,
    safety_stock
):
    """
    Calculate how many whole blood units are required
    to bring inventory back to safety stock.
    """

    required_units = (
        safety_stock - projected_stock
    )

    if required_units <= 0:
        return 0

    return ceil(required_units)


# ============================================================
# CALCULATE TRANSFER UNITS
# ============================================================

def calculate_transfer_units(
    required_units,
    supplier_surplus
):
    """
    Calculate the number of whole blood units that can
    actually be transferred.

    We never transfer fractional blood units.
    """

    return min(
        int(required_units),
        int(supplier_surplus)
    )


# ============================================================
# FIND BEST SUPPLIERS
# ============================================================


def find_best_suppliers(
    suppliers,
    required_units,
    inventory_state,
    blood_type,
    max_distance_km=300
):
    """
    Allocate blood from projected future supplier surplus.

    Suppliers are processed from nearest to farthest.
    Only suppliers within the configured distance are considered.
    """

    if suppliers.empty:
        return []

    suppliers = suppliers.copy()

    # Keep only suppliers within the permitted distance
    suppliers = suppliers[
        (suppliers["distance_km"] <= max_distance_km) &
        (suppliers["surplus"] > 0)
    ].sort_values("distance_km")

    if suppliers.empty:
        return []

    recommendations = []
    remaining_units = int(required_units)

    for _, supplier in suppliers.iterrows():

        if remaining_units <= 0:
            break

        supplier_hospital = supplier["hospital"]
        key = (supplier_hospital, blood_type)

        # Get the supplier's latest available future surplus
        future_surplus = inventory_state.get(
            key,
            supplier["surplus"]
        )

        if future_surplus <= 0:
            continue

        # Calculate transferable whole units
        transfer_units = calculate_transfer_units(
            remaining_units,
            future_surplus
        )

        if transfer_units <= 0:
            continue

        # Update supplier inventory to prevent duplicate allocation
        inventory_state[key] = max(
            0,
            future_surplus - transfer_units
        )

        recommendations.append({
            "supplier_hospital": supplier_hospital,
            "supplier_city": supplier["city"],
            "distance_km": round(
                float(supplier["distance_km"]), 2
            ),
            "projected_stock": round(
                float(supplier["projected_stock"]), 2
            ),
            "safety_stock": round(
                float(supplier["safety_stock"]), 2
            ),
            "future_surplus": int(future_surplus),
            "recommended_transfer": int(transfer_units)
        })

        remaining_units -= transfer_units

    return recommendations

# ============================================================
# FIND ALL CURRENT SHORTAGES
# ============================================================

def find_all_shortages(df):
    """
    Find all hospital + blood type combinations
    whose current inventory is below safety stock.
    """

    results = []

    hospitals = df["hospital"].unique()
    blood_types = df["blood_type"].unique()

    for hospital in hospitals:

        for blood_type in blood_types:

            series = df[
                (df["hospital"] == hospital)
                & (df["blood_type"] == blood_type)
            ].copy()

            if series.empty:
                continue

            # ------------------------------------------------
            # Calculate safety stock
            # ------------------------------------------------

            safety_stock = calculate_safety_stock(
                df,
                hospital,
                blood_type,
                buffer_days=3
            )

            # ------------------------------------------------
            # Get latest inventory
            # ------------------------------------------------

            current_stock = (
                series
                .sort_values("date")
                .iloc[-1]["closing_stock"]
            )

            # ------------------------------------------------
            # Calculate required units
            # ------------------------------------------------

            required_units = calculate_required_units(
                current_stock,
                safety_stock
            )

            if required_units > 0:

                results.append({
                    "hospital": hospital,
                    "blood_type": blood_type,
                    "current_stock": current_stock,
                    "safety_stock": safety_stock,
                    "required_units": required_units
                })

    return results

def find_forecasted_shortages(
    df,
    model,
    feature_columns
):
    """
    Find hospital + blood type combinations that are
    predicted to fall below safety stock within the next 7 days.
    """

    results = []

    hospitals = df["hospital"].unique()
    blood_types = df["blood_type"].unique()

    for hospital in hospitals:

        for blood_type in blood_types:

            # ------------------------------------------------
            # Get historical series
            # ------------------------------------------------

            series = df[
                (df["hospital"] == hospital)
                & (df["blood_type"] == blood_type)
            ].copy()

            if series.empty:
                continue

            series = series.sort_values("date")

            # ------------------------------------------------
            # Current stock
            # ------------------------------------------------

            current_stock = series.iloc[-1]["closing_stock"]

            # ------------------------------------------------
            # Safety stock
            # ------------------------------------------------

            safety_stock = calculate_safety_stock(
                df,
                hospital,
                blood_type,
                buffer_days=3
            )

            # ------------------------------------------------
            # Expected daily supply
            # ------------------------------------------------

            expected_daily_supply = (
                series["units_received"].mean()
            )

            # ------------------------------------------------
            # Forecast next 7 days
            # ------------------------------------------------

            forecast = forecast_next_7_days(
                model,
                df,
                hospital,
                blood_type,
                feature_columns
            )

            # ------------------------------------------------
            # Project inventory
            # ------------------------------------------------

            projected_stock = current_stock

            shortage_day = None
            shortage_stock = None

            for _, row in forecast.iterrows():

                projected_stock += expected_daily_supply
                projected_stock -= row["predicted_demand"]

                if projected_stock < safety_stock:

                    shortage_day = row["date"]
                    shortage_stock = projected_stock

                    break

            # ------------------------------------------------
            # Record shortage
            # ------------------------------------------------

            if shortage_day is not None:

                required_units = calculate_required_units(
                    shortage_stock,
                    safety_stock
                )

                results.append({
                    "hospital": hospital,
                    "blood_type": blood_type,
                    "current_stock": round(
                        current_stock,
                        2
                    ),
                    "safety_stock": round(
                        safety_stock,
                        2
                    ),
                    "shortage_date": shortage_day,
                    "projected_stock": round(
                        shortage_stock,
                        2
                    ),
                    "required_units": required_units
                })

    return results

# ============================================================
# MAIN
# ============================================================

def calculate_projected_inventory(
    df,
    model,
    feature_columns,
    hospital,
    blood_type
):
    """
    Calculate projected inventory for the next 7 days.
    """

    series = df[
        (df["hospital"] == hospital)
        & (df["blood_type"] == blood_type)
    ].copy()

    if series.empty:
        return pd.DataFrame()

    series = series.sort_values("date")

    # Current inventory
    current_stock = series.iloc[-1]["closing_stock"]

    # Expected daily supply
    expected_daily_supply = (
        series["units_received"].mean()
    )

    # Safety stock
    safety_stock = calculate_safety_stock(
        df,
        hospital,
        blood_type,
        buffer_days=3
    )

    # Demand forecast
    forecast = forecast_next_7_days(
        model,
        df,
        hospital,
        blood_type,
        feature_columns
    )

    projected_stock = current_stock

    results = []

    for _, row in forecast.iterrows():

        projected_stock += expected_daily_supply
        projected_stock -= row["predicted_demand"]

        results.append({
            "date": row["date"],
            "hospital": hospital,
            "blood_type": blood_type,
            "predicted_demand": row["predicted_demand"],
            "expected_supply": expected_daily_supply,
            "projected_stock": projected_stock,
            "safety_stock": safety_stock
        })

    return pd.DataFrame(results)

def generate_matching_results():
    df = load_data()

    # Train forecasting model
    ml_data = prepare_ml_data(df)

    train_data, test_data = split_data(
        ml_data,
        test_size=0.2
    )

    model, feature_columns = train_random_forest(
        train_data
    )

    mae = evaluate_model(
        model,
        test_data,
        feature_columns
    )[0]

    # Build future surplus inventory state
    inventory_state = {}

    for hospital in df["hospital"].unique():
        for blood_type in df["blood_type"].unique():

                inventory = calculate_projected_inventory(
                    df,
                    model,
                    feature_columns,
                    hospital,
                    blood_type
                )

                if inventory.empty:
                    continue

                latest_projection = inventory.iloc[-1]

                future_surplus = max(
                    0,
                    latest_projection["projected_stock"]
                    - latest_projection["safety_stock"]
                )

                inventory_state[(hospital, blood_type)] = int(
                    future_surplus
                )

        # Find forecasted shortages
    shortages = find_forecasted_shortages(
            df,
            model,
            feature_columns
        )
    
    
    # Generate supplier recommendations for each shortage
    matching_results = []

    for shortage in shortages:

        blood_type = shortage["blood_type"]
        shortage_hospital = shortage["hospital"]
        required_units = shortage["required_units"]

        # Find hospitals with available future surplus
        suppliers = get_surplus_hospitals(
            df,
            blood_type=blood_type,
            shortage_hospital=shortage_hospital,
            inventory_state=inventory_state,
            model=model,
            feature_columns=feature_columns
        )

        # Rank suppliers by distance
        ranked_suppliers = rank_suppliers(suppliers)

        # Allocate available blood units
        recommendations = find_best_suppliers(
            ranked_suppliers,
            required_units,
            inventory_state,
            blood_type
        )

        total_transferred = sum(
            item["recommended_transfer"]
            for item in recommendations
        )

        remaining_units = max(
            0,
            required_units - total_transferred
        )

        matching_results.append({
            "hospital": shortage_hospital,
            "blood_type": blood_type,
            "shortage_date": str(shortage["shortage_date"]),
            "current_stock": shortage["current_stock"],
            "safety_stock": shortage["safety_stock"],
            "required_units": required_units,
            "total_transferred": total_transferred,
            "remaining_units": remaining_units,
            "status": (
                "FULLY FULFILLED"
                if remaining_units == 0
                else "PARTIALLY FULFILLED"
                if total_transferred > 0
                else "UNFULFILLED"
            ),
            "recommendations": recommendations
        })

    return {
            "model": model,
            "feature_columns": feature_columns,
            "mae": mae,
            "data": df,
            "inventory_state": inventory_state,
            "shortages": shortages,
            "matching_results": matching_results
        }
      
def main():

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_data()
        # ========================================================
    # TRAIN FORECASTING MODEL
    # ========================================================

    print("\nTraining demand forecasting model...")

    ml_data = prepare_ml_data(df)

    train_data, test_data = split_data(
        ml_data,
        test_size=0.2
    )

    model, feature_columns = train_random_forest(
        train_data
    )

    mae = evaluate_model(
        model,
        test_data,
        feature_columns
    )[0]

    print(
        f"Forecast model MAE: {mae:.2f} units"
    )

    # --------------------------------------------------------
    # Create network inventory state
    # --------------------------------------------------------
    #
    # This stores the CURRENT remaining inventory for
    # every hospital + blood type.
    #
    # Example:
    #
    # ("Metro Health Institute", "O+") -> 45
    #
    # After transferring 10 units:
    #
    # ("Metro Health Institute", "O+") -> 35
    #
    # --------------------------------------------------------

    inventory_state = {}
    for hospital in df["hospital"].unique():

        for blood_type in df["blood_type"].unique():

            inventory = calculate_projected_inventory(
                df,
                model,
                feature_columns,
                hospital,
                blood_type
            )

            if inventory.empty:
                continue

            latest_projection = inventory.iloc[-1]

            future_surplus = max(
                0,
                latest_projection["projected_stock"]
                - latest_projection["safety_stock"]
            )

            inventory_state[
                (hospital, blood_type)
        ] = int(future_surplus)
    
    # --------------------------------------------------------
    # Find all current shortages
    # --------------------------------------------------------

    shortages = find_forecasted_shortages(
        df,
        model,
        feature_columns
    )

    if not shortages:

        print("\nNo shortages detected.")

        return

    # --------------------------------------------------------
    # Print shortage summary
    # --------------------------------------------------------

    print("\nForecasted Blood Shortages")
    print("---------------------------------")

    print(
        f"Total forecasted shortage cases: "
        f"{len(shortages)}"
    )

    # --------------------------------------------------------
    # Process every shortage
    # --------------------------------------------------------

    for shortage in shortages:

        blood_type = shortage["blood_type"]

        shortage_hospital = shortage["hospital"]

        required_units = shortage["required_units"]

        # ----------------------------------------------------
        # Print shortage
        # ----------------------------------------------------

        print("\nShortage")
        print("--------")

        print(
            f"hospital: {shortage_hospital}"
        )

        print(
            f"blood_type: {blood_type}"
        )

        print(
            f"current_stock: "
            f"{shortage['current_stock']}"
        )

        print(
            f"safety_stock: "
            f"{shortage['safety_stock']}"
        )

        print(
            f"required_units: "
            f"{required_units}"
        )
        
        print(
            f"shortage_date: "
            f"{shortage['shortage_date']}"
        )

        print(
            f"projected_stock: "
            f"{shortage['projected_stock']}"
        )

        # ----------------------------------------------------
        # Find suppliers
        # ----------------------------------------------------

        suppliers = get_surplus_hospitals(
            df,
            blood_type=blood_type,
            shortage_hospital=shortage_hospital,
            inventory_state=inventory_state,
            model=model,
            feature_columns=feature_columns
        )

        # ----------------------------------------------------
        # Rank suppliers
        # ----------------------------------------------------

        ranked_suppliers = rank_suppliers(
            suppliers
        )

        # ----------------------------------------------------
        # Allocate blood
        # ----------------------------------------------------

        recommendations = find_best_suppliers(
            ranked_suppliers,
            required_units,
            inventory_state,
            blood_type
        )

        # ----------------------------------------------------
        # Print recommendations
        # ----------------------------------------------------

        print("\nMatching Recommendations")
        print("-------------------------")

        if recommendations:

            total_transferred = 0

            for recommendation in recommendations:

                print("\nSupplier")
                print("--------")

                print(
                    f"supplier_hospital: "
                    f"{recommendation['supplier_hospital']}"
                )

                print(
                    f"supplier_city: "
                    f"{recommendation['supplier_city']}"
                )

                print(
                    f"distance_km: "
                    f"{recommendation['distance_km']}"
                )

                print(
                    f"future_surplus: "
                    f"{recommendation['future_surplus']}"
                )

                print(
                    f"recommended_transfer: "
                    f"{recommendation['recommended_transfer']}"
                )

                total_transferred += (
                    recommendation[
                        "recommended_transfer"
                    ]
                )

            # ------------------------------------------------
            # Calculate remaining shortage
            # ------------------------------------------------

            remaining_units = (
                required_units
                - total_transferred
            )

            print("\nTransfer Summary")
            print("----------------")

            print(
                f"required_units: "
                f"{required_units}"
            )

            print(
                f"total_transferred: "
                f"{total_transferred}"
            )

            print(
                f"remaining_units: "
                f"{remaining_units}"
            )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            if remaining_units <= 0:

                print(
                    "status: FULLY FULFILLED"
                )

            else:

                print(
                    "status: PARTIALLY FULFILLED"
                )

        else:

            print(
                "No suitable supplier found."
            )

            print(
                "status: UNFULFILLED"
            )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()