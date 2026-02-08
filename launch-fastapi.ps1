#!/usr/bin/env pwsh
# Launch FastAPI App - Works from any directory

# Detect script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# If script is in repo root, use that; otherwise check if we're already in my-fastapi-app
if (Test-Path (Join-Path $scriptDir "my-fastapi-app")) {
    # We're in repo root
    $repoRoot = $scriptDir
    $appDir = Join-Path $scriptDir "my-fastapi-app"
} elseif (Test-Path (Join-Path $scriptDir "app" "__init__.py")) {
    # We're in my-fastapi-app directory
    $appDir = $scriptDir
    $repoRoot = Split-Path -Parent $scriptDir
} else {
    Write-Host "Error: Could not find FastAPI app. Run from repo root or my-fastapi-app folder." -ForegroundColor Red
    exit 1
}

Write-Host "Starting FastAPI app..." -ForegroundColor Green
Write-Host "App directory: $appDir" -ForegroundColor Cyan

Set-Location $appDir

# Check if virtual environment exists
$venvPath = Join-Path $repoRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    $activateScript = Join-Path (Join-Path $venvPath "Scripts") "Activate.ps1"
    & $activateScript
} else {
    Write-Host "Warning: Virtual environment not found at $venvPath" -ForegroundColor Yellow
}

Write-Host "Launching FastAPI development server..." -ForegroundColor Green
Write-Host "Open your browser at http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API docs available at http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""

uvicorn app:app --reload --host 127.0.0.1 --port 8000
