


import streamlit as st
import requests
import pandas as pd

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="BloodLink Network",
    page_icon="🩸",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"
@st.cache_data(ttl=3600)
def get_matching_data():
    response = requests.get(
        f"{API_URL}/matching-recommendations",
        timeout=300
    )
    response.raise_for_status()
    return response.json()

def calculate_severity(row):
    safety_stock = float(row["safety_stock"])
    current_stock = float(row["closing_stock"])

    if safety_stock <= 0:
        return "Low"

    stock_ratio = current_stock / safety_stock

    if stock_ratio <= 0.25:
        return "Critical"
    elif stock_ratio <= 0.50:
        return "High"
    elif stock_ratio <= 0.75:
        return "Medium"
    else:
        return "Low"


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("🩸 BloodLink Network")
st.subheader("AI-Powered Hospital Blood Inventory & Forecasting")

st.markdown(
    "Monitor hospital blood inventory, predict future demand, "
    "detect potential shortages, and coordinate blood transfers."
)

st.caption(
    "Prototype using simulated hospital data. "
    "Forecasts and alerts are not clinically validated."
)

st.divider()

# --------------------------------------------------
# FETCH INVENTORY
# --------------------------------------------------

try:
    response = requests.get(
        f"{API_URL}/inventory",
        timeout=10
    )
    response.raise_for_status()

    inventory = pd.DataFrame(response.json())

    if inventory.empty:
        st.warning("No inventory data available.")

    else:
        # ------------------------------------------
        # DASHBOARD METRICS
        # ------------------------------------------

        total_hospitals = inventory["hospital"].nunique()
        total_units = inventory["closing_stock"].sum()
        total_blood_groups = inventory["blood_type"].nunique()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Hospitals",
            total_hospitals
        )

        col2.metric(
            "Total Blood Units",
            int(total_units)
        )

        col3.metric(
            "Blood Groups",
            total_blood_groups
        )

        st.divider()

        # ------------------------------------------
        # HOSPITAL INVENTORY
        # ------------------------------------------

        st.subheader("Hospital Blood Inventory")

        st.dataframe(
            inventory[
                [
                    "hospital",
                    "blood_type",
                    "closing_stock",
                    "units_demanded"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # BLOOD GROUP STOCK DISTRIBUTION
        # ------------------------------------------

        st.subheader("Blood Group Stock Distribution")

        blood_stock = (
            inventory.groupby("blood_type")["closing_stock"]
            .sum()
            .reset_index()
        )

        st.bar_chart(
            blood_stock,
            x="blood_type",
            y="closing_stock"
        )

        # ------------------------------------------
        # HOSPITAL SHORTAGE MONITORING
        # ------------------------------------------

        st.divider()

        st.header("🚨 Hospital Shortage Monitoring")

        try:
            shortage_response = requests.get(
                f"{API_URL}/shortages",
                timeout=10
            )
            shortage_response.raise_for_status()

            shortages = pd.DataFrame(
                shortage_response.json()
            )

            if shortages.empty:
                st.success(
                    "No hospitals currently below safety stock."
                )

            else:
                st.warning(
                    f"{len(shortages)} potential shortage "
                    "records detected."
                )

                
            # Calculate shortage severity
            shortages["severity"] = shortages.apply(
                  calculate_severity,
                  axis=1
              )

              # Add visual indicators
            severity_icons = {
                  "Critical": "🔴 Critical",
                  "High": "🟠 High",
                  "Medium": "🟡 Medium",
                  "Low": "🟢 Low"
              }

            shortages["severity"] = shortages["severity"].map(
                  severity_icons
              )

              # Display most urgent shortages first
            severity_order = {
                  "🔴 Critical": 1,
                  "🟠 High": 2,
                  "🟡 Medium": 3,
                  "🟢 Low": 4
              }

            shortages["priority"] = shortages["severity"].map(
                  severity_order
              )

            shortages = shortages.sort_values("priority")

            st.dataframe(
                  shortages[
                      [
                          "hospital",
                          "blood_type",
                          "closing_stock",
                          "safety_stock",
                          "average_daily_demand",
                          "severity"
                      ]
                  ],
                  use_container_width=True,
                  hide_index=True
                  )

        except requests.exceptions.RequestException as e:
            st.error(
                f"Could not load shortage data: {e}"
            )

      

# --------------------------------------------------
# SUPPLIER AVAILABILITY SUMMARY
# --------------------------------------------------

                
        st.divider()
        st.header("🏥 Supplier Availability Overview")

        try:
            with st.spinner("Analyzing hospital supplier availability..."):

                supplier_data = get_matching_data()
                matching_results = supplier_data["matching_results"]

                supplier_units = {}

                for case in matching_results:
                    for recommendation in case["recommendations"]:

                        hospital = recommendation["supplier_hospital"]
                        units = int(recommendation["recommended_transfer"])

                        supplier_units[hospital] = (
                            supplier_units.get(hospital, 0) + units
                        )

            total_suppliers = len(supplier_units)
            total_units = sum(supplier_units.values())

            col1, col2 = st.columns(2)

            col1.metric(
                "Hospitals Recommended as Suppliers",
                total_suppliers
            )

            col2.metric(
                "Total Recommended Transfer Units",
                total_units
            )

            if supplier_units:
                supplier_summary = pd.DataFrame(
                    list(supplier_units.items()),
                    columns=["Hospital", "Recommended Units"]
                ).sort_values(
                    "Recommended Units",
                    ascending=False
                )

                st.subheader("Supplier Contribution")

                st.bar_chart(
                    supplier_summary,
                    x="Hospital",
                    y="Recommended Units"
                )
            else:
                st.info("No supplier recommendations currently available.")

        except requests.exceptions.RequestException as e:
            st.error(f"Supplier API error: {e}")

        except (KeyError, ValueError, TypeError) as e:
            st.error(f"Could not process supplier data: {e}")


  # ------------------------------------------
        # AI-POWERED DEMAND FORECASTING
  # ------------------------------------------
        st.divider()

        st.header("📈 AI-Powered Demand Forecasting")

        hospital_list = sorted(
            inventory["hospital"].unique()
        )

        blood_groups = sorted(
            inventory["blood_type"].unique()
        )

        col1, col2 = st.columns(2)

        with col1:
            selected_hospital = st.selectbox(
                "Select Hospital",
                hospital_list
            )

        with col2:
            selected_blood_type = st.selectbox(
                "Select Blood Group",
                blood_groups
            )

        if st.button("Generate 7-Day Forecast"):

            try:
                forecast_url = (
                    f"{API_URL}/forecast/"
                    f"{selected_hospital}/{selected_blood_type}"
                )

                forecast_response = requests.get(
                    forecast_url,
                    timeout=120
                )

                forecast_response.raise_for_status()

                forecast_data = forecast_response.json()

                st.success(
                    "Forecast generated successfully!"
                )

                safety_stock = forecast_data["safety_stock"]

                st.metric(
                    "Recommended Safety Stock",
                    f"{safety_stock:.2f} units"
                )

                forecast_df = pd.DataFrame(
                    forecast_data["forecast"]
                )

                forecast_df["date"] = pd.to_datetime(
                    forecast_df["date"]
                )

                # ----------------------------------
                # PROJECTED SHORTAGE RISK
                # ----------------------------------

                selected_inventory = inventory[
                    (inventory["hospital"] == selected_hospital) &
                    (inventory["blood_type"] == selected_blood_type)
                ]

                if selected_inventory.empty:
                    st.error(
                        "Could not find inventory for this selection."
                    )

                else:
                    current_stock = float(
                        selected_inventory["closing_stock"].iloc[0]
                    )

                    forecast_df["projected_stock"] = (
                        current_stock -
                        forecast_df["predicted_demand"].cumsum()
                    )

                    minimum_stock = float(
                        forecast_df["projected_stock"].min()
                    )

                    st.subheader(
                        "🚨 Predictive Shortage Risk"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Current Inventory",
                        f"{current_stock:.0f} units"
                    )

                    col2.metric(
                        "Projected Minimum Stock",
                        f"{minimum_stock:.2f} units"
                    )

                    col3.metric(
                        "Safety Stock",
                        f"{safety_stock:.2f} units"
                    )

                    if minimum_stock <= safety_stock:
                        st.error(
                            "⚠️ Shortage Risk: Projected inventory "
                            "falls to or below safety stock."
                        )

                    else:
                        st.success(
                            "Inventory is projected to remain "
                            "above safety stock."
                        )

                # ----------------------------------
                # FORECAST CHART
                # ----------------------------------

                st.subheader(
                    f"Demand Forecast: {selected_blood_type}"
                )

                chart_data = forecast_df.copy()

                chart_data["date"] = (
                    chart_data["date"].dt.strftime("%d %b")
                )

                st.line_chart(
                    chart_data.set_index("date")[
                        ["predicted_demand"]
                    ],
                    height=350,
                    use_container_width=True
                )

                # ----------------------------------
                # FORECAST DETAILS
                # ----------------------------------

                st.subheader("📋 Forecast Details")

                display_df = forecast_df.copy()

                display_df["date"] = (
                    display_df["date"].dt.strftime("%d %b %Y")
                )

                display_df["predicted_demand"] = (
                    display_df["predicted_demand"].round(2)
                )

                st.dataframe(
                    display_df[
                        ["date", "predicted_demand"]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

            except requests.exceptions.RequestException as e:
                st.error(
                    f"Forecast API error: {e}"
                )

            except (KeyError, ValueError, IndexError) as e:
                st.error(
                    f"Could not process forecast response: {e}"
                )

        # ------------------------------------------
        # HOSPITAL RISK OVERVIEW
        # ------------------------------------------

        st.divider()

        st.header("🏥 Hospital Risk Overview")

        try:
            risk_response = requests.get(
                f"{API_URL}/shortages",
                timeout=10
            )

            risk_response.raise_for_status()

            risk_data = pd.DataFrame(
                risk_response.json()
            )

            if risk_data.empty:
                st.success(
                    "No current inventory shortages detected."
                )

            else:
                risk_data["stock_gap"] = (
                    risk_data["safety_stock"] -
                    risk_data["closing_stock"]
                )

                risk_data = risk_data.sort_values(
                    by="stock_gap",
                    ascending=False
                )

                st.warning(
                    f"{len(risk_data)} hospital/blood-group "
                    "combinations are below their safety-stock threshold."
                )

                st.dataframe(
                    risk_data[
                        [
                            "hospital",
                            "blood_type",
                            "closing_stock",
                            "safety_stock",
                            "stock_gap"
                        ]
                    ].round(2),
                    use_container_width=True,
                    hide_index=True
                )

        except requests.exceptions.RequestException as e:
            st.error(
                f"Could not load hospital risk overview: {e}"
            )

# --------------------------------------------------
# MAIN API ERROR HANDLING
# --------------------------------------------------

except requests.exceptions.RequestException as e:
    st.error(
        f"Could not connect to FastAPI: {e}"
    )


# --------------------------------------------------
# AI-POWERED HOSPITAL MATCHING RECOMMENDATIONS
# --------------------------------------------------

st.divider()
st.header("🤝 AI-Powered Blood Transfer Recommendations")

if st.button("Find Matching Hospitals"):

    try:
        matching_data = get_matching_data()

        st.metric(
            "Model Mean Absolute Error",
            f"{matching_data['mae']:.2f} units"
        )

        st.metric(
            "Potential Shortage Cases",
            matching_data["total_shortages"]
        )

        recommendations = matching_data["matching_results"]
        
                
        # --------------------------------------------------
        # TRANSFER RECOMMENDATION SUMMARY
        # --------------------------------------------------

        total_shortage_cases = len(recommendations)

        total_recommended_units = sum(
            int(item["total_transferred"])
            for item in recommendations
        )

        total_supplier_hospitals = len({
            supplier["supplier_hospital"]
            for item in recommendations
            for supplier in item.get("recommended_suppliers", [])
        })

        average_units_per_case = (
            round(total_recommended_units / total_shortage_cases, 2)
            if total_shortage_cases > 0
            else 0
        )

        st.subheader("📦 Transfer Recommendation Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Shortage Cases", total_shortage_cases)
        col2.metric("Suggested Transfer Units", total_recommended_units)
        col3.metric("Supplier Hospitals", total_supplier_hospitals)
        col4.metric("Avg. Units per Case", average_units_per_case)


        # --------------------------------------------------
        # UNFULFILLED SHORTAGE SUMMARY
        # --------------------------------------------------

        total_cases = len(recommendations)

        fully_fulfilled = sum(
            1 for item in recommendations
            if item["status"] == "FULLY FULFILLED"
        )

        partially_fulfilled = sum(
            1 for item in recommendations
            if item["status"] == "PARTIALLY FULFILLED"
        )

        unfulfilled = sum(
            1 for item in recommendations
            if item["status"] == "UNFULFILLED"
        )

        total_remaining_units = sum(
            int(item["remaining_units"])
            for item in recommendations
        )

        st.subheader("🚨 Shortage Fulfilment Status")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Cases", total_cases)
        col2.metric("Fully Fulfilled", fully_fulfilled)
        col3.metric("Partially Fulfilled", partially_fulfilled)
        col4.metric("Unfulfilled", unfulfilled)

        st.metric(
            "Total Units Still Required",
            total_remaining_units
        )

        if total_remaining_units > 0:
            st.error(
                f"⚠️ {total_remaining_units} blood units "
                "remain unfulfilled across the shortage cases."
            )
        else:
            st.success("All identified shortage cases have been covered by simulated allocations.")

        if not recommendations:
            st.success("No shortage cases requiring transfers were found.")

        else:
            st.subheader("Hospital Transfer Recommendations")

            for item in recommendations:
                with st.expander(
                    f"{item['hospital']} | {item['blood_type']} | "
                    f"{item['status']}"
                ):
                    st.write(f"**Shortage date:** {item['shortage_date']}")
                    st.write(f"**Required units:** {item['required_units']}")
                    st.write(f"**Transferred units:** {item['total_transferred']}")
                    st.write(f"**Remaining units:** {item['remaining_units']}")

                    supplier_df = pd.DataFrame(item["recommendations"])

                    if not supplier_df.empty:
                        st.write("**Suggested supplier hospitals**")

                        st.dataframe(
                            supplier_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("No suitable supplier was found.")

    except requests.exceptions.RequestException as e:
        st.error(f"Matching API error: {e}")

    except (KeyError, ValueError, TypeError) as e:
        st.error(f"Could not process matching recommendations: {e}")
