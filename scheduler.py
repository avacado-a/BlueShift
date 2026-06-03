import time
import subprocess
import sys
import os
from datetime import datetime, timedelta

def run_update_queue():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "update_queue.py"))
    python_path = sys.executable
    print(f"[{datetime.now()}] Starting update queue...")
    
    # Run the update queue process directly and wait for it
    subprocess.run([python_path, script_path])

if __name__ == "__main__":
    print("M-PULSE Background Scheduler Started.")
    
    if "--runOnExecute" in sys.argv:
        print("Running update queue immediately on startup (--runOnExecute detected)...")
        try:
            run_update_queue()
        except Exception as e:
            print(f"Error running startup task: {e}")
            
    while True:
        now = datetime.now()
        # Calculate time until next midnight
        next_run = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        sleep_seconds = (next_run - now).total_seconds()
        print(f"Next run scheduled at midnight ({next_run}). Sleeping for {sleep_seconds:.1f} seconds...")
        time.sleep(sleep_seconds)
        try:
            run_update_queue()
        except Exception as e:
            print(f"Error running scheduled task: {e}")
        # Sleep 60 seconds to avoid double-triggering
        time.sleep(60)
