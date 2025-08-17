import streamlit as st
import auth_ui
import navigation
import auth_sqlite as auth

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="ADP",
    page_icon="📊",
    layout="wide"
)

# initialize DB and tables
auth.init_db()

# ---- LOGIN CHECK ----
if not st.session_state.get("authenticated", False):
    auth_ui.login_widget()
    # ---- CSS STYLING ----
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    st.stop()

# ---- Authenticated Area ----
username = st.session_state["username"]

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

# ---- Sidebar Navigation (only AFTER login) ----
navigation.navigation_bar()

# ---- Main Page Styling ----
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom, #301934, #120c15); /* A dark purple gradient */
    }
</style>
""", unsafe_allow_html=True)

# ---- Helper Function for Sections ----
def add_section(title, description, emoji, image_on_left=True):
    emoji_html = f"<span style='font-size: 80px;'>{emoji}</span>"

    if image_on_left:
        col_img, col_desc = st.columns([1, 2])
    else:
        col_desc, col_img = st.columns([2, 1])

    with col_img:
        st.markdown(
            f"<div style='text-align: center; padding: 10px;'>{emoji_html}</div>",
            unsafe_allow_html=True,
        )

    with col_desc:
        st.markdown(
            f"""
            <div class="section-description">
                <strong>{title}</strong><br><br>
                {description}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<hr style='border:0.5px solid #444; margin:30px 0;'>", unsafe_allow_html=True)

# ---- Main Page Content ----
st.title("📊 MYCSV - Your Data Processing Hub 🚀")
st.markdown("<hr style='border:0.5px solid #ddd; margin:25px 0;'>", unsafe_allow_html=True)

add_section(
    "CSV Cleaner",
    "Data cleaning is an essential step in any data analysis process. "
    "It involves handling missing values, correcting inconsistencies, "
    "and transforming raw data into a structured format. This process ensures "
    "that your data is accurate, complete, and ready for analysis or further processing. "
    "In this section, you can upload your CSV files and clean them using various tools.",
    "🧹", True
)

add_section(
    "Visualize Data",
    "Data visualization is key to understanding trends and patterns within your data. "
    "By using charts, graphs, and other visual elements, you can communicate your findings "
    "in a way that is easily understood. This section provides tools to create various "
    "visualizations to help you analyze the relationships, distributions, and trends within your data.",
    "📊", False
)

add_section(
    "Generate Models",
    "In this section, you can apply machine learning models to predict trends or outcomes "
    "based on historical data. By utilizing algorithms like regression, classification, and clustering, "
    "you can generate predictions that help inform future decisions. The system also allows you to evaluate "
    "model performance and make improvements to your predictions over time.",
    "⚙️", True
)

add_section(
    "Testing Models",
    "Testing Models involves evaluating how well a machine learning or statistical model performs on unseen data. "
    "It helps determine the model’s accuracy, reliability, and generalization ability. This process typically includes "
    "using a separate test dataset, applying performance metrics (like accuracy, precision, recall, or RMSE), and "
    "identifying potential issues like overfitting or underfitting. Testing is a crucial step to ensure the model can "
    "make accurate predictions in real-world scenarios.",
    "🧪", False
)