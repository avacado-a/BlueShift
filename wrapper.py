import streamlit as st

st.set_page_config(
    page_title="BlueShift",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS to force the embedded iframe to take up 100% of the viewport and hide Streamlit UI
st.html("""
    <style>
        /* Hide all Streamlit UI overlays */
        header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
        }
        
        /* Force body and core containers to be marginless & full screen */
        body, .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            width: 100vw !important;
            height: 100vh !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            background-color: #0b0f19 !important;
        }
        
        /* Style the iframe to break out of the DOM flow and occupy the exact viewport */
        iframe {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 999999 !important;
            background-color: #0b0f19 !important;
        }
    </style>
""")

st.components.v1.iframe("https://a38siovkckb9.shares.zrok.io/", height=1000)
