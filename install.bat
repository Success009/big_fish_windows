@echo off
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
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/5] Installing Dependencies...
pip install -r requirements.txt

echo.
echo [3/5] Installing Chrome / Playwright Environment...
playwright install chromium

echo.
echo [4/5] Setting up Audio Engine (Downloading Piper TTS and Voice Model)...
python setup_audio.py

echo.
echo [5/5] Setting up Global Command and Shortcut...
echo @echo off > bigfish.bat
echo call "%~dp0venv\Scripts\activate.bat" >> bigfish.bat
echo python "%~dp0main.py" %%* >> bigfish.bat

powershell -NoProfile -ExecutionPolicy Bypass -Command "$repo = '%~dp0'; $repo = $repo.TrimEnd('\'); $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User'); if (-not $userPath) { $userPath = '' }; $paths = $userPath.Split(';'); if (-not $paths.Contains($repo)) { [Environment]::SetEnvironmentVariable('PATH', $userPath + ';' + $repo, 'User'); Write-Host 'Added to PATH.' }; $wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Big Fish.lnk'); $shortcut.TargetPath = $repo + '\bigfish.bat'; $shortcut.IconLocation = $repo + '\bigfishlogo.png'; $shortcut.WorkingDirectory = $repo; $shortcut.Save(); Write-Host 'Desktop Shortcut created.'"

echo.
echo ==============================================
echo Setup Complete!
echo You can now type 'bigfish' in ANY terminal to launch the CLI.
echo A desktop shortcut has also been created.
echo Note: You might need to restart your terminal for the PATH to take effect.
echo ==============================================
pause