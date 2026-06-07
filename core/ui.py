import streamlit as st
import base64
import os

def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. HIDE THE SIDEBAR AND TOP PADDING */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        
        /* Pull content to the top */
        .block-container {
            padding-top: 2rem !important; 
            padding-bottom: 0rem !important;
        }

        /* 2. CENTER AND ENLARGE THE HEADER */
        .center-header {
            text-align: center;
            font-size: 3.5rem !important;
            font-weight: 800;
            color: #1E293B;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .center-img {
            display: flex;
            justify-content: center;
            margin-bottom: 0px;
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
            font-size: 1.25rem !important; 
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

def get_base64_image(image_path):
    """Helper function to safely encode the image."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def render_header():
    """Forces the logo and title to the center, pulling them up."""
    # Attempt to load the logo
    base64_img = get_base64_image("logo.png")
    
    if base64_img:
        st.markdown(
            f'''
            <div class="center-img">
                <img src="data:image/png;base64,{base64_img}" width="150" style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            </div>
            ''', 
            unsafe_allow_html=True
        )
    else:
        # Fallback if logo is missing, still keeping things centered
        st.markdown(
            '<div class="center-img" style="color: #EF4444; font-size: 0.8rem;">(Logo file not found. Ensure logo.png is in the root directory)</div>', 
            unsafe_allow_html=True
        )
        
    st.markdown('<h1 class="center-header">B&I Financial ERP</h1>', unsafe_allow_html=True)
