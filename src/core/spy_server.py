import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from brain import judge_activity  # 👈 Make sure brain.py has this function!
from system_control import mute_system_volume, kill_browser
from audio_engine import speak
from identity import load_identity, save_identity 
from economy import process_transaction # 👈 Requires economy.py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- STATE ---
# False = Normal Mode (Can spend credits)
# True  = Recovery Mode (Locked until balance >= 100)
is_recovery_mode = False 
last_category = None

# --- PART 1: IDENTITY (PRESERVED) ---
@app.route('/')
def index():
    return "Katya Neural Link Active"

@socketio.on('connect')
def handle_connect():
    print("[CLIENT CONNECTED]")
    user = load_identity()
    if user["is_initialized"]:
        # User exists -> Send to Dashboard
        emit('auth_success', user)
    else:
        # New User -> Trigger Setup
        emit('trigger_setup', {"message": "IDENTITY_NOT_FOUND"})

@socketio.on('create_identity')
def handle_creation(data):
    print(f"[CREATING CHARACTER]: {data}")
    user = save_identity(data['name'], data['profession'], data['quest'])
    emit('auth_success', user)

# --- PART 2: THE TRACKER (ECONOMY MERGED) ---
@app.route('/track', methods=['POST'])
def track_activity():
    global is_recovery_mode, last_category

    data = request.json
    url = data.get('url', '')
    title = data.get('title', '') # 👈 Your Extension must send this!
    
    if not url: return {"status": "ignored"}
    
    # 1. JUDGE (Context-Aware)
    # Uses Profession + Title to decide if it's productive
    category, label = judge_activity(url, title) 
    category = category.upper() # PRODUCTIVE, DISTRACTION, NEUTRAL
    
    # 2. ECONOMY (The "Wage" System)
    # We assume 5 seconds per ping (standard for extensions)
    duration = 5 
    balance, change = process_transaction(category, duration)

    # 3. RECOVERY LOGIC (The Hysteresis Loop)
    # If you hit 0, you are locked until you save up 100.
    if balance <= 0:
        is_recovery_mode = True
    elif balance >= 100:
        is_recovery_mode = False

    # 4. EMIT TO HUD
    socketio.emit('status_update', {
        'status': category,
        'domain': label,
        'balance': int(balance),
        'change': int(change),
        'locked': is_recovery_mode # 👈 React can turn the UI RED if this is True
    })

    # 5. CONSOLE LOGGING (Cleaner)
    if category != last_category:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{category}] {timestamp} - {label} (Bal: {int(balance)})")
        last_category = category

    # 6. ENFORCEMENT (The Recovery Gatekeeper)
    if category == "DISTRACTION":
        if is_recovery_mode:
            # SCENARIO: User is bankrupt and trying to slack off -> BLOCK
            print(f"[BLOCKED] Balance: {balance}. Recovery Target: 100.")
            mute_system_volume()
            kill_browser()
            speak(f"Account frozen. Earn {100 - int(balance)} credits to unlock leisure.")
        
        # SCENARIO: Normal Mode (User has funds)
        # We DO NOT block. We just let the economy drain their funds.
        # Once funds hit 0, 'is_recovery_mode' flips to True, and the NEXT ping blocks them.

    return {"status": "logged"}

def start_server():
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_server()