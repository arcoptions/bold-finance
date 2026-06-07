import streamlit as st
import os
import base64

def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. HIDE THE SIDEBAR COMPLETELY */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }

        /* 2. CENTER AND ENLARGE THE HEADER */
        .center-header {
            text-align: center;
            font-size: 3.5rem !important; /* Extremely large font */
            font-weight: 800;
            color: #1E293B;
            margin-bottom: 0px;
            padding-bottom: 20px;
        }
        .center-img {
            display: flex;
            justify-content: center;
            margin-bottom: -10px;
            margin-top: 20px;
        }

        /* 3. CENTER THE HORIZONTAL TABS */
        [data-testid="stTabs"] {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        [data-testid="stTabs"] > div:first-child {
            justify-content: center;
            width: 100%;
            border-bottom: 2px solid #E2E8F0;
            margin-bottom: 20px;
        }
        [data-testid="stTabs"] button {
            font-size: 1.25rem !important; /* Make tab names larger */
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Professional Metric Cards */
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 600; color: #1E293B; }
        [data-testid="stMetricLabel"] { font-size: 1rem; font-weight: 500; color: #64748B; }
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Forces the logo and title to the exact center of the screen."""
    st.markdown('<div class="center-img">', unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        # Base64 encoding guarantees the image loads even if Streamlit Cloud misplaces the static path
        with open("logo.png", "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(f'<img src="data:image/png;base64,{data}" width="100">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<h1 class="center-header">B&I Financial ERP</h1>', unsafe_allow_html=True)
