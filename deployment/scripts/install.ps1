# =============================================================================
# AI Sales Agent SaaS — Enterprise Automated Installer (Windows)
# =============================================================================
# This script installs, configures, and starts the complete platform.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
# Parameters:
#   -Domain <domain>    Production domain (configures CORS)
#   -Dev                Development mode (no workers, reload enabled)
# =============================================================================

param(
  [string]$Domain = "",
  [switch]$Dev = $false
)

$ErrorActionPreference = "Stop"

function Write-Step  { Write-Host "[INFO]  $_" -ForegroundColor Cyan }
function Write-OK    { Write-Host "[OK]    $_" -ForegroundColor Green }
function Write-Warn  { Write-Host "[WARN]  $_" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $_" -ForegroundColor Red }

$ProjectDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Mode = if ($Dev) { "development" } else { "production" }

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Sales Agent SaaS - Enterprise Installer" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────────────
# 1. Check prerequisites
# ─────────────────────────────────────────────────────
Write-Step "Checking prerequisites..."

function Check-Command($cmd, $name) {
  $version = & $cmd --version 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Error "$name is not installed. Please install it first."
    exit 1
  }
  Write-OK "$name found: $version"
}

Check-Command "python" "Python"
Check-Command "node" "Node.js"
Check-Command "npm" "npm"
Check-Command "psql" "PostgreSQL psql"

# Check Redis
$redisRunning = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
if (-not $redisRunning) {
  Write-Warn "Redis service not found. Install Redis or set REDIS_URL to empty in .env"
}

# ─────────────────────────────────────────────────────
# 2. Create .env from example
# ─────────────────────────────────────────────────────
Write-Step "Configuring environment..."
$BackendEnv = Join-Path $ProjectDir "backend\.env"
$FrontendEnv = Join-Path $ProjectDir "frontend\.env.local"
$BackendExample = Join-Path $ProjectDir "backend\.env.example"
$FrontendExample = Join-Path $ProjectDir "frontend\.env.example"

if (-not (Test-Path $BackendEnv)) {
  Copy-Item $BackendExample $BackendEnv

  $JwtSecret = & python -c "import secrets; print(secrets.token_urlsafe(64))"
  $AdminJwtSecret = & python -c "import secrets; print(secrets.token_urlsafe(64))"
  $WhatsAppKey = & python -c "import secrets; print(secrets.token_hex(32))"

  (Get-Content $BackendEnv) `
    -replace 'APP_ENV=.*', "APP_ENV=$Mode" `
    -replace 'JWT_SECRET_KEY=.*', "JWT_SECRET_KEY=$JwtSecret" `
    -replace 'ADMIN_JWT_SECRET_KEY=.*', "ADMIN_JWT_SECRET_KEY=$AdminJwtSecret" `
    -replace 'WHATSAPP_ENCRYPTION_KEY=.*', "WHATSAPP_ENCRYPTION_KEY=$WhatsAppKey" `
    -replace 'REDIS_URL=.*', 'REDIS_URL=redis://127.0.0.1:6379/0' `
    | Set-Content $BackendEnv

  if ($Domain) {
    (Get-Content $BackendEnv) -replace 'BACKEND_CORS_ORIGINS=.*', "BACKEND_CORS_ORIGINS=https://$Domain" | Set-Content $BackendEnv
  }

  Write-OK "Created backend .env with generated secrets"
} else {
  Write-OK "Backend .env already exists, skipping"
}

if (-not (Test-Path $FrontendEnv)) {
  Copy-Item $FrontendExample $FrontendEnv
  if ($Domain) {
    (Get-Content $FrontendEnv) -replace 'NEXT_PUBLIC_API_BASE_URL=.*', "NEXT_PUBLIC_API_BASE_URL=https://$Domain/api/v1" | Set-Content $FrontendEnv
  }
  Write-OK "Created frontend .env.local"
} else {
  Write-OK "Frontend .env.local already exists, skipping"
}

# ─────────────────────────────────────────────────────
# 3. Install backend dependencies
# ─────────────────────────────────────────────────────
Write-Step "Installing backend dependencies..."
$BackendDir = Join-Path $ProjectDir "backend"
Set-Location $BackendDir

$VenvPath = Join-Path $BackendDir ".venv"
if (-not (Test-Path $VenvPath)) {
  & python -m venv $VenvPath
  Write-OK "Created Python virtual environment"
}

$Pip = Join-Path $VenvPath "Scripts\pip.exe"
& $Pip install --upgrade pip -q
& $Pip install -e ".[dev]" -q
Write-OK "Backend dependencies installed"

# ─────────────────────────────────────────────────────
# 4. Install frontend dependencies
# ─────────────────────────────────────────────────────
Write-Step "Installing frontend dependencies..."
$FrontendDir = Join-Path $ProjectDir "frontend"
Set-Location $FrontendDir
& npm install --silent 2>$null
Write-OK "Frontend dependencies installed"

# ─────────────────────────────────────────────────────
# 5. Run database migrations
# ─────────────────────────────────────────────────────
Write-Step "Running database migrations..."
Set-Location $BackendDir
$Python = Join-Path $VenvPath "Scripts\python.exe"
& $Python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
  Write-Warn "Migrations failed. Run manually: python -m alembic upgrade head"
} else {
  Write-OK "Migrations complete"
}

# ─────────────────────────────────────────────────────
# 6. Build frontend (production only)
# ─────────────────────────────────────────────────────
if (-not $Dev) {
  Write-Step "Building frontend for production..."
  Set-Location $FrontendDir
  & npm run build
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend build failed"
    exit 1
  }
  Write-OK "Frontend build complete"
}

# ─────────────────────────────────────────────────────
# 7. Start services
# ─────────────────────────────────────────────────────
Write-Step "Starting services..."
$LogsDir = Join-Path $ProjectDir "logs"
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir -Force }

Set-Location $BackendDir
$Uvicorn = Join-Path $VenvPath "Scripts\uvicorn.exe"
if ($Dev) {
  $BackendArgs = "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
} else {
  $BackendArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4"
}
$BackendProcess = Start-Process -PassThru -FilePath $Python -ArgumentList $BackendArgs -WindowStyle Hidden
Start-Sleep -Seconds 3

Set-Location $FrontendDir
if ($Dev) {
  $FrontendProcess = Start-Process -PassThru -FilePath "npm.cmd" -ArgumentList "run dev" -WindowStyle Hidden
} else {
  $FrontendProcess = Start-Process -PassThru -FilePath "npm.cmd" -ArgumentList "run start" -WindowStyle Hidden
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Installation Complete" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://127.0.0.1:8000"
Write-Host "  Frontend: http://127.0.0.1:3000"
Write-Host "  API Docs: http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "  Backend PID:  $($BackendProcess.Id)"
Write-Host "  Frontend PID: $($FrontendProcess.Id)"
Write-Host ""
Write-Host "  To create admin user:"
Write-Host "    cd backend && .venv\Scripts\python scripts\seed_admin.py"
Write-Host ""
Write-Host "  To stop services:"
Write-Host "    Stop-Process -Id $($BackendProcess.Id), $($FrontendProcess.Id)"
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
