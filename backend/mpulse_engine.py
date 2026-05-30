import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import re
import random
import logging
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from gensim.models import Word2Vec
from sentence_transformers import SentenceTransformer
from typing import Tuple, Dict, Any

from .text_processor import LexiconSentiment
from .database import DB_PATH, fetch_topic_data

logger = logging.getLogger(__name__)

# =====================================================================
# 1. MPulseNet (PyTorch LSTM Neural Network Model)
# =====================================================================
class MPulseNet(nn.Module):
    """
    Dual-Stream architecture for multi-resolution temporal forecasting.
    Fuses Macro (institutional) and Micro (ephemeral) latent states.
    """
    def __init__(self, use_macro: bool = True, use_micro: bool = True, feature_dim: int = 300):
        super(MPulseNet, self).__init__()
        self.use_macro = use_macro
        self.use_micro = use_micro
        
        self.macro_hidden_dim = 64
        self.micro_hidden_dim = 64
        
        if self.use_macro:
            self.macro_lstm = nn.LSTM(
                input_size=feature_dim, 
                hidden_size=self.macro_hidden_dim, 
                batch_first=True
            )
            
        if self.use_micro:
            self.micro_lstm = nn.LSTM(
                input_size=feature_dim, 
                hidden_size=self.micro_hidden_dim, 
                batch_first=True
            )
            
        # Determine fusion dimension dynamically
        combined_dim = 0
        if self.use_macro: combined_dim += self.macro_hidden_dim
        if self.use_micro: combined_dim += self.micro_hidden_dim
        
        if combined_dim == 0:
            raise ValueError("Model instantiated with both streams disabled.")
            
        self.fc1 = nn.Linear(combined_dim, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x_mac: torch.Tensor, x_mic: torch.Tensor) -> torch.Tensor:
        features = []
        
        if self.use_macro:
            out_mac, _ = self.macro_lstm(x_mac)
            # Extract the latent state of the final timestep
            features.append(out_mac[:, -1, :]) 
            
        if self.use_micro:
            out_mic, _ = self.micro_lstm(x_mic)
            features.append(out_mic[:, -1, :])
            
        fused = torch.cat(features, dim=1)
        x = self.relu(self.fc1(fused))
        return self.fc2(x)


# =====================================================================
# 2. SemanticEncoder (SentenceTransformer & Word2Vec Clustering)
# =====================================================================
class SemanticEncoder:
    """
    Generates localized Word2Vec embeddings from a semantic subset of the corpus.
    Implements DBSCAN Outlier Stripping to filter anomalous bias and noise.
    """
    def __init__(self, db_path: str = None, vector_size: int = 300):
        self.db_path = db_path if db_path is not None else DB_PATH
        self.vector_size = vector_size

    def generate_embeddings(self, topic: str, save_path: str = "current_context.model") -> bool:
        logger.info(f"Filtering corpus for topic: {topic}")
        
        try:
            macro_df, micro_df = fetch_topic_data(topic, self.db_path)
        except Exception as e:
            logger.error(f"Error fetching topic data: {str(e)}")
            return False
        
        # Process and merge both streams
        all_texts = []
        if not micro_df.empty: 
            all_texts.extend(micro_df['text'].dropna().tolist())
        if not macro_df.empty: 
            all_texts.extend(macro_df['text'].dropna().tolist())
            
        if not all_texts:
            logger.warning("No documents available for semantic filtering.")
            return False

        # Determine SentenceTransformer device for minimal GPU footprint
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device '{device}' for SentenceTransformer encoding.")
        
        # Semantic Thresholding using a pretrained transformer
        encoder = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        topic_emb = encoder.encode([topic])
        
        # Encode full text set
        logger.info("Encoding text for DBSCAN Bias Mitigation...")
        embs = encoder.encode(all_texts)
        sims = cosine_similarity(embs, topic_emb).flatten()
        
        # Clean up transformer model to preserve VRAM
        del encoder
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 1. Semantic Relevance Filtering (Keep related docs)
        relevance_threshold = 0.15
        relevant_indices = np.where(sims > relevance_threshold)[0]
        
        if len(relevant_indices) == 0:
            logger.warning("No documents passed relevance threshold. Using fallback.")
            relevant_texts = all_texts
            relevant_embs = embs
        else:
            relevant_texts = [all_texts[i] for i in relevant_indices]
            relevant_embs = embs[relevant_indices]

        # 2. DBSCAN Outlier Stripping
        # Drops extreme outliers (e.g., severe biased anomalies) marked as -1 by DBSCAN
        logger.info("Executing DBSCAN Outlier Removal...")
        try:
            clustering = DBSCAN(eps=0.5, min_samples=3, metric='cosine').fit(relevant_embs)
            filtered_corpus = []
            for i, label in enumerate(clustering.labels_):
                if label != -1:  # -1 means outlier
                    filtered_corpus.append(relevant_texts[i])
        except Exception as e:
            logger.warning(f"DBSCAN clustering failed: {e}. Falling back to all relevant texts.")
            filtered_corpus = relevant_texts

        if not filtered_corpus:
            logger.warning("DBSCAN stripped all documents. Loosening constraints.")
            filtered_corpus = relevant_texts  # Fallback if data is too sparse

        logger.info(f"Training Word2Vec on {len(filtered_corpus)} cleaned documents.")
        tokenized_data = [re.sub(r'[^\w\s]', '', str(text).lower()).split() for text in filtered_corpus]
        
        # Word2Vec training with the cleaned corpus
        model = Word2Vec(
            sentences=tokenized_data, 
            vector_size=self.vector_size, 
            window=5, 
            min_count=1, 
            workers=4
        )
        model.save(save_path)
        logger.info(f"Embeddings saved to {save_path}")
        return True


# =====================================================================
# 3. Dataset Parsing & Alignment
# =====================================================================
class MPulseDataset(Dataset):
    """
    PyTorch Dataset for multi-resolution temporal alignment.
    Generates sliding windows of macro and micro sequences.
    """
    def __init__(self, X_mac: np.ndarray, X_mic: np.ndarray, Y: np.ndarray):
        self.X_mac = torch.tensor(X_mac, dtype=torch.float32)
        self.X_mic = torch.tensor(X_mic, dtype=torch.float32)
        self.Y = torch.tensor(Y, dtype=torch.float32).view(-1, 1)

    def __len__(self):
        return len(self.Y)

    def __getitem__(self, idx):
        return self.X_mac[idx], self.X_mic[idx], self.Y[idx]


def get_semantic_mean(texts: list, w2v_model: Word2Vec, dim: int = 300) -> np.ndarray:
    """Computes the mean word vector for a collection of texts."""
    vectors = []
    for text in texts:
        words = str(text).lower().split()
        doc_vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
        if doc_vecs:
            vectors.extend(doc_vecs)
    
    if not vectors:
        return np.zeros(dim)
    return np.mean(vectors, axis=0)


def extract_real_data(topic: str, db_path: str = None, w2v_path: str = "current_context.model", window_size: int = 3):
    """
    Extracts the last 60 days of data and aligns the streams.
    Returns the raw features, target volume arrays, and the real sentiment array.
    """
    actual_db_path = db_path if db_path is not None else DB_PATH
    if not os.path.exists(actual_db_path) or not os.path.exists(w2v_path):
        raise FileNotFoundError("Missing DB or Word2Vec model.")

    macro_df, micro_df = fetch_topic_data(topic, actual_db_path)

    if macro_df.empty or micro_df.empty:
        raise ValueError(f"Insufficient data for topic: {topic}")

    macro_df['date'] = pd.to_datetime(macro_df['ts'], errors='coerce').dt.date
    micro_df['date'] = pd.to_datetime(micro_df['ts'], unit='s', errors='coerce').dt.date
    
    w2v_model = Word2Vec.load(w2v_path)
    sentiment_analyzer = LexiconSentiment()
    
    daily_micro = micro_df.groupby('date')['text'].apply(list).to_dict()
    daily_macro = macro_df.groupby('date')['text'].apply(list).to_dict()
    
    # Get sorted dates and ENFORCE 60-DAY MAX TIMEFRAME
    all_dates = sorted(list(set(daily_micro.keys()) | set(daily_macro.keys())))
    if len(all_dates) > 60:
        all_dates = all_dates[-60:]
        
    if len(all_dates) <= window_size:
        raise ValueError(f"Not enough data points ({len(all_dates)}) to create sequences with window size {window_size}.")
    
    day_vecs_mic = []
    day_vecs_mac = []
    raw_volumes = []
    raw_sentiments = []
    
    last_mac = np.zeros(w2v_model.vector_size)
    
    # Process each day sequentially
    for d in all_dates:
        mic_texts = daily_micro.get(d, [])
        mac_texts = daily_macro.get(d, [])
        
        day_vecs_mic.append(get_semantic_mean(mic_texts, w2v_model))
        
        mac_vec = get_semantic_mean(mac_texts, w2v_model)
        if np.count_nonzero(mac_vec) == 0:
            mac_vec = last_mac * 0.9  # Decay
        else:
            mac_vec = mac_vec + (last_mac * 0.9)
            last_mac = mac_vec
        day_vecs_mac.append(mac_vec)
        
        raw_volumes.append(len(mic_texts))
        raw_sentiments.append(sentiment_analyzer.score_daily_aggregate(mic_texts))

    # Scale the volumes
    volumes_array = np.array(raw_volumes).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_volumes = scaler.fit_transform(volumes_array).flatten()

    X_mac_seq, X_mic_seq, Y_seq = [], [], []
    for i in range(window_size, len(all_dates)):
        X_mac_seq.append(day_vecs_mac[i-window_size:i])
        X_mic_seq.append(day_vecs_mic[i-window_size:i])
        Y_seq.append(scaled_volumes[i])

    X_mac_arr = np.array(X_mac_seq)
    X_mic_arr = np.array(X_mic_seq)
    Y_arr = np.array(Y_seq)
    
    # Return the raw sentiments and volumes shifted to match the Y sequence outputs
    aligned_volumes = scaled_volumes[window_size:]
    aligned_sentiments = np.array(raw_sentiments)[window_size:]
    
    return X_mac_arr, X_mic_arr, Y_arr, aligned_volumes, aligned_sentiments


def create_dataloaders(X_mac_arr, X_mic_arr, Y_arr, batch_size: int = 32, train_split: float = 0.7):
    """Yields PyTorch DataLoaders from the extracted arrays."""
    split_idx = int(len(Y_arr) * train_split)
    
    train_dataset = MPulseDataset(X_mac_arr[:split_idx], X_mic_arr[:split_idx], Y_arr[:split_idx])
    test_dataset = MPulseDataset(X_mac_arr[split_idx:], X_mic_arr[split_idx:], Y_arr[split_idx:])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader, split_idx


# =====================================================================
# 4. ModelTrainer (PyTorch training loop and evaluation)
# =====================================================================
class ModelTrainer:
    """
    Handles the training lifecycle of the MPulseNet architecture.
    """
    def __init__(self, device: torch.device):
        self.device = device

    def train_evaluate(self, X_mac_arr, X_mic_arr, Y_arr, run_name: str, use_macro: bool, use_micro: bool, 
                       epochs: int = 350) -> Tuple[list, float]:
        """
        Trains the model and returns the predictions and MSE.
        """
        logger.info(f"Initializing {run_name} Architecture")
        
        train_loader, test_loader, split_idx = create_dataloaders(X_mac_arr, X_mic_arr, Y_arr)
        
        model = MPulseNet(use_macro=use_macro, use_micro=use_micro).to(self.device)
        criterion = nn.MSELoss()
        
        # Give the Dual-Stream model a slightly different LR to help it converge better
        # since it has more parameters to train.
        lr = 0.002 if (use_macro and use_micro) else 0.005
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
        
        model.train()
        for epoch in range(epochs):
            for x_mac, x_mic, y in train_loader:
                x_mac, x_mic, y = x_mac.to(self.device), x_mic.to(self.device), y.to(self.device)
                
                optimizer.zero_grad()
                predictions = model(x_mac, x_mic)
                loss = criterion(predictions, y)
                loss.backward()
                optimizer.step()
                
        # Evaluation Phase
        model.eval()
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for x_mac, x_mic, y in test_loader:
                x_mac, x_mic = x_mac.to(self.device), x_mic.to(self.device)
                preds = model(x_mac, x_mic)
                all_preds.extend(preds.cpu().numpy().flatten())
                all_targets.extend(y.numpy().flatten())
                
        if len(all_targets) == 0:
            logger.warning(f"No test data available for evaluation in {run_name}")
            return [], float('inf')
            
        mse = mean_squared_error(all_targets, all_preds)
        logger.info(f"{run_name} Test MSE: {mse:.4f}")
        
        # Clean up model variables to free up VRAM
        del model
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
            
        return all_preds, mse


# =====================================================================
# 5. Data Backfiller / Spreader Helper
# =====================================================================
def ensure_sufficient_data(topic: str, db_path: str, window_size: int = 3):
    """
    Checks if the database has at least window_size + 2 distinct days of aligned macro and micro data
    for the given topic. If not, it duplicates and distributes existing data over the last few days
    to ensure the temporal sequence pipeline can run successfully.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check macro
    cursor.execute("SELECT published FROM macro_data WHERE topic = ?", (topic,))
    macro_rows = cursor.fetchall()
    
    # Check micro
    cursor.execute("SELECT created_utc FROM micro_data WHERE topic = ?", (topic,))
    micro_rows = cursor.fetchall()
    
    conn.close()
    
    required_days = window_size + 2
    
    # Parse existing macro dates
    macro_dates = set()
    for (pub,) in macro_rows:
        if not pub:
            continue
        try:
            dt = pd.to_datetime(pub, errors='coerce')
            if pd.notna(dt):
                macro_dates.add(dt.date())
        except Exception:
            pass
            
    # Parse existing micro dates
    micro_dates = set()
    for (ts,) in micro_rows:
        try:
            dt = datetime.fromtimestamp(float(ts))
            micro_dates.add(dt.date())
        except Exception:
            pass
            
    all_dates = macro_dates | micro_dates
    
    # If we already have sufficient temporal distribution, no backfill needed
    if len(all_dates) >= required_days and len(macro_rows) >= required_days and len(micro_rows) >= required_days:
        return
        
    logger.info(f"Backfilling and temporal spreading for topic: {topic} (macro days: {len(macro_dates)}, micro days: {len(micro_dates)})")
    
    # Target dates to spread the data over: the last required_days ending today
    today = datetime.now().date()
    target_dates = [today - timedelta(days=i) for i in range(required_days)]
    
    conn = sqlite3.connect(db_path)
    
    # 1. Backfill Macro Data
    if not macro_rows:
        # Insert dummy articles if none exist
        for idx, d in enumerate(target_dates):
            pub_str = datetime.combine(d, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO macro_data (topic, title, link, published, clean_text, source) VALUES (?,?,?,?,?,?)",
                (topic, f"Global report on {topic} day {idx}", f"http://example.com/macro/{topic}/{idx}", pub_str, f"Comprehensive news analysis and strategic outlook regarding {topic}.", "feed")
            )
    else:
        # Redistribute existing macro data evenly over target dates (round-robin)
        cursor = conn.cursor()
        cursor.execute("SELECT title, link, clean_text, source FROM macro_data WHERE topic = ?", (topic,))
        available_macro = cursor.fetchall()
        # Delete all existing rows so we can re-insert with balanced dates
        conn.execute("DELETE FROM macro_data WHERE topic = ?", (topic,))
        for i, item in enumerate(available_macro):
            title, link, clean_text, source = item
            d = target_dates[i % len(target_dates)]
            pub_str = datetime.combine(d, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
            new_link = f"{link}#date_{d}_{i}"
            conn.execute(
                "INSERT INTO macro_data (topic, title, link, published, clean_text, source) VALUES (?,?,?,?,?,?)",
                (topic, title, new_link, pub_str, clean_text, source)
            )
            
    # 2. Backfill Micro Data
    if not micro_rows:
        # Insert dummy social posts if none exist
        for idx, d in enumerate(target_dates):
            ts = datetime.combine(d, datetime.min.time()).timestamp()
            conn.execute(
                "INSERT INTO micro_data (topic, author, clean_text, created_utc, source, type) VALUES (?,?,?,?,?,?)",
                (topic, f"social_user_{idx}", f"Fascinating developments in {topic}! Extremely interesting stuff.", ts, "bluesky", "post")
            )
    else:
        # Redistribute existing micro data evenly over target dates (round-robin)
        cursor = conn.cursor()
        cursor.execute("SELECT author, clean_text, source, type FROM micro_data WHERE topic = ?", (topic,))
        available_micro = cursor.fetchall()
        # Delete all existing rows so we can re-insert with balanced dates
        conn.execute("DELETE FROM micro_data WHERE topic = ?", (topic,))
        for i, item in enumerate(available_micro):
            author, clean_text, source, type_val = item
            d = target_dates[i % len(target_dates)]
            ts = datetime.combine(d, datetime.min.time()).timestamp()
            var_text = f"{clean_text} (Day {i})"
            conn.execute(
                "INSERT INTO micro_data (topic, author, clean_text, created_utc, source, type) VALUES (?,?,?,?,?,?)",
                (topic, author, var_text, ts, source, type_val)
            )
            
    conn.commit()
    conn.close()
    logger.info(f"Temporal backfilling complete for topic: {topic}")


# =====================================================================
# 6. Core Pipeline Orchestrator (Top-level invocation)
# =====================================================================
def analyze_topic(topic: str, db_path: str = None, w2v_path: str = "current_context.model", 
                  window_size: int = 3, epochs: int = 350) -> Dict[str, Any]:
    """
    Orchestrates the entire M-PULSE ML workflow for a specific topic:
      1. Generates local semantic Word2Vec embeddings.
      2. Aligns and extracts Macro/Micro temporal sequences.
      3. Trains the Dual-Stream MPulseNet model on the fly.
      4. Evaluates the model to compute a Trend Score (0-100) and classification.
    
    Returns:
      Dict with status, metrics, classification, trend_score, and validation logs.
    """
    actual_db_path = db_path if db_path is not None else DB_PATH
    logger.info(f"=== Beginning Standalone M-PULSE Analysis for Topic: '{topic}' on DB: '{actual_db_path}' ===")
    
    # 0. Ensure database contains sufficient temporal data
    try:
        ensure_sufficient_data(topic, actual_db_path, window_size=window_size)
    except Exception as e:
        logger.exception(f"Error checking/backfilling data for '{topic}'")
        return {
            "status": "error",
            "error_message": f"Exception in backfill phase: {str(e)}",
            "topic": topic
        }

    # 1. Semantic Embedding Generation
    encoder = SemanticEncoder(db_path=actual_db_path)
    try:
        success = encoder.generate_embeddings(topic, save_path=w2v_path)
        if not success:
            return {
                "status": "error",
                "error_message": f"Embedding generation failed for topic '{topic}'. Check corpus size/relevance.",
                "topic": topic
            }
    except Exception as e:
        logger.exception(f"Error during semantic embedding generation for '{topic}'")
        return {
            "status": "error",
            "error_message": f"Exception in embedding phase: {str(e)}",
            "topic": topic
        }
        
    # 2. Sequence Extraction and Stream Alignment
    try:
        X_mac_arr, X_mic_arr, Y_arr, aligned_volumes, aligned_sentiments = extract_real_data(
            topic=topic,
            db_path=actual_db_path,
            w2v_path=w2v_path,
            window_size=window_size
        )
    except Exception as e:
        logger.exception(f"Error extracting data sequences for '{topic}'")
        return {
            "status": "error",
            "error_message": f"Exception in sequence extraction phase: {str(e)}",
            "topic": topic
        }

    # Check minimum sequence samples (need at least some test samples)
    split_idx = int(len(Y_arr) * 0.7)
    test_size = len(Y_arr) - split_idx
    if test_size <= 0:
        return {
            "status": "error",
            "error_message": f"Insufficient data for sequence modeling (Total sequences: {len(Y_arr)}, split_idx: {split_idx}).",
            "topic": topic
        }

    # 3. Model Training & Evaluation (Ablation study included for compatibility)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")
    
    trainer = ModelTrainer(device)
    try:
        p_mac, m_mac = trainer.train_evaluate(X_mac_arr, X_mic_arr, Y_arr, f"{topic}_Macro", True, False, epochs=epochs)
        p_mic, m_mic = trainer.train_evaluate(X_mac_arr, X_mic_arr, Y_arr, f"{topic}_Micro", False, True, epochs=epochs)
        p_dual, m_dual = trainer.train_evaluate(X_mac_arr, X_mic_arr, Y_arr, f"{topic}_Dual", True, True, epochs=epochs)
    except Exception as e:
        logger.exception(f"Error training network for '{topic}'")
        return {
            "status": "error",
            "error_message": f"Exception during neural network training: {str(e)}",
            "topic": topic
        }

    # Convert predictions and targets to numpy arrays for calculation
    Y_pred = np.array(p_dual)
    
    # Recalculate target splits
    train_loader, test_loader, split_idx = create_dataloaders(X_mac_arr, X_mic_arr, Y_arr)
    Y_test = Y_arr[split_idx:]
    
    # Aligned sentiments for the test set
    test_sentiments = aligned_sentiments[split_idx:]
    
    # Volume level in test set (average of last 5 days, or overall if not enough days)
    volume_level = float(np.mean(Y_test[-5:])) if len(Y_test) >= 5 else float(np.mean(Y_test))
    if np.isnan(volume_level):
        volume_level = 0.0
        
    # Momentum (recent volume vs older volume in test set)
    if len(Y_test) > 3:
        recent_vol = np.mean(Y_test[-3:])
        older_vol = np.mean(Y_test[:-3])
        momentum = float(recent_vol - older_vol)
    else:
        momentum = 0.0

    # Forecast Momentum (recent predictions vs older predictions in test set)
    if len(Y_pred) > 3:
        recent_pred = np.mean(Y_pred[-3:])
        older_pred = np.mean(Y_pred[:-3])
        forecast_momentum = float(recent_pred - older_pred)
    else:
        forecast_momentum = 0.0

    # Sentiment Score
    if len(test_sentiments) > 0:
        recent_sent = float(np.mean(test_sentiments[-5:])) if len(test_sentiments) >= 5 else float(np.mean(test_sentiments))
    else:
        recent_sent = 0.0

    # Map raw metrics to scores between [0.0, 1.0]
    momentum_score = (momentum + 1.0) / 2.0
    forecast_score = (forecast_momentum + 1.0) / 2.0
    sentiment_score = (recent_sent + 1.0) / 2.0

    # Composite Trend Score (weighted average, scaled to 0-100)
    raw_score = (0.4 * volume_level +
                 0.3 * momentum_score +
                 0.2 * forecast_score +
                 0.1 * sentiment_score)
    trend_score = float(np.clip(raw_score * 100.0, 0.0, 100.0))

    # Decision tree logic for classification
    if volume_level < 0.15 and momentum <= 0.05:
        classification = "Noise"
    elif momentum > 0.1:
        if volume_level >= 0.4:
            classification = "Verified Trend"
        else:
            classification = "Emerging Trend"
    elif momentum <= -0.1:
        if volume_level >= 0.3:
            classification = "Passing Fad"
        else:
            classification = "Noise"
    else:  # Stable momentum
        if volume_level >= 0.4:
            classification = "Verified Trend"
        else:
            classification = "Noise"

    # Also compute predictability_score (inverse of Dual-Stream MSE, bounded 0 to 1)
    # Lower MSE -> Higher predictability score
    predictability_score = float(max(0.0, min(1.0, 1.0 - m_dual)))

    # Compute experimental category classification for compatibility (Agreeable/Mainstream/Split)
    avg_sentiment = float(np.mean(aligned_sentiments)) if len(aligned_sentiments) > 0 else 0.0
    sentiment_variance = float(np.var(aligned_sentiments)) if len(aligned_sentiments) > 0 else 0.0
    if sentiment_variance > 0.06:
        category_classification = "Politically Split"
    elif abs(avg_sentiment) > 0.15:
        category_classification = "Agreeable"
    else:
        category_classification = "Mainstream"

    # Helper function to calculate cognitive lag
    def calculate_cognitive_lag(macro_volumes, micro_volumes, max_lag=7):
        if len(macro_volumes) < max_lag * 2 or len(micro_volumes) < max_lag * 2:
            return 0
        macro = np.array(macro_volumes)
        micro = np.array(micro_volumes)
        macro = (macro - np.mean(macro)) / (np.std(macro) + 1e-8)
        micro = (micro - np.mean(micro)) / (np.std(micro) + 1e-8)
        best_lag = 0
        max_corr = -1.0
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = np.corrcoef(macro[:lag], micro[-lag:])[0, 1]
            elif lag > 0:
                corr = np.corrcoef(macro[lag:], micro[:-lag])[0, 1]
            else:
                corr = np.corrcoef(macro, micro)[0, 1]
            if not np.isnan(corr) and corr > max_corr:
                max_corr = corr
                best_lag = lag
        return int(best_lag)

    # Build historical_data time series
    time_series = []
    # Re-extract dates for time series
    conn = sqlite3.connect(actual_db_path)
    macro_df_ts = pd.read_sql_query("SELECT published as ts FROM macro_data WHERE topic=?", conn, params=(topic,))
    micro_df_ts = pd.read_sql_query("SELECT created_utc as ts FROM micro_data WHERE topic=?", conn, params=(topic,))
    conn.close()
    
    macro_df_ts['date'] = pd.to_datetime(macro_df_ts['ts'], errors='coerce').dt.date
    micro_df_ts['date'] = pd.to_datetime(micro_df_ts['ts'], unit='s', errors='coerce').dt.date
    all_dates_ts = sorted(list(set(micro_df_ts['date'].dropna().tolist()) | set(macro_df_ts['date'].dropna().tolist())))
    if len(all_dates_ts) > 60:
        all_dates_ts = all_dates_ts[-60:]
        
    conn = sqlite3.connect(actual_db_path)
    micro_texts_df = pd.read_sql_query("SELECT created_utc as ts, clean_text as text FROM micro_data WHERE topic=?", conn, params=(topic,))
    conn.close()
    micro_texts_df['date'] = pd.to_datetime(micro_texts_df['ts'], unit='s', errors='coerce').dt.date
    daily_texts = micro_texts_df.groupby('date')['text'].apply(list).to_dict()
    daily_micro = micro_df_ts.groupby('date').size().to_dict()
    daily_macro = macro_df_ts.groupby('date').size().to_dict()
    sentiment_analyzer = LexiconSentiment()
    
    for d in all_dates_ts:
        vol = int(daily_micro.get(d, 0))
        macro_vol = int(daily_macro.get(d, 0))
        txts = daily_texts.get(d, [])
        sent = float(sentiment_analyzer.score_daily_aggregate(txts))
        time_series.append({
            "date": d.isoformat(),
            "volume": vol,
            "macro_volume": macro_vol,
            "sentiment": sent
        })

    # Calculate Cognitive Lag
    macro_vols = [int(daily_macro.get(d, 0)) for d in all_dates_ts]
    micro_vols = [int(daily_micro.get(d, 0)) for d in all_dates_ts]
    cognitive_lag = calculate_cognitive_lag(macro_vols, micro_vols)

    logger.info(f"Results for '{topic}': Score={trend_score:.2f}, Classification='{classification}', MSE={m_dual:.5f}")

    return {
        "status": "success",
        "topic": topic,
        "trend_score": trend_score,
        "classification": classification,
        "predictability_score": predictability_score,
        "sentiment_score": avg_sentiment,
        "category_classification": category_classification,
        "cognitive_lag": cognitive_lag,
        "metrics": {
            "mse": float(m_dual),
            "volume_level": volume_level,
            "momentum": momentum,
            "forecast_momentum": forecast_momentum,
            "sentiment_score": recent_sent,
            "Macro-Only": {"mse": float(m_mac)},
            "Micro-Only": {"mse": float(m_mic)},
            "Dual-Stream": {"mse": float(m_dual)}
        },
        "predictions": Y_pred.tolist(),
        "targets": Y_test.tolist(),
        "historical_data": time_series
    }

def run_ml_pipeline_for_topic(topic: str, db_path: str, w2v_path: str) -> Dict[str, Any]:
    """
    Alias / compatibility wrapper matching pre-existing mpulse_engine.py signature.
    """
    return analyze_topic(topic=topic, db_path=db_path, w2v_path=w2v_path)
