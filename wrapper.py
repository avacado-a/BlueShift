import streamlit as st

st.set_page_config(
    page_title="BlueShift Gateway",
    page_icon="🌊",
    layout="wide"
)

# Render a modern, styled control header at the top
st.html("""
    <div style="text-align: center; margin-bottom: 25px; font-family: sans-serif; padding: 25px; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);">
        <h1 style="color: #00f2fe; margin-bottom: 8px; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em;">🌊 BlueShift Gateway</h1>
        <p style="color: #9ca3af; margin: 0 auto 15px auto; max-width: 650px; font-size: 1rem; line-height: 1.6;">
            Welcome to the BlueShift trend forecasting system. The backend ML pipeline and database are running locally. You can use the embedded portal below or launch the dashboard directly in a new tab.
        </p>
        <div>
            <a href="https://poor-laws-march.loca.lt" target="_blank" style="
                display: inline-block;
                padding: 12px 28px;
                background: #00f2fe;
                color: #0b0f19;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.05rem;
                border-radius: 6px;
                box-shadow: 0 4px 20px rgba(0, 242, 254, 0.25);
                transition: all 0.2s ease-in-out;
            ">⚡ Launch Dashboard in New Tab</a>
        </div>
    </div>
""")

# Native Streamlit iframe container for embedding
st.markdown("### 🖥️ Embedded Live Preview")
st.components.v1.iframe("https://poor-laws-march.loca.lt", height=950, scrolling=True)
