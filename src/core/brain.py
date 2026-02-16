import os
import json
import psutil
from datetime import datetime
from groq import Groq

# Handling config safely
try:
    from config import GROQ_API_KEY, MEMORY_FILE, CACHE_FILE
except ImportError:
    from config import GROQ_API_KEY, MEMORY_FILE
    CACHE_FILE = "activity_cache.json" 

from identity import load_identity

client = Groq(api_key=GROQ_API_KEY)

# --- DATA TOOLS ---
def load_data(file_path):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r') as f: return json.load(f)
    except: return []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    try: 
        with open(CACHE_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_cache(data):
    with open(CACHE_FILE, 'w') as f: json.dump(data, f, indent=4)

def get_domain(url):
    try:
        clean = url.replace("https://", "").replace("http://", "").split('/')[0]
        return clean.replace("www.", "")
    except: return url

# --- AUDIO & STATS ---
def transcribe_audio(filename):
    if not filename or not os.path.exists(filename): 
        print("[ERROR] Audio file not found.")
        return ""
    with open(filename, "rb") as file:
        try:
            return client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text"
            ).strip()
        except Exception as e: 
            print(f"[TRANSCRIPTION ERROR]: {e}")
            return ""
        
def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage('C:\\')
        free_gb = round(disk.free / (1024**3), 1)
        total_gb = round(disk.total / (1024**3), 1)
        disk_stat = f"C: Drive ({free_gb}GB free of {total_gb}GB)"
    except: disk_stat = "C: Unknown"
    
    processes = []
    for proc in psutil.process_iter(['name', 'memory_info']):
        try: processes.append(proc.info)
        except: pass
    top_procs = sorted(processes, key=lambda p: p['memory_info'].rss, reverse=True)[:3]
    proc_list = ", ".join([p['name'].replace('.exe', '').title() for p in top_procs])
    
    return f"CPU: {cpu}%, RAM: {ram}%, {disk_stat}. Top Apps: [{proc_list}]"

def ask_katya(user_input):
    history = load_data(MEMORY_FILE)
    real_stats = get_system_stats()
    context = ""
    for item in history[-3:]:
        context += f"User: {item['user']}\nKatya: {item['katya']}\n"
    
    system_prompt = f"You are Katya. System: {real_stats}. Context: {context}. User: {user_input}. Reply in 1 sentence."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}]
        )
        reply = completion.choices[0].message.content
        history.append({"time": str(datetime.now()), "user": user_input, "katya": reply})
        if len(history) > 10: history = history[-10:]
        save_data(MEMORY_FILE, history)
        return reply
    except: return "Connection lost."

# --- SMART CLASSIFIER (NO MORE STATIC LISTS) ---
def classify_url_via_groq(url, title):
    print(f"🧠 [KATYA LEARNING] Analyzing new domain: {url}...")
    
    # We ask Groq to output a SPECIFIC TAG
    prompt = f"""
    CLASSIFY this website for a Software Engineer.
    URL: {url}
    PAGE TITLE: {title}
    
    RETURN ONE OF THESE TAGS ONLY:
    - JOB_PORTAL (LinkedIn, Indeed, Company Careers, Job Boards)
    - DEV_TOOL (Github, StackOverflow, Docs, Localhost, Tools)
    - LEARNING (Tutorials, Courses, Articles)
    - SOCIAL (Facebook, Twitter, Instagram)
    - ENTERTAINMENT (Netflix, Games, Comics)
    - NEUTRAL (Search engines, Login pages)
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}], max_tokens=15
        )
        tag = completion.choices[0].message.content.strip().upper()
        
        # MAP TAGS TO PRODUCTIVITY
        if "JOB_PORTAL" in tag: return "productive", "Job Portal"
        if "DEV_TOOL" in tag: return "productive", "Coding Resource"
        if "LEARNING" in tag: return "productive", "Learning"
        
        if "SOCIAL" in tag: return "distraction", "Social Media"
        if "ENTERTAINMENT" in tag: return "distraction", "Entertainment"
        
        return "neutral", "Browsing"
    except Exception as e:
        print(f"[AI ERROR]: {e}")
        return "neutral", "Unknown"

def judge_activity(url, title):
    clean_url = url.replace("https://", "").replace("http://", "").lower()
    clean_title = title.lower() if title else ""
    domain = get_domain(url)

    # 1. FAST LANE (Localhost/Github are always safe)
    if "localhost" in clean_url or "127.0.0.1" in clean_url: return "productive", "Local Development"
    if "github.com" in clean_url: return "productive", "Github"

    # 2. YOUTUBE CONTEXT (Dynamic)
    if "youtube.com" in clean_url:
        productive_keywords = ["tutorial", "course", "python", "react", "coding", "math", "lecture", "system design"]
        if any(k in clean_title for k in productive_keywords):
            return "productive", f"Learning: {clean_title[:15]}..."
        return "distraction", "YouTube Leisure"

    # 3. MEMORY CHECK
    cache = load_cache()
    if domain in cache:
        # Cache stores: {"category": "productive", "label": "Job Portal"}
        cached_entry = cache[domain]
        # Handle legacy cache format (string) vs new format (dict/list)
        if isinstance(cached_entry, list):
            return cached_entry[0], f"{cached_entry[1]}: {domain}"
        return cached_entry.lower(), f"{cached_entry}: {domain}"

    # 4. ASK AI (The Learning Step)
    cat, label = classify_url_via_groq(url, title)
    
    # Save both Category AND Label
    cache[domain] = [cat, label]
    save_cache(cache)
    
    return cat.lower(), f"{label}: {domain}"