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
    from economy import process_transaction, calculate_level_threshold
    from quests import update_quest_progress, load_quests
except ImportError as e:
    print(f"[CRITICAL] Missing: {e}")
    exit()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# SILENCE FLASK LOGS
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

is_recovery_mode = False 
last_category = None
last_label = None

# --- NEW: MEMORY TO PREVENT SPAM ---
active_streams = {} 
last_payload = {} # <--- Stores the last sent data to compare

@app.route('/')
def index(): return "Katya Neural Link Active"

# --- HUD ---
@socketio.on('connect')
def handle_connect():
    # print("[UI] HUD Connected") # <--- Silenced
    user = load_identity()
    if user["is_initialized"]: emit('auth_success', user)
    else: emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', load_identity())

# --- MAIN LOGIC ---
def process_logic(tabs_list):
    global is_recovery_mode, last_category, last_label, last_payload

    has_distraction = False
    has_productive = False
    target_url = ""
    active_display = "Idle"

    # MERGED LOGIC
    priority_tab = None
    
    for tab in tabs_list:
        cat, label = judge_activity(tab['url'], tab['title'])
        
        if cat.lower() == "distraction": 
            has_distraction = True
            priority_tab = tab 
        if cat.lower() == "productive": 
            has_productive = True
            if not target_url: target_url = tab['url']
            if not has_distraction: priority_tab = tab 
        
        if tab['active'] and not priority_tab:
            priority_tab = tab

    if priority_tab:
        _, active_display = judge_activity(priority_tab['url'], priority_tab['title'])
        if has_distraction: active_display = "DISTRACTION DETECTED"

    # DECISION ENGINE
    final_category = "NEUTRAL"
    balance = 0
    change = 0
    xp = 0
    level = 1
    levelup_bonus = 0

    if has_distraction:
        final_category = "DISTRACTION"
        balance, change, xp, level, levelup_bonus = process_transaction("DISTRACTION", 2)
        
    elif has_productive:
        final_category = "PRODUCTIVE"
        
        # PASS LABEL TO QUESTS
        q_reward, q_msg = update_quest_progress(target_url, 2, active_display)
        
        if q_msg == "FREE_FLOW":
            active_display = "✨ FREE FLOW: " + active_display
            balance, change, xp, level, levelup_bonus = process_transaction("PRODUCTIVE", 2)
            
        elif "BLOCKED" in q_msg or q_msg == "NO_QUEST_MATCH":
            active_display = "⚠️ " + q_msg
            balance, change, xp, level, levelup_bonus = process_transaction("NEUTRAL", 2) 
            
        else:
            active_display = q_msg
            if q_reward > 0:
                balance, change, xp, level, levelup_bonus = process_transaction("PRODUCTIVE", 0, bonus=q_reward)
                speak(f"Quest Complete. {q_reward} credits earned.")
            else:
                balance, change, xp, level, levelup_bonus = process_transaction("QUEST_ACTIVE", 2) 

    else:
        balance, change, xp, level, levelup_bonus = process_transaction("NEUTRAL", 2)

    if levelup_bonus > 0:
        speak(f"Level Up! You are now Level {level}. {levelup_bonus} credits awarded.")
        active_display = f"🌟 LEVEL UP! (+{levelup_bonus})"

    if balance <= 0: is_recovery_mode = True
    elif balance >= 100: is_recovery_mode = False

    quest_data = load_quests()
    next_xp_goal = calculate_level_threshold(level)
    
    # --- SMART EMIT: ONLY SEND IF CHANGED ---
    current_payload = {
        'status': final_category,
        'domain': active_display,
        'balance': balance,
        'change': change,
        'locked': is_recovery_mode,
        'quests': quest_data.get("quests", []),
        'xp': xp,                
        'level': level,          
        'next_level_xp': next_xp_goal 
    }

    # Compare dictionaries (ignores order)
    if current_payload != last_payload:
        socketio.emit('status_update', current_payload)
        last_payload = current_payload
        
        # LOGGING (Optional: Only print on status change to keep terminal clean)
        # if final_category != last_category or active_display != last_label:
        #    timestamp = datetime.now().strftime("%H:%M:%S")
        #    print(f"[QUEST] {timestamp} | {final_category} -> {active_display}")

    last_category = final_category
    last_label = active_display

    if final_category == "DISTRACTION" and is_recovery_mode:
        mute_system_volume()
        kill_browser()
        speak("Bankrupt.")

@app.route('/track_batch', methods=['POST'])
def track_batch():
    data = request.json
    if not data: return {"status": "ignored"}

    client_id = data.get('client_id', 'unknown')
    
    active_streams[client_id] = {
        'tabs': data.get('tabs', []),
        'ts': time.time()
    }

    merged_tabs = []
    cleanup_ids = []
    now = time.time()

    for cid, stream in active_streams.items():
        if now - stream['ts'] > 5:
            cleanup_ids.append(cid)
        else:
            merged_tabs.extend(stream['tabs'])
    
    for cid in cleanup_ids:
        del active_streams[cid]

    process_logic(merged_tabs)
    
    return {"status": "ok"}

@app.route('/track', methods=['POST'])
def track_legacy():
    data = request.json
    fake_list = [{'url': data.get('url'), 'title': data.get('title', ''), 'active': True}]
    active_streams['legacy'] = {'tabs': fake_list, 'ts': time.time()}
    process_logic(fake_list)
    return {"status": "logged"}

def start_server():
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_server()