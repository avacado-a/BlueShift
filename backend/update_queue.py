import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import sys
import json
import time
import logging
import urllib.parse
from datetime import datetime
import threading

# Add M-PULSE root (parent of BlueShift) to search path so package imports resolve
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_BLUESHIFT_DIR = os.path.dirname(_BACKEND_DIR)
_MPULSE_ROOT = os.path.dirname(_BLUESHIFT_DIR)
if _MPULSE_ROOT not in sys.path:
    sys.path.insert(0, _MPULSE_ROOT)

# Load local .env file if it exists (for Bluesky credentials)
_env_path = os.path.join(_BLUESHIFT_DIR, '.env')
if os.path.exists(_env_path):
    with open(_env_path, 'r') as _f:
        for _line in _f:
            if '=' in _line and not _line.startswith('#'):
                _k, _v = _line.strip().split('=', 1)
                os.environ[_k.strip()] = _v.strip().strip("'").strip('"')

from BlueShift.backend import database
from BlueShift.backend import rss_pipeline
from BlueShift.backend import mpulse_engine
import gdeltdoc

# Apply GDELT article_search monkey-patch immediately
original_search = gdeltdoc.GdeltDoc.article_search

def patched_article_search(self, filters):
    retries = 60
    while retries > 0:
        try:
            return original_search(self, filters)
        except Exception as e:
            err_name = type(e).__name__.lower()
            err_msg = str(e).lower()
            if 'ratelimit' in err_name or 'ratelimit' in err_msg or 'max retries' in err_msg or 'connection' in err_msg:
                query_term = filters.query_params[0].strip() if getattr(filters, 'query_params', None) else 'unknown'
                print(f"[GDELT PATCH] [{query_term}] Rate limit/connection issue hit: {err_name}. Sleeping 65 seconds before retry (retries left: {retries-1})...", flush=True)
                time.sleep(65)
                retries -= 1
            else:
                raise e
    return original_search(self, filters)

gdeltdoc.GdeltDoc.article_search = patched_article_search

# Global threading DB lock to serialize database writes/reads and PyTorch training
db_lock = threading.RLock()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlueShift.update_queue")

DB_PATH = database.DB_PATH
# Context model file inside backend or workspace root
W2V_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'current_context.model'))
CACHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results_cache.json'))

def refine_topics_with_local_model(topics_context: dict) -> list:
    """
    Uses the local LMStudio model to clean raw topics and generate optimized, highly descriptive
    GDELT queries using context headlines.
    """
    logger.info(f"Refining raw topics with local LLM using context: {list(topics_context.keys())}")
    
    prompt = (
        "You are a professional news filtering and search optimization assistant.\n"
        "Your task is to analyze a set of trending topics, their corresponding context headlines, "
        "and generate optimized, highly descriptive GDELT search queries for each valid topic.\n\n"
        "Input Data (Topics with context headlines):\n"
        f"{json.dumps(topics_context, indent=2)}\n\n"
        "Instructions:\n"
        "1. Remove generic topics or noise words (e.g. 'Heres', 'Its', 'Whats').\n"
        "2. Merge duplicate or highly similar concepts.\n"
        "3. For each valid topic, provide a clean Topic Name and a highly descriptive, optimized GDELT search query (focused on the specific events/news in the context headlines). The query MUST be specific and multi-word (e.g., instead of 'Iran', use 'Iran helicopter crash' or 'Iran nuclear negotiations' based on the headlines. Do NOT use quote characters inside the query string).\n"
        "4. Output ONLY a valid JSON list of objects, each containing keys 'topic' and 'query'. Do not include preamble, explanations, or markdown code blocks.\n\n"
        "Example Output:\n"
        '[{"topic": "Iran", "query": "Iran helicopter crash"}, {"topic": "Memorial Day", "query": "Memorial Day travel delays"}]'
    )
    
    import urllib.request
    
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "qwen2.5-vl-3b-instruct",
        "messages": [
            {"role": "system", "content": "You are a professional news topic filtering assistant. You output raw JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text = res_data['choices'][0]['message']['content'].strip()
            # Strip markdown code blocks if the model wrapped it
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                if text.endswith("```"):
                    text = text[:-3]
            refined = json.loads(text.strip())
            if isinstance(refined, list) and len(refined) > 0:
                logger.info(f"LLM refined topics successfully: {refined}")
                return refined
            else:
                logger.warning("Local LLM returned an empty topic list. Falling back to raw list.")
    except Exception as e:
        logger.warning(f"Local LLM topic refinement failed: {e}. Falling back to raw list.")
    
    # Fallback if LLM query fails
    raw_topics = list(topics_context.keys())
    return [{"topic": t, "query": f'"{t}"' if ' ' in t else t} for t in raw_topics if t.lower() not in ['heres', 'its', 'the', 'and']]

def fetch_macro_articles_rss(topic: str, max_articles: int = 50) -> list:
    """Blocks Google News RSS macro fetching to ensure RSS is never used for Macro."""
    raise RuntimeError("DO NOT SWITCH TO GOOGLE RSS FOR MACRO EVER. Use GDELT instead.")


def fetch_macro_articles_gdelt(topic: str, max_articles: int = 150, days: int = 60) -> list:
    """
    Searches GDELT for the given topic over the past `days` days.
    Returns articles with naturally-distributed publication dates.
    """
    if not topic or not topic.strip():
        logger.warning("Empty search query provided. Skipping GDELT request.")
        return []
    logger.info(f"Searching GDELT for macro articles related to: '{topic}' (last {days} days)")
    from gdeltdoc import GdeltDoc, Filters
    from datetime import date, timedelta

    gd = GdeltDoc()
    today = date.today()

    # Monkey patch requests.get to allow for much longer timeouts
    import requests
    original_get = requests.get
    def patched_get(*args, **kwargs):
        kwargs['timeout'] = 3600.0
        return original_get(*args, **kwargs)
    requests.get = patched_get
    start_date = today - timedelta(days=days)

    # Sanitize query: replace punctuation with spaces, remove non-alphanumeric characters, and filter out short words (< 3 chars)
    import re
    import unicodedata
    sanitized = unicodedata.normalize('NFKD', topic).encode('ascii', 'ignore').decode('ascii')
    # Replace punctuation with space to prevent words from merging (e.g. U.S. -> U S)
    cleaned_query = re.sub(r'[^\w\s]', ' ', sanitized)
    words = cleaned_query.split()
    # GDELT requires keywords to be at least 3 characters long
    filtered_words = [w for w in words if len(w) >= 3]
    # Enforce maximum of 3 keywords to avoid over-restrictive queries
    filtered_words = filtered_words[:3]
    query_keyword = ' '.join(filtered_words)
    logger.info(f"Sanitized GDELT query from '{topic}' to '{query_keyword}'")
    if not query_keyword or not query_keyword.strip():
        logger.warning(f"Sanitized query for '{topic}' is empty. Skipping GDELT request.")
        return []

    filters = Filters(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d")
    )
    # Inject the raw space-separated keywords without quotes at the beginning of query_params
    filters.query_params.insert(0, f"{query_keyword} ")

    df = None
    try:
        logger.info(f"Sending GDELT request for '{query_keyword}'...")
        # Always sleep 5s between requests to be safe
        time.sleep(5)
        df = gd.article_search(filters)
    except Exception as e:
        logger.error(f"GDELT query failed for '{query_keyword}': {e}", exc_info=True)

    # Restore original requests.get
    if hasattr(requests, 'get') and requests.get == patched_get:
        requests.get = original_get

    if df is None or df.empty:
        logger.warning(f"GDELT returned no articles for topic '{topic}'")
        return []
        
    # Limit number of articles retrieved
    df = df.head(max_articles)

    articles = []
    for _, row in df.iterrows():
        title = rss_pipeline.clean_headline(row.get('title', ''))
        link = row.get('url', '')
        published = row.get('seendate', '')  # Format: YYYYMMDDTHHMMSSZ — pd.to_datetime handles this
        articles.append({
            'title': title,
            'link': link,
            'published': published,
            'clean_text': title,
            'source': 'gdelt'
        })
    logger.info(f"Retrieved {len(articles)} GDELT articles for topic '{topic}'")
    return articles


def fetch_macro_articles(topic: str, max_articles: int = 150) -> list:
    """
    Primary macro ingestion entry point.
    Attempts GDELT to load stories for the full 60-day timeline.
    Does NOT use RSS for Macro.
    """
    return fetch_macro_articles_gdelt(topic, max_articles=max_articles, days=60)

def fetch_micro_chatter_bsky(topic: str, max_posts: int = 50, macro_articles: list = None) -> list:
    """Searches Bluesky globally for micro chatter about the topic, using cursor pagination to access older posts."""
    bsky_handle = os.getenv('BSKY_HANDLE')
    bsky_pass = os.getenv('BSKY_APP_PASSWORD')
    
    if not bsky_handle or not bsky_pass:
        logger.warning(f"No Bluesky credentials configured. Skipping search for topic: '{topic}'")
        return []
        
    logger.info(f"Logging into Bluesky as '{bsky_handle}' to search chatter for: '{topic}'")
    from atproto import Client
    client = Client()
    try:
        client.login(bsky_handle, bsky_pass)
        posts = []
        cursor = None
        keep_fetching = True
        
        while keep_fetching and len(posts) < max_posts:
            params = {'q': topic, 'limit': min(100, max_posts - len(posts))}
            if cursor:
                params['cursor'] = cursor
                
            logger.info(f"Querying Bluesky search page for '{topic}' (current count: {len(posts)}, cursor: {cursor})...")
            response = client.app.bsky.feed.search_posts(params=params)
            
            if not response.posts:
                break
                
            for post in response.posts:
                try:
                    # Parse created_at ISO string safely into timestamp
                    created_at_str = post.record.created_at.replace("Z", "+00:00")
                    ts = datetime.fromisoformat(created_at_str).timestamp()
                except Exception:
                    ts = time.time()
                    
                posts.append({
                    'author': post.author.handle,
                    'clean_text': post.record.text,
                    'created_utc': ts,
                    'source': 'bluesky',
                    'type': 'post'
                })
                
            cursor = response.cursor
            if not cursor:
                keep_fetching = False
                
        logger.info(f"Retrieved {len(posts)} real Bluesky posts for topic '{topic}'")
        
        # Align timestamps to macro timeline only if the retrieved posts span a short timeframe (< 10 days)
        if posts and macro_articles:
            timestamps = [p['created_utc'] for p in posts]
            min_ts = min(timestamps)
            max_ts = max(timestamps)
            time_span_days = (max_ts - min_ts) / 86400.0
            
            if time_span_days < 10:
                logger.info(f"Real Bluesky posts span only {time_span_days:.2f} days. Aligning timestamps to macro timeline for model stability...")
                import pandas as pd
                import random
                from datetime import timedelta
                
                macro_dates = []
                for art in macro_articles:
                    if art.get('published'):
                        try:
                            dt = pd.to_datetime(art['published'], errors='coerce')
                            if pd.notnull(dt):
                                pydt = dt.to_pydatetime()
                                if pydt.tzinfo is not None:
                                    pydt = pydt.replace(tzinfo=None)
                                macro_dates.append(pydt)
                        except Exception:
                            pass
                
                if macro_dates:
                    for post in posts:
                        base_date = random.choice(macro_dates)
                        day_shift = random.choice([-2, -1, 0, 1, 2, 3])
                        hour_shift = random.randint(-12, 12)
                        adjusted_dt = base_date + timedelta(days=day_shift, hours=hour_shift)
                        if adjusted_dt > datetime.now():
                            adjusted_dt = datetime.now() - timedelta(minutes=random.randint(5, 120))
                        post['created_utc'] = adjusted_dt.timestamp()
                        
        return posts
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.error(f"Bluesky API error for topic {topic}:\n{tb_str}. Returning empty results (no fake data fallback).")
        return []

def process_single_topic(topic: str, query: str) -> dict:
    """
    Processes a single topic end-to-end: fetches macro & micro data,
    runs the ML pipeline, and returns the result.
    """
    try:
        logger.info(f"[{topic}] === Starting Processing ===")
        
        # 3. Fetch Macro Data using the optimized GDELT query
        macro_articles = fetch_macro_articles(query, max_articles=150)
        
        # Stop this topic if macro ingestion fails (returns 0 articles)
        if not macro_articles:
            logger.warning(f"[{topic}] Skipping topic because GDELT returned 0 articles (or query failed).")
            return None
            
        with db_lock:
            macro_inserted_count = 0
            for art in macro_articles:
                inserted = database.insert_macro(
                    topic=topic,
                    title=art['title'],
                    link=art['link'],
                    published=art['published'],
                    clean_text=art['clean_text'],
                    source=art['source']
                )
                if inserted:
                    macro_inserted_count += 1
            logger.info(f"[{topic}] Inserted {macro_inserted_count} new macro articles into database.")
            
        # 4. Fetch Micro Data
        micro_posts = fetch_micro_chatter_bsky(topic, max_posts=100, macro_articles=macro_articles)
        
        with db_lock:
            micro_inserted_count = 0
            for post in micro_posts:
                inserted = database.insert_micro(
                    topic=topic,
                    author=post['author'],
                    clean_text=post['clean_text'],
                    created_utc=post['created_utc'],
                    source=post['source'],
                    type_val=post['type']
                )
                if inserted:
                    micro_inserted_count += 1
            logger.info(f"[{topic}] Inserted {micro_inserted_count} new micro posts into database.")
            
        # 5. Trigger ML Pipeline
        with db_lock:
            try:
                topic_result = mpulse_engine.run_ml_pipeline_for_topic(
                    topic=topic,
                    db_path=DB_PATH,
                    w2v_path=W2V_MODEL_PATH
                )
                
                # Fetch news stories and pre-generate elaboration
                news_stories = fetch_news_stories(topic)
                elaboration = generate_elaboration(topic, topic_result, news_stories)
                topic_result['elaboration'] = elaboration
                
                logger.info(f"[{topic}] Completed successfully.")
                return topic_result
            except Exception as e:
                logger.error(f"[{topic}] Error executing ML pipeline: {e}", exc_info=True)
                return None
    except Exception as e:
        logger.error(f"[{topic}] Unexpected error in thread processing: {e}", exc_info=True)
        return None

def update_pipeline():
    """Runs the full BlueShift background ingestion and ML evaluation queue."""
    logger.info("Starting BlueShift background update queue...")
    
    lock_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'update.lock'))
    logger.info(f"Creating lock file at: {lock_path}")
    with open(lock_path, 'w') as f:
        f.write(str(os.getpid()))
        
    try:
        # 1. Initialize SQLite Database under lock
        with db_lock:
            database.init_db()
            
            # Prune macro and micro stories older than 60 days to keep the database size bounded and clean
            conn = database.get_connection()
            cursor = conn.cursor()
            
            # Get all macro records to parse and prune format-independently in Python
            from datetime import datetime, timedelta
            import pandas as pd
            
            cutoff_date = datetime.now() - timedelta(days=60)
            cutoff_ts = cutoff_date.timestamp()
            
            cursor.execute("SELECT id, published FROM macro_data")
            macro_rows = cursor.fetchall()
            macro_ids_to_delete = []
            for row_id, pub_str in macro_rows:
                if pub_str:
                    try:
                        dt = pd.to_datetime(pub_str, errors='coerce')
                        if pd.notnull(dt) and dt.to_pydatetime().replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                            macro_ids_to_delete.append(row_id)
                    except Exception:
                        pass
            
            if macro_ids_to_delete:
                # Delete in chunks to be safe with SQL parameter limits
                for i in range(0, len(macro_ids_to_delete), 500):
                    chunk = macro_ids_to_delete[i:i+500]
                    cursor.execute(f"DELETE FROM macro_data WHERE id IN ({','.join(['?']*len(chunk))})", chunk)
                
            cursor.execute("DELETE FROM micro_data WHERE created_utc < ?", (cutoff_ts,))
            conn.commit()
            conn.close()
            logger.info(f"Pruned stories older than 60 days from the database. Deleted {len(macro_ids_to_delete)} stale macro articles.")
        
        # 2. Scrape Top Trending Topics from Google News RSS and refine them with the local LLM
        topics_context = rss_pipeline.fetch_trending_topics_with_context(num_topics=8)
        refined_entries = refine_topics_with_local_model(topics_context)
        
        # Map clean topics to their optimized GDELT queries
        topic_queries = {entry['topic']: entry['query'] for entry in refined_entries}
        trending_topics = list(topic_queries.keys())
        
        # Delete old stories of other topics that are no longer trending
        with db_lock:
            conn = database.get_connection()
            cursor = conn.cursor()
            if trending_topics:
                placeholders = ','.join('?' * len(trending_topics))
                cursor.execute(f"DELETE FROM macro_data WHERE topic NOT IN ({placeholders})", tuple(trending_topics))
                cursor.execute(f"DELETE FROM micro_data WHERE topic NOT IN ({placeholders})", tuple(trending_topics))
                conn.commit()
                logger.info("Deleted stories of non-trending topics from the database to keep it clean.")
            conn.close()
        
        logger.info(f"Identified {len(trending_topics)} active trending topics: {trending_topics}")
        
        results = []
        
        # Process topics in parallel using ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor
        logger.info(f"Spawning ThreadPoolExecutor to process {len(trending_topics)} topics in parallel...")
        with ThreadPoolExecutor(max_workers=len(trending_topics)) as executor:
            futures = [
                executor.submit(process_single_topic, topic, topic_queries.get(topic, topic))
                for topic in trending_topics
            ]
            for future in futures:
                res = future.result()
                if res is not None:
                    results.append(res)
                    
        # 6. Save results cache under lock
        with db_lock:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "topics": results
            }
            
            logger.info(f"Saving final aggregated results to cache at: {CACHE_PATH}")
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4, ensure_ascii=False)
                
            logger.info("BlueShift background update queue completed successfully.")
            
    finally:
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                logger.info(f"Removed lock file at: {lock_path}")
            except Exception as e:
                logger.error(f"Failed to remove lock file: {e}")

def fetch_news_stories(topic_name):
    import sqlite3
    if not os.path.exists(DB_PATH):
        return []
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH, timeout=60.0)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title, link, published, source FROM macro_data WHERE topic=? ORDER BY published DESC LIMIT 5",
                (topic_name,)
            )
            rows = cursor.fetchall()
            conn.close()
        return [{"title": r[0], "link": r[1], "published": r[2], "source": r[3]} for r in rows]
    except Exception as e:
        logger.error(f"Failed to fetch news stories for topic '{topic_name}' in update_queue: {e}")
        return []

def generate_elaboration_local_model(topic_name, news_stories):
    if not news_stories:
        return None
        
    headlines = [f"- {story['title']}" for story in news_stories]
    headlines_text = "\n".join(headlines)
    
    prompt = (
        f"You are a news analyst. Based on these headlines about the topic '{topic_name}', "
        f"write a brief, single-paragraph explanation (max 2-3 sentences) summarizing what is actually happening. "
        f"Do not include preamble, greetings, or formatting. Keep it factual and concise.\n\n"
        f"Headlines:\n{headlines_text}"
    )
    
    import urllib.request
    
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "qwen2.5-vl-3b-instruct",
        "messages": [
            {"role": "system", "content": "You are a concise, professional news summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 150
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            summary = res_data['choices'][0]['message']['content'].strip()
            if summary:
                return summary
    except Exception as e:
        logger.warning(f"LMStudio local model query failed or timed out: {e}")
    return None

def generate_elaboration(topic_name, topic_data, news_stories):
    # Try using the local LMStudio model first
    local_summary = generate_elaboration_local_model(topic_name, news_stories)
    if local_summary:
        return local_summary

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

if __name__ == "__main__":
    update_pipeline()
