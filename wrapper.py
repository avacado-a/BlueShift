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
            /* Custom button styling centered inside the card */
            .custom-gateway-btn {
                display: inline-block !important;
                width: auto !important;
                min-width: 220px !important;
                margin: 25px auto 0 auto !important;
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
                text-decoration: none !important;
                text-align: center !important;
            }
            .custom-gateway-btn:hover {
                background: #00e0eb !important;
                color: #0b0f19 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 25px rgba(0, 242, 254, 0.35) !important;
            }
            .custom-gateway-btn:active {
                transform: translateY(0) !important;
            }
            /* Hide the real native Streamlit button */
            div.stButton {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                width: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        </style>
    """)
    
    # Render gateway card with custom centered button inside
    st.html("""
        <div class="gateway-card">
            <div class="gateway-title">🌊 BlueShift Gateway</div>
            <p class="gateway-desc">
                The forecasting models are running locally. Click below to launch the dashboard in fullscreen mode, hiding all Streamlit headers and side panels.
            </p>
            <button class="custom-gateway-btn" onclick="(window.parent.document.querySelector('div.stButton button') || document.querySelector('div.stButton button')).click()">Enter BlueShift</button>
        </div>
    """)
    
    # Standard Streamlit button (hidden, triggered programmatically)
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
        </style>
    """)
    
    # Embed the local app tunnel native wrapper using custom HTML iframe for proper fullscreen support
    st.html("""
        <iframe src="https://a38siovkckb9.shares.zrok.io/" 
                style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 999999;" 
                sandbox="allow-forms allow-modals allow-popups allow-same-origin allow-scripts allow-fullscreen" 
                allow="fullscreen" 
                allowfullscreen>
        </iframe>
    """)


