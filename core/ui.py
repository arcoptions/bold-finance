import streamlit as st
import base64
import os

def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. HIDE SIDEBAR AND PULL CONTENT UP */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 0rem !important;
            max-width: 95% !important; 
        }

        /* 2. INLINE HEADER (PERFECTLY CENTERED VERTICALLY) */
        .header-container {
            display: flex;
            align-items: center; /* Locks logo and text inline */
            justify-content: flex-start;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #E2E8F0; /* Clean separator line */
        }
        .header-logo {
            height: 75px; /* Significantly larger logo */
            border-radius: 8px;
            object-fit: contain;
        }
        .header-title {
            font-size: 2.6rem !important; 
            font-weight: 800;
            color: #1E293B;
            margin: 0px !important;
            padding: 0px !important;
            margin-left: 20px !important;
            line-height: 1; 
        }

        /* 3. TABS AND METRICS */
        [data-testid="stTabs"] { display: flex; flex-direction: column; }
        [data-testid="stTabs"] > div:first-child {
            justify-content: flex-start;
            width: 100%;
            border-bottom: 2px solid #E2E8F0;
            margin-bottom: 20px;
        }
        [data-testid="stTabs"] button {
            font-size: 1.1rem !important; 
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
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

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def render_header():
    base64_img = get_base64_image("logo.png")
    img_html = f'<img src="data:image/png;base64,{base64_img}" class="header-logo">' if base64_img else '<span style="font-size: 40px;">🏢</span>'
    
    st.markdown(f'''
        <div class="header-container">
            {img_html}
            <h1 class="header-title">B&I Financial ERP</h1>
        </div>
    ''', unsafe_allow_html=True)
