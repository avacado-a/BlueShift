import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_MPULSE_ROOT = os.path.dirname(_BACKEND_DIR)
if _MPULSE_ROOT not in sys.path:
    sys.path.insert(0, _MPULSE_ROOT)

from BlueShift.backend import database
from BlueShift.backend import mpulse_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlueShift.refresh_cache")

DB_PATH = database.DB_PATH
CACHE_PATH = os.path.join(_BACKEND_DIR, 'results_cache.json')
W2V_MODEL_PATH = os.path.join(_BACKEND_DIR, 'backend', 'current_context.model')

def refresh_research_results():
    topics = ["FIRST Robotics Competition", "NVIDIA Blackwell", "The Middle East"]
    results = []
    
    logger.info(f"🚀 Refreshing Research Cache for topics: {topics}")
    
    for topic in topics:
        try:
            logger.info(f"Processing '{topic}'...")
            res = mpulse_engine.analyze_topic(
                topic=topic,
                db_path=DB_PATH,
                w2v_path=W2V_MODEL_PATH,
                epochs=100 # Fast run for the dashboard demo
            )
            
            if res.get('status') == 'success':
                # Generate a simple elaboration if not present
                if 'elaboration' not in res:
                    res['elaboration'] = f"Academic baseline for {topic}. Predicting trend volume based on 3-year multi-resolution fusion."
                results.append(res)
            else:
                logger.error(f"Failed to analyze {topic}: {res.get('error_message')}")
        except Exception as e:
            logger.error(f"Exception analyzing {topic}: {e}")

    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "topics": results
    }
    
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=4, ensure_ascii=False)
    
    logger.info(f"✅ Cache refreshed successfully with {len(results)} topics.")

if __name__ == "__main__":
    refresh_research_results()
