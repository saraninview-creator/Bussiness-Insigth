# DataNarrate — Quick Start Script (Windows PowerShell)
# Run from the insight/ directory:  .\start.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DataNarrate — Setup and Start" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$Root = $PSScriptRoot

# ── 1. Python deps ────────────────────────────────────────────────────────────
Write-Host "`n[1/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r "$Root\backend\requirements.txt"

# ── 2. Remotion deps ──────────────────────────────────────────────────────────
Write-Host "`n[2/4] Installing Remotion dependencies..." -ForegroundColor Yellow
Push-Location "$Root\remotion_project"; npm install; Pop-Location

# ── 3. Frontend deps ──────────────────────────────────────────────────────────
Write-Host "`n[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location "$Root\frontend"; npm install; Pop-Location

# ── 4. Start servers ──────────────────────────────────────────────────────────
Write-Host "`n[4/4] Starting servers..." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:5173"
Write-Host ""

# Launch FastAPI in a new PowerShell window
Write-Host "Starting backend..." -ForegroundColor Gray
Start-Process powershell -ArgumentList `
  "-NoExit", "-Command", `
  "Set-Location '$Root\backend'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# ── Health-check loop — wait for backend before starting Vite ─────────────────
Write-Host "Waiting for backend to be ready..." -ForegroundColor Gray
$attempts = 0
$ready    = $false
while ($attempts -lt 20 -and -not $ready) {
  Start-Sleep -Seconds 2
  $attempts++
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($r.StatusCode -eq 200) { $ready = $true }
  } catch { }
}

if ($ready) {
  Write-Host "Backend is up! (took ~$($attempts*2)s)" -ForegroundColor Green
} else {
  Write-Host "WARNING: Backend did not respond after 40s. Frontend starting anyway." -ForegroundColor Yellow
  Write-Host "         Check the backend window for errors." -ForegroundColor Yellow
}

# ── Start Vite dev server ─────────────────────────────────────────────────────
Write-Host "Starting frontend..." -ForegroundColor Gray
Push-Location "$Root\frontend"
npm run dev
Pop-Location
