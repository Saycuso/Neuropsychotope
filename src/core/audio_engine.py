# audio_engine.py
import os
import time
import asyncio
import edge_tts
import sounddevice as sd
import wavio
import pygame
import random
from config import VOICE

# Initialize Mixer
try: pygame.mixer.init()
except: pass

async def speak_async(text):
    print(f"\033[96m[Katya]: {text}\033[0m")
    rand_id = random.randint(1000, 9999)
    filename = f"response_{int(time.time())}_{rand_id}.mp3"
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    
    timeout = 0
    while not os.path.exists(filename) and timeout < 10:
        time.sleep(0.1)
        timeout += 1

    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except: pass
    
    pygame.mixer.music.unload()
    try:
        if os.path.exists(filename): os.remove(filename)
    except: pass

def speak(text):
    try: asyncio.run(speak_async(text))
    except: pass

def record_audio(filename="input.wav", duration=4, fs=44100):
    print("\033[91m[Listening...]\033[0m")
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        wavio.write(filename, recording, fs, sampwidth=2)
        return filename
    except: return None