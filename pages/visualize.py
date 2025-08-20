import streamlit as st
import io
from Back_End import csv_processor2
from Back_End import process
import base64

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Visualize Data",
    page_icon="📊",
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
st.markdown('<h1 class="title">📊 Visualize Data</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #FFFFFF;">Upload your CSV file, and we’ll Analyze and Visualized it for you!</p>', unsafe_allow_html=True)

uploaded_file_analizer = st.file_uploader("Choose a CSV file", type=["csv"])

st.markdown("⚠️ **Note:** For best performance, please upload smaller CSV files.")
st.markdown("⚠️ **Note:** For best performance, please upload **Cleaned CSV files**.")

if uploaded_file_analizer:
    with st.spinner("Processing... ⏳"):
        processed_output = csv_processor2.process_file(uploaded_file_analizer)

    if isinstance(processed_output, io.BytesIO):
        st.success("✅ Successfully processed!")

        # --- Download button ---
        st.download_button(
            label="⬇️ Download PDF",
            data=processed_output.getvalue(),
            file_name="simple_pdf.pdf",
            mime="application/pdf"
        )
    else:
        st.error(f"❌ Error: {processed_output}")
