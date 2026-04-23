import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime
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
# CLEAN UI
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
# ROUTES (PUBLIC)
# =========================
ROUTES = [
    "Hassan Abdal → Wah Cantt → Taxila",
    "Islamabad IJP Road → Karachi Company",
    "Range Road → Kalma Chowk → Chakri Road",
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

# USERS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

# COMPLAINTS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
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
    c.execute("INSERT INTO users VALUES (NULL,'admin','1234','Admin')")
    conn.commit()

# =========================
# FRONT PAGE (ROUTES BEFORE LOGIN)
# =========================
st.title("🚌 University Transport Routes")

for i, r in enumerate(ROUTES, 1):
    st.write(f"{i}. {r}")

st.markdown("---")

# =========================
# SESSION STATE
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None

# =========================
# LOGIN / SIGNUP
# =========================
if not st.session_state.auth:

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Student Signup"])

    # ---------------- LOGIN ----------------
    with tab1:
        st.subheader("Login")

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
                st.rerun()
            else:
                st.error("Invalid credentials")

    # ---------------- SIGNUP ----------------
    with tab2:
        st.subheader("Student Signup")

        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")

        if st.button("Create Account"):
            exists = c.execute(
                "SELECT * FROM users WHERE username=?",
                (new_user,)
            ).fetchone()

            if exists:
                st.warning("Username already exists")
            elif new_user and new_pass:
                c.execute(
                    "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                    (new_user, new_pass, "Student")
                )
                conn.commit()
                st.success("Account created! Now login.")
            else:
                st.warning("Fill all fields")

    st.stop()

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Add Complaint",
    "View Complaints",
    "Resolve Complaints"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM complaints", conn)

    col1, col2 = st.columns(2)
    col1.metric("Total Complaints", len(df))
    col2.metric("Resolved", len(df[df["status"]=="Resolved"]) if not df.empty else 0)

# =========================
# ADD COMPLAINT
# =========================
elif menu == "Add Complaint":
    st.title("📝 Add Complaint")

    bus = st.text_input("Bus No")
    route = st.selectbox("Route", ROUTES)
    ctype = st.selectbox("Type", ["Late", "Breakdown", "Driver Issue", "Overcrowding"])
    desc = st.text_area("Description")

    if st.button("Submit"):
        c.execute("""
        INSERT INTO complaints VALUES (NULL,?,?,?,?,?,?,?)
        """, (st.session_state.user, bus, route, ctype, desc, "Pending", str(datetime.now())))
        conn.commit()

        st.success("Complaint Submitted")

# =========================
# VIEW COMPLAINTS
# =========================
elif menu == "View Complaints":
    st.title("📋 Complaints")

    df = pd.read_sql("SELECT * FROM complaints", conn)
    st.dataframe(df, use_container_width=True)

# =========================
# RESOLVE COMPLAINTS
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