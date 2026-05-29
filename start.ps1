param(
  [string]$PythonCmd = "python",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 3000,
  [switch]$SkipDbCheck
)

function Write-Step($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host $msg -ForegroundColor Green }
function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }

Write-Host "=== AI Sales Agent SaaS ===" -ForegroundColor Cyan

Write-Step "[Pre-check] Verificando Python..."
$pyVer = & $PythonCmd --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: Python no encontrado. Usa -PythonCmd para especificar la ruta." -ForegroundColor Red
  exit 1
}
Write-OK "  $pyVer"

if (-not $SkipDbCheck) {
  Write-Step "[Pre-check] Verificando conexión a base de datos..."
  & $PythonCmd -c "
import asyncio
from app.database.session import check_database_connection
result = asyncio.run(check_database_connection())
exit(0 if result else 1)
" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "  ATENCIÓN: DB no disponible. El backend iniciará igual pero los endpoints de BD fallarán." -ForegroundColor DarkYellow
  } else {
    Write-OK "  DB connection OK"
  }
}

Write-Step "[1/3] Corriendo migraciones Alembic..."
& $PythonCmd -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
  Write-Host "  WARN: Migraciones fallaron. Puedes correrlas manualmente con: python -m alembic upgrade head" -ForegroundColor DarkYellow
} else {
  Write-OK "  Migraciones OK"
}

Write-Step "[2/3] Iniciando backend (puerto $BackendPort)..."
$be = Start-Process -PassThru -FilePath "$PythonCmd" -ArgumentList "-m uvicorn app.main:app --reload --host 127.0.0.1 --port $BackendPort" -WorkingDirectory "backend" -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Step "[3/3] Iniciando frontend (puerto $FrontendPort)..."
$fe = Start-Process -PassThru -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "frontend" -WindowStyle Hidden

Write-Host ""
Write-OK "=== Todo listo ==="
Write-Info "Backend:   http://localhost:$BackendPort"
Write-Info "Frontend:  http://localhost:$FrontendPort"
Write-Info "Login:     demo@fashionsales.ai / Demo@2024!"
Write-Info "Auto-Login: http://localhost:$FrontendPort/auto-login"
Write-Host ""
Write-Host "Para detener: Get-Process | Where-Object { \$_.Id -in @($($be.Id), $($fe.Id)) } | Stop-Process" -ForegroundColor Gray
Write-Host "O usa: taskkill /F /PID $($be.Id) & taskkill /F /PID $($fe.Id)" -ForegroundColor Gray
