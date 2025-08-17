import streamlit as st
import auth_sqlite as auth  # new SQLite-based auth

def login_widget():
    """
    User-friendly login/signup page with SQLite-based authentication.
    """

    if st.session_state.get("authenticated", False):
        return

    # ------------------- Styling -------------------
    st.markdown(
        """
        <style>
        .stApp { background-color: #f4f6f9; }
        .login-title { font-size: 32px; font-weight: 700; text-align: center; margin-bottom: 20px; color: #222222; }
        .link { margin-top: 12px; font-size: 14px; text-align: center; }
        .link a { text-decoration: none; color: #0066cc; }
        .stTabs [role="tablist"] { justify-content: center; }
        div[data-testid="stSidebarNav"] { display: none; }
        </style>
        """, unsafe_allow_html=True
    )

    # ------------------- Title -------------------
    st.markdown('<div class="login-title">🔐 ADP Portal</div>', unsafe_allow_html=True)

    # ------------------- Tabs -------------------
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # ---------------- LOGIN ----------------
    with tab1:
        username = st.text_input("Username", placeholder="Enter your username", key="login_user", max_chars=20)
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass", max_chars=20)

        if st.button("Login", use_container_width=True, key="login_btn"):
            if username and password:
                if auth.verify_user(username, password):
                    # Get salt from DB for Fernet key
                    conn = auth.get_connection()
                    c = conn.cursor()
                    c.execute("SELECT salt FROM users WHERE username=?", (username,))
                    salt_b64 = c.fetchone()[0]
                    conn.close()

                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["fernet_key"] = auth.derive_fernet_key(password, salt_b64)

                    st.success(f"✅ Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.error("⚠️ Please enter both username and password")

        st.markdown('<div class="link">Forgot your password? <a href="#">Reset here</a></div>', unsafe_allow_html=True)

    # ---------------- SIGN UP ----------------
    with tab2:
        new_user = st.text_input("New Username", placeholder="Choose a username", key="signup_user", max_chars=20)
        display_name = st.text_input("Display Name", placeholder="Your name (optional)", key="signup_name", max_chars=30)
        new_pass = st.text_input("New Password", type="password", placeholder="Create a password", key="signup_pass", max_chars=20)

        if st.button("Create Account", use_container_width=True, key="signup_btn"):
            if new_user and new_pass:
                ok, msg = auth.create_user(new_user, display_name or new_user, new_pass)
                if ok:
                    # Automatically log in after signup
                    conn = auth.get_connection()
                    c = conn.cursor()
                    c.execute("SELECT salt FROM users WHERE username=?", (new_user,))
                    salt_b64 = c.fetchone()[0]
                    conn.close()

                    st.session_state["authenticated"] = True
                    st.session_state["username"] = new_user
                    st.session_state["fernet_key"] = auth.derive_fernet_key(new_pass, salt_b64)
                    st.success(f"✅ Account created! Welcome, {new_user}!")
                    st.rerun()
                else:
                    st.error(f"⚠️ {msg}")
            else:
                st.error("⚠️ Username and password cannot be empty")
