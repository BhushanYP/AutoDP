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

import navigation
navigation.navigation_bar()

# ---- CSS STYLING ----
st.markdown("""
<style>
/* Main app background */
.stApp {
    background-color: #151019; 
    color: #E3E3E3;
}

/* Headers and titles */
.main-header {
    color: #A68CE6;
}

/* Subtitles and secondary text */
.subheader {
    color: #BFB4D4;
}

/* Buttons */
.stButton>button {
    background-color: #A68CE6;
    color: #151019; /* Use the dark background color for button text */
}

.stButton>button:hover {
    background-color: #9078C0; /* Slightly darker lavender on hover */
}

/* Input fields */
.stTextInput>div>div>input {
    background-color: #2D2533; /* A slightly lighter shade of the background */
    color: #E3E3E3;
    border: 1px solid #4A4050; /* A soft, dark border */
}

/* Tabs */
.stTabs [aria-selected="true"] {
    color: #A68CE6 !important;
    border-bottom: 3px solid #A68CE6 !important;
}
div[data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ---- CSS Styling ----
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #d6b4f8, #6d28d9);
    }
    .section-description {
        font-size: 15px;
        line-height: 1.6;
        margin-top: 20px;
    }
    div[data-testid="stSidebarNav"] {
        display: none;
    }  
</style>
""", unsafe_allow_html=True)

# ---- PAGE LAYOUT ----
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(f'<h1 class="main-header">Welcome, {username}!</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">This is your personalized account dashboard.</p>', unsafe_allow_html=True)

    st.header("Change Your Password")
    st.markdown("For your security, please enter your current password to change it.")
    
    # Change password form
    with st.form("change_password_form", clear_on_submit=True):
        current_pass = st.text_input("Current Password", type="password", key="current_pass", placeholder="Current Password")
        new_pass = st.text_input("New Password", type="password", key="new_pass", placeholder="New Password")
        confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass", placeholder="Confirm New Password")
        
        change_submitted = st.form_submit_button("Update Password", use_container_width=True)
        
        if change_submitted:
            if new_pass != confirm_pass:
                st.error("New passwords do not match!")
            elif not current_pass or not new_pass or not confirm_pass:
                st.error("Please fill in all fields.")
            elif auth.verify_user(username, current_pass):
                if auth.change_password(username, new_pass):
                    st.success("Your password has been changed successfully!")
                else:
                    st.error("Failed to change password. Please try again.")
            else:
                st.error("Incorrect current password.")

    st.markdown('<hr style="border-top: 1px solid #444; margin: 30px 0;">', unsafe_allow_html=True)

    # ---- LOAD AND DISPLAY LOGS ----
    st.header("Your Activity")
    st.markdown("This data is stored securely in the app database and reflects your activity.")
    
    st.session_state["logs"] = st.session_state.get("logs") or auth.load_logs(username)
    logs = st.session_state["logs"]
    st.json(logs)