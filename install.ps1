# Big Fish CLI - Full Auto-Installer for Windows
$repoUrl = "https://github.com/success009/big_fish_windows.git"
$installDir = "$HOME\Desktop\big_fish_windows"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Big Fish CLI - Windows Auto Installer" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Check/Install Git
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "Git is missing. Installing Git via winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    if (-not $?) { Write-Host "Failed to install Git automatically. Please install it manually from https://git-scm.com/" -ForegroundColor Red; exit }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 2. Check/Install Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Python is missing. Installing Python 3.12 via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
    if (-not $?) { Write-Host "Failed to install Python automatically. Please install it manually from https://python.org" -ForegroundColor Red; exit }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 3. Clone or Update Repo
if (-not (Test-Path $installDir)) {
    Write-Host "Cloning repository to $installDir..." -ForegroundColor Yellow
    git clone $repoUrl $installDir
} else {
    Write-Host "Directory $installDir already exists. Pulling latest updates..." -ForegroundColor Yellow
    Set-Location $installDir
    git pull
}

Set-Location $installDir
Write-Host "Starting local configuration..." -ForegroundColor Yellow
cmd.exe /c "install.bat"