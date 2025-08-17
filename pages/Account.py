# pages/accounts.py
import streamlit as st
from session_initializer import init_session
import auth_sqlite as auth  # use SQLite-based auth/logs

# ---- INIT SESSION ----
init_session()

# ---- AUTH CHECK ----
if not st.session_state.get("authenticated", False):
    st.warning("Please log in.")
    st.stop()

username = st.session_state.get("username")
if not username:
    st.error("User information missing. Please log out and log in again.")
    st.stop()

# ---- LOAD LOGS ----
st.session_state["logs"] = st.session_state.get("logs") or auth.load_logs(username)

logs = st.session_state["logs"]

# ---- PAGE CONTENT ----
st.title("Your Activity")
st.markdown("This data is stored securely in the app database and reflects your CSV cleaning activity.")

st.json(logs)
