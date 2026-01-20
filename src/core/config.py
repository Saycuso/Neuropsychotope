# config.py
import os
from dotenv import load_dotenv # <--- NEW IMPORT

# Load the variables from .env
load_dotenv()

# GET THE KEY SECURELY
# If .env is missing or empty, this will be None (safety check)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found. check your .env file!")

# FILES
MEMORY_FILE = "katya_memory.json"
CACHE_FILE = "activity_cache.json"
VOICE = "en-US-AriaNeural"

# TRANCE BREAKER TIMINGS
PHASE_1_LIMIT = 30  # Seconds to Mute (Warning)
PHASE_2_LIMIT = 40  # Seconds to KILL BROWSER (Nuclear)