# session.py - URL, History, CWD & Profile Session Manager (Immutable Edition)
import os
import json
import time
import ui

SESSION_DIR = os.path.expanduser("~/gemini_local_agent/sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

def save_current_session(first_prompt, current_url, chat_history, current_cwd, profile_email, profile_dir, filename=None):
    """Saves the session. Locks the URL, Email, and Profile ID so they can never be overwritten once set."""
    if not current_url or "new_chat" in current_url or not first_prompt: 
        return filename
        
    existing_url = None
    existing_email = None
    existing_profile_dir = None
    
    # Immutability Check: Read the existing file to preserve the original URL and Accounts.
    if filename:
        filepath = os.path.join(SESSION_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    existing_url = data.get("url")
                    existing_email = data.get("email")
                    existing_profile_dir = data.get("profile_dir")
            except: pass
            
    # If we already have valid locked data, DO NOT overwrite it.
    final_url = existing_url if existing_url else current_url
    final_email = existing_email if (existing_email and existing_email != "Unknown Profile") else profile_email
    final_profile_dir = existing_profile_dir if existing_profile_dir else profile_dir
    
    if not filename:
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"session_{timestamp}.json"
        
    filepath = os.path.join(SESSION_DIR, filename)
    
    session_data = {
        "url": final_url,
        "preview": (first_prompt[:60] + '...') if len(first_prompt) > 60 else first_prompt,
        "history": chat_history,
        "cwd": current_cwd,
        "email": final_email if final_email else "Unknown Profile",
        "profile_dir": final_profile_dir if final_profile_dir else "Default"
    }
    
    try:
        with open(filepath, 'w') as f: 
            json.dump(session_data, f, indent=4)
        return filename
    except Exception: 
        return filename

def resume_session():
    """Reads the saved data and restores the environment perfectly."""
    trash =[]
    while True:
        sessions = sorted([f for f in os.listdir(SESSION_DIR) if f.endswith('.json')])
        if not sessions and not trash:
            ui.show_status("No past sessions found.")
            return None, None, None,[], os.getcwd(), "Unknown Profile", "Default"
            
 os.system("cls" if os.name == "nt" else "clear")
 print("=== Big Fish CLI Session Manager ===")
        print("Commands: [number] to load | 'd[number]' to delete | 'u' to undo | 'q' to cancel\n")
        
        for i, filename in enumerate(sessions):
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, 'r') as f: data = json.load(f)
                preview = data.get("preview", "Unknown Session")
                email = data.get("email", "Unknown Profile")
                print(f"  {i + 1}: {filename} - [{email}] \"{preview}\"")
            except: 
                print(f"  {i + 1}: {filename} - (Could not load preview)")
                
        if trash: print(f"\n[ {len(trash)} session(s) in trash. Type 'u' to undo. ]")
        choice = input("\nSelect: ").strip().lower()
        
        if choice == 'q': return None, None, None,[], os.getcwd(), "Unknown Profile", "Default"
        elif choice == 'u':
            if trash: os.rename(trash.pop()['trash_path'], trash.pop()['original_path'])
        elif choice.startswith('d'):
            try:
                idx = int(choice.replace('d', '').strip()) - 1
                if 0 <= idx < len(sessions):
                    orig_path = os.path.join(SESSION_DIR, sessions[idx])
                    trash_path = orig_path + ".bak"
                    os.rename(orig_path, trash_path)
                    trash.append({"original_path": orig_path, "trash_path": trash_path})
            except: pass
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                filename = sessions[idx]
                filepath = os.path.join(SESSION_DIR, filename)
                try:
                    with open(filepath, 'r') as f: data = json.load(f)
                    
                    url = data.get("url") 
                    preview = data.get("preview", "") 
                    history = data.get("history",[]) 
                    cwd = data.get("cwd", os.getcwd()) 
                    email = data.get("email", "Unknown Profile")
                    profile_dir = data.get("profile_dir", "Default")
                    
                    if not url: 
                        ui.show_error("Old session format. No URL found.")
                        time.sleep(2)
                        continue
                        
                    ui.show_status(f"\nResuming session: {filename}...")
                    time.sleep(1)
                    return url, filename, preview, history, cwd, email, profile_dir
                except: 
                    ui.show_error("Failed to load session.")
                    time.sleep(1)
