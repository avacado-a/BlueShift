import streamlit as st

st.set_page_config(
    page_title="Redirecting to BlueShift...",
    page_icon="🌊",
    layout="centered"
)

st.markdown("""
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h2 style="color: #00f2fe;">🌊 Redirecting to BlueShift...</h2>
        <p style="color: #9ca3af; font-size: 1.1rem;">
            We are redirecting you to the secure local tunnel hosting the dashboard.
        </p>
        <p style="color: #6b7280; font-size: 0.9rem;">
            If you are not redirected automatically within a few seconds, click the link below:
        </p>
        <a href="https://poor-laws-march.loca.lt" target="_top" style="
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: #00f2fe;
            color: #0b0f19;
            text-decoration: none;
            font-weight: bold;
            border-radius: 5px;
        ">Go to Dashboard</a>
    </div>
""", unsafe_allow_html=True)

# Use window.top.location.href to break out of Streamlit Cloud's parent sandboxed iframe and redirect
st.html("""
    <script>
        setTimeout(function() {
            window.top.location.href = "https://poor-laws-march.loca.lt";
        }, 1000);
    </script>
""")
