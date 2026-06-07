import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.html("""
    <style>
        header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {
            display: none !important;
            /* visibility: hidden !important; */
            height: 0 !important;
            width: 0 !important;
        }
        .stApp {
            background-color: #0b0f19 !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container, [data-testid="stVerticalBlock"] {
            margin: 0 !important;
            padding: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
        }
    </style>
""")
        
# Hide Streamlit header, footer and adjust margins
st.markdown("""
    <style>
        .reportview-container .main .block-container {
            padding-top: 0rem;
            padding-right: 0rem;
            padding-left: 0rem;
            padding-bottom: 0rem;
        }
        iframe {
            width: 100vw;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

components.iframe("https://9kaivl7ebvfu.shares.zrok.io", height=1000)