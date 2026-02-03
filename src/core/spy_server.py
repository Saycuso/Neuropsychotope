import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime

# IMPORTS
try:
    from brain import judge_activity
    from system_control import mute_system_volume, kill_browser
    from audio_engine import speak
    from identity import load_identity, save_identity 
    from economy import process_transaction 
    from quests import update_quest_progress, load_quests # <--- NEW IMPORT
except ImportError as e:
    print(f"[CRITICAL] Missing: {e}")
    exit()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")
log = logging.getLogger('werkzeug'); log.setLevel(logging.ERROR)

is_recovery_mode = False 
last_category = None
last_label = None

@app.route('/')
def index(): return "Katya Neural Link Active"

# --- HUD ---
@socketio.on('connect')
def handle_connect():
    print("[UI] HUD Connected")
    user = load_identity()
    if user["is_initialized"]: emit('auth_success', user)
    else: emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', load_identity())

# --- MAIN LOGIC ---
def process_logic(tabs_list):
    global is_recovery_mode, last_category, last_label

    # 1. GOD VIEW SCAN
    has_distraction = False
    has_productive = False
    target_url = ""
    active_display = "Idle"

    # Find what user is looking at (for display)
    active_tab = next((t for t in tabs_list if t['active']), tabs_list[0])
    _, active_display = judge_activity(active_tab['url'], active_tab['title'])
    
    # Priority Scan
    for tab in tabs_list:
        cat, _ = judge_activity(tab['url'], tab['title'])
        if cat.lower() == "distraction": 
            has_distraction = True
            active_display = "DISTRACTION DETECTED"
        if cat.lower() == "productive": 
            has_productive = True
            if not target_url: target_url = tab['url'] # Grab productive URL for quest check

    # 2. DECISION ENGINE
    final_category = "NEUTRAL"
    balance = 0
    change = 0

    if has_distraction:
        final_category = "DISTRACTION"
        balance, change = process_transaction("DISTRACTION", 2)
        
    elif has_productive:
        final_category = "PRODUCTIVE"
        
        # --- QUEST CHECK ---
        q_reward, q_msg = update_quest_progress(target_url, 2)
        
        if q_msg == "FREE_FLOW":
            # All quests done -> Standard Pay
            active_display = "✨ FREE FLOW: " + active_display
            balance, change = process_transaction("PRODUCTIVE", 2)
            
        elif q_msg == "NO_QUEST_MATCH":
            # Productive, but NOT in Queue -> No Pay!
            active_display = "⚠️ QUEUE BLOCKED: " + active_display
            balance, change = process_transaction("NEUTRAL", 2) # Cost of idling
            
        else:
            # Working on Quest -> Progressing...
            active_display = q_msg
            if q_reward > 0:
                # Quest Completed!
                balance, change = process_transaction("PRODUCTIVE", 0, bonus=q_reward)
                speak(f"Quest Completed. {q_reward} credits earned.")
            else:
                # Just progress, small maintenance cost
                balance, change = process_transaction("NEUTRAL", 2)

    else:
        # Neutral/Idle
        balance, change = process_transaction("NEUTRAL", 2)

    # 3. RECOVERY
    if balance <= 0: is_recovery_mode = True
    elif balance >= 100: is_recovery_mode = False

    # 4. EMIT
    # 1. Load the latest quest data
    quest_data = load_quests()
    current_quests = quest_data.get("quests", [])

    # 2. Add 'quests' to the emission
    socketio.emit('status_update', {
        'status': final_category,
        'domain': active_display,
        'balance': int(balance),
        'change': int(change),
        'locked': is_recovery_mode,
        'quests': current_quests  # <--- NEW FIELD
    })

    # 5. PUNISH
    if final_category == "DISTRACTION" and is_recovery_mode:
        mute_system_volume()
        kill_browser()
        speak("Bankrupt.")

    # 6. LOGGING
    if final_category != last_category or active_display != last_label:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[QUEST] {timestamp} | {final_category} -> {active_display}")
        last_category = final_category
        last_label = active_display

@app.route('/track_batch', methods=['POST'])
def track_batch():
    data = request.json
    return {"status": "processed"} if not data else (process_logic(data.get('tabs', [])), {"status": "ok"})[1]

# Legacy Support
@app.route('/track', methods=['POST'])
def track_legacy():
    data = request.json
    fake_list = [{'url': data.get('url'), 'title': data.get('title', ''), 'active': True}]
    process_logic(fake_list)
    return {"status": "logged"}

def start_server():
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_server()