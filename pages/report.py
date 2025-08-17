import streamlit as st
from Back_End import process
from Back_End import csv_processor3  # Assuming the modified backend logic is in this script

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Generate Models",
    page_icon="📜",
    layout="wide"
)

# Set background image
process.set_bg_image("Background.webp")

# ---- Sidebar Navigation ----
import navigation
navigation.navigation_bar()

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
st.markdown('<h1 class="title">📜 Generate Reports</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #FFFFFF;">Upload your CSV file, and we’ll create a model for you!</p>', unsafe_allow_html=True)

uploaded_file_report = st.file_uploader("Choose a CSV file", type=["csv"])

st.markdown('<h3>Make sure that the target value should be at least column.</h2>', unsafe_allow_html=True)

st.markdown("⚠️ **Note:** For best performance, please upload smaller CSV files.")
st.markdown("⚠️ **Note:** For best performance, please upload **Cleaned CSV files**.")

if st.button("If you are doing Anomaly detection Click me."):
    st.switch_page("pages/Anomaly.py")

if uploaded_file_report:
    # Inform the user that the file is being processed
    with st.spinner("Processing... ⏳"):
        # Process the file using the backend function
        processed_output = csv_processor3.process_file(uploaded_file_report)

    # Check if the output is valid and provide a downloadable model file
    if isinstance(processed_output, tuple) and len(processed_output) == 4:
        model_filename, best_model_name, best_score, best_params = processed_output
        st.success(f"✅ Successfully processed! Best model: {best_model_name} with performance score: {best_score:.4f}")

        # Offer the pickled model file for download
        with open(model_filename, 'rb') as model_file:
            st.download_button(
                label="⬇️ Download Model",
                data=model_file,
                file_name="best_model.pkl",
                mime="application/pkl"
            )
    else:
        st.error(f"❌ Error: {processed_output}")
