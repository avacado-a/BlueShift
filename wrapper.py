import streamlit as st

st.set_page_config(
    page_title="BlueShift",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom css to clean the page styling and prevent vertical scrollbars on the body
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
    </style>
""")

# HTML5 Fullscreen API container wrapper using raw HTML & JavaScript (avoids st.components warnings)
st.html("""
    <div id="fullscreen-container" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #0b0f19;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    ">
        <div id="launch-box" style="text-align: center; max-width: 500px; padding: 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); background: rgba(255,255,255,0.01); box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <h2 style="color: #00f2fe; margin-bottom: 12px; font-weight: 800; font-size: 1.8rem; letter-spacing: -0.01em;">🌊 BlueShift Gateway</h2>
            <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin-bottom: 25px;">
                The forecasting models are running locally. Click below to launch the dashboard in fullscreen mode, hiding all Streamlit headers and side panels.
            </p>
            <button id="launch-btn" style="
                padding: 12px 32px;
                background: #00f2fe;
                color: #0b0f19;
                font-size: 1.05rem;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(0, 242, 254, 0.25);
                transition: transform 0.1s ease;
            ">⚡ Go Full Screen</button>
        </div>
        <iframe id="dashboard-iframe" src="https://a38siovkckb9.shares.zrok.io/" style="
            width: 100%;
            height: 100%;
            border: none;
            display: none;
        " allow="fullscreen"></iframe>
    </div>

    <script>
        const btn = document.getElementById('launch-btn');
        const box = document.getElementById('launch-box');
        const iframe = document.getElementById('dashboard-iframe');
        const container = document.getElementById('fullscreen-container');

        btn.addEventListener('click', () => {
            box.style.display = 'none';
            iframe.style.display = 'block';
            
            // Request fullscreen on the container to overlay everything
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.mozRequestFullScreen) { // Firefox
                container.mozRequestFullScreen();
            } else if (container.webkitRequestFullscreen) { // Chrome, Safari, Opera
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) { // IE/Edge
                container.msRequestFullscreen();
            }
        });

        // Ensure that if they exit fullscreen, the iframe stays visible in windowed mode
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                iframe.style.display = 'block';
                box.style.display = 'none';
            }
        });
    </script>
""")
