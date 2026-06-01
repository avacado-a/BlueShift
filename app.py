import os
import sys
import json
import time
import subprocess
from datetime import datetime
import pandas as pd
import altair as alt
import streamlit as st
import urllib
import urllib.parse
import textwrap

# Set Streamlit page config
st.set_page_config(
    page_title="BlueShift Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Resolve paths
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(DIR_PATH)
if PARENT_PATH not in sys.path:
    sys.path.insert(0, PARENT_PATH)
CACHE_PATH = os.path.join(DIR_PATH, "results_cache.json")
LOCK_PATH = os.path.join(DIR_PATH, "update.lock")
CSS_PATH = os.path.join(DIR_PATH, "assets", "style.css")

# Load CSS
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r") as f:
        st.html(f"<style>{f.read()}</style>")
else:
    st.warning("Custom CSS file not found. Falling back to native Streamlit styling.")

def render_research_page():
    html_content = """
        <style>
            /* Flip Card CSS */
            .flip-card {
                background-color: transparent;
                height: 250px;
                perspective: 1000px;
                cursor: pointer;
            }
            .flip-card-inner {
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.6s;
                transform-style: preserve-3d;
            }
            .flip-card:hover .flip-card-inner {
                transform: rotateY(180deg);
            }
            .flip-card-front, .flip-card-back {
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                border-radius: 12px;
                padding: 22px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                box-sizing: border-box;
            }
            .flip-card-front {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .flip-card-back {
                background: rgba(0, 242, 254, 0.05);
                border: 1px solid rgba(0, 242, 254, 0.3);
                transform: rotateY(180deg);
            }

            /* Pipeline Stepper Hover */
            .pipeline-step {
                transition: all 0.3s ease;
                overflow: hidden;
                position: relative;
            }
            .pipeline-step::before {
                content: '';
                position: absolute;
                top: 0; left: -100%; width: 100%; height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 242, 254, 0.1), transparent);
                transition: left 0.5s ease;
            }
            .pipeline-step:hover::before {
                left: 100%;
            }
            .pipeline-step:hover {
                transform: translateY(-5px);
                border-color: #00f2fe;
                box-shadow: 0 5px 15px rgba(0, 242, 254, 0.15);
            }
            .pipeline-detail {
                opacity: 0.4;
                transition: opacity 0.3s ease;
                filter: blur(2px);
            }
            .pipeline-step:hover .pipeline-detail {
                opacity: 1;
                filter: blur(0px);
            }

            /* VRAM Game CSS */
            .btn-game {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                transition: 0.2s;
                font-weight: 600;
            }
            .btn-game:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            #vram-fill {
                transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.4s;
            }
        </style>

        <div class="glass-container paper-layout" style="padding: 40px; max-width: 100%; box-sizing: border-box; margin: 0 auto;">
            
            <div class="paper-header" style="text-align: center; margin-bottom: 45px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 35px;">
                <span class="badge" style="background: rgba(0, 242, 254, 0.12); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.25); margin-bottom: 12px; cursor: pointer;" title="Machine-Prediction Using Linguistic Semantic Embeddings">M-PULSE METHODOLOGY</span>
                <h1 style="font-size: 2.4rem; font-weight: 800; color: #ffffff; line-height: 1.3; margin-bottom: 15px; letter-spacing: -0.02em;">
                    How M-PULSE Forecasts Media Trends
                </h1>
                <div class="paper-author" style="font-size: 1.2rem; font-weight: 600; color: #00f2fe; margin-bottom: 5px;">Sidh Parikh</div>
                <div style="font-size: 0.95rem; color: #9ca3af; line-height: 1.5;">
                    Glenelg High School &bull; Gifted and Talented Independent Research &bull; Ms. Leila Chawkat
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 45px;">
                <div class="news-item" style="padding: 25px; background: rgba(243, 85, 136, 0.02); border: 1px solid rgba(243, 85, 136, 0.15); border-radius: 12px;">
                    <h3 style="color: #f35588; margin-bottom: 12px;">The Core Problem</h3>
                    <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6;">
                        Standard Large Language Models (LLMs) are frozen in time, treat all topics identically, and require thousands of dollars in server hardware to run.
                    </p>
                </div>
                <div class="news-item" style="padding: 25px; background: rgba(0, 242, 254, 0.02); border: 1px solid rgba(0, 242, 254, 0.15); border-radius: 12px;">
                    <h3 style="color: #00f2fe; margin-bottom: 12px;">The M-PULSE Solution</h3>
                    <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6;">
                        A dual-stream NLP framework that builds dynamic semantic spaces on-the-fly, using lightweight LSTMs that run on standard consumer computers.
                    </p>
                </div>
            </div>

            <div class="section-title" style="margin-top: 0; display: flex; align-items: center; justify-content: space-between;">
                <span>Step-by-Step Forecasting Engine</span>
                <span style="font-size: 0.75rem; color: #6b7280; font-weight: normal;">Hover over steps to decrypt</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 45px;">
                <div class="news-item pipeline-step" style="display: flex; flex-direction: column; justify-content: space-between; padding: 20px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); height: 260px;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #00f2fe; margin-bottom: 8px;">01</div>
                        <h4 style="color: #ffffff; margin-bottom: 8px;">Dual-Stream Ingest</h4>
                        <div class="pipeline-detail">
                            <p style="color: #9ca3af; font-size: 0.85rem; line-height: 1.5;">
                                Ingests news timelines from <strong>GDELT</strong> and real-time social conversations from <strong>Bluesky</strong>.
                            </p>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe; font-size: 0.7rem;">PIPELINE ENTRY</span>
                </div>
                <div class="news-item pipeline-step" style="display: flex; flex-direction: column; justify-content: space-between; padding: 20px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); height: 260px;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #00f2fe; margin-bottom: 8px;">02</div>
                        <h4 style="color: #ffffff; margin-bottom: 8px;">DBSCAN Filtering</h4>
                        <div class="pipeline-detail">
                            <p style="color: #9ca3af; font-size: 0.85rem; line-height: 1.5;">
                                Uses a <strong>SentenceTransformer</strong> and <strong>DBSCAN Clustering</strong> to drop anomalies and strip extreme political bias.
                            </p>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe; font-size: 0.7rem;">BIAS MITIGATION</span>
                </div>
                <div class="news-item pipeline-step" style="display: flex; flex-direction: column; justify-content: space-between; padding: 20px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); height: 260px;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #00f2fe; margin-bottom: 8px;">03</div>
                        <h4 style="color: #ffffff; margin-bottom: 8px;">Local Word2Vec</h4>
                        <div class="pipeline-detail">
                            <p style="color: #9ca3af; font-size: 0.85rem; line-height: 1.5;">
                                Trains a custom, localized <strong>Word2Vec</strong> model to extract high-context local semantic maps.
                            </p>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe; font-size: 0.7rem;">CONTEXT BUILDING</span>
                </div>
                <div class="news-item pipeline-step" style="display: flex; flex-direction: column; justify-content: space-between; padding: 20px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); height: 260px;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #00f2fe; margin-bottom: 8px;">04</div>
                        <h4 style="color: #ffffff; margin-bottom: 8px;">LSTM Prediction</h4>
                        <div class="pipeline-detail">
                            <p style="color: #9ca3af; font-size: 0.85rem; line-height: 1.5;">
                                Fuses the latent vectors from news & social streams inside a <strong>PyTorch LSTM</strong> network to forecast volume.
                            </p>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe; font-size: 0.7rem;">DUAL-STREAM FORECAST</span>
                </div>
            </div>

            <div class="section-title" style="display: flex; align-items: center; justify-content: space-between;">
                <span>Core Research Discoveries</span>
                <span style="font-size: 0.75rem; color: #6b7280; font-weight: normal;">Flip cards to reveal findings</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 45px;">
                
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <span style="font-size: 3rem; margin-bottom: 15px;">📊</span>
                            <h4 style="color: #ffffff; margin: 0;">What drives predictability?</h4>
                            <p style="color: #6b7280; font-size: 0.8rem; margin-top: 10px;">Hover to uncover</p>
                        </div>
                        <div class="flip-card-back">
                            <h4 style="color: #00f2fe; margin-bottom: 10px;">Topic Structure Rules All</h4>
                            <p style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.5; margin:0;">
                                Objective topics produce the lowest model errors. Politically polarized topics exhibit high volatility and diverge rapidly.
                            </p>
                        </div>
                    </div>
                </div>

                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <span style="font-size: 3rem; margin-bottom: 15px;">⚓</span>
                            <h4 style="color: #ffffff; margin: 0;">Social Media vs. Reality</h4>
                            <p style="color: #6b7280; font-size: 0.8rem; margin-top: 10px;">Hover to uncover</p>
                        </div>
                        <div class="flip-card-back">
                            <h4 style="color: #00f2fe; margin-bottom: 10px;">The Anchoring Power of News</h4>
                            <p style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.5; margin:0;">
                                Isolated social media models fail entirely. Introducing institutional news as a "dual-stream anchor" absorbs outlier shocks and stabilizes predictions.
                            </p>
                        </div>
                    </div>
                </div>

                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <span style="font-size: 3rem; margin-bottom: 15px;">⏱️</span>
                            <h4 style="color: #ffffff; margin: 0;">Do feelings predict trends?</h4>
                            <p style="color: #6b7280; font-size: 0.8rem; margin-top: 10px;">Hover to uncover</p>
                        </div>
                        <div class="flip-card-back">
                            <h4 style="color: #00f2fe; margin-bottom: 10px;">The Cognitive Lag Window</h4>
                            <p style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.5; margin:0;">
                                Sentiment is a lagging indicator. Conversation volume spikes first, followed by a latency window while the public processes updates before sentiment catches up.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="glass-container" style="background: rgba(0, 242, 254, 0.02); border: 1px solid rgba(0, 242, 254, 0.2); padding: 30px; margin-bottom: 20px; border-radius: 12px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #00f2fe; margin-bottom: 10px;">Hardware Accessibility Benchmark</h3>
                    <p style="color: #9ca3af; font-size: 0.95rem; max-width: 600px; margin: 0 auto;">
                        Run the simulation below to see how M-PULSE keeps research democratized by enforcing a strict operational memory ceiling.
                    </p>
                </div>

                <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; max-width: 600px; margin: 0 auto; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.85rem; color: #9ca3af;">
                        <span>System VRAM Utilization</span>
                        <span id="vram-text">0.0 GB / 8.0 GB (Idle)</span>
                    </div>
                    
                    <div style="width: 100%; height: 24px; background: rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; margin-bottom: 20px;">
                        <div id="vram-fill" style="width: 0%; height: 100%; background: #6b7280;"></div>
                    </div>
                    
                    <div id="system-status" style="text-align: center; height: 30px; font-weight: bold; color: #6b7280; margin-bottom: 15px;">
                        Ready for benchmark...
                    </div>

                    <div style="display: flex; justify-content: center; gap: 15px;">
                        <button class="btn-game" onclick="runStandardLLM()">Run Standard LLM</button>
                        <button class="btn-game" onclick="runMPulse()" style="border-color: #00f2fe; color: #00f2fe;">Run M-PULSE</button>
                        <button class="btn-game" onclick="resetSim()" style="background: transparent; border: none; font-size: 0.8rem; text-decoration: underline;">Reset</button>
                    </div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 35px;">
                <p style="color: #6b7280; font-size: 0.9rem;">
                    Full M-PULSE source code, models, and research parameters are open source:
                    <a href="https://github.com/avacado-a/M-PULSE" target="_blank" style="color: #00f2fe; text-decoration: underline; margin-left: 5px;">GitHub Repository</a>
                </p>
            </div>
        </div>

        <script>
            function runStandardLLM() {
                const fill = document.getElementById('vram-fill');
                const text = document.getElementById('vram-text');
                const status = document.getElementById('system-status');
                
                fill.style.width = '100%';
                fill.style.backgroundColor = '#f35588'; // Red/Pink
                text.innerText = '80.0 GB / 8.0 GB (Critical)';
                
                status.style.color = '#f35588';
                status.innerText = '💥 SYSTEM CRASH: Out of Memory! GPU requires A100 cluster.';
            }

            function runMPulse() {
                const fill = document.getElementById('vram-fill');
                const text = document.getElementById('vram-text');
                const status = document.getElementById('system-status');
                
                fill.style.width = '70%'; // Under 6GB limit
                fill.style.backgroundColor = '#00f2fe'; // Cyan
                text.innerText = '5.8 GB / 8.0 GB (Stable)';
                
                status.style.color = '#00f2fe';
                status.innerText = '🚀 SUCCESS: Model training locally. Zero cloud overhead.';
            }

            function resetSim() {
                const fill = document.getElementById('vram-fill');
                const text = document.getElementById('vram-text');
                const status = document.getElementById('system-status');
                
                fill.style.width = '0%';
                fill.style.backgroundColor = '#6b7280';
                text.innerText = '0.0 GB / 8.0 GB (Idle)';
                
                status.style.color = '#6b7280';
                status.innerText = 'Ready for benchmark...';
            }
        </script>
    """
    st.html(html_content)

def render_feedback_page():
    st.html("""
        <div class="dashboard-header">
            <div class="dashboard-title">Feedback Hub</div>
            <div class="dashboard-subtitle">Help us improve the M-PULSE project by leaving your feedback & criticism</div>
        </div>
    """)
    
    col_form, col_reviews = st.columns([1, 1], gap="large")
    
    with col_form:
        st.html('<div class="glass-container" style="padding: 24px;">')
        with st.form("feedback_form", clear_on_submit=True):
            st.markdown("### Share your feedback")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name (Optional)")
            with col2:
                role = st.selectbox("Your Role", ["Student", "High Schooler", "Academic/Researcher", "Developer", "General User", "Other"])
            rating = st.slider("Rating (1 = Poor, 5 = Excellent)", 1, 5, 5)
            comments = st.text_area("Criticism & Suggestions", placeholder="Write your thoughts here...")
            submitted = st.form_submit_button("Submit Feedback")
            if submitted:
                if not comments.strip():
                    st.error("Please enter some comments/suggestions.")
                else:
                    try:
                        from BlueShift.backend import database
                        database.insert_feedback(name, role, rating, comments)
                        fb_file = os.path.join(DIR_PATH, "feedback_submissions.json")
                        fb_list = []
                        if os.path.exists(fb_file):
                            try:
                                with open(fb_file, "r") as f:
                                    fb_list = json.load(f)
                            except Exception:
                                pass
                        fb_list.append({
                            "name": name,
                            "role": role,
                            "rating": rating,
                            "comments": comments,
                            "timestamp": datetime.now().isoformat()
                        })
                        with open(fb_file, "w") as f:
                            json.dump(fb_list, f, indent=4)
                        st.success("Thank you! Your feedback has been recorded successfully.")
                    except Exception as e:
                        st.error(f"Error saving feedback: {e}")
        st.html('</div>')
            
    with col_reviews:
        st.html('<div class="glass-container" style="padding: 24px; min-height: 480px;">')
        st.markdown("### Recent Submissions")
        fb_file = os.path.join(DIR_PATH, "feedback_submissions.json")
        if os.path.exists(fb_file):
            try:
                with open(fb_file, "r") as f:
                    fb_list = json.load(f)
                if fb_list:
                    for item in reversed(fb_list[-5:]):
                        stars = "★" * item["rating"] + "☆" * (5 - item["rating"])
                        st.html(f"""
                            <div class="news-item" style="margin-bottom: 12px; display: block; height: auto; padding: 15px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                    <strong>{item["name"] or "Anonymous"}</strong>
                                    <span style="color: #6b7280; font-size: 0.85rem;">{item["role"]}</span>
                                </div>
                                <div style="color: #00f2fe; margin-bottom: 8px;">{stars}</div>
                                <div style="color: #e5e7eb; font-style: italic;">"{item["comments"]}"</div>
                            </div>
                        """)
                else:
                    st.info("No feedback submissions yet. Be the first to share your thoughts!")
            except Exception:
                pass
        else:
            st.info("No feedback submissions yet. Be the first to share your thoughts!")
        st.html('</div>')

# Check which page the user is visiting
current_page = st.query_params.get("page", "dashboard")

# Render header navbar
active_dash = "active" if current_page == "dashboard" else ""
active_paper = "active" if current_page == "paper" else ""
active_feedback = "active" if current_page == "feedback" else ""

st.html(f"""
    <div class="navbar">
        <div class="navbar-brand">🌊 BlueShift</div>
        <div class="navbar-links">
            <a href="?page=dashboard" target="_self" class="nav-item {active_dash}">Dashboard</a>
            <a href="?page=paper" target="_self" class="nav-item {active_paper}">Research Paper</a>
            <a href="?page=feedback" target="_self" class="nav-item {active_feedback}">Feedback Hub</a>
        </div>
    </div>
""")

if current_page == "dashboard":
    st.html("""
        <div class="dashboard-header">
            <div class="dashboard-title">BlueShift</div>
            <div class="dashboard-subtitle">Predicting Media Trends Through Dual-Stream NLP Analysis</div>
        </div>
    """)

if current_page == "paper":
    render_research_page()
    st.html("""
        <div class="footer">
            BlueShift Dashboard &copy; 2026. Made with ❤️ for Sidh Parikh's M-PULSE research. <br>
            We value your input! Help us improve by visiting the <a class="feedback-link" href="?page=feedback" target="_self">Feedback Hub</a>.
        </div>
    """)
    st.stop()

if current_page == "feedback":
    render_feedback_page()
    st.html("""
        <div class="footer">
            BlueShift Dashboard &copy; 2026. Made with ❤️ for Sidh Parikh's M-PULSE research.
        </div>
    """)
    st.stop()

# Helper function to check if background process is active
def check_update_status():
    if os.path.exists(LOCK_PATH):
        mtime = os.path.getmtime(LOCK_PATH)
        # If lock file is less than 1 hour old, assume active
        if time.time() - mtime < 3600:
            return True
        else:
            try:
                os.remove(LOCK_PATH)
            except Exception:
                pass
    return False

is_updating = check_update_status()

# Load Cache Data
data = None
cache_exists = os.path.exists(CACHE_PATH)
if cache_exists:
    try:
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Error loading cache: {e}")

# Helper function to fetch news stories for a topic
def fetch_news_stories(topic_name):
    import sqlite3
    db_path = os.path.join(DIR_PATH, "backend", "blueshift.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, link, published, source FROM macro_data WHERE topic=? ORDER BY published DESC LIMIT 5",
            (topic_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"title": r[0], "link": r[1], "published": r[2], "source": r[3]} for r in rows]
    except Exception as e:
        return []

# Helper function to generate elaboration text
def generate_elaboration(topic_name, topic_data, news_stories):
    # Retrieve pre-generated elaboration from cache if it exists to avoid card click delay
    cached_elaboration = topic_data.get('elaboration')
    if cached_elaboration:
        return cached_elaboration

    classification = topic_data.get('classification', 'Unknown')
    score = round(topic_data.get('trend_score', topic_data.get('m_pulse_score', 0)), 1)
    lag = topic_data.get('cognitive_lag', 0)
    
    # Analyze alignment
    if lag > 0:
        lag_desc = f"social media chatter (Micro-stream) leading news coverage by {lag} days"
    elif lag < 0:
        lag_desc = f"traditional news outlets (Macro-stream) leading social media reaction by {abs(lag)} days"
    else:
        lag_desc = "real-time alignment between social chatter and news coverage"
        
    # Build explanation based on classification
    if classification == "Verified Trend":
        desc = (
            f"**{topic_name}** represents a verified, robust trend with a high M-PULSE score of **{score}/100**. "
            f"There is a {lag_desc}. Our Dual-Stream forecasting model shows high alignment, indicating "
            f"this topic has deep, persistent societal traction that is actively discussed across both news networks and social media platforms."
        )
    elif classification == "Emerging Trend":
        desc = (
            f"**{topic_name}** is an emerging trend to watch, with an M-PULSE score of **{score}/100**. "
            f"We are observing a {lag_desc}. This suggests that discussion is rapidly scaling up and starting "
            f"to bridge the gap between social media platforms and mainstream journalistic outlets."
        )
    elif classification == "Passing Fad":
        desc = (
            f"**{topic_name}** is classified as a passing fad (M-PULSE score: **{score}/100**). "
            f"Despite active chatter on social media, there is low correlation with institutional news coverage. "
            f"Our forecasting models show that this surge is likely an isolated echo chamber with low outrage persistency."
        )
    else:
        desc = (
            f"**{topic_name}** is currently under monitoring with an M-PULSE score of **{score}/100**. "
            f"There is currently a {lag_desc} observed across the ingestion networks."
        )
        
    # Append context from news headlines if available
    if news_stories:
        first_title = news_stories[0]['title']
        source = news_stories[0].get('source', 'News')
        desc += f" Context is driven by major recent events, including: *\"{first_title}\"* ({source})."
        
    return desc

# Header Control bar (Operations & Last Updated indicator moved to the top)
if is_updating:
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        st.html('<div class="status-badge updating" style="margin-top:5px; padding:8px; border-radius:8px; background:rgba(0, 242, 254, 0.1); border:1px solid rgba(0, 242, 254, 0.3); text-align:center; color:#00f2fe; font-weight:600;">⚡ Model Training Active</div>')
        if st.button("🔄 Check Status"):
            st.rerun()
    with col_info:
        st.info("The system is currently running background model training. Click 'Check Status' in a moment to reload.")
else:
    col_info = st.container()
    with col_info:
        if data:
            ts_val = data.get('timestamp', 0)
            if isinstance(ts_val, str):
                try:
                    dt_ts = datetime.fromisoformat(ts_val)
                    ts_float = dt_ts.timestamp()
                    ts_str = dt_ts.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts_float = time.time()
                    ts_str = ts_val
            else:
                ts_float = ts_val
                ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts_float))
                
            st.info(f"📅 Last Updated: {ts_str} (Data updates automatically every night at midnight)")
        else:
            st.info("📅 Last Updated: Never cached (Data updates automatically every night at midnight)")

# Main dashboard body
if is_updating:
    st.html("""
        <div class="glass-container" style="text-align: center; padding: 50px 30px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20px; border: 1px solid rgba(0, 242, 254, 0.3); box-shadow: 0 0 25px rgba(0, 242, 254, 0.08);">
            <style>
                @keyframes spin-glow {
                    0% { transform: rotate(0deg); border-top-color: #00f2fe; border-right-color: rgba(0, 242, 254, 0.2); }
                    50% { transform: rotate(180deg); border-top-color: #f35588; border-right-color: rgba(243, 85, 136, 0.2); }
                    100% { transform: rotate(360deg); border-top-color: #00f2fe; border-right-color: rgba(0, 242, 254, 0.2); }
                }
                @keyframes pulse-text {
                    0%, 100% { opacity: 0.6; }
                    50% { opacity: 1; }
                }
                .modern-spinner {
                    width: 70px;
                    height: 70px;
                    border: 4px solid rgba(255, 255, 255, 0.05);
                    border-radius: 50%;
                    animation: spin-glow 2s linear infinite;
                    position: relative;
                    box-shadow: 0 0 20px rgba(0, 242, 254, 0.1);
                    margin: 0 auto;
                }
                .modern-spinner::after {
                    content: '';
                    position: absolute;
                    top: 4px; left: 4px; right: 4px; bottom: 4px;
                    border: 2px solid transparent;
                    border-radius: 50%;
                    border-bottom-color: #4facfe;
                    opacity: 0.6;
                    animation: spin-glow 1.2s linear infinite reverse;
                }
                .pulsing-text {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #ffffff;
                    letter-spacing: -0.01em;
                    margin-top: 15px;
                    animation: pulse-text 2s infinite ease-in-out;
                }
            </style>
            <div class="modern-spinner"></div>
            <div class="pulsing-text">🔮 M-PULSE Pipeline Active</div>
            <div style="max-width: 600px; color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin: 0 auto;">
                Our Dual-Stream forecasting engine is currently fetching headlines from <strong>GDELT</strong>, scraping social sentiment from <strong>Bluesky</strong>, aligning the semantic word embeddings, and training standard-compliant LSTM networks on the CPU.
            </div>
            <div style="color: #6b7280; font-size: 0.85rem; margin-top: 5px;">
                This process typically completes in 10 to 45 seconds depending on server latency. Please click <strong>"Check Status"</strong> in the top bar in a moment to reload.
            </div>
            <div style="margin-top: 10px;">
                <span class="badge" style="background: rgba(0, 242, 254, 0.12); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.25); padding: 8px 16px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; border-radius: 30px; display: inline-block;">TRAINING ACTIVE</span>
            </div>
        </div>
    """)

elif data is None:
    st.html("""
        <div class="glass-container" style="text-align: center; padding: 40px;">
            <h3>👋 Welcome to BlueShift</h3>
            <p>No cached research results were found. BlueShift requires an initial analysis queue run to inspect GDELT and Bluesky streams.</p>
            <p>The system will automatically run model training and build the cache every night at midnight.</p>
            <div style="margin-top: 20px;">
                <span class="badge" style="background: rgba(243, 85, 136, 0.15); color: #f35588; border: 1px solid #f35588; padding: 10px 20px;">STATUS: NO CACHE</span>
            </div>
        </div>
    """)

else:
    # We have cached data! Let's display the grid of cards.
    # Convert list of topics to dict mapping topic name -> topic dict
    if isinstance(data.get("topics"), list):
        topics = {t["topic"]: t for t in data["topics"]}
    else:
        topics = data.get("topics", {})
    
    if not topics:
        st.info("No active topics found in the cache. Please refresh the data queue to scan for trends.")
    else:
        # Select topic based on query parameters
        query_params = st.query_params
        param_topic = query_params.get("topic", None)
        
        # Normalize and validate
        if param_topic and param_topic in topics:
            selected_topic = param_topic
        else:
            selected_topic = list(topics.keys())[0] if topics else None

        # Create side-by-side layout to utilize blank side space
        dash_col1, dash_col2 = st.columns([1, 2], gap="large")

        with dash_col1:
            st.markdown("### 📋 Active Topics")
            grid_html = '<div class="topic-grid" style="grid-template-columns: 1fr; gap: 15px; margin-top: 10px;">'
            for name, topic_data in topics.items():
                t_score = round(topic_data.get('trend_score', topic_data.get('m_pulse_score', 0)), 1)
                t_category = topic_data.get('category_classification', topic_data.get('category', 'General'))
                class_type = "trend" if topic_data.get('classification') in ["Verified Trend", "Emerging Trend"] else "fad"
                
                is_sel = "selected" if name == selected_topic else ""
                border_style = "border: 1px solid rgba(0, 242, 254, 0.6); box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);" if name == selected_topic else "border: 1px solid rgba(255,255,255,0.08);"
                if class_type == "fad" and name == selected_topic:
                    border_style = "border: 1px solid rgba(243, 85, 136, 0.6); box-shadow: 0 0 15px rgba(243, 85, 136, 0.2);"
                
                card_html = (
                    f'<a href="?topic={urllib.parse.quote(name)}" target="_self" class="topic-card {class_type} {is_sel}" style="{border_style} width: 100%; height: 160px; margin-bottom: 12px; display: flex; flex-direction: column; justify-content: space-between; padding: 18px; box-sizing: border-box;">'
                    f'<div>'
                    f'<div class="card-title" style="font-size: 1.15rem; margin-bottom: 2px;">{name}</div>'
                    f'<div class="category-tag">{t_category}</div>'
                    f'</div>'
                    f'<div class="score-display" style="margin: 4px 0;">'
                    f'<span class="score-val" style="font-size: 1.8rem;">{t_score}</span>'
                    f'<span class="score-label" style="font-size: 0.65rem; margin-left: 8px;">M-PULSE</span>'
                    f'</div>'
                    f'<div class="badge" style="padding: 4px 10px; font-size: 0.7rem; align-self: flex-start;">{topic_data.get("classification", "Unknown")}</div>'
                    f'</a>'
                )
                grid_html += card_html
            grid_html += '</div>'
            st.html(grid_html)

        with dash_col2:
            if selected_topic and selected_topic in topics:
                name = selected_topic
                topic_data = topics[name]
                t_score = round(topic_data.get('trend_score', topic_data.get('m_pulse_score', 0)), 1)
                t_category = topic_data.get('category_classification', topic_data.get('category', 'General'))
                class_type = "trend" if topic_data.get('classification') in ["Verified Trend", "Emerging Trend"] else "fad"
                
                news_stories = fetch_news_stories(name)
                news_links_html = ""
                for story in news_stories:
                    source_str = f"({story['source']})" if story.get('source') else ""
                    news_links_html += f'<div class="news-item"><a href="{story["link"]}" target="_blank" class="news-link">📰 {story["title"]}</a><span class="news-meta">{source_str}</span></div>'
                
                if not news_links_html:
                    news_links_html = '<div class="news-item" style="color: #6b7280;">No recent news articles found in queue database.</div>'
                
                elaboration = generate_elaboration(name, topic_data, news_stories)
                
                selected_card_html = (
                    f'<div class="topic-card {class_type} selected expanded" style="width: 100%; max-width: 100%; box-sizing: border-box; margin-bottom: 25px;">'
                    f'<div class="expanded-left">'
                    f'<div>'
                    f'<div class="card-title">{name}</div>'
                    f'<div class="category-tag">{t_category}</div>'
                    f'</div>'
                    f'<div class="score-display">'
                    f'<div class="score-val">{t_score}</div>'
                    f'<div class="score-label">M-PULSE Score</div>'
                    f'</div>'
                    f'<div class="badge">{topic_data.get("classification", "Unknown")}</div>'
                    f'</div>'
                    f'<div class="card-divider"></div>'
                    f'<div class="expanded-right">'
                    f'<div class="expanded-section-title">Context & Elaboration</div>'
                    f'<div class="elaboration-text">{elaboration}</div>'
                    f'<div class="expanded-section-title" style="margin-top: 10px;">Latest News Stories</div>'
                    f'<div class="news-list">{news_links_html}</div>'
                    f'</div>'
                    f'</div>'
                )
                st.html(selected_card_html)
                
                st.markdown(f"### 📊 Detailed Forecasts for **{name}**")
                
                # Quick metrics row
                col1, col2 = st.columns(2)
                with col1:
                    t_class = topic_data.get('classification', 'Unknown')
                    st.metric(
                        label="M-PULSE Score", 
                        value=f"{t_score}/100", 
                        delta=t_class,
                        delta_color="normal" if t_class in ["Verified Trend", "Emerging Trend"] else "inverse"
                    )
                    
                with col2:
                    dual_val = topic_data.get('metrics', {}).get('Dual-Stream', {})
                    dual_mse = dual_val.get('mse') if isinstance(dual_val, dict) else dual_val
                    if dual_mse is None:
                        dual_mse = topic_data.get('metrics', {}).get('mse')
                    
                    mse_text = f"{dual_mse:.5f}" if (dual_mse is not None and dual_mse != float('inf')) else "N/A"
                    st.metric(label="Dual-Stream Model MSE", value=mse_text)
                    
                # Extract historical data
                t_data = topics[selected_topic]
                if 'historical_data' in t_data:
                    dates = [x['date'] for x in t_data['historical_data']]
                    macro_volumes = [x.get('macro_volume', 0) for x in t_data['historical_data']]
                    micro_volumes = [x.get('volume', 0) for x in t_data['historical_data']]
                    sentiment_scores = [x.get('sentiment', 0.0) for x in t_data['historical_data']]
                else:
                    dates = t_data.get('dates', [])
                    macro_volumes = t_data.get('macro_volumes', [])
                    micro_volumes = t_data.get('micro_volumes', [])
                    sentiment_scores = t_data.get('sentiment_scores', [])

                # Render detailed time-series charts
                tab1, tab2 = st.tabs(["📈 Volume Comparison (Macro vs Micro)", "🤖 Forecast Validation (Actual vs Predicted)"])
                
                with tab1:
                    chart_data = pd.DataFrame({
                        'Date': pd.to_datetime(dates),
                        'Macro Volume (News)': macro_volumes,
                        'Micro Volume (Social)': micro_volumes
                    })
                    
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %d', labelAngle=-45))
                    )
                    
                    line_macro = base.mark_line(color='#00f2fe', strokeWidth=2.5).encode(
                        y=alt.Y('Macro Volume (News):Q', title='Macro Volume (News)', axis=alt.Axis(titleColor='#00f2fe'))
                    )
                    
                    line_micro = base.mark_line(color='#f35588', strokeWidth=2.5).encode(
                        y=alt.Y('Micro Volume (Social):Q', title='Micro Volume (Social Media)', axis=alt.Axis(titleColor='#f35588'))
                    )
                    
                    lag_chart = alt.layer(line_macro, line_micro).resolve_scale(
                        y='independent'
                    ).properties(
                        height=400,
                        title=f"Macro (News) vs Micro (Social Media) Volumes for '{selected_topic}'"
                    )
                    
                    st.altair_chart(lag_chart, use_container_width=True)
                    
                with tab2:
                    predictions = t_data.get('predictions', [])
                    targets = t_data.get('targets', t_data.get('aligned_volumes', []))
                    
                    if predictions and len(predictions) > 0:
                        aligned_dates = t_data.get('aligned_dates', dates[-len(predictions):])
                        
                        pred_data = pd.DataFrame({
                            'Date': pd.to_datetime(aligned_dates),
                            'Actual Normalized Volume': targets,
                            'M-PULSE Prediction': predictions
                        })
                        
                        melted_pred = pred_data.melt('Date', var_name='Metric', value_name='Volume')
                        
                        pred_chart = alt.Chart(melted_pred).mark_line(strokeWidth=2.5).encode(
                            x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %d', labelAngle=-45)),
                            y=alt.Y('Volume:Q', title='Normalized Volume'),
                            color=alt.Color('Metric:N', scale=alt.Scale(domain=['Actual Normalized Volume', 'M-PULSE Prediction'], range=['#f35588', '#00f2fe']))
                        ).properties(
                            height=400,
                            title=f"Dual-Stream Model Forecasting Performance for '{selected_topic}'"
                        )
                        
                        st.altair_chart(pred_chart, use_container_width=True)
                        
                        st.markdown("##### Stream Ablation Study Results (Test Set Mean Squared Error)")
                        
                        def get_mse(metric_entry):
                            if isinstance(metric_entry, dict):
                                val = metric_entry.get('mse', 'N/A')
                            else:
                                val = metric_entry
                            return f"{val:.5f}" if isinstance(val, (int, float)) and val != float('inf') else "N/A"
                        
                        metrics_df = pd.DataFrame({
                            'Architecture Stream': ['Macro-Only (News)', 'Micro-Only (Social)', 'Dual-Stream (Fused)'],
                            'MSE (Lower is Better)': [
                                get_mse(t_data.get('metrics', {}).get('Macro-Only')),
                                get_mse(t_data.get('metrics', {}).get('Micro-Only')),
                                get_mse(t_data.get('metrics', {}).get('Dual-Stream'))
                            ]
                        })
                        st.table(metrics_df)
                    else:
                        st.info("No sequence forecasts available for this topic (likely due to limited dataset range).")

# Footer and feedback link
st.html("""
    <div class="footer">
        BlueShift Dashboard &copy; 2026. Made with ❤️ for Sidh Parikh's M-PULSE research. <br>
        We value your input! Help us improve by visiting the <a class="feedback-link" href="?page=feedback" target="_self">Feedback Hub</a>.
    </div>
""")