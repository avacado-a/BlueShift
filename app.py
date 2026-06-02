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
    html_content = r"""
        <style>
            /* Layout & General Classes */
            .paper-layout {
                color: #e5e7eb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            .badge {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 12px;
            }
            .glass-panel {
                background: rgba(255, 255, 255, 0.01);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
            }
            .interactive-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                align-items: center;
            }
            @media (max-width: 768px) {
                .interactive-grid {
                    grid-template-columns: 1fr;
                }
            }

            /* Custom Interactive Controls */
            .sim-btn {
                background: #00f2fe;
                color: #0b0f19;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 700;
                font-size: 0.9rem;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0, 242, 254, 0.2);
                transition: all 0.2s ease;
            }
            .sim-btn:hover {
                background: #00e0eb;
                transform: translateY(-1px);
                box-shadow: 0 6px 20px rgba(0, 242, 254, 0.3);
            }
            .sim-btn-secondary {
                background: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .sim-btn-secondary:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            .sim-input {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-size: 0.9rem;
                outline: none;
                width: 100%;
                box-sizing: border-box;
            }
            .sim-select {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-size: 0.9rem;
                outline: none;
                cursor: pointer;
            }
            .slider-control {
                width: 100%;
                margin: 10px 0;
                accent-color: #00f2fe;
            }

            /* Consoles and SVGs */
            .console-box {
                background: #05070c;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
                height: 180px;
                overflow: hidden;
                padding: 15px;
                display: flex;
                flex-direction: column-reverse;
                box-sizing: border-box;
            }
            .svg-container {
                background: #05070c;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
                width: 100%;
                height: 250px;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }

            @keyframes slideIn {
                from { opacity: 0; transform: translateY(-15px); }
                to { opacity: 1; transform: translateY(0); }
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
            
            <!-- Header Section -->
            <div class="paper-header" style="text-align: center; margin-bottom: 45px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 35px;">
                <span class="badge" style="background: rgba(0, 242, 254, 0.12); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.25);">Interactive Technical Showcase</span>
                <h1 style="font-size: 2.6rem; font-weight: 800; color: #ffffff; line-height: 1.3; margin-bottom: 15px; letter-spacing: -0.02em;">
                    The M-PULSE Forecasting Architecture
                </h1>
                <div class="paper-author" style="font-size: 1.25rem; font-weight: 600; color: #00f2fe; margin-bottom: 5px;">Sidh Parikh</div>
                <div style="font-size: 0.95rem; color: #9ca3af; line-height: 1.5; margin-bottom: 15px;">
                    Glenelg High School &bull; Gifted and Talented Independent Research &bull; Ms. Leila Chawkat
                </div>
                <div>
                    <a href="https://github.com/avacado-a/M-PULSE" target="_blank" class="sim-btn-secondary" style="font-size: 0.85rem; padding: 6px 14px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                        <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" style="display:inline-block; vertical-align:middle;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
                        Explore the GitHub Repository
                    </a>
                </div>
            </div>

            <!-- Pipeline Step 1 -->
            <div class="glass-panel">
                <div class="interactive-grid">
                    <div>
                        <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe;">STEP 01</span>
                        <h2 style="color: #ffffff; margin-top: 0; margin-bottom: 12px;">Multi-Resolution Ingestion</h2>
                        <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px;">
                            M-PULSE pulls timeline snapshots from two distinct resolutions: institutional news anchors (<strong>Macro-stream</strong> via GDELT API) and real-time public chatter (<strong>Micro-stream</strong> via Bluesky/AT Protocol). Click the simulator controls to load data chunks.
                        </p>
                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <button class="sim-btn" onclick="ingestItem('macro')">Pull News (GDELT)</button>
                            <button class="sim-btn-secondary" onclick="ingestItem('micro')" style="border-color: #f35588; color: #f35588;">Pull Post (Bluesky)</button>
                        </div>
                        <div style="font-size: 0.9rem; color: #9ca3af;">
                            Total Ingested -- GDELT News: <code id="macro-count" style="color: #00f2fe;">0</code> | Social Posts: <code id="micro-count" style="color: #f35588;">0</code>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.8rem; color: #6b7280; text-transform: uppercase;">Temporal Data Stream Ingest</span>
                            <span id="db-icon" style="transition: all 0.15s ease; font-size: 1.4rem;">💾</span>
                        </div>
                        <div class="console-box" id="ingest-list">
                            <div style="color: #4b5563; font-size: 0.8rem; text-align: center; margin-bottom: 60px;">Database empty. Click buttons to scrape streams...</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pipeline Step 2 -->
            <div class="glass-panel">
                <div class="interactive-grid">
                    <div>
                        <span class="badge" style="background: rgba(163, 230, 53, 0.12); color: #a3e635;">STEP 02</span>
                        <h2 style="color: #ffffff; margin-top: 0; margin-bottom: 12px;">DBSCAN Bias Mitigation</h2>
                        <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px;">
                            Raw text is encoded using a <strong>SentenceTransformer</strong> into high-dimensional space. We apply <strong>DBSCAN Clustering</strong> to identify core topic densities. Isolated points that do not fall into dense clusters represent noise or extreme outlier political bias, which are dynamically deleted.
                        </p>
                        <div>
                            <label style="font-size: 0.85rem; color: #9ca3af;">Adjust Cluster Radius (Epsilon):</label>
                            <input type="range" id="dbscan-eps" class="slider-control" min="20" max="120" value="65" oninput="updateDBSCAN()">
                        </div>
                        <div id="dbscan-status" style="font-size: 0.9rem; color: #a3e635; font-family: monospace; margin-top: 10px;">
                            Epsilon: 65.0 px | Outliers Removed: 4 / 12
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.8rem; color: #6b7280; text-transform: uppercase;">DBSCAN Outlier Removal Grid</span>
                            <span style="font-size: 0.75rem; color: #9ca3af;"><span style="color: #00f2fe;">●</span> Tech <span style="color: #a3e635;">●</span> Space <span style="color: #6b7280;">●</span> Outlier</span>
                        </div>
                        <div class="svg-container">
                            <svg id="dbscan-svg" width="350" height="300" style="background:transparent;"></svg>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pipeline Step 3 -->
            <div class="glass-panel">
                <div class="interactive-grid">
                    <div>
                        <span class="badge" style="background: rgba(243, 85, 136, 0.12); color: #f35588;">STEP 03</span>
                        <h2 style="color: #ffffff; margin-top: 0; margin-bottom: 12px;">The Local Vector Space</h2>
                        <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin-bottom: 15px;">
                            A custom Word2Vec model maps vocabulary into a 2D coordinate system. Words that share contexts align closer together. Project a new word into the vector space below to see how it groups with existing topics.
                        </p>
                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <input type="text" id="vector-word-input" class="sim-input" placeholder="Type a word (e.g. processor, orbit)">
                            <select id="vector-category-select" class="sim-select">
                                <option value="tech">Tech Cluster</option>
                                <option value="space">Space Cluster</option>
                                <option value="health">Health Cluster</option>
                            </select>
                        </div>
                        <button class="sim-btn" style="background: #f35588; color: white; box-shadow: 0 4px 15px rgba(243, 85, 136, 0.2); width: 100%; margin-bottom: 15px;" onclick="addWordToVector()">Project into Vector Database</button>
                        
                        <div id="vector-report" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; font-size: 0.8rem; line-height: 1.4; display: none; font-family: monospace;"></div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.8rem; color: #6b7280; text-transform: uppercase;">2D Semantic Vector Grid</span>
                            <span style="font-size: 0.8rem; color: #9ca3af; font-family: monospace;">cos(θ) Calculation</span>
                        </div>
                        <div class="svg-container">
                            <svg id="vector-svg" width="300" height="300" style="background:transparent;"></svg>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pipeline Step 4 -->
            <div class="glass-panel">
                <div class="interactive-grid">
                    <div>
                        <span class="badge" style="background: rgba(0, 242, 254, 0.08); color: #00f2fe;">STEP 04</span>
                        <h2 style="color: #ffffff; margin-top: 0; margin-bottom: 12px;">LSTM Dual-Stream Prediction</h2>
                        <p style="color: #9ca3af; font-size: 0.95rem; line-height: 1.6; margin-bottom: 15px;">
                            A recurrent <strong>PyTorch LSTM</strong> network fuses the temporal profiles of news and social media streams. Adjust the weights of each stream and the time alignment offset to see how it shapes the forecasted target trend line.
                        </p>
                        <div style="margin-bottom: 10px;">
                            <div style="display:flex; justify-content:space-between; font-size: 0.8rem; color: #9ca3af;">
                                <span>Macro News Weight (Anchoring):</span>
                                <span id="val-wmacro">50%</span>
                            </div>
                            <input type="range" id="lstm-wmacro" class="slider-control" min="0" max="100" value="50" oninput="document.getElementById('val-wmacro').innerText=this.value+'%'; updateLSTMChart();">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <div style="display:flex; justify-content:space-between; font-size: 0.8rem; color: #9ca3af;">
                                <span>Micro Social Weight (Reaction):</span>
                                <span id="val-wmicro">50%</span>
                            </div>
                            <input type="range" id="lstm-wmicro" class="slider-control" min="0" max="100" value="50" oninput="document.getElementById('val-wmicro').innerText=this.value+'%'; updateLSTMChart();">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display:flex; justify-content:space-between; font-size: 0.8rem; color: #9ca3af;">
                                <span>Micro Cognitive Lag Offset:</span>
                                <span id="val-lag">0 days</span>
                            </div>
                            <input type="range" id="lstm-lag" class="slider-control" min="-5" max="5" value="0" oninput="document.getElementById('val-lag').innerText=this.value+' days'; updateLSTMChart();">
                        </div>
                        <div id="lstm-status" style="font-size: 0.85rem; color: #00f2fe; font-family: monospace;"></div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.8rem; color: #6b7280; text-transform: uppercase;">Dual-Stream LSTM Timeline Output</span>
                            <span style="font-size: 0.75rem; color: #9ca3af;"><span style="color: rgba(0, 242, 254, 0.5); font-weight: bold;">--</span> GDELT <span style="color: rgba(243, 85, 136, 0.5); font-weight: bold;">--</span> Social <span style="color: #00f2fe; font-weight: bold;">─</span> M-PULSE</span>
                        </div>
                        <div class="svg-container">
                            <svg id="lstm-svg" width="350" height="150" style="background:transparent;"></svg>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Hardware Accessibility Game / Benchmark -->
            <div class="glass-panel" style="background: rgba(0, 242, 254, 0.02); border: 1px solid rgba(0, 242, 254, 0.2); padding: 30px; border-radius: 12px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #00f2fe; margin-bottom: 10px;">Hardware Accessibility Benchmark</h3>
                    <p style="color: #9ca3af; font-size: 0.95rem; max-width: 600px; margin: 0 auto; line-height: 1.6;">
                        M-PULSE keeps research democratized by enforcing a strict memory ceiling, running local simulations under a strict VRAM cap.
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

            <!-- Deep Dive Footer Link -->
            <div style="text-align: center; margin-top: 45px; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 35px;">
                <p style="color: #6b7280; font-size: 0.95rem; margin-bottom: 20px;">
                    Want to explore the codebase, research parameters, and access the full paper PDF?
                </p>
                <a href="https://github.com/avacado-a/M-PULSE" target="_blank" class="sim-btn" style="text-decoration: none; padding: 12px 28px; font-size: 1rem;">
                    Explore M-PULSE on GitHub
                </a>
            </div>
        </div>

        <script>
            // STEP 01 - Ingestion Simulator
            const gdeltHeadlines = [
                "NVIDIA Blackwell processors begin global shipments",
                "SpaceX launches 23 Starlink satellites into orbit",
                "WHO reports new Ebola outbreak containment success",
                "Global semiconductor indices hit new records",
                "Liverpool FC appoints Arne Slot as head coach",
                "China maritime border negotiations conclude in Manila"
            ];
            const bskyChatter = [
                "Blackwell B200 specs are absolutely insane!",
                "Starlink train visible in the sky tonight!",
                "Hoping the WHO limits the outbreak spread.",
                "Semiconductor stocks are carrying my portfolio.",
                "Slot has a huge task ahead post-Klopp.",
                "Border security talks in SCS heating up."
            ];

            let macroCount = 0;
            let microCount = 0;

            function ingestItem(stream) {
                const list = document.getElementById("ingest-list");
                
                // Clear initial placeholder if exists
                if (list.querySelector("div[style*='color: #4b5563']")) {
                    list.innerHTML = "";
                }
                
                const item = document.createElement("div");
                item.style.padding = "10px";
                item.style.marginBottom = "8px";
                item.style.borderRadius = "6px";
                item.style.fontSize = "0.85rem";
                item.style.border = "1px solid rgba(255,255,255,0.05)";
                item.style.fontFamily = "monospace";
                item.style.animation = "slideIn 0.3s ease-out";
                
                if (stream === 'macro') {
                    const text = gdeltHeadlines[Math.floor(Math.random() * gdeltHeadlines.length)];
                    item.style.background = "rgba(0, 242, 254, 0.05)";
                    item.style.borderColor = "rgba(0, 242, 254, 0.2)";
                    item.innerHTML = `<span style="color: #00f2fe; font-weight: bold;">[MACRO GDELT]</span> ${text}`;
                    macroCount++;
                    document.getElementById("macro-count").innerText = macroCount;
                } else {
                    const text = bskyChatter[Math.floor(Math.random() * bskyChatter.length)];
                    item.style.background = "rgba(243, 85, 136, 0.05)";
                    item.style.borderColor = "rgba(243, 85, 136, 0.2)";
                    item.innerHTML = `<span style="color: #f35588; font-weight: bold;">[MICRO BSKY]</span> ${text}`;
                    microCount++;
                    document.getElementById("micro-count").innerText = microCount;
                }
                
                list.insertBefore(item, list.firstChild);
                if (list.children.length > 5) {
                    list.removeChild(list.lastChild);
                }
                
                // Pulse the database icon
                const dbIcon = document.getElementById("db-icon");
                dbIcon.style.transform = "scale(1.2)";
                dbIcon.style.filter = "drop-shadow(0 0 10px #00f2fe)";
                setTimeout(() => {
                    dbIcon.style.transform = "scale(1)";
                    dbIcon.style.filter = "none";
                }, 150);
            }

            // STEP 02 - DBSCAN Simulator
            const dbscanPoints = [
                { x: 80, y: 80, name: "nvidia B200" },
                { x: 95, y: 90, name: "blackwell chip" },
                { x: 70, y: 95, name: "gpu hardware" },
                { x: 90, y: 75, name: "processor specs" },
                
                { x: 260, y: 160, name: "spacex starlink" },
                { x: 280, y: 150, name: "satellite orbit" },
                { x: 245, y: 180, name: "rocket booster" },
                { x: 290, y: 165, name: "falcon 9 launch" },
                
                { x: 60, y: 220, name: "spam outrage post" },
                { x: 270, y: 70, name: "random link bait" },
                { x: 150, y: 120, name: "irrelevant news" },
                { x: 200, y: 230, name: "unrelated chatter" }
            ];

            function updateDBSCAN() {
                const eps = parseFloat(document.getElementById("dbscan-eps").value);
                const minPts = 3;
                const svg = document.getElementById("dbscan-svg");
                svg.innerHTML = ""; // Clear
                
                // Draw grid lines
                for (let i = 50; i <= 300; i += 50) {
                    const lineH = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    lineH.setAttribute("x1", "0");
                    lineH.setAttribute("y1", i);
                    lineH.setAttribute("x2", "350");
                    lineH.setAttribute("y2", i);
                    lineH.setAttribute("stroke", "rgba(255,255,255,0.03)");
                    svg.appendChild(lineH);
                    
                    const lineV = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    lineV.setAttribute("x1", i);
                    lineV.setAttribute("y1", "0");
                    lineV.setAttribute("x2", i);
                    lineV.setAttribute("y2", "300");
                    lineV.setAttribute("stroke", "rgba(255,255,255,0.03)");
                    svg.appendChild(lineV);
                }

                // Compute neighbors
                const neighborCounts = dbscanPoints.map(p1 => {
                    let count = 0;
                    dbscanPoints.forEach(p2 => {
                        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
                        if (dist <= eps) count++;
                    });
                    return count;
                });

                dbscanPoints.forEach((p, idx) => {
                    const isCore = neighborCounts[idx] >= minPts;
                    let isNoise = true;
                    
                    dbscanPoints.forEach((p2, idx2) => {
                        if (neighborCounts[idx2] >= minPts) {
                            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                            if (dist <= eps) {
                                isNoise = false;
                            }
                        }
                    });

                    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    circle.setAttribute("cx", p.x);
                    circle.setAttribute("cy", p.y);
                    circle.setAttribute("r", "7");
                    
                    if (isNoise) {
                        circle.setAttribute("fill", "#4b5563");
                        circle.setAttribute("stroke", "rgba(255,255,255,0.1)");
                        circle.setAttribute("style", "opacity: 0.55; transition: all 0.3s;");
                    } else {
                        if (p.x < 150) {
                            circle.setAttribute("fill", "#00f2fe");
                            circle.setAttribute("stroke", "rgba(0, 242, 254, 0.4)");
                        } else {
                            circle.setAttribute("fill", "#a3e635");
                            circle.setAttribute("stroke", "rgba(163, 230, 53, 0.4)");
                        }
                        circle.setAttribute("style", "filter: drop-shadow(0 0 5px rgba(255,255,255,0.1)); transition: all 0.3s;");
                    }
                    
                    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
                    title.textContent = `${p.name} (${isNoise ? 'Noise / Outlier' : 'Core Cluster Point'})`;
                    circle.appendChild(title);
                    
                    g.appendChild(circle);
                    svg.appendChild(g);
                });

                const noiseCount = dbscanPoints.filter((p, idx) => {
                    let isNoise = true;
                    dbscanPoints.forEach((p2, idx2) => {
                        if (neighborCounts[idx2] >= minPts) {
                            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                            if (dist <= eps) isNoise = false;
                        }
                    });
                    return isNoise;
                }).length;
                
                document.getElementById("dbscan-status").innerHTML = `Epsilon Cluster Radius: <code>${eps.toFixed(1)}px</code> | Outliers Deleted: <strong style="color:#f35588;">${noiseCount}</strong> / ${dbscanPoints.length}`;
            }

            // STEP 03 - Vector space Database Simulator
            const vectorPoints = [
                { x: -0.6, y: 0.4, label: "nvidia", cat: "tech" },
                { x: -0.7, y: 0.3, label: "processor", cat: "tech" },
                { x: -0.5, y: 0.5, label: "chip", cat: "tech" },
                
                { x: 0.6, y: 0.5, label: "spacex", cat: "space" },
                { x: 0.7, y: 0.4, label: "starlink", cat: "space" },
                { x: 0.5, y: 0.6, label: "rocket", cat: "space" },
                
                { x: 0.0, y: -0.6, label: "ebola", cat: "health" },
                { x: 0.1, y: -0.7, label: "outbreak", cat: "health" },
                { x: -0.1, y: -0.5, label: "virus", cat: "health" }
            ];

            function drawVectorSpace() {
                const svg = document.getElementById("vector-svg");
                svg.innerHTML = "";
                
                // Draw grid lines
                for (let i = 50; i < 300; i += 50) {
                    const lineX = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    lineX.setAttribute("x1", "0"); lineX.setAttribute("y1", i);
                    lineX.setAttribute("x2", "300"); lineX.setAttribute("y2", i);
                    lineX.setAttribute("stroke", "rgba(255,255,255,0.02)");
                    svg.appendChild(lineX);

                    const lineY = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    lineY.setAttribute("x1", i); lineY.setAttribute("y1", "0");
                    lineY.setAttribute("x2", i); lineY.setAttribute("y2", "300");
                    lineY.setAttribute("stroke", "rgba(255,255,255,0.02)");
                    svg.appendChild(lineY);
                }

                // Draw central axes
                const axisX = document.createElementNS("http://www.w3.org/2000/svg", "line");
                axisX.setAttribute("x1", "0"); axisX.setAttribute("y1", "150");
                axisX.setAttribute("x2", "300"); axisX.setAttribute("y2", "150");
                axisX.setAttribute("stroke", "rgba(255,255,255,0.12)");
                svg.appendChild(axisX);
                
                const axisY = document.createElementNS("http://www.w3.org/2000/svg", "line");
                axisY.setAttribute("x1", "150"); axisY.setAttribute("y1", "0");
                axisY.setAttribute("x2", "150"); axisY.setAttribute("y2", "300");
                axisY.setAttribute("stroke", "rgba(255,255,255,0.12)");
                svg.appendChild(axisY);

                // Cluster areas (Shaded boundaries)
                const regTech = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                regTech.setAttribute("cx", "60"); regTech.setAttribute("cy", "90"); regTech.setAttribute("r", "45");
                regTech.setAttribute("fill", "rgba(0, 242, 254, 0.02)");
                regTech.setAttribute("stroke", "rgba(0, 242, 254, 0.08)");
                regTech.setAttribute("stroke-dasharray", "3");
                svg.appendChild(regTech);

                const regSpace = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                regSpace.setAttribute("cx", "240"); regSpace.setAttribute("cy", "90"); regSpace.setAttribute("r", "45");
                regSpace.setAttribute("fill", "rgba(163, 230, 53, 0.02)");
                regSpace.setAttribute("stroke", "rgba(163, 230, 53, 0.08)");
                regSpace.setAttribute("stroke-dasharray", "3");
                svg.appendChild(regSpace);

                const regHealth = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                regHealth.setAttribute("cx", "150"); regHealth.setAttribute("cy", "240"); regHealth.setAttribute("r", "45");
                regHealth.setAttribute("fill", "rgba(243, 85, 136, 0.02)");
                regHealth.setAttribute("stroke", "rgba(243, 85, 136, 0.08)");
                regHealth.setAttribute("stroke-dasharray", "3");
                svg.appendChild(regHealth);

                vectorPoints.forEach(p => {
                    const cx = 150 + p.x * 150;
                    const cy = 150 - p.y * 150; 
                    
                    let color = "#00f2fe";
                    if (p.cat === "space") color = "#a3e635";
                    if (p.cat === "health") color = "#f35588";

                    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                    
                    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    circle.setAttribute("cx", cx);
                    circle.setAttribute("cy", cy);
                    circle.setAttribute("r", "5");
                    circle.setAttribute("fill", color);
                    circle.setAttribute("style", "filter: drop-shadow(0 0 3px rgba(255,255,255,0.1));");
                    g.appendChild(circle);
                    
                    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                    text.setAttribute("x", cx + 8);
                    text.setAttribute("y", cy + 3);
                    text.setAttribute("fill", "#9ca3af");
                    text.setAttribute("font-size", "9px");
                    text.setAttribute("font-family", "monospace");
                    text.textContent = p.label;
                    g.appendChild(text);
                    
                    svg.appendChild(g);
                });
            }

            function addWordToVector() {
                const input = document.getElementById("vector-word-input");
                const catSelect = document.getElementById("vector-category-select");
                const word = input.value.trim().toLowerCase();
                
                if (!word) return;
                
                const cat = catSelect.value;
                
                let base = { x: 0, y: 0 };
                if (cat === "tech") base = { x: -0.6, y: 0.4 };
                else if (cat === "space") base = { x: 0.6, y: 0.5 };
                else if (cat === "health") base = { x: 0.0, y: -0.6 };
                
                const newPt = {
                    x: base.x + (Math.random() - 0.5) * 0.15,
                    y: base.y + (Math.random() - 0.5) * 0.15,
                    label: word,
                    cat: cat
                };
                
                vectorPoints.push(newPt);
                drawVectorSpace();
                
                let nearestNode = null;
                let maxSim = -1;
                
                vectorPoints.forEach(p => {
                    if (p.label !== word) {
                        // Cosine Similarity formula: cos(theta) = A.B / (||A||*||B||)
                        const dotProduct = newPt.x * p.x + newPt.y * p.y;
                        const magA = Math.hypot(newPt.x, newPt.y);
                        const magB = Math.hypot(p.x, p.y);
                        const sim = dotProduct / (magA * magB);
                        
                        if (sim > maxSim) {
                            maxSim = sim;
                            nearestNode = p;
                        }
                    }
                });

                const report = document.getElementById("vector-report");
                report.style.display = "block";
                report.innerHTML = `
                    <span style="color: #f35588; font-weight: bold;">[Semantic Mapping]</span><br>
                    Word "<strong>${word}</strong>" mapped to coordinates: <code>(${newPt.x.toFixed(3)}, ${newPt.y.toFixed(3)})</code>.<br>
                    Similarity Algorithm: <code>cos(θ) = A·B / (||A|| ||B||)</code><br>
                    Nearest Semantic Node: "<strong>${nearestNode.label}</strong>" (Cosine Similarity: <strong style="color: #00f2fe;">${maxSim.toFixed(4)}</strong>).
                `;
                
                input.value = "";
            }

            // STEP 04 - LSTM Forecasting Timeline Chart
            function updateLSTMChart() {
                const wMacro = parseFloat(document.getElementById("lstm-wmacro").value) / 100;
                const wMicro = parseFloat(document.getElementById("lstm-wmicro").value) / 100;
                const lag = parseInt(document.getElementById("lstm-lag").value); // Shift
                
                const svg = document.getElementById("lstm-svg");
                svg.innerHTML = ""; 
                
                // Draw chart grid
                for (let i = 30; i <= 120; i += 30) {
                    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    line.setAttribute("x1", "0");
                    line.setAttribute("y1", i);
                    line.setAttribute("x2", "350");
                    line.setAttribute("y2", i);
                    line.setAttribute("stroke", "rgba(255,255,255,0.03)");
                    svg.appendChild(line);
                }
                
                const xPoints = [15, 55, 95, 135, 175, 215, 255, 295, 335];
                const macroY = [120, 120, 115, 100, 50, 35, 60, 100, 120];
                const microY = [120, 100, 40, 20, 70, 110, 120, 120, 120];
                
                // Draw GDELT Macro Timeline (Blue)
                let macroPathD = `M ${xPoints[0]} ${macroY[0]}`;
                for (let i = 1; i < xPoints.length; i++) {
                    macroPathD += ` L ${xPoints[i]} ${macroY[i]}`;
                }
                const macroPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                macroPath.setAttribute("d", macroPathD);
                macroPath.setAttribute("fill", "none");
                macroPath.setAttribute("stroke", "rgba(0, 242, 254, 0.35)");
                macroPath.setAttribute("stroke-width", "2");
                macroPath.setAttribute("stroke-dasharray", "4");
                svg.appendChild(macroPath);
                
                // Draw Social Micro Timeline (Red/Pink, shifted horizontally by Lag)
                const microPoints = xPoints.map((x, idx) => {
                    return { x: x + lag * 8, y: microY[idx] };
                });
                
                let microPathD = `M ${microPoints[0].x} ${microPoints[0].y}`;
                for (let i = 1; i < microPoints.length; i++) {
                    microPathD += ` L ${microPoints[i].x} ${microPoints[i].y}`;
                }
                const microPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                microPath.setAttribute("d", microPathD);
                microPath.setAttribute("fill", "none");
                microPath.setAttribute("stroke", "rgba(243, 85, 136, 0.35)");
                microPath.setAttribute("stroke-width", "2");
                microPath.setAttribute("stroke-dasharray", "4");
                svg.appendChild(microPath);
                
                // Draw M-PULSE Forecast Line (Cyan Solid)
                const combinedPoints = xPoints.map((x, idx) => {
                    const yMacroVal = macroY[idx];
                    const yMicroVal = microY[idx];
                    
                    const idleY = 125;
                    const macroDelta = idleY - yMacroVal;
                    const microDelta = idleY - yMicroVal;
                    
                    // Fusion equation weight multiplier
                    const combinedDelta = (macroDelta * wMacro + microDelta * wMicro);
                    const finalY = idleY - combinedDelta;
                    
                    return { x, y: Math.max(10, Math.min(140, finalY)) };
                });
                
                let forecastPathD = `M ${combinedPoints[0].x} ${combinedPoints[0].y}`;
                for (let i = 1; i < combinedPoints.length; i++) {
                    forecastPathD += ` L ${combinedPoints[i].x} ${combinedPoints[i].y}`;
                }
                const forecastPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                forecastPath.setAttribute("d", forecastPathD);
                forecastPath.setAttribute("fill", "none");
                forecastPath.setAttribute("stroke", "#00f2fe");
                forecastPath.setAttribute("stroke-width", "3.5");
                forecastPath.setAttribute("style", "filter: drop-shadow(0 0 5px rgba(0, 242, 254, 0.5));");
                svg.appendChild(forecastPath);
                
                document.getElementById("lstm-status").innerHTML = `
                    LSTM Weight distribution: <code>[Macro ${Math.round(wMacro*100)}% | Micro ${Math.round(wMicro*100)}%]</code><br>
                    Alignment Sync: <code>${lag >= 0 ? '+' + lag : lag} day offset</code>
                `;
            }

            // VRAM Access Benchmarking Simulator
            function runStandardLLM() {
                const fill = document.getElementById('vram-fill');
                const text = document.getElementById('vram-text');
                const status = document.getElementById('system-status');
                
                fill.style.width = '100%';
                fill.style.backgroundColor = '#f35588'; 
                text.innerText = '80.0 GB / 8.0 GB (Critical)';
                
                status.style.color = '#f35588';
                status.innerText = '💥 SYSTEM CRASH: Out of Memory! GPU requires A100 cluster.';
            }

            function runMPulse() {
                const fill = document.getElementById('vram-fill');
                const text = document.getElementById('vram-text');
                const status = document.getElementById('system-status');
                
                fill.style.width = '72.5%'; 
                fill.style.backgroundColor = '#00f2fe'; 
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

            // Run initializers
            window.onload = function() {
                updateDBSCAN();
                drawVectorSpace();
                updateLSTMChart();
            };
            
            // Handle cases where scripts evaluate before/after DOM completes inside Streamlit frames
            setTimeout(() => {
                updateDBSCAN();
                drawVectorSpace();
                updateLSTMChart();
            }, 100);
        </script>
    """
    import streamlit.components.v1 as components
    components.html(html_content, height=1750, scrolling=False)

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
            <a href="?page=paper" target="_self" class="nav-item {active_paper}">Research Visuals</a>
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