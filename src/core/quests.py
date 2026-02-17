import json
import os
from datetime import datetime

QUEST_FILE = "daily_quests.json"

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
                "smart_tags": ["Job Portal", "Career"], # <--- NEW: Brain Labels accepted
                "target_minutes": 5,
                "current_minutes": 0,
                "completed": False,
                "reward": 100
            },
            {
                "id": "q2",
                "title": "Job Applications",
                "priority": "HIGH",
                "keywords": ["naukri.com", "wellfound.com"], # Fallbacks
                "smart_tags": ["Job Portal", "Career"],      # <--- NEW: Accepts ANY job site
                "target_minutes": 15,
                "current_minutes": 0,
                "completed": False,
                "reward": 300
            },
            {
                "id": "q3",
                "title": "Deep Work: Project",
                "priority": "MEDIUM",
                "keywords": ["localhost", "github.com"],
                "smart_tags": ["Coding Resource", "Local Development", "Dev Tool"],
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
    if not os.path.exists(QUEST_FILE):
        new_plan = get_default_plan()
        save_quests(new_plan)
        return new_plan
    try:
        with open(QUEST_FILE, 'r') as f: data = json.load(f)
        today_str = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") != today_str:
            fresh_plan = get_default_plan()
            save_quests(fresh_plan)
            return fresh_plan
        return data
    except: return get_default_plan()

# --- THE UPDATE ---
def update_quest_progress(url, duration_seconds, brain_label=""):
    data = load_quests()
    
    current_priority = next((q for q in data["quests"] if not q["completed"]), None)
    
    if not current_priority:
        if not data.get("all_complete"):
            data["all_complete"] = True 
            save_quests(data)
        return 0, "FREE_FLOW"

    clean_url = url.lower()
    
    # 1. CHECK URL
    url_match = any(k in clean_url for k in current_priority.get("keywords", []))
    
    # 2. CHECK BRAIN LABEL (The Smart AI Match)
    label_match = False
    if brain_label:
        smart_tags = current_priority.get("smart_tags", [])
        # Check if "Job Portal" is inside the brain label (e.g. "Job Portal: unknown.com")
        label_match = any(tag.lower() in brain_label.lower() for tag in smart_tags)

    if url_match or label_match:
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