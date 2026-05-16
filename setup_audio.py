import os
import urllib.request
import zipfile
import sys

def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
            out_file.write(response.read())
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False
    return True

def main():
    base_dir = os.path.expanduser("~/gemini_local_agent/piper_tts")
    piper_dir = os.path.join(base_dir, "piper")
    models_dir = os.path.join(base_dir, "models")
    
    os.makedirs(piper_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    piper_exe = os.path.join(piper_dir, "piper.exe")
    
    if not os.path.exists(piper_exe):
        archive_name = "piper_windows_amd64.zip"
        archive_path = os.path.join(base_dir, archive_name)
        
        # Using the official Piper release for Windows
        url = f"https://github.com/rhasspy/piper/releases/download/2023.11.14-2/{archive_name}"
        if download_file(url, archive_path):
            print("Extracting Piper TTS for Windows...")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(base_dir)
            if os.path.exists(archive_path):
                os.remove(archive_path)
    else:
        print("Piper TTS engine already installed.")

    # Fixed URLs for Jenny Voice (UK English)
    model_path = os.path.join(models_dir, "jenny.onnx")
    json_path = os.path.join(models_dir, "jenny.onnx.json")
    
    # Try multiple sources for the Jenny voice if one fails
    sources = [
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx",
        "https://huggingface.co/ruslanmv/hp-piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx"
    ]
    json_sources = [
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx.json",
        "https://huggingface.co/ruslanmv/hp-piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx.json"
    ]

    if not os.path.exists(model_path):
        for s in sources:
            if download_file(s, model_path): break
    
    if not os.path.exists(json_path):
        for js in json_sources:
            if download_file(js, json_path): break

    # Final Check
    if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
        print("\nAudio Engine successfully configured! Voice capabilities are unlocked.")
    else:
        print("\n[Warning] Voice models failed to download. The CLI will work, but text-to-speech will be disabled.")

if __name__ == "__main__":
    main()