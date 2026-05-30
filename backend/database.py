import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'blueshift.db'))

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    logger.info(f"Initializing SQLite database at: {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            title TEXT,
            link TEXT,
            published TEXT,
            clean_text TEXT,
            source TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS micro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            author TEXT,
            clean_text TEXT,
            created_utc REAL,
            source TEXT,
            type TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            rating INTEGER,
            comments TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database schema initialized successfully.")

def insert_feedback(name: str, role: str, rating: int, comments: str) -> None:
    """Inserts a user feedback record into the database."""
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO feedback (name, role, rating, comments, timestamp) VALUES (?,?,?,?,?)',
        (name, role, rating, comments, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def insert_macro(topic: str, title: str, link: str, published: str, clean_text: str, source: str) -> bool:
    """Inserts a macro article if its link is unique. Returns True if inserted, False if duplicate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM macro_data WHERE link = ?", (link,))
    if cursor.fetchone() is None:
        cursor.execute(
            'INSERT INTO macro_data (topic, title, link, published, clean_text, source) VALUES (?,?,?,?,?,?)',
            (topic, title, link, published, clean_text, source)
        )
        conn.commit()
        inserted = True
    else:
        inserted = False
    conn.close()
    return inserted

def insert_micro(topic: str, author: str, clean_text: str, created_utc: float, source: str, type_val: str) -> bool:
    """Inserts a micro post if unique. Returns True if inserted, False if duplicate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM micro_data WHERE topic = ? AND author = ? AND created_utc = ? AND clean_text = ?",
        (topic, author, created_utc, clean_text)
    )
    if cursor.fetchone() is None:
        cursor.execute(
            'INSERT INTO micro_data (topic, author, clean_text, created_utc, source, type) VALUES (?,?,?,?,?,?)',
            (topic, author, clean_text, created_utc, source, type_val)
        )
        conn.commit()
        inserted = True
    else:
        inserted = False
    conn.close()
    return inserted

def fetch_topic_data(topic: str, db_path: str = None):
    """
    Fetches clean text and timestamp data for macro and micro streams for a given topic.
    Returns:
        macro_df (pd.DataFrame): DataFrame with columns ['ts', 'text']
        micro_df (pd.DataFrame): DataFrame with columns ['ts', 'text']
    """
    import pandas as pd
    actual_db_path = db_path if db_path is not None else DB_PATH
    if not os.path.exists(actual_db_path):
        raise FileNotFoundError(f"Database {actual_db_path} not found.")
        
    conn = sqlite3.connect(actual_db_path)
    try:
        macro_df = pd.read_sql_query(
            "SELECT published as ts, clean_text as text FROM macro_data WHERE topic=?", 
            conn, 
            params=(topic,)
        )
        micro_df = pd.read_sql_query(
            "SELECT created_utc as ts, clean_text as text FROM micro_data WHERE topic=?", 
            conn, 
            params=(topic,)
        )
    finally:
        conn.close()
        
    return macro_df, micro_df

