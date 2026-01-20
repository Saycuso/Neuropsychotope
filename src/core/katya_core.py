import os
import time
import json
import asyncio
import edge_tts
import sounddevice as sd
import wavio
import pygame
import threading
import logging
import random # <--- NEW: For unique audio files
import comtypes
from flask import Flask, request
from datetime import datetime
from groq import Groq

# Imports for Volume Control
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- CONFIGURATION ---
GROQ_API_KEY = "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" 
MEMORY_FILE = "katya_memory.json"
CACHE_FILE = "activity_cache.json"
VOICE = "en-US-AriaNeural"

# --- TRANCE BREAKER CONFIG ---
PHASE_1_LIMIT = 30  # Seconds to Mute (Warning)
PHASE_2_LIMIT = 40  # Seconds to KILL BROWSER (Nuclear)

# Initialize Global Objects
pygame.mixer.init()
client = Groq(api_key=GROQ_API_KEY)

# State Variables for tracking time
current_distraction_domain = None
distraction_start_time = None
last_category = None
punishment_phase = 0  # 0 = Safe, 1 = Muted, 2 = Killed

# --- PART 1: THE SPY SERVER (FLASK) ---
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    try:
        with open(CACHE_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4)

def mute_system_volume():
    """Mutes volume using PowerShell (Silent)"""
    try:
        os.system('powershell -c "$w=New-Object -ComObject WScript.Shell; 1..50 | % {$w.SendKeys([char]174)}"')
        print("\033[41m[SYSTEM SILENCED] - Phase 1 Activated\033[0m")
    except: pass

def kill_browser():
    """Nuclear Option: Kills Chrome Silently"""
    speak("Escalation protocol engaged. Terminating browser.")
    print("\033[41m[NUCLEAR] - Phase 2 Activated: Killing Chrome\033[0m")
    # >nul 2>&1 hides the massive list of PID successes/errors
    os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")

def judge_url_category(url):
    """Decides if a URL is Productive or Distraction"""
    try:
        clean_domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0].lower()
    except: return "neutral", ""

    # A. Check Local Cache (FAST)
    cache = load_cache()
    if clean_domain in cache:
        return cache[clean_domain], clean_domain

    # B. Ask Groq (SLOW - Only for new sites)
    print(f"\033[93m[Katya]: Analyzing new domain: {clean_domain}...\033[0m")
    prompt = f"""
    Categorize '{clean_domain}' into exactly one word: 'Productive', 'Distraction', or 'Neutral'.
    Context: User is a Full Stack Developer.
    Examples: github.com->Productive, youtube.com->Distraction, localhost->Productive.
    Output ONLY the word.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        verdict = completion.choices[0].message.content.strip().lower()
        if "productive" in verdict: final = "productive"
        elif "distraction" in verdict: final = "distraction"
        else: final = "neutral"
        
        cache[clean_domain] = final
        save_cache(cache)
        return final, clean_domain
    except: return "neutral", clean_domain

@app.route('/track', methods=['POST'])
def track_activity():
    """Receives URL silently. Handles Phase 1 (Mute) and Phase 2 (Kill)."""
    global current_distraction_domain, distraction_start_time, last_category, punishment_phase

    data = request.json
    url = data.get('url', '')
    if not url: return {"status": "ignored"}
    
    category, domain = judge_url_category(url)
    
    # --- LOGIC: Only Print on CHANGE ---
    if category != last_category:
        timestamp = datetime.now().strftime("%H:%M:%S")
        if category == "distraction":
            print(f"\n\033[91m[VIOLATION STARTED] {timestamp} - {domain}\033[0m")
        elif category == "productive":
            print(f"\n\033[92m[FOCUS MODE] {timestamp} - {domain}\033[0m")
        last_category = category

    # --- TRANCE BREAKER LOGIC ---
    if category == "distraction":
        # 1. New Session?
        if current_distraction_domain != domain:
            current_distraction_domain = domain
            distraction_start_time = time.time()
            punishment_phase = 0 # Reset punishment level
        
        # 2. Check Duration
        if distraction_start_time:
            duration = time.time() - distraction_start_time
            
            # Warning at 15s
            if int(duration) == 15 and punishment_phase == 0:
                print(f"\033[93m   >>> Warning: 15 seconds remaining...\r\033[0m", end="")

            # PHASE 1: MUTE (30s) - Only triggers ONCE
            if duration > PHASE_1_LIMIT and punishment_phase == 0:
                mute_system_volume() 
                speak("The algorithm has trapped you. Break the loop immediately.")
                punishment_phase = 1 # Mark as muted

            # PHASE 2: NUKE (40s) - Only triggers ONCE
            if duration > PHASE_2_LIMIT and punishment_phase == 1:
                punishment_phase = 2 # Set flag BEFORE killing to prevent loops
                kill_browser()

    elif category == "productive":
        # Reset counters
        current_distraction_domain = None
        distraction_start_time = None
        punishment_phase = 0

    return {"status": "logged"}

def start_server_thread():
    """Runs Flask in a separate thread"""
    app.run(port=5000, debug=False, use_reloader=False)

# --- PART 2: VOICE & AUDIO (Improved Safety) ---
async def speak_async(text):
    print(f"\033[96m[Katya]: {text}\033[0m")
    
    # FIX: Use unique filename to prevent collision errors
    rand_id = random.randint(1000, 9999)
    filename = f"response_{int(time.time())}_{rand_id}.mp3"
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    
    # FIX: Wait for file to exist (prevents "No file found" error)
    timeout = 0
    while not os.path.exists(filename) and timeout < 10:
        time.sleep(0.1)
        timeout += 1

    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Audio Error: {e}")
    
    pygame.mixer.music.unload()
    # Robust cleanup
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except: pass

def speak(text):
    try: asyncio.run(speak_async(text))
    except Exception as e: print(f"Voice Error: {e}")

# --- PART 3: MEMORY & TOOLS (Unchanged) ---
def record_audio(filename="input.wav", duration=4, fs=44100):
    print("\033[91m[Listening...]\033[0m")
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        wavio.write(filename, recording, fs, sampwidth=2)
        return filename
    except: return None

def transcribe_audio(filename):
    if not filename or not os.path.exists(filename): return ""
    with open(filename, "rb") as file:
        try:
            return client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text"
            ).strip()
        except: return ""

def load_memory():
    if not os.path.exists(MEMORY_FILE): return []
    try: 
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    except: return []

def save_memory(user_text, katya_text):
    history = load_memory()
    entry = {"time": str(datetime.now()), "user": user_text, "katya": katya_text}
    history.append(entry)
    if len(history) > 10: history = history[-10:]
    with open(MEMORY_FILE, 'w') as f: json.dump(history, f, indent=4)

def ask_katya(user_input):
    history = load_memory()
    context = ""
    for item in history[-3:]:
        context += f"User: {item['user']}\nKatya: {item['katya']}\n"
    system_prompt = f"You are Katya. Strict, helpful. CONTEXT:\n{context}\nUser: {user_input}\nReply in 1 sentence."
    try:
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "system", "content": system_prompt}])
        reply = completion.choices[0].message.content
        save_memory(user_input, reply)
        return reply
    except: return "Connection lost."

def close_app(app_name):
    target = app_name.lower().replace(" ", "")
    speak(f"Terminating {target}.")
    # Silent kill for user requests too
    os.system(f"taskkill /F /IM {target}.exe /T >nul 2>&1")

def find_and_open_folder(target_name):
    target = target_name.lower().strip()
    user_profile = os.path.expanduser("~")
    priority_paths = [
        os.path.join(user_profile, "Desktop"),
        os.path.join(user_profile, "OneDrive", "Desktop"),
        os.path.join(os.environ['PUBLIC'], 'Desktop'), 
        os.path.join(user_profile, "Downloads")
    ]
    print(f"[System]: Quick-scanning for '{target}'...")
    for folder_path in priority_paths:
        if not os.path.exists(folder_path): continue
        try:
            for item in os.listdir(folder_path):
                if os.path.splitext(item)[0].lower() == target:
                    os.startfile(os.path.join(folder_path, item))
                    speak(f"Opening {os.path.splitext(item)[0]}")
                    return True
        except: continue
    return False 

# --- MAIN ENGINE ---
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- KATYA V6.1 (Polished) ---")
    server_thread = threading.Thread(target=start_server_thread)
    server_thread.daemon = True 
    server_thread.start()
    print("--- SERVER RUNNING ---")

    while True:
        try:
            input("Press Enter to speak...")
            audio = record_audio()
            if not audio: continue
            text = transcribe_audio(audio)
            clean = text.lower().replace(".", "").strip()
            print(f"[You]: {clean}")
            if not clean: continue
            
            if "open" in clean: 
                tgt = clean.split("open")[-1].strip()
                if not find_and_open_folder(tgt): speak(f"Cannot find {tgt}")
            elif "close" in clean: close_app(clean.split("close")[-1].strip())
            elif "exit" in clean: break
            else: speak(ask_katya(clean))
            
            if os.path.exists(audio): os.remove(audio)
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()