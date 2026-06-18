# DataNarrate - Quick Start Script (Windows PowerShell)
# Run this from the insight/ directory

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DataNarrate - Setup and Start" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Backend - install Python dependencies
Write-Host "`n[1/4] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
Set-Location ..

# 2. Remotion - install Node dependencies
Write-Host "`n[2/4] Installing Remotion dependencies..." -ForegroundColor Yellow
Set-Location remotion
npm install
Set-Location ..

# 3. Frontend - install Node dependencies
Write-Host "`n[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

Write-Host "`n[4/4] Starting servers..." -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Starting backend in new window..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location `"$PWD\backend`"; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "Starting frontend..." -ForegroundColor Gray
Set-Location frontend
npm run dev
