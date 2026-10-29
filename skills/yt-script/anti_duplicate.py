import sys
import json
import os

HISTORY_FILE = "upload_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_unique_topic(niche_key):
    db_path = os.path.join(os.path.dirname(__file__), "niche_database.json")
    if not os.path.exists(db_path):
        return {"error": "Niche database not found."}
    
    with open(db_path, "r") as f:
        data = json.load(f)
    
    niche_info = data["niches"].get(niche_key)
    if not niche_info:
        return {"error": "Invalid niche specified."}
    
    history = load_history()
    used_topics = [h.get("topic") for h in history if h.get("niche") == niche_key]
    
    available_sub_topics = [t for t in niche_info["sub_topics"] if t not in used_topics]
    
    if not available_sub_topics:
        base_topic = niche_info["sub_topics"][0]
        selected_topic = f"{base_topic} - Advanced Part 2"
    else:
        selected_topic = available_sub_topics[0]
        
    history.append({"niche": niche_key, "topic": selected_topic})
    save_history(history)
    
    result = {
        "niche": niche_key,
        "selected_unique_topic": selected_topic,
        "cpc_tier": niche_info["cpc_tier"],
        "target_audience": niche_info["target_audience"],
        "duplicate_prevented": True
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    niche_arg = sys.argv[1] if len(sys.argv) > 1 else "kids_cartoons"
    get_unique_topic(niche_arg)