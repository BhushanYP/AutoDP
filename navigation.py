import streamlit as st
def navigation_bar():
    tabs = {
        "Home": ("🏠", "home.py"),  # No link for Home
        "Cleaning": ("🧹", "Cleaner.py"),
        "Visualize": ("📊", "visualize.py"),
        "Model Creator": ("⚙️", "report.py"),
        "Model Tester": ("🧪", "testing_ground.py"),
        "Account": ("📚", "Account.py"),
        "About": ("ℹ️", "about.py")
    }

    with st.sidebar:
        st.markdown("## 📊 Pipelines 📁")
        st.markdown("---")
        for tab, (icon, filename) in tabs.items():
            if filename:  # Skip Home
                st.page_link(f"pages/{filename}", label=f"{icon} {tab}")