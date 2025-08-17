import streamlit as st

# Set page config
st.set_page_config(page_title="About | DataFlow Studio", page_icon="ℹ️", layout="centered")

# ---- CSS Styling ----
st.markdown("""
<style>
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

# ---- Main Page Styling ----
st.markdown("""
<style>
    .stApp {
        background-color: #212833; /* A dark blue-gray */
    }
</style>
""", unsafe_allow_html=True)

# ---- Sidebar Navigation ----
import navigation
navigation.navigation_bar()

# Title and Introduction
st.title("🧹📊 About This Application")
st.markdown("""
Welcome to **DataFlow Studio** – your all-in-one interactive platform for data cleaning, visualization, modeling, and testing, built entirely with Python and powered by **Streamlit**.
""")

# Section: What is DataFlow Studio?
st.header("🚀 What is DataFlow Studio?")
st.markdown("""
**DataFlow Studio** is a streamlined web application designed for data scientists, analysts, and enthusiasts who want a fast and intuitive way to explore and analyze data. Whether you're working with messy datasets, building machine learning models, or validating predictions, this app brings every stage of the data pipeline into one seamless experience.
""")

# Core Features
st.header("🔧 Core Features")

st.subheader("🧼 1. Data Cleaning")
st.markdown("""
- Upload datasets in CSV or Excel format.
- Identify and handle missing values.
- Remove duplicates, rename columns, and filter outliers.
- Basic transformations like encoding categorical data and standardizing values.
""")

st.subheader("📈 2. Data Visualization")
st.markdown("""
- Generate beautiful, interactive charts using Plotly and Matplotlib.
- Visualize distributions, correlations, and time-series data.
- Custom chart options for bar plots, scatter plots, heatmaps, boxplots, and more.
""")

st.subheader("🤖 3. Modeling")
st.markdown("""
- Train machine learning models using scikit-learn.
- Choose from a range of algorithms like Linear Regression, Random Forest, SVM, and more.
- Customize model parameters through user-friendly controls.
""")

st.subheader("✅ 4. Testing & Evaluation")
st.markdown("""
- Split your data into training and testing sets.
- Evaluate models using common metrics: Accuracy, Precision, Recall, F1-score, ROC AUC.
- Display confusion matrices and prediction visualizations.
""")

# Why Use This App
st.header("🧠 Why Use This App?")
st.markdown("""
- **No coding required**: Use an intuitive interface to perform complex data tasks.  
- **Built with Python**: Uses popular data science libraries like Pandas, NumPy, Scikit-learn, Plotly, and Matplotlib.  
- **Flexible & Expandable**: Easily adaptable to different datasets and modeling tasks.  
- **Runs locally or on the cloud**: Deploy using Streamlit Share, Hugging Face Spaces, or your own server.  
""")

# Technologies Used
st.header("🛠️ Technologies Used")
st.markdown("""
- **Frontend/Backend**: [Streamlit](https://streamlit.io/)  
- **Data Processing**: Pandas, NumPy  
- **Visualization**: Matplotlib, Seaborn, Plotly  
- **Modeling & ML**: Scikit-learn  
- **Deployment**: Streamlit Cloud / Custom Server  
""")

# Contact
st.header("📫 Contact & Contributions")
st.markdown("""
Want to contribute, report an issue, or collaborate? Feel free to reach out or check out the source code on GitHub:

- GitHub: [github.com/your-repo](https://github.com/bushan_patil)  
- Email: [quicktest04@gmail.com](mailto:Test@gmail.com)
""")
