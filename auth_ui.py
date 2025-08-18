import streamlit as st
import re
import time
import auth_sqlite as auth  # your authentication module


# ---------------- Security Helpers ----------------
def is_strong_password(password: str) -> bool:
    """Check password strength (min 8 chars, upper, lower, number, special)."""
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[@$!%*?&#]", password)
    )


def login_widget():
    """Secure login/signup page with optimized UI."""

    if st.session_state.get("authenticated", False):
        return

    # ------------------- Global CSS Styling -------------------
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(to bottom, #a8c0ff, #3f2b96);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding-top: 5rem;
            padding-bottom: 5rem;
            color: white;
        }
        .login-title {
            font-size: 38px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 8px;
            color: white;
            letter-spacing: -1px;
        }
        .login-subtitle {
            font-size: 16px;
            text-align: center;
            color: #d1d8e0;
            margin-bottom: 30px;
        }
        .stTabs [role="tablist"] {
            justify-content: center;
            margin-bottom: 25px;
        }
        .stTabs [data-testid="stTab"] {
            font-size: 16px;
            font-weight: bold;
            color: #d1d8e0;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            color: white !important;
            border-bottom: 3px solid white !important;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #dcdcdc;
            padding: 12px;
            font-size: 16px;
            background-color: rgba(255, 255, 255, 0.9);
        }
        .stButton>button {
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            transition: background-color 0.2s ease, transform 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #2980b9;
            transform: translateY(-1px);
        }
        div[data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ------------------- Centered Layout -------------------
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 Welcome to the Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sign in or create a new account to continue.</div>', unsafe_allow_html=True)

        # ---------------- Tabs ----------------
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        # ---------------- LOGIN ----------------
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username", key="login_user", max_chars=20, label_visibility="collapsed")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass", max_chars=50, label_visibility="collapsed")
                submitted = st.form_submit_button("Login", use_container_width=True)

                # Brute-force protection
                if "failed_attempts" not in st.session_state:
                    st.session_state["failed_attempts"] = 0
                if "lockout_time" not in st.session_state:
                    st.session_state["lockout_time"] = 0

                if submitted:
                    if time.time() < st.session_state["lockout_time"]:
                        st.error("🚫 Too many failed attempts. Please try again later.")
                    elif username and password:
                        if auth.verify_user(username, password):
                            conn = auth.get_connection()
                            c = conn.cursor()
                            c.execute("SELECT salt FROM users WHERE username=?", (username,))
                            row = c.fetchone()
                            conn.close()

                            if row:
                                salt_b64 = row[0]
                                st.session_state.update({
                                    "authenticated": True,
                                    "username": username,
                                    "fernet_key": auth.derive_fernet_key(password, salt_b64),
                                    "failed_attempts": 0,
                                    "lockout_time": 0
                                })
                                st.success(f"✅ Welcome back, {username}!")
                                st.rerun()
                        else:
                            st.session_state["failed_attempts"] += 1
                            if st.session_state["failed_attempts"] >= 5:
                                st.session_state["lockout_time"] = time.time() + 60  # lock for 1 min
                                st.error("🚫 Too many failed attempts. Please try again in 1 minute.")
                            else:
                                st.error("❌ Invalid username or password")
                    else:
                        st.error("⚠️ Please enter both username and password")

        # ---------------- SIGN UP ----------------
        with tab2:
            with st.form("signup_form", clear_on_submit=False):
                new_user = st.text_input("New Username", placeholder="Choose a username", key="signup_user", max_chars=20, label_visibility="collapsed")
                display_name = st.text_input("Display Name", placeholder="Your full name (optional)", key="signup_name", max_chars=30, label_visibility="collapsed")
                new_pass = st.text_input("New Password", type="password", placeholder="Create a password", key="signup_pass", max_chars=50, label_visibility="collapsed")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    if not new_user or not new_pass:
                        st.error("⚠️ Username and password cannot be empty")
                    elif not is_strong_password(new_pass):
                        st.error("⚠️ Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.")
                    elif auth.user_exists(new_user):  # assumes your module has this
                        st.error("⚠️ Username already taken, please choose another.")
                    else:
                        ok, msg = auth.create_user(new_user, display_name or new_user, new_pass)
                        if ok:
                            conn = auth.get_connection()
                            c = conn.cursor()
                            c.execute("SELECT salt FROM users WHERE username=?", (new_user,))
                            row = c.fetchone()
                            conn.close()

                            if row:
                                salt_b64 = row[0]
                                st.session_state.update({
                                    "authenticated": True,
                                    "username": new_user,
                                    "fernet_key": auth.derive_fernet_key(new_pass, salt_b64),
                                })
                                st.success(f"✅ Account created! Welcome, {new_user}!")
                                st.rerun()
                        else:
                            st.error(f"⚠️ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)  # close login-card