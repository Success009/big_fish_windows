@echo off
setlocal enabledelayedexpansion
echo ==============================================
echo Big Fish CLI - Windows One-Click Installer
echo ==============================================
echo.

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)

echo [1/5] Setting up Python Virtual Environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo.
echo [2/5] Installing Dependencies...
pip install -r requirements.txt

echo.
echo [3/5] Installing Chrome / Playwright Environment...
playwright install chromium

echo.
echo [4/5] Setting up Audio Engine...
python setup_audio.py

echo.
echo [5/5] Setting up Global Command and Shortcut...

:: Create the launcher batch file
(
echo @echo off
echo cd /d "%%~dp0"
echo if not exist venv (
echo     echo [ERROR] Virtual environment not found. Please run install.bat again.
echo     pause
echo     exit /b
echo ^)
echo call venv\Scripts\activate.bat
echo python main.py %%*
echo if %%ERRORLEVEL%% neq 0 (
echo     echo.
echo     echo [CRASH] Big Fish CLI exited with an error.
echo     pause
echo ^)
) > bigfish.bat

:: Add to User PATH and create Shortcut via PowerShell (Simplified to avoid batch-to-ps1 line break bugs)
set "PS_CMD=$repo='%~dp0'.TrimEnd('\'); $userPath=[Environment]::GetEnvironmentVariable('PATH','User'); if(!$userPath){$userPath=''}; $paths=$userPath.Split(';',[System.StringSplitOptions]::RemoveEmptyEntries); if(!$paths.Contains($repo)){[Environment]::SetEnvironmentVariable('PATH',$userPath+';'+$repo,'User'); write-host 'Added to PATH.'}else{write-host 'Already in PATH.'}; $wshell=New-Object -ComObject WScript.Shell; $dk=[Environment]::GetFolderPath('Desktop'); $s=$wshell.CreateShortcut($dk+'\Big Fish.lnk'); $s.TargetPath=$repo+'\bigfish.bat'; $s.WorkingDirectory=$repo; if(Test-Path ($repo+'\bigfishlogo.png')){$s.IconLocation=$repo+'\bigfishlogo.png'}else{$s.IconLocation='shell32.dll,1'}; $s.Save(); write-host 'Shortcut created.'"

powershell -NoProfile -ExecutionPolicy Bypass -Command "%PS_CMD%"

echo.
echo ==============================================
echo Setup Complete!
echo.
echo [IMPORTANT] Restart your terminal (CMD or PowerShell) for the 'bigfish' 
echo command to start working.
echo.
echo You can now launch by typing 'bigfish' from anywhere.
echo ==============================================
pause