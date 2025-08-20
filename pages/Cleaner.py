import streamlit as st
from session_initializer import init_session
from Back_End import csv_processor
from Back_End import process
import io
import pandas as pd
import auth_sqlite as auth
import navigation
from sqlalchemy import create_engine

# ---- INIT SESSION ----
init_session()

# ---- PAGE CONFIG ----
st.set_page_config(page_title="CSV/SQL Data Cleaner", page_icon="🧼", layout="wide")

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

# ---- CUSTOM STYLES ----
custom_css = """
<style>
/* Center title with shadow */
.title {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 10px;
    color: #FFFFFF;
}

/* Center tab title */
.tab_title {
    text-align: center;
    font-weight: bold;
}

/* Upload section styling */
.upload-box {
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
}

/* Styled button */
[data-testid="stDownloadButton"] button {
    background: #4caf50 !important;
    color: white !important;
    font-size: 18px !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    transition: 0.3s;
}
[data-testid="stDownloadButton"] button:hover {
    background: #388e3c !important;
}
div[data-testid="stSidebarNav"] {
        display: none;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

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

# ---- TITLE ----
st.markdown('<h1 style="text-align:center; color:#FFFFFF;">🧼 Data Cleaner</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#FFFFFF;">Upload a CSV or fetch from SQL to get cleand data back.</p>', unsafe_allow_html=True)

# ---- TABS ----
tab_csv, tab_sql = st.tabs(["📂 CSV Upload", "🗄️ SQL Database"])

temp_df = None
source_choice = None
conn_str = None  # store SQLAlchemy connection string

# =============== CSV TAB ==================
with tab_csv:
    uploaded_file_cleaner = st.file_uploader("Choose a CSV file", type=["csv"])
    st.markdown("⚠️ **Note:** For best performance, please upload smaller CSV files.")

    if uploaded_file_cleaner:
        try:
            temp_df = pd.read_csv(uploaded_file_cleaner)
            st.success("✅ File uploaded successfully!")
            st.dataframe(temp_df.head(5))
            source_choice = "CSV Upload"
        except Exception as e:
            st.error(f"❌ Pandas could not read file: {e}")


# =============== SQL TAB ==================
with tab_sql:
    st.subheader("🔗 Connect to SQL Database")
    st.markdown("ℹ️ Enter a valid **SQLAlchemy connection string** (works for SQLite, MySQL, PostgreSQL).")

    conn_str = st.text_input(
        "Connection String",
        "sqlite:///example.db", 
        help="Examples:\nSQLite → sqlite:///example.db\nMySQL → mysql+pymysql://user:pass@localhost:3306/db\nPostgres → postgresql+psycopg2://user:pass@localhost:5432/db"
    )
    query = st.text_area("Enter SQL Query", "SELECT * FROM my_table LIMIT 10")

    if st.button("Run Query"):
        try:
            engine = create_engine(conn_str)
            temp_df = pd.read_sql(query, engine)
            st.success("✅ Query executed successfully")
            st.dataframe(temp_df.head(10))
            source_choice = "SQL Database"
        except Exception as e:
            st.error(f"❌ SQL Error: {e}")

# =============== CLEANING FLOW (COMMON) ==================
if temp_df is not None and isinstance(temp_df, pd.DataFrame):
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
            processed_output = csv_processor.process_file(
                temp_df,  # always pass df directly
                columns_to_include=selected_columns,
                columns_to_clean=selected_columns
            )

        if isinstance(processed_output, io.StringIO):
            st.success("✅ Successfully processed!")
            preview_df = pd.read_csv(io.StringIO(processed_output.getvalue()))
            st.write("### 👀 Preview of Cleaned Data:")
            st.dataframe(preview_df.head(10), use_container_width=True)

            # Download as CSV
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=processed_output.getvalue(),
                file_name="cleaned_data.csv",
                mime="text/csv"
            )

            # --- NEW: Save back to SQL ---
            if source_choice == "SQL Database":
                with st.expander("💾 Save to Database"):
                    target_table = st.text_input("Target table name", "cleaned_table")
                    save_mode = st.selectbox("Save Mode", ["Replace (overwrite)", "Append (add rows)"])
                    save_btn = st.button("Save Cleaned Data to SQL")

                    if save_btn:
                        try:
                            engine = create_engine(conn_str)
                            write_mode = "replace" if "Replace" in save_mode else "append"
                            preview_df.to_sql(target_table, engine, if_exists=write_mode, index=False)
                            st.success(f"✅ Cleaned data saved to table `{target_table}` ({write_mode})")
                        except Exception as e:
                            st.error(f"❌ Failed to save: {e}")

        else:
            st.error(f"❌ Error: {processed_output}")
