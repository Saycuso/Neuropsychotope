import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from brain import judge_activity  # Requires updated brain.py
from system_control import mute_system_volume, kill_browser
from audio_engine import speak
from identity import load_identity, save_identity 
from economy import process_transaction

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

is_recovery_mode = False 
last_category = None

# --- PART 1: IDENTITY (Unchanged) ---
@app.route('/')
def index(): return "Katya Neural Link Active"

@socketio.on('connect')
def handle_connect():
    user = load_identity()
    if user["is_initialized"]: emit('auth_success', user)
    else: emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', load_identity())

# --- PART 2: THE BATCH TRACKER (NEW LOGIC) ---
@app.route('/track_batch', methods=['POST'])
def track_batch():
    global is_recovery_mode, last_category

    data = request.json
    tabs = data.get('tabs', [])
    
    if not tabs: return {"status": "ignored"}
    
    # 1. ANALYZE ALL TABS
    has_distraction = False
    has_productive = False
    active_tab_label = "System Idle"
    
    for tab in tabs:
        # Judge each tab
        cat, label = judge_activity(tab['url'], tab['title'])
        
        if tab['active']: 
            active_tab_label = label # Save what user is looking at for the HUD

        if cat == "distraction":
            has_distraction = True
        elif cat == "productive":
            has_productive = True

    # 2. APPLY THE HIERARCHY RULE
    # Distraction overrides Productivity (You can't code with Netflix open)
    final_category = "NEUTRAL"
    
    if has_distraction:
        final_category = "DISTRACTION"
        active_tab_label = "Distraction Detected" # Override label to shame user
    elif has_productive:
        final_category = "PRODUCTIVE"
    
    # 3. ECONOMY (One Price Rule)
    # We assume 2 seconds per ping (since interval is 2000ms)
    duration = 2 
    balance, change = process_transaction(final_category.upper(), duration)

    # 4. RECOVERY LOGIC
    if balance <= 0: is_recovery_mode = True
    elif balance >= 100: is_recovery_mode = False

    # 5. EMIT TO HUD
    socketio.emit('status_update', {
        'status': final_category,
        'domain': active_tab_label,
        'balance': int(balance),
        'change': int(change),
        'locked': is_recovery_mode
    })

    # 6. ENFORCEMENT
    if final_category == "DISTRACTION" and is_recovery_mode:
        print(f"[BLOCKED] Balance: {balance}. Recovery Target: 100.")
        mute_system_volume()
        kill_browser()
        speak(f"Account frozen. Earn {100 - int(balance)} credits to unlock leisure.")

    return {"status": "processed"}

def start_server():
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_server()