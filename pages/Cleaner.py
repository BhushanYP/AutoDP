import streamlit as st
from session_initializer import init_session
from Back_End import csv_processor
from Back_End import process
import io
import pandas as pd
import auth_sqlite as auth  # updated logging and auth
import navigation

# ---- INIT SESSION ----
init_session()

# ---- PAGE CONFIG ----
st.set_page_config(page_title="CSV Data Cleaner", page_icon="🧼", layout="wide")

# Optional: set background image
try:
    process.set_bg_image("Background.webp")
except Exception:
    pass

# ---- NAVIGATION ----
navigation.navigation_bar()

# ---- AUTH CHECK ----
if not st.session_state.get("authenticated", False):
    st.warning("Please log in.")
    st.stop()

username = st.session_state.get("username")
fernet_key = st.session_state.get("fernet_key")
if not fernet_key:
    st.error("Encryption key missing. Please log out and log in again.")
    st.stop()

# ---- LOAD LOGS INTO SESSION ----
st.session_state["logs"] = st.session_state.get("logs") or auth.load_logs(username)

# ---- STYLES ----
custom_css = """
<style>
.title {text-align: center; font-size: 3rem; font-weight: bold; margin-bottom: 10px; color: #FFFFFF;}
.upload-box { background: rgba(255,255,255,0.9); padding: 20px; border-radius: 8px; text-align: center; }
[data-testid="stDownloadButton"] button { background: #4caf50 !important; color: white !important; font-size: 18px !important; border-radius: 8px !important; padding: 10px 16px !important; }
div[data-testid="stSidebarNav"] { display: none; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---- TITLE ----
st.markdown('<h1 class="title">🧼 CSV Data Cleaner</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#FFFFFF;">Upload a CSV file and clean it.</p>', unsafe_allow_html=True)

# ---- FILE UPLOADER ----
uploaded_file_cleaner = st.file_uploader("Choose a CSV file", type=["csv"])
st.markdown("⚠️ **Note:** For best performance, please upload smaller CSV files.")

if uploaded_file_cleaner and uploaded_file_cleaner.name.endswith('.csv'):
    temp_df, _ = process.read_csv_with_encoding(uploaded_file_cleaner)

    # ---- INCREMENT CLEANING LOG ----
    st.session_state.setdefault("logs", {"uploads": {}})
    logs = st.session_state["logs"]
    logs["uploads"]["Cleaning"] = logs["uploads"].get("Cleaning", 0) + 1

    # ---- SAVE LOGS TO SQLITE ----
    auth.save_logs(username, logs)
    st.session_state["logs"] = logs  # update session

    # ---- ERROR CHECK ----
    if temp_df is None:
        st.error("❌ Error: No data was loaded.")
    elif isinstance(temp_df, str):
        st.error(f"❌ Error: {temp_df}")
    else:
        with st.form("column_selection_form"):
            st.write("### Select Columns to Include in Export and Apply Cleaning")
            selected_columns = st.multiselect(
                "📤 Choose columns to export (they will also be cleaned):",
                temp_df.columns.tolist(),
                default=temp_df.columns.tolist()
            )
            submitted = st.form_submit_button("✅ Clean and Export")

        if submitted:
            with st.spinner("Processing... ⏳"):
                uploaded_file_cleaner.seek(0)
                processed_output = csv_processor.process_file(
                    uploaded_file_cleaner,
                    columns_to_include=selected_columns,
                    columns_to_clean=selected_columns
                )

            if isinstance(processed_output, io.StringIO):
                st.success("✅ Successfully processed!")
                preview_df = pd.read_csv(io.StringIO(processed_output.getvalue()))
                st.write("### 👀 Preview of Cleaned CSV:")
                st.dataframe(preview_df.head(10), use_container_width=True)
                st.download_button(
                    label="⬇️ Download Cleaned CSV",
                    data=processed_output.getvalue(),
                    file_name="cleaned_data.csv",
                    mime="text/csv"
                )
            else:
                st.error(f"❌ Error: {processed_output}")
else:
    if uploaded_file_cleaner:
        st.error("❌ Please upload a valid CSV file.")
