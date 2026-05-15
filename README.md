# Big Fish CLI (Windows Edition)

### Install It
Pop open PowerShell and run this one-liner. It does everything.
powershell
irm https://raw.githubusercontent.com/success009/big_fish_windows/main/install.ps1 | iex
### What the hell is this?
This is a hardcore local development agent. It hooks directly into your system to write code, edit files, and execute shell commands right from your terminal. It bridges your local environment with Google Gemini. No API keys to buy, no bullshit. 

### ⚠️ Fair Warning
If you give this agent simple, mundane tasks or try to small-talk it, it will get extremely profane and hostile. It's built for real work. You've been warned.

### The Setup
The installation command at the top handles the entire setup process automatically. It downloads the repo, installs Python dependencies, sets up the audio engine, pulls the TTS voice models, adds the `bigfish` command to your global PATH (so you can run it anywhere), and drops a shortcut on your desktop.

### First Run Instructions
When you launch Big Fish for the very first time, a minimal Chrome window will pop up. **You must log in to a Google account.** Once you're logged in, the agent takes over.