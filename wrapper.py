import streamlit as st

st.set_page_config(
    page_title="BlueShift",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Strip all Streamlit headers, footers, and margins to allow full screen object/embed rendering
st.html("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {margin: 0; padding: 0; overflow: hidden; background: #0b0f19;}
        div.block-container {padding: 0; max-width: 100%; margin: 0;}
        .embed-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            border: none;
            z-index: 999999;
        }
    </style>
""")

# Render using HTML5 <object> and <embed> tags to wrap the localtunnel URL (bypassing <iframe> filters)
st.html("""
    <object class="embed-container" data="https://poor-laws-march.loca.lt">
        <embed class="embed-container" src="https://poor-laws-march.loca.lt"></embed>
    </object>
""")
