# session_initializer.py
import streamlit as st

def init_session():
    """
    Ensure basic session_state keys exist.
    We DON'T create fernet_key here; key is created at successful login/signup.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "username" not in st.session_state:
        st.session_state["username"] = None

    if "logs" not in st.session_state:
        st.session_state["logs"] = {"uploads": {}}
