import streamlit as st
import os

def inject_custom_css():
    st.markdown("""
        <style>
        /* Professional Metric Cards */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 600;
            color: #1E293B;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1rem;
            font-weight: 500;
            color: #64748B;
        }
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #F8FAFC;
            border-right: 1px solid #E2E8F0;
        }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar_logo():
    if os.path.exists("logo.png"):
        st.logo("logo.png", size="large")

    st.sidebar.markdown("### B&I Financial ERP")
    st.sidebar.markdown("---")
