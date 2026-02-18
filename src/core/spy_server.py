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
    from economy import (
        process_transaction,
        calculate_level_threshold,
        load_economy
    )
    from quests import update_quest_progress, load_quests
except ImportError as e:
    print(f"[CRITICAL] Missing: {e}")
    exit()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# SILENCE FLASK LOGS
logging.getLogger('werkzeug').setLevel(logging.ERROR)

is_recovery_mode = False
last_category = None
last_label = None
last_payload = {}
active_streams = {}

# --------------------------------------------------
# SNAPSHOT BUILDER (THIS FIXES THE BLANK HUD BUG)
# --------------------------------------------------
def build_status_snapshot():
    global last_payload

    if last_payload:
        return last_payload

    economy = load_economy()
    quests = load_quests()

    level = int(economy.get("level", 1))
    balance = int(economy.get("balance", 0))

    return {
        'status': 'IDLE',
        'domain': 'SYSTEM READY',
        'balance': balance,
        'change': 0,
        'locked': balance <= 0,
        'quests': quests.get("quests", []),
        'xp': int(economy.get("xp", 0)),
        'level': level,
        'next_level_xp': calculate_level_threshold(level)
    }

@app.route('/')
def index():
    return "Katya Neural Link Active"

# --------------------------------------------------
# HUD SOCKETS
# --------------------------------------------------
@socketio.on('connect')
def handle_connect():
    user = load_identity()

    if user.get("is_initialized"):
        emit('auth_success', user)
        emit('status_update', build_status_snapshot())
    else:
        emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    save_identity(data['name'], data['profession'], data['quest'])
    user = load_identity()
    socketio.emit('auth_success', user)
    socketio.emit('status_update', build_status_snapshot())

# --------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------
def process_logic(tabs_list):
    global is_recovery_mode, last_category, last_label, last_payload

    has_distraction = False
    has_productive = False
    target_url = ""
    active_display = "Idle"
    priority_tab = None

    for tab in tabs_list:
        cat, label = judge_activity(tab['url'], tab['title'])

        if cat == "distraction":
            has_distraction = True
            priority_tab = tab

        elif cat == "productive":
            has_productive = True
            if not target_url:
                target_url = tab['url']
            if not has_distraction:
                priority_tab = tab

        if tab.get("active") and not priority_tab:
            priority_tab = tab

    if priority_tab:
        _, active_display = judge_activity(priority_tab['url'], priority_tab['title'])
        if has_distraction:
            active_display = "DISTRACTION DETECTED"

    final_category = "NEUTRAL"
    balance = change = xp = level = levelup_bonus = 0

    if has_distraction:
        final_category = "DISTRACTION"
        balance, change, xp, level, levelup_bonus = process_transaction("DISTRACTION", 2)

    elif has_productive:
        final_category = "PRODUCTIVE"
        q_reward, q_msg = update_quest_progress(target_url, 2, active_display)

        if q_msg == "FREE_FLOW":
            active_display = "✨ FREE FLOW"
            balance, change, xp, level, levelup_bonus = process_transaction("PRODUCTIVE", 2)

        elif "BLOCKED" in q_msg:
            active_display = q_msg
            balance, change, xp, level, levelup_bonus = process_transaction("NEUTRAL", 2)

        else:
            active_display = q_msg
            if q_reward > 0:
                balance, change, xp, level, levelup_bonus = process_transaction(
                    "PRODUCTIVE", 0, bonus=q_reward
                )
                speak(f"Quest complete. {q_reward} credits earned.")
            else:
                balance, change, xp, level, levelup_bonus = process_transaction("QUEST_ACTIVE", 2)

    else:
        balance, change, xp, level, levelup_bonus = process_transaction("NEUTRAL", 2)

    if levelup_bonus > 0:
        speak(f"Level Up! Level {level}.")
        active_display = f"🌟 LEVEL UP (+{levelup_bonus})"

    is_recovery_mode = balance <= 0

    quests = load_quests()
    payload = {
        'status': final_category,
        'domain': active_display,
        'balance': balance,
        'change': change,
        'locked': is_recovery_mode,
        'quests': quests.get("quests", []),
        'xp': xp,
        'level': level,
        'next_level_xp': calculate_level_threshold(level)
    }

    if payload != last_payload:
        socketio.emit('status_update', payload)
        last_payload = payload

    if final_category == "DISTRACTION" and is_recovery_mode:
        mute_system_volume()
        kill_browser()

# --------------------------------------------------
# TRACKING ENDPOINTS
# --------------------------------------------------
@app.route('/track_batch', methods=['POST'])
def track_batch():
    data = request.json or {}
    cid = data.get('client_id', 'unknown')

    active_streams[cid] = {
        'tabs': data.get('tabs', []),
        'ts': time.time()
    }

    merged = []
    now = time.time()
    for k, v in list(active_streams.items()):
        if now - v['ts'] > 5:
            del active_streams[k]
        else:
            merged.extend(v['tabs'])

    process_logic(merged)
    return {"status": "ok"}

@app.route('/track', methods=['POST'])
def track_legacy():
    data = request.json
    fake = [{'url': data.get('url'), 'title': data.get('title', ''), 'active': True}]
    process_logic(fake)
    return {"status": "logged"}

def start_server():
    t = threading.Thread(
        target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False)
    )
    t.daemon = True
    t.start()

if __name__ == "__main__":
    start_server()
