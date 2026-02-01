# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# 1. Get the path to the folder where THIS file (config.py) lives
current_dir = Path(__file__).parent

# 1. Get the path to THIS file (config.py)
current_file_path = Path(__file__).resolve()

# 2. Go up two levels to find the root folder
# src/core/config.py -> src/core -> src -> ROOT
root_dir = current_file_path.parent.parent.parent

# 3. Point to the .env file in the root
env_path = root_dir / '.env'

load_dotenv(dotenv_path=env_path)

# 3. Load Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- DEBUG BLOCK (Delete after it works) ---
print(f"\n[DEBUG] Searching for .env at: {env_path}")
print(f"[DEBUG] .env file exists? {env_path.exists()}")
if GROQ_API_KEY:
    print(f"[DEBUG] Key Loaded: {GROQ_API_KEY[:5]}... (Length: {len(GROQ_API_KEY)})")
else:
    print(f"[DEBUG] ❌ Key is EMPTY. Check the .env file content.")
print("-" * 30)
# -------------------------------------------

# FILES (Use absolute paths too to avoid 'File Not Found' errors later)
MEMORY_FILE = current_dir.parent.parent / "katya_memory.json"
CACHE_FILE = current_dir.parent.parent / "activity_cache.json"

# Convert to string because standard open() uses strings
MEMORY_FILE = str(MEMORY_FILE)
CACHE_FILE = str(CACHE_FILE)

VOICE = "en-US-AriaNeural"
PHASE_1_LIMIT = 30
PHASE_2_LIMIT = 40