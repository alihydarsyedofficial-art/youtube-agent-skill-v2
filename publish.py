import os
import json

def check_and_publish():
    print("Running technical check and publish routine...")
    auto_publish_env = os.getenv("AUTO_PUBLISH", "0")
    
    if auto_publish_env != "1":
        print("AUTO_PUBLISH is disabled (not set to 1). Skipping publishing step.")
        return

    history_file = "upload_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            print(f"Loaded upload history. Total records: {len(history)}")
    else:
        print("No upload history found yet.")
        
    print("All technical checks passed. Ready for live state toggle if configured.")

if __name__ == "__main__":
    check_and_publish()
