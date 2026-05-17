@echo off
setlocal
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
echo [4/5] Setting up Audio Engine and Icons...
python setup_audio.py
python convert_icon.py

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

:: Add to User PATH and create Shortcut via PowerShell
:: We avoid using '!' to prevent conflicts with Batch expansion
powershell -NoProfile -ExecutionPolicy Bypass -Command "$r='%~dp0'.TrimEnd('\'); $u=[Environment]::GetEnvironmentVariable('PATH','User'); if(-not $u){$u=''}; $p=$u.Split(';',[System.StringSplitOptions]::RemoveEmptyEntries); if(-not $p.Contains($r)){[Environment]::SetEnvironmentVariable('PATH',$u+';'+$r,'User'); write-host 'Added to PATH.'}else{write-host 'Already in PATH.'}; $w=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $s=$w.CreateShortcut($d+'\Big Fish.lnk'); $s.TargetPath=$r+'\bigfish.bat'; $s.WorkingDirectory=$r; if(Test-Path ($r+'\bigfishlogo.ico')){$s.IconLocation=$r+'\bigfishlogo.ico'}else{$s.IconLocation='shell32.dll,1'}; $s.Save(); write-host 'Shortcut created.'"

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