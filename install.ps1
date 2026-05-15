# Big Fish CLI - Web Downloader & Installer for Windows
$repoUrl = "https://github.com/success009/big_fish_windows.git"
$installDir = "$HOME\Desktop\big_fish_windows"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Big Fish CLI - Windows Auto Installer" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Check for Git
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git is not installed! Please install Git for Windows from https://git-scm.com/" -ForegroundColor Red
    exit
}

# Clone or Update Repo
if (-not (Test-Path $installDir)) {
    Write-Host "Cloning repository to $installDir..." -ForegroundColor Yellow
    git clone $repoUrl $installDir
} else {
    Write-Host "Directory $installDir already exists. Pulling latest updates..." -ForegroundColor Yellow
    Set-Location $installDir
    git pull
}

Set-Location $installDir
Write-Host "Starting local installer..." -ForegroundColor Yellow
cmd.exe /c "install.bat"