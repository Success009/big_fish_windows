# Big Fish CLI (Windows)

To install, open PowerShell and run this command:

powershell
irm https://raw.githubusercontent.com/success009/big_fish_windows/main/install.ps1 | iex
## About
This is a local development agent that uses Google Gemini to write code, edit files, and run terminal commands directly on your system. 

## Warning
The agent is programmed to use profanity and be hostile if you give it simple, non-coding tasks or try to make small talk. It is meant strictly for development work.

## Installation details
The installation command at the top handles everything automatically. It will:
- Download the repository
- Install the required Python dependencies
- Set up the text-to-speech audio engine and voice models
- Add the `bigfish` command to your global PATH so you can use it anywhere
- Create a shortcut on your desktop

## First startup
When you run Big Fish for the first time, a minimal Chrome window will open. You need to log in to a Google account for the agent to work. Once you log in, the agent will take over automatically.