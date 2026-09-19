"""
BloodLink Network - demand forecasting agent.

Loads historical hospital blood-demand data and prepares it
for forecasting.
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

DATA_PATH = "data/hospital_blood_data.csv"


def load_data():
    """Load and prepare the hospital blood-demand dataset."""

    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    return df


def get_time_series(df, hospital, blood_type):
    """Return daily demand for one hospital and blood type."""

    series = df[
        (df["hospital"] == hospital) &
        (df["blood_type"] == blood_type)
    ].copy()

    series = series.sort_values("date")

    return series[["date", "units_demanded", "closing_stock"]]


def create_features(df):
    """Create time-series features for each hospital and blood type."""

    df = df.copy()

    df["day_of_week"] = df["date"].dt.dayofweek

    df = df.sort_values(
        ["hospital", "blood_type", "date"]
    )

    grouped = df.groupby(
        ["hospital", "blood_type"]
    )["units_demanded"]

    df["lag_1"] = grouped.shift(1)
    df["lag_7"] = grouped.shift(7)

    df["rolling_7"] = grouped.transform(
        lambda x: x.shift(1).rolling(7).mean()
    )

    df["rolling_14"] = grouped.transform(
        lambda x: x.shift(1).rolling(14).mean()
    )

    return df
  

def prepare_ml_data(df):
    """Prepare leakage-safe features and target for ML forecasting."""

    df = create_features(df)

    df = df.dropna(
        subset=[
            "lag_1",
            "lag_7",
            "rolling_7",
            "rolling_14"
        ]
    )

    features = [
        "lat",
        "lon",
        "bed_capacity",
        "day_of_week",
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_14",
        "hospital",
        "blood_type",
        "hospital_type"
    ]

    ml_data = df[["date"] + features + ["units_demanded"]].copy()

    ml_data = pd.get_dummies(
        ml_data,
        columns=["hospital", "blood_type", "hospital_type"],
        dtype=int
    )

    return ml_data
  

def split_data(df, test_size=0.2):
    """Split data chronologically by date."""

    dates = sorted(df["date"].unique())

    split_index = int(len(dates) * (1 - test_size))

    train_dates = dates[:split_index]
    test_dates = dates[split_index:]

    train = df[df["date"].isin(train_dates)].copy()
    test = df[df["date"].isin(test_dates)].copy()

    return train, test
  
def train_random_forest(train):
    """Train a Random Forest demand forecasting model."""

    feature_columns = [
        column
        for column in train.columns
        if column not in ["date", "units_demanded"]
    ]

    X_train = train[feature_columns]
    y_train = train["units_demanded"]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        max_depth=10
    )

    model.fit(X_train, y_train)

    return model, feature_columns
  

def evaluate_model(model, test, feature_columns):
    """Evaluate the model on future test data."""

    X_test = test[feature_columns]
    y_test = test["units_demanded"]

    predictions = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    return mae, predictions
  

def forecast_next_7_days(model, df, hospital, blood_type, feature_columns):
    """Forecast demand for the next 7 days for one hospital and blood type."""

    series = get_time_series(df, hospital, blood_type).copy()

    history = series["units_demanded"].tolist()
    last_date = series["date"].max()

    hospital_info = df[
        (df["hospital"] == hospital) &
        (df["blood_type"] == blood_type)
    ].iloc[-1]

    forecasts = []

    for day in range(1, 8):
        forecast_date = last_date + pd.Timedelta(days=day)

        lag_1 = history[-1]
        lag_7 = history[-7]

        rolling_7 = sum(history[-7:]) / 7
        rolling_14 = sum(history[-14:]) / 14

        row = {
            "lat": hospital_info["lat"],
            "lon": hospital_info["lon"],
            "bed_capacity": hospital_info["bed_capacity"],
            "day_of_week": forecast_date.dayofweek,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "rolling_7": rolling_7,
            "rolling_14": rolling_14,
            "hospital": hospital,
            "blood_type": blood_type,
            "hospital_type": hospital_info["hospital_type"]
        }

        row_df = pd.DataFrame([row])

        row_df = pd.get_dummies(
            row_df,
            columns=["hospital", "blood_type", "hospital_type"],
            dtype=int
        )

        row_df = row_df.reindex(
            columns=feature_columns,
            fill_value=0
        )

        prediction = model.predict(row_df)[0]
        prediction = max(0, prediction)

        forecasts.append({
            "date": forecast_date,
            "hospital": hospital,
            "blood_type": blood_type,
            "predicted_demand": prediction
        })

        history.append(prediction)

    return pd.DataFrame(forecasts)


def detect_shortage(current_stock, forecast, expected_daily_supply, safety_stock):
    """Calculate projected inventory and classify shortage risk."""
    forecast = forecast.copy()

    forecast["expected_supply"] = expected_daily_supply

    forecast["projected_stock"] = (
        current_stock
        + forecast["expected_supply"].cumsum()
        - forecast["predicted_demand"].cumsum()
    )

    forecast["risk"] = forecast["projected_stock"].apply(
        lambda stock: calculate_risk(stock, safety_stock)
    )

    forecast["shortage"] = forecast["risk"].isin(["HIGH", "CRITICAL"])

    return forecast

def detect_network_shortages(
    model,
    df,
    feature_columns,
    forecast_days=7,
):
    """Scan every hospital and blood type for future shortage risk."""

    shortage_cases = []

    hospitals = df["hospital"].unique()
    blood_types = df["blood_type"].unique()

    for hospital in hospitals:
        for blood_type in blood_types:

            forecast = forecast_next_7_days(
                model,
                df,
                hospital,
                blood_type,
                feature_columns
            )

            forecast = forecast.head(forecast_days)

            current_stock = (
                df[
                    (df["hospital"] == hospital) &
                    (df["blood_type"] == blood_type)
                ]
                .sort_values("date")
                .iloc[-1]["closing_stock"]
            )

            expected_supply = calculate_expected_supply(
                df,
                hospital,
                blood_type
            )
            safety_stock = calculate_safety_stock(
                df,
                hospital,
                blood_type,
                buffer_days=3
            )
            forecast = detect_shortage(
                current_stock,
                forecast,
                expected_supply,
                safety_stock
            )

            # Keep only days where action is required
            risky_days = forecast[
                forecast["shortage"] == True
            ]

            for _, row in risky_days.iterrows():
                shortage_cases.append({
                    "date": row["date"],
                    "hospital": hospital,
                    "blood_type": blood_type,
                    "current_stock": int(current_stock),
                    "predicted_demand": round(
                        row["predicted_demand"], 2
                    ),
                    "expected_supply": round(
                        expected_supply, 2
                    ),
                    "projected_stock": round(
                        row["projected_stock"], 2
                    ),
                    "risk": row["risk"]
                })

    return pd.DataFrame(shortage_cases)
  
def summarize_shortages(shortage_cases):
    """Create one actionable shortage case per hospital and blood type."""

    if shortage_cases.empty:
        return shortage_cases

    summary = (
        shortage_cases
        .sort_values(["hospital", "blood_type", "date"])
        .groupby(["hospital", "blood_type"], as_index=False)
        .first()
    )

    return summary[
        [
            "date",
            "hospital",
            "blood_type",
            "current_stock",
            "predicted_demand",
            "expected_supply",
            "projected_stock",
            "risk"
        ]
    ]
    
def calculate_safety_stock(df, hospital, blood_type, buffer_days=3):
    """Calculate demand-scaled safety stock for a hospital and blood type."""
    series = df[
        (df["hospital"] == hospital) &
        (df["blood_type"] == blood_type)
    ]

    average_daily_demand = series["units_demanded"].mean()

    safety_stock = average_daily_demand * buffer_days

    return safety_stock
  
       
def calculate_risk(projected_stock, safety_stock):
    """Classify inventory risk based on projected stock."""
    if projected_stock < 0:
        return "CRITICAL"
    elif projected_stock < safety_stock:
        return "HIGH"
    elif projected_stock < safety_stock * 1.5:
        return "MEDIUM"
    else:
        return "LOW"
      
         

def calculate_expected_supply(df, hospital, blood_type):
    """Estimate average daily incoming supply from historical data."""

    series = df[
        (df["hospital"] == hospital) &
        (df["blood_type"] == blood_type)
    ]

    return series["units_received"].mean()
  
         
def forecast_moving_average(series, window=7):
    """Generate one-step-ahead forecasts using a moving average."""

    demand = series["units_demanded"]

    forecasts = demand.shift(1).rolling(window=window).mean()

    result = series.copy()
    result["forecast"] = forecasts

    return result
  
  
def evaluate_forecast(result):
    """Calculate MAE for a forecast result."""

    evaluation = result.dropna(subset=["forecast"])

    mae = mean_absolute_error(
        evaluation["units_demanded"],
        evaluation["forecast"]
    )

    return mae
  

def evaluate_all_series(df, window=7):
    """Evaluate the moving-average model for every hospital and blood type."""

    results = []

    for hospital in df["hospital"].unique():
        for blood_type in df["blood_type"].unique():

            series = get_time_series(
                df,
                hospital,
                blood_type
            )

            forecast_result = forecast_moving_average(
                series,
                window
            )

            mae = evaluate_forecast(forecast_result)

            results.append({
                "hospital": hospital,
                "blood_type": blood_type,
                "mae": mae
            })

    return pd.DataFrame(results)
  
    
def main():
    df = load_data()

    ml_data = prepare_ml_data(df)

    train, test = split_data(ml_data)

    model, feature_columns = train_random_forest(train)

    mae, _ = evaluate_model(
        model,
        test,
        feature_columns
    )

    print("Random Forest Forecasting")
    print("--------------------------")
    print("Training rows:", len(train))
    print("Testing rows:", len(test))
    print("Number of features:", len(feature_columns))
    print("MAE:", round(mae, 3), "units")

    hospital = "Regional Trauma Center"
    blood_type = "O-"

    forecast = forecast_next_7_days(
        model,
        df,
        hospital,
        blood_type,
        feature_columns
    )

    current_stock = (
        df[
            (df["hospital"] == hospital) &
            (df["blood_type"] == blood_type)
        ]
        .sort_values("date")
        .iloc[-1]["closing_stock"]
    )

    expected_supply = calculate_expected_supply(
        df,
        hospital,
        blood_type
    )
    safety_stock = calculate_safety_stock(
        df,
        hospital,
        blood_type,
        buffer_days=3
    )
    forecast = detect_shortage(
        current_stock,
        forecast,
        expected_supply,
        safety_stock
    )

    print("\nCurrent stock:", int(current_stock))
    print("Expected daily supply:", round(expected_supply, 2))
    print("Safety stock:", round(safety_stock, 2))
    
    print("\n7-Day Forecast:")
    print(forecast.to_string(index=False))

    # --------------------------------
    # NETWORK SHORTAGE DETECTION
    # --------------------------------

    print("\nNetwork Shortage Detection")
    print("--------------------------")

    shortage_cases = detect_network_shortages(
        model,
        df,
        feature_columns,
        forecast_days=7,
    )

    print("Total shortage-risk cases:", len(shortage_cases))

    if not shortage_cases.empty:
        print("\nShortage Cases:")
        print(shortage_cases.to_string(index=False))

        shortage_summary = summarize_shortages(shortage_cases)

        print("\nShortage Summary")
        print("----------------")

        print(
            shortage_summary.to_string(index=False)
        )
    else:
        print("No shortage risks detected.")


if __name__ == "__main__":
    main()