# spy_server.py
import time
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO # <--- NEW
from datetime import datetime
from config import PHASE_1_LIMIT, PHASE_2_LIMIT
from brain import judge_url
from system_control import mute_system_volume, kill_browser
from audio_engine import speak

app = Flask(__name__)
app.config['SECRET_KEY'] = 'katya_secret'
socketio = SocketIO(app, cors_allowed_origins="*") # <--- Allows React to connect

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# State
current_distraction_domain = None
distraction_start_time = None
punishment_phase = 0
last_category = None

@app.route('/track', methods=['POST'])
def track_activity():
    global current_distraction_domain, distraction_start_time, last_category, punishment_phase

    data = request.json
    url = data.get('url', '')
    if not url: return {"status": "ignored"}
    
    category, domain = judge_url(url)
    
    # 1. EMIT TO HUD (The Magic Line)
    # We send the status to React instantly
    socketio.emit('status_update', {'status': category.upper(), 'domain': domain})

    # Print Logic
    if category != last_category:
        timestamp = datetime.now().strftime("%H:%M:%S")
        if category == "distraction":
            print(f"\n\033[91m[VIOLATION] {timestamp} - {domain}\033[0m")
        elif category == "productive":
            print(f"\n\033[92m[FOCUS] {timestamp} - {domain}\033[0m")
        last_category = category

    # Punishment Logic
    if category == "distraction":
        if current_distraction_domain != domain:
            current_distraction_domain = domain
            distraction_start_time = time.time()
            punishment_phase = 0 
        
        if distraction_start_time:
            duration = time.time() - distraction_start_time
            
            # Send "Sanity" Level to HUD (100% -> 0%)
            sanity = max(0, 100 - int((duration / PHASE_2_LIMIT) * 100))
            socketio.emit('sanity_update', {'level': sanity})

            if duration > PHASE_1_LIMIT and punishment_phase == 0:
                mute_system_volume() 
                speak("Warning. Sanity Critical.")
                punishment_phase = 1

            if duration > PHASE_2_LIMIT and punishment_phase == 1:
                punishment_phase = 2
                kill_browser()
                speak("Terminating.")

    elif category == "productive":
        current_distraction_domain = None
        distraction_start_time = None
        punishment_phase = 0
        socketio.emit('sanity_update', {'level': 100}) # Restore Sanity

    return {"status": "logged"}

def start_server():
    # We use socketio.run instead of app.run
    server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()