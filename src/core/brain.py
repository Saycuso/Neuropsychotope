# brain.py
import os
import json
import psutil
from datetime import datetime
from groq import Groq
from config import GROQ_API_KEY, MEMORY_FILE, CACHE_FILE
from identity import load_identity

client = Groq(api_key=GROQ_API_KEY)

def load_data(file_path):
    if not os.path.exists(file_path): return {} if "cache" in file_path else []
    try: 
        with open(file_path, 'r') as f: return json.load(f)
    except: return {} if "cache" in file_path else []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

def transcribe_audio(filename):
    if not filename or not os.path.exists(filename): 
        print("[ERROR] Audio file not found.")
        return ""
    
    with open(filename, "rb") as file:
        try:
            # print("Transcribing...") # Optional debug
            return client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text"
            ).strip()
        except Exception as e: 
            print(f"\033[91m[TRANSCRIPTION ERROR]: {e}\033[0m") # <--- PRINT THE ERROR
            return ""
        
def get_system_stats():
    """Grabs CPU, RAM, Top Processes, AND Disk Space"""
    # 1. Basic Stats
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # 2. C: Drive Space (New)
    try:
        disk = psutil.disk_usage('C:\\')
        free_gb = round(disk.free / (1024**3), 1) # Convert bytes to GB
        total_gb = round(disk.total / (1024**3), 1)
        disk_stat = f"C: Drive ({free_gb}GB free of {total_gb}GB)"
    except:
        disk_stat = "C: Drive Unknown"

    # 3. Find Top 3 Processes by Memory
    processes = []
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    # Sort by memory usage (RSS)
    top_procs = sorted(processes, key=lambda p: p['memory_info'].rss, reverse=True)[:3]
    
    # Clean names
    clean_names = [p['name'].replace('.exe', '').title() for p in top_procs]
    proc_list = ", ".join(clean_names)
    
    # Combine everything
    stats = f"CPU: {cpu}%, RAM: {ram}%, {disk_stat}. Top Apps: [{proc_list}]"
    
    # DEBUG PRINT
    print(f"\033[90m[DEBUG SYSTEM DATA]: {stats}\033[0m")
    
    return stats

def ask_katya(user_input):
    history = load_data(MEMORY_FILE)
    
    # 1. Get Real Stats
    real_stats = get_system_stats()
    
    context = ""
    for item in history[-3:]:
        context += f"User: {item['user']}\nKatya: {item['katya']}\n"
    
    # 2. STRICTER Prompt
    system_prompt = f"""
    You are Katya, a helpful AI assistant.
    
    LIVE SYSTEM DATA: {real_stats}
    
    INSTRUCTION:
    - The System Data is for your reference ONLY. 
    - USE IT ONLY if the user explicitly asks about CPU, RAM, Apps, or Storage. 
    - If the user talks about anything else (life, code, feelings), IGNORE the system data completely.
    
    CONTEXT:
    {context}
    
    User: {user_input}
    Reply in 1 sentence. Natural tone.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}]
        )
        reply = completion.choices[0].message.content
        
        entry = {"time": str(datetime.now()), "user": user_input, "katya": reply}
        history.append(entry)
        if len(history) > 10: history = history[-10:]
        save_data(MEMORY_FILE, history)
        
        return reply
    except: return "Connection lost."

def judge_activity(url, title): # Renamed from judge_activity to judge_activity
    user = load_identity()
    profession = user.get("profession", "Novice").lower()
    
    clean_url = url.replace("https://", "").replace("http://", "").lower()
    clean_title = title.lower() if title else ""

    # 1. PROFESSION-BASED WHITELIST (Hardcoded Rules)
    if "content creator" in profession or "artist" in profession:
        if "instagram.com" in clean_url or "pinterest.com" in clean_url:
            return "productive", "Market Research"
            
    if "developer" in profession:
        if "github.com" in clean_url or "stackoverflow.com" in clean_url or "localhost" in clean_url:
            return "productive", "Coding"

    # 2. YOUTUBE CONTEXT ANALYSIS (The "Smart" Judge)
    if "youtube.com" in clean_url:
        # If title indicates learning, let it pass
        productive_keywords = ["tutorial", "course", "lecture", "python", "react", "coding", "math"]
        if any(k in clean_title for k in productive_keywords):
            return "productive", f"Learning: {clean_title[:20]}..."
        else:
            return "distraction", "YouTube Leisure"

    # 3. FALLBACK: AI JUDGMENT (For unknown sites)
    # (Use your existing AI cache logic here, but pass the Title too for better context)
    # ... keep your existing cache/groq logic here ...
    
    # Temporary fallback for this snippet:
    return "neutral", clean_url