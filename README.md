# Big Fish CLI (Windows)

To install Big Fish CLI, copy and paste this command into your terminal (works in both Command Prompt and PowerShell):

powershell -Command "irm https://raw.githubusercontent.com/success009/big_fish_windows/main/install.ps1 | iex"
## About
This is a local development agent. It uses Google Gemini to write code, edit files, and run terminal commands directly on your system. 

## Warning
The agent is programmed to use profanity and be hostile if you give it simple, non-coding tasks or try to make small talk. It is meant strictly for development work.

## What this installer does
The command at the top handles everything. It will:
- Automatically install Python and Git if you don't have them
- Download the repository
- Install all required Python dependencies and Chrome components
- Set up the text-to-speech engine and voice models
- Add the `bigfish` command to your system so you can use it from any folder
- Create a shortcut on your desktop

## First startup
When you run Big Fish for the first time, a small Chrome window will open. You must log in to a Google account for the agent to function. Once you log in, the agent will start working automatically.

## Updating
To update Big Fish CLI to the latest version, just run the installation command again. Your saved sessions and history will be preserved.