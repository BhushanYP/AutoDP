import streamlit as st
import auth_sqlite as auth  # Assuming this exists

def login_widget():
    """
    User-friendly login/signup page with a modern UI and a light-to-dark blue gradient background.
    """

    if st.session_state.get("authenticated", False):
        return

    # ------------------- Global CSS Styling -------------------
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(to bottom, #a8c0ff, #3f2b96);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: white; /* Changed font color to white for better contrast */
            padding-top: 5rem;
            padding-bottom: 5rem;
        }
        .login-title {
            font-size: 38px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 8px;
            color: white; /* Title color also changed to white */
            letter-spacing: -1px;
        }
        .login-subtitle {
            font-size: 16px;
            text-align: center;
            color: #d1d8e0; /* Lighter shade of white for subtitle */
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
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
            background-color: rgba(255, 255, 255, 0.9); /* Semi-transparent white background */
        }
        .stButton>button {
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            transition: background-color 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #2980b9;
            transform: translateY(-1px);
        }
        div[data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # ------------------- Layout using columns -------------------
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-title">🔐 Welcome to the Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sign in or create a new account to continue.</div>', unsafe_allow_html=True)

        # ------------------- Tabs -------------------
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        # ---------------- LOGIN ----------------
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username", key="login_user", max_chars=20, label_visibility="collapsed")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass", max_chars=20, label_visibility="collapsed")

                st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if username and password:
                        if auth.verify_user(username, password):
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
        
        # ---------------- SIGN UP ----------------
        with tab2:
            with st.form("signup_form", clear_on_submit=False):
                new_user = st.text_input("New Username", placeholder="Choose a username", key="signup_user", max_chars=20, label_visibility="collapsed")
                display_name = st.text_input("Display Name", placeholder="Your full name (optional)", key="signup_name", max_chars=30, label_visibility="collapsed")
                new_pass = st.text_input("New Password", type="password", placeholder="Create a password", key="signup_pass", max_chars=20, label_visibility="collapsed")

                st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    if new_user and new_pass:
                        ok, msg = auth.create_user(new_user, display_name or new_user, new_pass)
                        if ok:
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