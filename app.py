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
st.set_page_config(page_title="Transport System", page_icon="🚌", layout="wide")

# =========================
# UI
# =========================
st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}
h1, h2, h3 { color: #1e3a8a; }
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGO
# =========================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.title("🚍 Transport System")

# =========================
# ROUTES
# =========================
ROUTES = [
    "Hassan Abdal → Wah Cantt → Taxila",
    "Islamabad IJP Road → Karachi Company",
    "Range Road → Kalma Chowk → Chakri Road",
    "Murree Road → Islamabad Highway",
    "Gujjar Khan → Rawat",
    "PWD → Chaklala Scheme III",
    "Adyala Road (All Stops)"
]

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("transport.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

# Complaints table with status
c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus TEXT,
    route TEXT,
    type TEXT,
    description TEXT,
    status TEXT,
    time TEXT
)
""")

conn.commit()

# =========================
# DEFAULT ADMIN
# =========================
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (NULL, 'admin', '1234', 'Admin')")
    conn.commit()

# =========================
# LOGIN
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None

if not st.session_state.auth:
    st.title("🔐 Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Admin", "Driver", "Student"])

    if st.button("Login"):
        result = c.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (user, pwd, role)
        ).fetchone()

        if result:
            st.session_state.auth = True
            st.session_state.role = role
            st.session_state.user = user
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# =========================
# AI MODEL
# =========================
@st.cache_resource
def train_model():
    X, y = [], []
    for _ in range(300):
        X.append([random.randint(1,5), random.randint(6,23), random.randint(0,1)])
        y.append(random.randint(5,40))
    model = RandomForestRegressor()
    model.fit(X, y)
    return model

model = train_model()

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Add Complaint",
    "View Complaints",
    "Resolve Complaints",
    "AI Predictor",
    "Student Generator"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    col1, col2 = st.columns(2)
    col1.metric("Total", len(df))
    col2.metric("Resolved", len(df[df["status"]=="Resolved"]))

# =========================
# ADD COMPLAINT
# =========================
elif menu == "Add Complaint":
    st.title("📝 Add Complaint")

    bus = st.text_input("Bus")
    route = st.selectbox("Route", ROUTES)
    ctype = st.selectbox("Type", ["Late", "Breakdown", "Driver Issue"])
    desc = st.text_area("Description")

    if st.button("Submit"):
        c.execute("""
        INSERT INTO complaints VALUES (NULL,?,?,?,?,?,?)
        """, (bus, route, ctype, desc, "Pending", str(datetime.now())))
        conn.commit()
        st.success("Submitted")

# =========================
# VIEW
# =========================
elif menu == "View Complaints":
    st.title("📋 Complaints")

    df = pd.read_sql("SELECT * FROM complaints", conn)
    st.dataframe(df)

# =========================
# RESOLVE SYSTEM
# =========================
elif menu == "Resolve Complaints":
    st.title("✔ Resolve Complaints")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    for i, row in df.iterrows():
        col1, col2 = st.columns([4,1])

        with col1:
            st.write(f"{row['id']} | {row['route']} | {row['type']} | {row['status']}")

        with col2:
            if row["status"] == "Pending":
                if st.button(f"Resolve {row['id']}"):
                    c.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (row["id"],))
                    conn.commit()
                    st.rerun()

# =========================
# AI
# =========================
elif menu == "AI Predictor":
    st.title("🤖 AI Delay")

    route = st.selectbox("Route", [1,2,3,4,5])
    hour = st.slider("Hour", 0, 23)
    traffic = st.selectbox("Traffic", ["Low","High"])

    t = 1 if traffic=="High" else 0

    if st.button("Predict"):
        st.success(f"Delay: {round(model.predict([[route,hour,t]])[0],2)} mins")

# =========================
# STUDENT GENERATOR
# =========================
elif menu == "Student Generator":
    st.title("🎓 Generate Students (Admin Only)")

    if st.session_state.role != "Admin":
        st.warning("Only Admin allowed")
    else:
        num = st.number_input("Number of students", 1, 50, 5)

        if st.button("Generate"):
            for i in range(num):
                username = f"student{i+1}"
                password = "1234"
                c.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                          (username, password, "Student"))
            conn.commit()
            st.success("Students generated!")