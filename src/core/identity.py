# src/core/identity.py
import json
import os

IDENTITY_FILE = "user_identity.json"

DEFAULT_IDENTITY = {
    "name": "Unknown User",
    "profession": "Novice",
    "main_quest": "Survive",
    "is_initialized": False
}

def load_identity():
    if not os.path.exists(IDENTITY_FILE):
        return DEFAULT_IDENTITY
    try:
        with open(IDENTITY_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_IDENTITY

def save_identity(name, profession, quest):
    data = {
        "name": name,
        "profession": profession, # e.g. "Full Stack Developer"
        "main_quest": quest,      # e.g. "Get ₹10 LPA Job"
        "is_initialized": True
    }
    with open(IDENTITY_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[IDENTITY]: Neural Link Established for {name} ({profession}).")
    return data