import json
import os
import time

ECONOMY_FILE = "user_economy.json"

# CONFIG: The "Prices" of life
RATES = {
    "PRODUCTIVE": 10,   # Earn 10 credits per minute
    "DISTRACTION": -30, # Cost 60 credits per minute (Expensive!)
    "NEUTRAL": -1       # Slight cost for idling
}

DEFAULT_STATE = {
    "balance": 100,      # Start with a small buffer
    "lifetime_earnings": 0
}

def load_economy():
    if not os.path.exists(ECONOMY_FILE): return DEFAULT_STATE.copy()
    try:
        with open(ECONOMY_FILE, 'r') as f: return json.load(f)
    except: return DEFAULT_STATE.copy()

def save_economy(data):
    with open(ECONOMY_FILE, 'w') as f: json.dump(data, f, indent=4)

def process_transaction(category, duration_seconds):
    """Calculates cost/pay based on time spent"""
    state = load_economy()
    
    # Convert duration to minutes
    minutes = duration_seconds / 60.0
    
    # Calculate Rate
    rate = RATES.get(category, -1)
    amount = rate * minutes
    
    # Update Balance
    state["balance"] += amount
    if amount > 0:
        state["lifetime_earnings"] += amount
        
    save_economy(state)
    
    return int(state["balance"]), int(amount)