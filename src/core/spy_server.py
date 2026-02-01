import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime

# IMPORTS (Must exist)
try:
    from brain import judge_activity
    from system_control import mute_system_volume, kill_browser
    from audio_engine import speak
    from identity import load_identity, save_identity 
    from economy import process_transaction 
except ImportError as e:
    print(f"\n\033[91m[CRITICAL ERROR] Missing File: {e}\033[0m")
    print("Make sure brain.py, system_control.py, etc. are in src/core/")
    exit()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Reduce Flask logging spam
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- STATE ---
is_recovery_mode = False 
last_category = None

@app.route('/')
def index(): return "Katya Neural Link Active"

# --- IDENTITY HANDLERS ---
@socketio.on('connect')
def handle_connect():
    print("\n\033[96m[UI] HUD Connected via SocketIO\033[0m")
    user = load_identity()
    if user["is_initialized"]:
        emit('auth_success', user)
    else:
        emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    print(f"[UI] Creating Character: {data}")
    user = save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', user)

# --- CORE LOGIC: PROCESS ANY INPUT ---
def process_activity(url, title, source="SINGLE"):
    global is_recovery_mode, last_category

    # 1. JUDGE
    category, label = judge_activity(url, title) 
    category = category.upper() # PRODUCTIVE, DISTRACTION, NEUTRAL
    
    # 2. ECONOMY (2 seconds per tick)
    balance, change = process_transaction(category, 2)

    # 3. RECOVERY LOGIC
    if balance <= 0: is_recovery_mode = True
    elif balance >= 100: is_recovery_mode = False

    # 4. EMIT TO HUD
    socketio.emit('status_update', {
        'status': category,
        'domain': label,
        'balance': int(balance),
        'change': int(change),
        'locked': is_recovery_mode
    })

    # 5. CONSOLE LOGGING (Only if status changes)
    if category != last_category:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{source}] {timestamp} -> {category}: {label} (Bal: {int(balance)})")
        last_category = category

    # 6. PUNISHMENT
    if category == "DISTRACTION" and is_recovery_mode:
        print(f"\033[91m[PUNISH] Bankruptcy! Killing Browser.\033[0m")
        mute_system_volume()
        kill_browser()
        speak(f"Bankrupt. Earn {100 - int(balance)} credits to unlock.")

# --- ENDPOINT 1: OLD EXTENSION (Single Tab) ---
@app.route('/track', methods=['POST'])
def track_single():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '') # Might be empty on old extension
    if url: process_activity(url, title, source="SINGLE")
    return {"status": "logged"}

# --- ENDPOINT 2: NEW EXTENSION (Batch / God View) ---
@app.route('/track_batch', methods=['POST'])
def track_batch():
    data = request.json
    tabs = data.get('tabs', [])
    if not tabs: return {"status": "ignored"}

    # God View Logic: Find the worst tab
    target_url = ""
    target_title = ""
    has_distraction = False
    
    for tab in tabs:
        # Check every tab to find a distraction
        cat, _ = judge_activity(tab['url'], tab['title'])
        if cat.lower() == "distraction":
            has_distraction = True
            target_url = tab['url']   # Lock onto the bad tab
            target_title = tab['title']
            break # Found one, that's enough to punish
    
    # If no distraction, just use the active tab
    if not has_distraction:
        active = next((t for t in tabs if t['active']), tabs[0])
        target_url = active['url']
        target_title = active['title']

    process_activity(target_url, target_title, source="BATCH")
    return {"status": "processed"}

def start_server():
    print("--- SERVER STARTED on PORT 5000 ---")
    print("Waiting for Chrome Extension data...")
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_server()