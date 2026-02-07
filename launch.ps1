#!/usr/bin/env pwsh
# Launch Flask App - Works from any directory

# Detect script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# If script is in repo root, use that; otherwise check if we're already in my-flask-app
if (Test-Path (Join-Path $scriptDir "my-flask-app")) {
    # We're in repo root
    $repoRoot = $scriptDir
    $appDir = Join-Path $scriptDir "my-flask-app"
} elseif (Test-Path (Join-Path $scriptDir "app" "__init__.py")) {
    # We're in my-flask-app directory
    $appDir = $scriptDir
    $repoRoot = Split-Path -Parent $scriptDir
} else {
    Write-Host "Error: Could not find Flask app. Run from repo root or my-flask-app folder." -ForegroundColor Red
    exit 1
}

Write-Host "Starting Flask app..." -ForegroundColor Green
Write-Host "App directory: $appDir" -ForegroundColor Cyan

Set-Location $appDir

# Check if virtual environment exists
$venvPath = Join-Path $repoRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & (Join-Path $venvPath "Scripts" "Activate.ps1")
} else {
    Write-Host "Warning: Virtual environment not found at $venvPath" -ForegroundColor Yellow
}

# Set Flask app
$env:FLASK_APP = "app"
$env:FLASK_ENV = "development"

Write-Host "Launching Flask development server..." -ForegroundColor Green
Write-Host "Open your browser at http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""

flask run
