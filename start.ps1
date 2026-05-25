# Start AI Sales Agent SaaS — Backend + Frontend
Write-Host "=== AI Sales Agent SaaS ===" -ForegroundColor Cyan

# 1. Start backend
Write-Host "[1/2] Starting backend (port 8000)..." -ForegroundColor Yellow
$be = Start-Process -PassThru -FilePath "venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory "backend" -WindowStyle Hidden
Start-Sleep -Seconds 3

# 2. Start frontend
Write-Host "[2/2] Starting frontend (port 3000)..." -ForegroundColor Yellow
$fe = Start-Process -PassThru -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "frontend" -WindowStyle Hidden

Write-Host ""
Write-Host "=== Todo listo ===" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login: demo@fashionsales.ai / Demo@2024!" -ForegroundColor Magenta
Write-Host ""
Write-Host "Para detener: cierra las ventanas o mata los procesos" -ForegroundColor Gray