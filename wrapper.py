import streamlit as st

st.set_page_config(
    page_title="BlueShift",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for entry
if "entered" not in st.session_state:
    st.session_state.entered = False

if not st.session_state.entered:
    # Custom CSS for Gateway styling
    st.html("""
        <style>
            /* Hide Streamlit UI elements */
            header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                width: 0 !important;
            }
            .stApp {
                background-color: #0b0f19 !important;
            }
            .block-container {
                max-width: 500px !important;
                padding-top: 20vh !important;
                margin: 0 auto !important;
            }
            .gateway-card {
                text-align: center;
                padding: 35px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                background: rgba(255, 255, 255, 0.01);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin-bottom: 25px;
            }
            .gateway-title {
                color: #00f2fe;
                margin-bottom: 16px;
                font-weight: 800;
                font-size: 2rem;
                letter-spacing: -0.02em;
            }
            .gateway-desc {
                color: #9ca3af;
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0;
            }
            /* Premium button styling to match design system */
            div.stButton > button {
                width: 100% !important;
                padding: 14px 40px !important;
                background: #00f2fe !important;
                color: #0b0f19 !important;
                font-size: 1.1rem !important;
                font-weight: bold !important;
                border: none !important;
                border-radius: 6px !important;
                cursor: pointer !important;
                box-shadow: 0 4px 20px rgba(0, 242, 254, 0.25) !important;
                transition: all 0.2s ease !important;
            }
            div.stButton > button:hover {
                background: #00e0eb !important;
                color: #0b0f19 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 25px rgba(0, 242, 254, 0.35) !important;
            }
            div.stButton > button:active {
                transform: translateY(0) !important;
            }
        </style>
    """)
    
    # Render gateway card
    st.html("""
        <div class="gateway-card">
            <div class="gateway-title">🌊 BlueShift Gateway</div>
            <p class="gateway-desc">
                The forecasting models are running locally. Click below to launch the dashboard in fullscreen mode, hiding all Streamlit headers and side panels.
            </p>
        </div>
    """)
    
    # Standard Streamlit button, which triggers session state update and rerun when clicked
    if st.button("Enter BlueShift"):
        st.session_state.entered = True
        st.rerun()

else:
    # Aggressive CSS to hide Streamlit UI and stretch the iframe to fill 100% of screen
    st.html("""
        <style>
            header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {
                display: none !important;
                visibility: hidden !important;
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
            iframe {
                width: 100vw !important;
                height: 100vh !important;
                border: none !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        </style>
    """)
    
    # Embed the local app tunnel native wrapper using st.iframe
    st.iframe("https://a38siovkckb9.shares.zrok.io/", height=1000)


