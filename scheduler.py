import time
import subprocess
import sys
import os
from datetime import datetime, timedelta

def run_at_midnight():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "update_queue.py"))
    python_path = sys.executable
    print(f"[{datetime.now()}] Starting scheduled update queue...")
    
    # Inline python snippet that monkeypatches gdeltdoc.GdeltDoc.article_search and then runs update_queue.py
    patch_code = (
        "import sys\n"
        "import time\n"
        "import gdeltdoc\n\n"
        "original_search = gdeltdoc.GdeltDoc.article_search\n\n"
        "def patched_article_search(self, filters):\n"
        "    retries = 60\n"
        "    while retries > 0:\n"
        "        try:\n"
        "            return original_search(self, filters)\n"
        "        except Exception as e:\n"
        "            err_name = type(e).__name__.lower()\n"
        "            err_msg = str(e).lower()\n"
        "            if 'ratelimit' in err_name or 'ratelimit' in err_msg or 'max retries' in err_msg or 'connection' in err_msg:\n"
        "                print(f'[GDELT PATCH] Rate limit/connection issue hit: {err_name}. Sleeping 65 seconds before retry (retries left: {retries-1})...', flush=True)\n"
        "                time.sleep(65)\n"
        "                retries -= 1\n"
        "            else:\n"
        "                raise e\n"
        "    return original_search(self, filters)\n\n"
        "gdeltdoc.GdeltDoc.article_search = patched_article_search\n\n"
        "script_file = sys.argv[1]\n"
        "sys.argv = [script_file]\n"
        "import runpy\n"
        "runpy.run_path(script_file, run_name='__main__')\n"
    )
    
    # Run the update queue process and wait for it
    subprocess.run([python_path, "-c", patch_code, script_path])

if __name__ == "__main__":
    print("M-PULSE Background Scheduler Started.")
    while True:
        now = datetime.now()
        # Calculate time until next midnight
        next_run = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        sleep_seconds = (next_run - now).total_seconds()
        print(f"Next run scheduled at midnight ({next_run}). Sleeping for {sleep_seconds:.1f} seconds...")
        time.sleep(sleep_seconds)
        try:
            run_at_midnight()
        except Exception as e:
            print(f"Error running scheduled task: {e}")
        # Sleep 60 seconds to avoid double-triggering
        time.sleep(60)
