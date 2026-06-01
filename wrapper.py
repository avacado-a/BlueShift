import streamlit as st

st.set_page_config(
    page_title="BlueShift",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for entry

# Aggressive CSS to hide Streamlit UI and stretch the iframe to fill 100% of screen
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

# Embed the local app tunnel native wrapper using custom HTML iframe for proper fullscreen support
st.html("""
    <iframe src="https://g0eglhcqa0pt.shares.zrok.io/">
            style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 999999;" 
            sandbox="allow-forms allow-modals allow-popups allow-same-origin allow-scripts allow-fullscreen" 
            allow="fullscreen" 
            allowfullscreen>
    </iframe>
""")


