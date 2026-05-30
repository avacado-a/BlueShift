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
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {margin: 0; padding: 0; overflow: hidden; background: #0b0f19;}
        div.block-container {padding: 0; max-width: 100%; margin: 0; height: 100vh;}
        iframe {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            border: none;
            margin: 0;
            padding: 0;
            z-index: 999999;
        }
    </style>
""")

# Embed the tunnel URL natively (keeps nice URL in address bar)
# Note: For localtunnel, you must bypass the warning screen once in your browser.
# For a warning-free experience, consider using Serveo or Pinggy.
st.components.v1.iframe("https://poor-laws-march.loca.lt", height=1000)
