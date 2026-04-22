import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import random
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="University Transport System",
    page_icon="🚌",
    layout="wide"
)

# =========================
# CLEAN UI DESIGN
# =========================
st.markdown("""
<style>
.stApp {
    background-color: #f8fafc;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

h1, h2, h3 {
    color: #1e3a8a;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    width: 100%;
    padding: 8px;
    border: none;
}

.stButton>button:hover {
    background-color: #1d4ed8;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🚍 Transport System")

# =========================
# UNIVERSITY ROUTES (NO FEES)
# =========================
ROUTES = [
    "Hassan Abdal → Wah Cantt → Taxila",
    "Islamabad IJP Road → Karachi Company",
    "Range Road → Kalma Chowk → Dhoke Syedain → Chakri Road",
    "Murree Road → Islamabad Highway → Old Airport",
    "Gujjar Khan → Rawat",
    "PWD → Chaklala Scheme III → Naval Enclave",
    "Adyala Road (All Stops)"
]

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("transport.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus TEXT,
    route TEXT,
    type TEXT,
    description TEXT,
    time TEXT
)
""")
conn.commit()

# =========================
# LOGIN SYSTEM
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None

if not st.session_state.auth:
    st.title("🔐 Login System")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Admin", "Driver"])

    if st.button("Login"):
        if user == "admin" and pwd == "1234" and role == "Admin":
            st.session_state.auth = True
            st.session_state.role = "Admin"
            st.rerun()

        elif user == "driver" and pwd == "1234" and role == "Driver":
            st.session_state.auth = True
            st.session_state.role = "Driver"
            st.rerun()

        else:
            st.error("Invalid credentials")

    st.stop()

# =========================
# AI MODEL (DELAY PREDICTION)
# =========================
@st.cache_resource
def train_model():
    X = []
    y = []

    for _ in range(400):
        route = random.randint(1, 6)
        hour = random.randint(6, 23)
        traffic = random.randint(0, 1)

        delay = route * 5 + hour * 0.7 + traffic * 18 + random.randint(-5, 5)

        X.append([route, hour, traffic])
        y.append(delay)

    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    return model

model = train_model()

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Add Complaint",
    "View Complaints",
    "AI Delay Predictor",
    "Live GPS Tracking",
    "Export Data"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 University Transport Dashboard")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Complaints", len(df))
    col2.metric("Active Buses", random.randint(10, 25))
    col3.metric("Routes", len(ROUTES))

    st.subheader("🚌 Available Routes")

    for i, r in enumerate(ROUTES, start=1):
        st.write(f"{i}. {r}")

    if not df.empty:
        fig = px.pie(df, names="type", title="Complaint Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No complaints yet")

# =========================
# ADD COMPLAINT
# =========================
elif menu == "Add Complaint":
    st.title("📝 Add Complaint")

    bus = st.text_input("Bus No")
    route = st.selectbox("Select Route", ROUTES)
    ctype = st.selectbox("Complaint Type", [
        "Late Bus", "Breakdown", "Driver Issue", "Overcrowding"
    ])
    desc = st.text_area("Description")

    if st.button("Submit"):
        if bus and route and desc:
            c.execute("""
            INSERT INTO complaints (bus, route, type, description, time)
            VALUES (?, ?, ?, ?, ?)
            """, (bus, route, ctype, desc, str(datetime.now())))
            conn.commit()

            st.success("Complaint submitted successfully!")
        else:
            st.warning("Please fill all fields")

# =========================
# VIEW COMPLAINTS
# =========================
elif menu == "View Complaints":
    st.title("📋 Complaints Data")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    st.dataframe(df, use_container_width=True)

    if not df.empty:
        fig = px.bar(df["type"].value_counts(),
                     x=df["type"].value_counts().index,
                     y=df["type"].value_counts().values,
                     title="Complaint Analysis")

        st.plotly_chart(fig, use_container_width=True)

# =========================
# AI PREDICTION
# =========================
elif menu == "AI Delay Predictor":
    st.title("🤖 AI Delay Prediction System")

    route = st.selectbox("Route", list(range(1, 7)))
    hour = st.slider("Hour", 0, 23, 9)
    traffic = st.selectbox("Traffic", ["Low", "High"])

    t = 1 if traffic == "High" else 0

    if st.button("Predict Delay"):
        pred = model.predict([[route, hour, t]])[0]
        st.success(f"Estimated Delay: {round(pred, 2)} minutes")

# =========================
# GPS TRACKING
# =========================
elif menu == "Live GPS Tracking":
    st.title("🛰 Live GPS Tracking (Simulation)")

    base_lat = 33.6844
    base_lon = 73.0479

    buses = []

    for i in range(6):
        buses.append({
            "bus": f"BUS-{i+1}",
            "lat": base_lat + np.random.uniform(-0.05, 0.05),
            "lon": base_lon + np.random.uniform(-0.05, 0.05)
        })

    df = pd.DataFrame(buses)

    st.map(df[["lat", "lon"]])

    st.caption("Refresh page to update locations")

# =========================
# EXPORT DATA
# =========================
elif menu == "Export Data":
    st.title("📤 Export Complaints")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    if not df.empty:
        file = "complaints.xlsx"
        df.to_excel(file, index=False)

        with open(file, "rb") as f:
            st.download_button("Download Excel", f, file_name="complaints.xlsx")
    else:
        st.warning("No data available")