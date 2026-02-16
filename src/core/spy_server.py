import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime

# --- FIXED IMPORTS ---
try:
    from brain import judge_activity
    from system_control import mute_system_volume, kill_browser
    from audio_engine import speak
    from identity import load_identity, save_identity 
    # Added load_economy here!
    from economy import process_transaction, calculate_level_threshold, load_economy 
    from quests import update_quest_progress, load_quests
except ImportError as e:
    print(f"[CRITICAL] Missing: {e}")
    # Don't just pass, exit if imports fail so we know what's broken!
    exit()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 1. SILENCE LOGS (Stops Terminal Spam)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

is_recovery_mode = False 
active_streams = {} 
last_payload = {} # <--- Stores previous state to prevent re-renders

@app.route('/')
def index(): return "Katya Neural Link Active"

# --- HUD ---
@socketio.on('connect')
def handle_connect():
    global last_payload
    user = load_identity()
    
    if user.get("is_initialized", False): 
        emit('auth_success', user)
        
        # --- SEND INITIAL STATE IMMEDIATELY ON REFRESH ---
        if last_payload:
            # If server already has data, send it instantly
            emit('status_update', last_payload)
        else:
            # If server just started, load directly from files
            eco = load_economy()  
            q_data = load_quests()
            
            initial_payload = {
                'status': "NEUTRAL",
                'domain': "SYSTEM READY",
                'balance': eco.get("balance", 100),
                'change': 0,
                'locked': eco.get("balance", 100) <= 0,
                'quests': q_data.get("quests", []),
                'xp': eco.get("xp", 0),                
                'level': eco.get("level", 1),          
                'next_level_xp': calculate_level_threshold(eco.get("level", 1)) 
            }
            emit('status_update', initial_payload)
            last_payload = initial_payload
            
    else: 
        emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', load_identity())

# --- HELPER: SORT TABS BY IMPORTANCE (Stops Flickering) ---
def get_highest_priority_tab(tabs_list):
    best_tab = None
    best_score = -1 

    for tab in tabs_list:
        cat, label = judge_activity(tab['url'], tab['title'])
        
        score = 0
        if cat.lower() == "productive": score = 1
        if cat.lower() == "distraction": score = 2 
        
        if score > best_score:
            best_score = score
            best_tab = tab
            
    return best_tab if best_tab else (tabs_list[0] if tabs_list else None)

# --- MAIN LOGIC ---
def process_logic(tabs_list):
    global is_recovery_mode, last_payload

    if not tabs_list: return

    # 1. SELECT THE TRUE TAB
    target_tab = get_highest_priority_tab(tabs_list)
    if not target_tab: return

    target_url = target_tab['url']
    target_title = target_tab['title']
    
    # 2. JUDGE IT
    cat, active_display = judge_activity(target_url, target_title)
    
    final_category = "NEUTRAL"
    balance = 0
    change = 0
    xp = 0
    level = 1
    levelup_bonus = 0

    # 3. CALCULATE ECONOMY
    if cat == "distraction":
        final_category = "DISTRACTION"
        active_display = "DISTRACTION DETECTED"
        balance, change, xp, level, levelup_bonus = process_transaction("DISTRACTION", 2)
        
    elif cat == "productive":
        final_category = "PRODUCTIVE"
        
        # --- SMART QUEST UPDATE ---
        try:
            q_reward, q_msg = update_quest_progress(target_url, 2, active_display)
        except TypeError:
            q_reward, q_msg = update_quest_progress(target_url, 2)
        
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

    # 4. LEVEL UP
    if levelup_bonus > 0:
        speak(f"Level Up! Level {level}.")
        active_display = f"🌟 LEVEL UP! (+{levelup_bonus})"

    if balance <= 0: is_recovery_mode = True
    elif balance >= 100: is_recovery_mode = False

    quest_data = load_quests()
    next_xp_goal = calculate_level_threshold(level)
    
    # 5. SMART EMIT (Debouncing)
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

    if current_payload != last_payload:
        socketio.emit('status_update', current_payload)
        last_payload = current_payload

    # 6. PUNISHMENT
    if final_category == "DISTRACTION" and is_recovery_mode:
        mute_system_volume()
        kill_browser()

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
    
    for cid in cleanup_ids: del active_streams[cid]

    process_logic(merged_tabs)
    return {"status": "ok"}

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