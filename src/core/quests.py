import json
import os
from datetime import datetime

QUEST_FILE = "daily_quests.json"

def load_quests():
    if not os.path.exists(QUEST_FILE): return {"quests": [], "all_complete": False}
    with open(QUEST_FILE, 'r') as f: return json.load(f)

def save_quests(data):
    with open(QUEST_FILE, 'w') as f: json.dump(data, f, indent=4)

def update_quest_progress(url, duration_seconds):
    """
    Returns: (reward_earned, message_to_display)
    """
    data = load_quests()
    
    # 1. Check if we are already in "Free Flow" (All Done)
    if data.get("all_complete", False):
        return 0, "FREE_FLOW" # Signal to Spy Server to use Standard Pay

    # 2. Find matching active quest
    active_quest = None
    clean_url = url.lower()
    
    for quest in data["quests"]:
        if quest["completed"]: continue
        
        # Check if URL matches quest keywords
        if any(k in clean_url for k in quest["keywords"]):
            active_quest = quest
            break # Found the priority task!
    
    if not active_quest:
        return 0, "NO_QUEST_MATCH" # Productive but not in Quest Queue

    # 3. Update Progress
    # Convert seconds to minutes (partial)
    progress = duration_seconds / 60.0
    active_quest["current_minutes"] += progress
    
    reward = 0
    message = f"Quest: {active_quest['title']} ({int(active_quest['current_minutes'])}/{active_quest['target_minutes']}m)"

    # 4. Check Completion
    if active_quest["current_minutes"] >= active_quest["target_minutes"]:
        active_quest["completed"] = True
        reward = active_quest["reward"]
        message = f"🏆 COMPLETED: {active_quest['title']} (+{reward})"
        
        # Check if ALL are done
        incomplete = [q for q in data["quests"] if not q["completed"]]
        if not incomplete:
            data["all_complete"] = True
            message = "🌟 ALL DAILIES COMPLETE! FREE FLOW UNLOCKED."

    save_quests(data)
    return reward, message