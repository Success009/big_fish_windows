# audio.py - Background TTS Parallel Pipeline Engine
import os
import subprocess
import json
import queue
import uuid
import re
import threading

try:
    from prompt_toolkit.application import run_in_terminal
except ImportError:
    def run_in_terminal(func): func()

CONFIG_FILE = os.path.expanduser("~/gemini_local_agent/.cli_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"speech_enabled": False}

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump({"speech_enabled": SPEECH_ENABLED}, f)
    except: pass

SPEECH_ENABLED = load_config().get("speech_enabled", False)

def toggle_speech():
    global SPEECH_ENABLED
    SPEECH_ENABLED = not SPEECH_ENABLED
    save_config()
    return SPEECH_ENABLED

# Audio Engine Configuration
BASE_DIR = os.path.expanduser("~/gemini_local_agent/piper_tts")
PIPER_BIN = os.path.join(BASE_DIR, "piper", "piper.exe")
VOICE_MODEL = os.path.join(BASE_DIR, "models", "jenny.onnx")

TEXT_QUEUE = queue.Queue()
AUDIO_QUEUE = queue.Queue()
GENERATING_AUDIO = False
PLAYING_AUDIO = False

def is_speaking():
    return GENERATING_AUDIO or PLAYING_AUDIO or not TEXT_QUEUE.empty() or not AUDIO_QUEUE.empty()

def _tts_generator_worker():
    global GENERATING_AUDIO
    while True:
        text = TEXT_QUEUE.get()
        if text is None: break 
        
        GENERATING_AUDIO = True
        
        if not all(os.path.exists(p) for p in [PIPER_BIN, VOICE_MODEL]):
            run_in_terminal(lambda: print("\n[Audio Error: Piper engine/model not found.]"))
            GENERATING_AUDIO = False
            TEXT_QUEUE.task_done()
            continue
            
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        temp_wav = os.path.join(temp_dir, f"gemini_speech_{uuid.uuid4().hex}.wav")
        
        try:
            cmd = [PIPER_BIN, "--model", VOICE_MODEL, "--length_scale", "0.9", "--output_file", temp_wav]
            subprocess.run(cmd, input=text.encode('utf-8'), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
                AUDIO_QUEUE.put(temp_wav)
            else:
                run_in_terminal(lambda: print("\n[Audio Error: WAV file failed to generate.]"))
        except Exception as e:
            run_in_terminal(lambda: print(f"\n[Audio Crash: {e}]"))
        finally: 
            GENERATING_AUDIO = False
            TEXT_QUEUE.task_done()

def _tts_playback_worker():
    global PLAYING_AUDIO
    while True:
        wav_path = AUDIO_QUEUE.get()
        if wav_path is None: break
        
        PLAYING_AUDIO = True
                 try:
            if os.path.exists(wav_path):
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        except Exception as e:
            run_in_terminal(lambda: print(f"\n[Audio Playback Crash: {e}]"))
        finally:
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path) 
            except: pass
            PLAYING_AUDIO = False
            AUDIO_QUEUE.task_done()

# Start both threads simultaneously
threading.Thread(target=_tts_generator_worker, daemon=True).start()
threading.Thread(target=_tts_playback_worker, daemon=True).start()

def stop_audio():
    global GENERATING_AUDIO, PLAYING_AUDIO
    
    with TEXT_QUEUE.mutex:
        TEXT_QUEUE.queue.clear()
        
    with AUDIO_QUEUE.mutex:
        for wav_path in list(AUDIO_QUEUE.queue):
            try: os.remove(wav_path)
            except: pass
        AUDIO_QUEUE.queue.clear()
        
        os.system("taskkill /F /IM piper.exe 2>nul")
    os.system(r"del /Q %TEMP%\gemini_speech_*.wav 2>nul")
    
    GENERATING_AUDIO = False
    PLAYING_AUDIO = False

def speak(text):
    if not text.strip(): return
    
    clean_text = text.replace('🗣️ **Big Fish Asks:**', '').replace('🗣️', '').replace('Big Fish Asks:', '')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('_', '').replace('`', '').strip()
    clean_text = re.sub(r'https?://\S+|www\.\S+', 'provided URL', clean_text)
    clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', clean_text)  
    clean_text = re.sub(r'[\u2600-\u27BF]', '', clean_text)          
    
    if not clean_text.strip(): return
    
    chunks = re.split(r'(?<=[.!?])\s+|\n+', clean_text)
    for chunk in chunks:
        if chunk.strip():
            TEXT_QUEUE.put(chunk.strip())
