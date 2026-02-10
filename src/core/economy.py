import json
import os
import math

ECONOMY_FILE = "user_economy.json"

# CONFIG: The "Prices" of life
RATES = {
    "PRODUCTIVE": 10,    # 10 XP/min
    "DISTRACTION": -30,  # No XP
    "NEUTRAL": 0,        # <--- FIXED: 0 Cost (No Drain)
    "QUEST_ACTIVE": 0    # 0 Cost (No Drain while working)
}

DEFAULT_STATE = {
    "balance": 100,
    "lifetime_earnings": 0,
    "xp": 0,       # RPG Stat
    "level": 1     # RPG Stat
}

def load_economy():
    if not os.path.exists(ECONOMY_FILE): return DEFAULT_STATE.copy()
    try:
        with open(ECONOMY_FILE, 'r') as f: 
            data = json.load(f)
            # Migration: Add missing keys if upgrading from old version
            if "xp" not in data: data["xp"] = 0
            if "level" not in data: data["level"] = 1
            return data
    except: return DEFAULT_STATE.copy()

def save_economy(data):
    with open(ECONOMY_FILE, 'w') as f: json.dump(data, f, indent=4)

def calculate_level_threshold(level):
    # RPG Formula: Level 2 needs 500 XP, Level 3 needs 1200 XP...
    return int(500 * (level ** 1.5))

def process_transaction(category, duration_seconds, bonus=0):
    """
    Returns: (balance, change, xp, level, level_up_reward)
    """
    state = load_economy()
    
    minutes = duration_seconds / 60.0
    rate = RATES.get(category, 0)
    
    # 1. MONEY LOGIC
    amount = (rate * minutes) + bonus
    state["balance"] += amount
    if amount > 0:
        state["lifetime_earnings"] += amount

    # 2. XP LOGIC (Only goes UP)
    # You earn XP for Productive time, Active Quests, and Bonuses
    xp_gain = 0
    if category in ["PRODUCTIVE", "QUEST_ACTIVE"] or bonus > 0:
        # Base XP: 10 XP per minute of real work
        base_xp = 10 * minutes
        # Bonus XP: Equal to the cash bonus (e.g. 300 credits = 300 XP)
        xp_gain = base_xp + bonus
        state["xp"] += xp_gain

    # 3. LEVEL UP LOGIC
    level_up_reward = 0
    next_threshold = calculate_level_threshold(state["level"])
    
    if state["xp"] >= next_threshold:
        state["level"] += 1
        # STIMULUS CHECK: Level * 500 Credits
        level_up_reward = state["level"] * 500
        state["balance"] += level_up_reward
        print(f"🌟 LEVEL UP! Now Level {state['level']}. Reward: +{level_up_reward}")

    save_economy(state)
    
    # Return everything so the HUD can show it
    return (
        int(state["balance"]), 
        int(amount), 
        int(state["xp"]), 
        int(state["level"]), 
        int(level_up_reward)
    )