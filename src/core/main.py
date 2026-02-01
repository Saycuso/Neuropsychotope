# main.py
import os
import time

from spy_server import start_server
from audio_engine import record_audio, speak
from brain import transcribe_audio, ask_katya
from system_control import close_app, find_and_open_folder

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- NEUROPSYCHOTOPE: KATYA V7 (Modular) ---")
    
    # 1. Start Server
    start_server()
    print("--- SPY SERVER RUNNING (Port 5000) ---")

    # 2. Main Loop
    while True:
        
        try:
            input("Press Enter to speak...")
            audio_file = record_audio()
            if not audio_file: continue
            
            text = transcribe_audio(audio_file)
            clean = text.lower().replace(".", "").strip()
            print(f"[You]: {clean}")
            
            if not clean: continue
            
            # Router
            if "open" in clean:
                target = clean.split("open")[-1].strip()
                if not find_and_open_folder(target): speak(f"Cannot find {target}.")
            elif "close" in clean:
                target = clean.split("close")[-1].strip()
                close_app(target)
                speak(f"Terminating {target}.")
            elif "exit" in clean:
                speak("Shutting down.")
                break
            else:
                reply = ask_katya(clean)
                speak(reply)
            
            # Cleanup
            if os.path.exists(audio_file): os.remove(audio_file)
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()