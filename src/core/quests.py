import json
import os
from datetime import datetime

QUEST_FILE = "daily_quests.json"

# --- HELPER: Generates a Fresh Plan for TODAY ---
def get_default_plan():
    today_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "date": today_str,
        "quests": [
            {
                "id": "q1",
                "title": "Update LinkedIn",
                "priority": "HIGH",
                "keywords": ["linkedin.com"],
                "target_minutes": 5,
                "current_minutes": 0,
                "completed": False,
                "reward": 100
            },
            {
                "id": "q2",
                "title": "Job Applications",
                "priority": "HIGH",
                "keywords": ["linkedin.com/jobs", "naukri.com", "instahyre.com"],
                "target_minutes": 15,
                "current_minutes": 0,
                "completed": False,
                "reward": 300
            },
            {
                "id": "q3",
                "title": "Deep Work: Project",
                "priority": "MEDIUM",
                "keywords": ["localhost", "github.com", "stackoverflow.com"],
                "target_minutes": 60,
                "current_minutes": 0,
                "completed": False,
                "reward": 500
            }
        ],
        "all_complete": False
    }

def save_quests(data):
    with open(QUEST_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_quests():
    # 1. If file missing, create fresh plan
    if not os.path.exists(QUEST_FILE):
        new_plan = get_default_plan()
        save_quests(new_plan)
        return new_plan
    
    try:
        with open(QUEST_FILE, 'r') as f: 
            data = json.load(f)

        # 2. DATE CHECK (The Fix)
        # Does the file's date match Today?
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if data.get("date") != today_str:
            print(f"[QUESTS] New Day Detected ({today_str}). Resetting Protocol...")
            # It's a new day! WIPE IT.
            fresh_plan = get_default_plan()
            save_quests(fresh_plan)
            return fresh_plan

        return data

    except:
        # If file is corrupt, reset
        return get_default_plan()

def update_quest_progress(url, duration_seconds, brain_label=""):
    data = load_quests()
    
    current_priority = next((q for q in data["quests"] if not q["completed"]), None)
    
    if not current_priority:
        if not data.get("all_complete"):
            data["all_complete"] = True 
            save_quests(data)
        return 0, "FREE_FLOW"

    clean_url = url.lower()

    # --- THE BUG KILLER: Fuzzy Match Logic ---
    # Instead of looking for an exact path match, we just check if the main word
    # (like "linkedin") exists in whatever URL string got passed here.
    match_found = any(
    k in clean_url
    for k in current_priority.get("keywords", [])
)


    if match_found:
        minutes_added = duration_seconds / 60.0
        current_priority["current_minutes"] += minutes_added
        
        reward = 0
        message = f"QUEST: {current_priority['title']} ({int(current_priority['current_minutes'])}/{current_priority['target_minutes']}m)"

        if current_priority["current_minutes"] >= current_priority["target_minutes"]:
            current_priority["completed"] = True
            reward = current_priority["reward"]
            message = f"🏆 UNLOCKED NEXT: {current_priority['title']} Done! (+{reward})"
        
        save_quests(data)
        return reward, message

    else:
        return 0, f"⛔ BLOCKED: Finish '{current_priority['title']}' First!"