# BlueShift - Media Trend Forecasting Pipeline

BlueShift is a lightweight, local trend prediction system utilizing the **M-PULSE** (Micro-Parametric Understanding of Localized Social Events) dual-stream NLP architecture. It fuses traditional news media (via GDELT) and social media chatter (via Bluesky API) to forecast trend trajectory while respecting consumer-grade hardware constraints (VRAM < 6GB).

---

## 📁 Repository Structure

```text
BlueShift/
├── app.py                  # Main Streamlit UI dashboard
├── requirements.txt        # System requirements
├── results_cache.json      # Pre-generated ML forecasts for immediate load
├── assets/
│   ├── logo.png            # Project logo
│   └── style.css           # Custom dark theme and glassmorphism styling
├── backend/
│   ├── database.py         # SQLite interface for stream persistence
│   ├── mpulse_engine.py    # PyTorch dual-stream LSTM forecasting engine
│   ├── rss_pipeline.py     # Live trending topics scraper
│   ├── text_processor.py   # Sentiment lexicon and processor
│   └── update_queue.py     # Data ingestion and model backfiller queue
└── docs/
    └── index.html          # Serverless, GitHub-Pages-compatible static version
```

---

## ⚡ How to Run Locally

### 1. Installation
Clone the repository and install the dependencies in your Python environment:
```bash
pip install -r requirements.txt
```

### 2. Running the Dashboard
Start the Streamlit dashboard:
```bash
streamlit run app.py
```
Open `http://localhost:8501` to view the interactive dashboard.

### 3. Running Data Updates
To ingest new data streams and retrain the LSTM neural network forecasting models, run:
```bash
python -m BlueShift.backend.update_queue
```
*Note: This will fetch GDELT article history over a 60-day window, scrape Bluesky posts, train the neural network, and refresh `results_cache.json`.*

---

## 🚀 GitHub Pages (Static Hosting)

The `/docs` directory is configured to host the static version of BlueShift on **GitHub Pages** with zero-configuration:
1. Push this folder to your GitHub repository.
2. In your repository settings, navigate to **Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Choose the `main` branch and the `/docs` folder, then click save.

The static page provides an interactive demonstration of the M-PULSE paper's research findings using client-side Chart.js charts, the full research paper viewer, and a feedback submission log.
