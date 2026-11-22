


import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="BloodLink Network",
    page_icon="🩸",
    layout="wide"
)


# --------------------------------------------------
# BLOODLINK PREMIUM UI THEME
# --------------------------------------------------

st.markdown("""
<style>

/* Main application background */
.stApp {
    background-color: #F7F3EF;
    color: #302630;
}

/* Main content spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

/* Main headings */
h1 {
    color: #652D4B !important;
    font-weight: 750 !important;
    letter-spacing: -1px;
}

h2, h3 {
    color: #652D4B !important;
    font-weight: 650 !important;
}

/* Premium KPI cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #EADDE3;
    border-top: 4px solid #89516E;
    border-radius: 16px;
    padding: 24px 22px;
    min-height: 125px;
    box-shadow: 0 5px 18px rgba(75, 35, 55, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 24px rgba(75, 35, 55, 0.11);
}

[data-testid="stMetricLabel"] {
    color: #806B77 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    color: #652D4B !important;
    font-size: 32px !important;
    font-weight: 750 !important;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #806B77 !important;
    font-weight: 600;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #652D4B !important;
    font-weight: 750;
}

/* Buttons */
.stButton > button {
    background-color: #652D4B;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: #81415F;
    color: #FFFFFF;
    border: none;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #EADDE3;
}

/* Select boxes */
[data-testid="stSelectbox"] {
    background-color: #FFFFFF;
}

/* Dividers */
hr {
    border-color: #EADDE3;
}

/* Captions */
.stCaption {
    color: #8A7580;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #652D4B;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

</style>
""", unsafe_allow_html=True)






# --------------------------------------------------
# CUSTOM FIXED BLOODLINK SIDEBAR
# --------------------------------------------------


st.markdown("""
<style>
[data-testid="stSidebar"] {
    display: none !important;
}


/* Main content layout */
[data-testid="stMainBlockContainer"] {
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: none !important;
    padding-left: 330px !important;
    padding-right: 30px !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    margin-left: 0 !important;
}

/* Keep the main area full width */
[data-testid="stAppViewContainer"] .main {
    width: 100% !important;
    margin-left: 0 !important;
}

.bloodlink-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 250px;
    height: 100vh;
    background: #652D4B;
    padding: 30px 18px;
    z-index: 999999;
    box-sizing: border-box;
    overflow-y: auto;
}

.bloodlink-brand {
    color: white;
    font-size: 27px;
    font-weight: 750;
    margin-bottom: 5px;
}

.bloodlink-subtitle {
    color: #E8C9D7;
    font-size: 12px;
    margin-bottom: 45px;
}

.bloodlink-nav-label {
    color: #D9B8C8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin: 25px 0 12px 8px;
}

.bloodlink-nav-item {
    display: block;
    text-decoration: none !important;
    color: #F7EAF0 !important;
    padding: 12px 14px;
    margin: 5px 0;
    border-radius: 9px;
    font-size: 14px;
    transition: background 0.2s ease;
}

.bloodlink-nav-item:hover {
    background: #89516E;
    color: white !important;
}

/* Active navigation highlighting */
.bloodlink-nav-item:hover {
    background: #89516E;
    color: white !important;
}

/* Highlight the selected section */
body:not(:has(#inventory:target, #shortages:target, #forecasting:target, #suppliers:target, #transfers:target))
.bloodlink-nav-item[href="#overview"],
body:has(#inventory:target) .bloodlink-nav-item[href="#inventory"],
body:has(#shortages:target) .bloodlink-nav-item[href="#shortages"],
body:has(#forecasting:target) .bloodlink-nav-item[href="#forecasting"],
body:has(#suppliers:target) .bloodlink-nav-item[href="#suppliers"],
body:has(#transfers:target) .bloodlink-nav-item[href="#transfers"] {
    background: #89516E;
    color: white !important;
    font-weight: 700;
}

.bloodlink-footer {
    position: absolute;
    bottom: 25px;
    color: #E8C9D7;
    font-size: 11px;
}
html {
    scroll-behavior: smooth;
}

[id] {
    scroll-margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<div class="bloodlink-sidebar">
<div class="bloodlink-brand">🩸 BloodLink</div>
<div class="bloodlink-subtitle">
Hospital Intelligence Platform
</div>


<div class="bloodlink-nav-label">WORKSPACE</div>

<a href="#overview" class="bloodlink-nav-item ">
▦ &nbsp; Overview
</a>

<a href="#inventory" class="bloodlink-nav-item">
🏥 &nbsp; Hospital Inventory
</a>

<a href="#shortages" class="bloodlink-nav-item">
🚨 &nbsp; Shortage Monitoring
</a>

<a href="#forecasting" class="bloodlink-nav-item">
📈 &nbsp; Demand Forecasting
</a>

<a href="#suppliers" class="bloodlink-nav-item">
🔗 &nbsp; Supplier Network
</a>

<a href="#transfers" class="bloodlink-nav-item">
↔ &nbsp; Transfer Recommendations
</a>

<div class="bloodlink-footer">
BLOODLINK NETWORK · 2026
</div>
</div>
""", unsafe_allow_html=True)






API_URL = "https://bloodlink-network.onrender.com"
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
# DASHBOARD WELCOME HEADER
# --------------------------------------------------

st.markdown(
    '<div id="overview"></div>',
    unsafe_allow_html=True
)

header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown(
        """
        <div style="padding: 10px 0 5px 0;">
            <div style="
                color: #9B6682;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1.5px;
            ">
                HOSPITAL OPERATIONS DASHBOARD
            </div>
            <h1 style="
                color: #652D4B;
                font-size: 34px;
                margin: 10px 0;
            ">
                Welcome to BloodLink 🩸
            </h1>
            <p style="color: #806B77; font-size: 15px;">
                Monitor inventory, anticipate shortages and coordinate
                hospital blood supply.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_col2:
    st.markdown(
        f"""
        <div style="
            text-align: right;
            padding-top: 20px;
        ">
            <div style="color: #806B77; font-size: 13px;">
                TODAY
            </div>
            <div style="
                color: #652D4B;
                font-size: 17px;
                font-weight: 700;
            ">
                {datetime.now().strftime("%d %b %Y")}
            </div>
            <div style="
                color: #287D61;
                font-size: 12px;
                margin-top: 10px;
            ">
                ● DEMO SYSTEM
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.caption(
    "Prototype powered by simulated hospital data. "
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
        st.markdown(
            '<div id="inventory"></div>',
             unsafe_allow_html=True
        )
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

        
        # Calculate total stock for each blood group
        blood_stock = (
            inventory.groupby("blood_type")["closing_stock"]
            .sum()
            .reset_index()
            .sort_values("closing_stock", ascending=False)
        )

        # Identify highest and lowest stock groups
        highest_stock = blood_stock.iloc[0]
        lowest_stock = blood_stock.iloc[-1]

        col1, col2 = st.columns(2)

        col1.metric(
            "Highest Stock Group",
            highest_stock["blood_type"],
            f'{int(highest_stock["closing_stock"])} units'
        )

        col2.metric(
            "Lowest Stock Group",
            lowest_stock["blood_type"],
            f'{int(lowest_stock["closing_stock"])} units',
            delta_color="off"
        )

        # Display stock distribution
        st.bar_chart(
            blood_stock,
            x="blood_type",
            y="closing_stock",
            color="#89516E",
            use_container_width=True
        )


        # ------------------------------------------
        # HOSPITAL SHORTAGE MONITORING
        # ------------------------------------------
        st.markdown(
            '<div id="shortages"></div>',
            unsafe_allow_html=True
        )
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
                
                # Shortage overview metrics
                total_hospitals_affected = shortages["hospital"].nunique()
                critical_count = (shortages["severity"] == "🔴 Critical").sum()
                high_count = (shortages["severity"] == "🟠 High").sum()
                affected_blood_groups = shortages["blood_type"].nunique()

                st.subheader("Shortage Overview")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Hospitals Affected", total_hospitals_affected)
                col2.metric("Critical Shortages", int(critical_count))
                col3.metric("High Shortages", int(high_count))
                col4.metric("Blood Groups Affected", affected_blood_groups)

                st.divider()
                
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

                display_shortages = shortages[
                    [
                        "hospital",
                        "blood_type",
                        "closing_stock",
                        "safety_stock",
                        "average_daily_demand",
                        "severity"
                    ]
                ].copy()

                display_shortages["safety_stock"] = (
                    display_shortages["safety_stock"].round(2)
                )

                display_shortages["average_daily_demand"] = (
                    display_shortages["average_daily_demand"].round(2)
                )

                display_shortages = display_shortages.rename(columns={
                    "hospital": "Hospital",
                    "blood_type": "Blood Type",
                    "closing_stock": "Current Stock",
                    "safety_stock": "Safety Stock",
                    "average_daily_demand": "Avg. Daily Demand",
                    "severity": "Severity"
                })

                st.dataframe(
                    display_shortages,
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
        st.markdown(
            '<div id="suppliers"></div>',
            unsafe_allow_html=True
        )          
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
        st.markdown(
            '<div id="forecasting"></div>',
            unsafe_allow_html=True
        )
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
st.markdown(
    '<div id="transfers"></div>',
    unsafe_allow_html=True
)
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
            for supplier in item.get("recommendations", [])
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
