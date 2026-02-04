import json
import os
import time

ECONOMY_FILE = "user_economy.json"

# CONFIG: The "Prices" of life
RATES = {
    "PRODUCTIVE": 10,   # Earn 10 credits per minute (Base Wage)
    "DISTRACTION": -30, # Cost 30 credits per minute
    "NEUTRAL": 0       # Cost 1 credit per minute
}

DEFAULT_STATE = {
    "balance": 100,
    "lifetime_earnings": 0
}

def load_economy():
    if not os.path.exists(ECONOMY_FILE): return DEFAULT_STATE.copy()
    try:
        with open(ECONOMY_FILE, 'r') as f: return json.load(f)
    except: return DEFAULT_STATE.copy()

def save_economy(data):
    with open(ECONOMY_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- THE UPDATE IS HERE ---
def process_transaction(category, duration_seconds, bonus=0):
    """Calculates cost/pay based on time spent + bonuses"""
    state = load_economy()
    
    # Convert duration to minutes
    minutes = duration_seconds / 60.0
    
    # Calculate Rate
    rate = RATES.get(category, -1)
    
    # Formula: (Wage * Time) + Quest Bonus
    amount = (rate * minutes) + bonus
    
    # Update Balance
    state["balance"] += amount
    if amount > 0:
        state["lifetime_earnings"] += amount
        
    save_economy(state)
    
    return int(state["balance"]), int(amount)