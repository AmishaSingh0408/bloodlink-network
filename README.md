# BloodLink Network

**BloodLink Network is a prototype hospital blood-inventory monitoring and coordination platform that forecasts blood demand, identifies potential shortages, and recommends nearby hospitals with projected surplus inventory.**

<p align="center">
  <a href="https://bloodlink-network-t5darcmvftlnma3pdijun8.streamlit.app/"><strong>Live Dashboard</strong></a> ·
  <a href="https://bloodlink-network.onrender.com/docs"><strong>API Documentation</strong></a> ·
  <a href="https://bloodlink-network.onrender.com/health"><strong>API Health</strong></a>
</p>

> **Demo-data notice:** BloodLink currently uses synthetic hospital inventory data for eight simulated hospitals across Hyderabad, Vijayawada, and Guntur. It does not connect to real hospital systems, process patient data, execute blood transfers, or provide clinically validated recommendations. It is a software prototype, not a medical decision-making system.

## Overview

BloodLink combines a demand-forecasting workflow with inventory-risk analysis and distance-aware supplier matching. The forecasting model uses historical demand, lag features, rolling averages, hospital metadata, and blood-group information. The matching workflow estimates seven-day inventory, identifies forecasted shortages, and allocates projected surplus from nearby hospitals while reducing each supplier's available surplus after an allocation.

## Workflow

~~~mermaid
flowchart TD
    A["Synthetic hospital inventory data"] --> B["Data preparation and time-series features"]
    B --> C["Random Forest demand forecasting"]
    C --> D["Seven-day inventory projection"]
    D --> E["Shortage-risk detection"]
    D --> F["Projected supplier surplus"]
    E --> G["Distance-aware supplier ranking"]
    F --> G
    G --> H["Transfer recommendations"]
    H --> I["FastAPI backend"]
    I --> J["Streamlit dashboard"]
~~~

## Live Demo

| Component | Link |
|---|---|
| Streamlit dashboard | [Open BloodLink](https://bloodlink-network-t5darcmvftlnma3pdijun8.streamlit.app/) |
| FastAPI service | [Open API](https://bloodlink-network.onrender.com/) |
| Interactive API docs | [Swagger UI](https://bloodlink-network.onrender.com/docs) |
| Health check | [API health](https://bloodlink-network.onrender.com/health) |

The backend is hosted on Render and the dashboard on Streamlit Community Cloud. The first request after an idle period may take longer while the free backend instance wakes up and computes cached recommendations.

## Features implemented

- Synthetic dataset generator for 90 days of daily inventory activity across 8 simulated hospitals and 8 blood groups.
- Random Forest regression model for demand forecasting, using chronological train/test splitting.
- Time-series feature engineering with previous-day and previous-week demand, rolling 7-day and 14-day averages, day of week, and hospital metadata.
- Seven-day demand and projected-inventory calculations.
- Safety-stock calculations and shortage-risk identification.
- Supplier discovery using projected surplus inventory.
- Haversine-distance calculation and nearest-supplier ranking, with a 300 km matching limit.
- Greedy whole-unit transfer allocation that updates remaining projected surplus to avoid allocating the same units more than once.
- FastAPI endpoints for inventory, hospital inventory, shortages, forecasts, and matching recommendations.
- Streamlit dashboard for inventory, shortage monitoring, forecasting, suppliers, and transfer recommendations.

## Current implementation status

### Built and running

- Demand forecasting agent (agents/forecast_agent.py).
- Supplier matching agent (agents/matching_agent.py).
- FastAPI service (api/main.py).
- Streamlit dashboard (dashboard/app.py).
- Synthetic inventory data generator (data_sim/generate_data.py).
- Render and Streamlit Community Cloud deployments.

### Not implemented / future work

- Automated hospital-to-hospital coordination agent.
- SMS, WhatsApp, email, or other automated hospital alerts.
- Integration with live hospital inventory systems or blood-bank databases.
- Real-time verified blood availability and actual transfer execution.
- Clinical validation, regulatory review, and production-grade security.

The project should therefore be described as a forecasting and recommendation prototype; automated alerts and autonomous coordination are not currently implemented.

## Tech stack

- **Language:** Python
- **Data processing:** Pandas, NumPy
- **Machine learning:** scikit-learn, Random Forest Regressor
- **API:** FastAPI, Uvicorn
- **Dashboard:** Streamlit
- **Deployment:** Render (API), Streamlit Community Cloud (dashboard)

The requirements file also includes Prophet, Neo4j, and Twilio for possible extensions; their presence in requirements.txt does not mean those integrations are currently active in the application.

## Repository structure

~~~text
bloodlink-network/
├── agents/
│   ├── forecast_agent.py       # Demand features, model training, forecasts and risk logic
│   └── matching_agent.py       # Projected surplus, distance ranking and transfer allocation
├── api/
│   └── main.py                 # FastAPI routes and cached matching results
├── dashboard/
│   └── app.py                  # Streamlit dashboard
├── data/
│   └── hospital_blood_data.csv # Generated synthetic inventory dataset
├── data_sim/
│   └── generate_data.py        # Synthetic dataset generator
├── docs/
│   └── images/
│       └── bloodlink-dashboard.png # Dashboard screenshot used in this README
├── .streamlit/
├── requirements.txt
└── README.md
~~~

## Run locally

Use Python 3.10+ and run commands from the repository root.

1. Clone the repository and enter the project folder:

   ~~~bash
   git clone https://github.com/AmishaSingh0408/bloodlink-network.git
   cd bloodlink-network
   ~~~

2. Create and activate a virtual environment (Windows PowerShell):

   ~~~powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ~~~

   On macOS/Linux, activate it with source venv/bin/activate.

3. Install dependencies:

   ~~~bash
   pip install -r requirements.txt
   ~~~

4. Generate the synthetic dataset (this overwrites data/hospital_blood_data.csv):

   ~~~bash
   python data_sim/generate_data.py
   ~~~

5. Start the API in one terminal:

   ~~~bash
   uvicorn api.main:app --reload
   ~~~

6. In a second terminal, start the dashboard:

   ~~~bash
   streamlit run dashboard/app.py
   ~~~

   The dashboard's configured API URL currently points to the deployed Render backend. To use the local API instead, change API_URL in dashboard/app.py to http://127.0.0.1:8000 before starting Streamlit.

7. Open the local dashboard at http://localhost:8501 and API docs at http://127.0.0.1:8000/docs.

## Model evaluation and results

The forecasting code evaluates the Random Forest model with a chronological 80/20 date-based train/test split and reports Mean Absolute Error (MAE) in blood units. Run:

~~~bash
python -m agents.forecast_agent
~~~

This prints the measured MAE along with training/test row counts and a sample seven-day forecast. **A verified MAE value and a like-for-like baseline comparison have not yet been recorded in this README**, so no performance-improvement claim is made here. Add the measured Random Forest MAE and baseline MAE after running an evaluation on the committed dataset with the same chronological test period.

## Screenshots

The screenshot below shows the deployed dashboard overview. The displayed figures are generated from the project's synthetic demo dataset.

![BloodLink dashboard](docs/images/bloodlink-dashboard.png)

## Limitations

- Data is synthetic and generated for demonstration; it is not a representation of actual hospital stock.
- Forecasts and supplier recommendations are experimental and have not been clinically validated.
- Supplier distance is calculated from static coordinates; road travel time, transport constraints, blood component compatibility rules, expiry, cold-chain logistics, and operational approvals are not modeled.
- Recommended transfers are simulated allocations only. Blood is not reserved, dispatched, or transferred by the software.

## Author

**Amisha Singh**  
[GitHub](https://github.com/AmishaSingh0408)

---

If you find the project useful, feel free to explore the code and open an issue with feedback.
