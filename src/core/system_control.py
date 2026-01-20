# system_control.py
import os

def mute_system_volume():
    """Mutes volume using PowerShell (Silent & Crash Proof)"""
    try:
        os.system('powershell -c "$w=New-Object -ComObject WScript.Shell; 1..50 | % {$w.SendKeys([char]174)}"')
        print("\033[41m[SYSTEM SILENCED] - Phase 1 Activated\033[0m")
    except: pass

def kill_browser():
    """Nuclear Option: Kills Chrome Silently"""
    print("\033[41m[NUCLEAR] - Phase 2 Activated: Killing Chrome\033[0m")
    os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")

def close_app(app_name):
    target = app_name.lower().replace(" ", "")
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
                    return True
        except: continue
    return False