#!/usr/bin/env bash
# =============================================================================
# AI Sales Agent SaaS — Enterprise Automated Installer (Linux)
# =============================================================================
# This script installs, configures, and starts the complete platform.
#
# Usage:
#   chmod +x install.sh
#   sudo ./install.sh
#
# Options:
#   --domain <domain>     Production domain (configures CORS)
#   --dev                 Development mode (no workers, reload enabled)
#   --help                Show this help
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

MODE="production"
DOMAIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2 ;;
    --dev) MODE="development"; shift ;;
    --help)
      echo "Usage: sudo ./install.sh [--domain <domain>] [--dev]"
      echo ""
      echo "  --domain <domain>  Production domain (e.g., app.mycompany.com)"
      echo "  --dev              Development mode (reload enabled)"
      echo "  --help             Show this help"
      exit 0
      ;;
    *) log_error "Unknown option: $1"; exit 1 ;;
  esac
done

echo ""
echo "================================================"
echo "  AI Sales Agent SaaS — Enterprise Installer"
echo "================================================"
echo ""

# ─────────────────────────────────────────────────────
# 1. Check prerequisites
# ─────────────────────────────────────────────────────
log_info "Checking prerequisites..."

check_command() {
  if ! command -v "$1" &>/dev/null; then
    log_error "$1 is not installed. Please install it first."
    exit 1
  fi
  log_ok "$1 found: $($1 --version 2>&1 | head -1)"
}

check_command python3
check_command node
check_command npm
check_command psql
check_command redis-cli

# ─────────────────────────────────────────────────────
# 2. Check PostgreSQL connection
# ─────────────────────────────────────────────────────
log_info "Checking PostgreSQL..."
if pg_isready -q 2>/dev/null; then
  log_ok "PostgreSQL is running"
else
  log_warn "PostgreSQL is not running. Attempting to start..."
  sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null || {
    log_error "Could not start PostgreSQL. Start it manually and re-run this script."
    exit 1
  }
fi

# ─────────────────────────────────────────────────────
# 3. Create database (if not exists)
# ─────────────────────────────────────────────────────
log_info "Setting up database..."
DB_NAME="ai_sales_agent_saas"
DB_USER="aisa_admin"
DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
  log_ok "Database user $DB_USER already exists"
else
  sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
  log_ok "Created database user: $DB_USER"
fi

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  log_ok "Database $DB_NAME already exists"
else
  sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
  log_ok "Created database: $DB_NAME"
fi

# ─────────────────────────────────────────────────────
# 4. Create .env from example
# ─────────────────────────────────────────────────────
log_info "Configuring environment..."
cd "$PROJECT_DIR/backend"

if [ ! -f .env ]; then
  cp .env.example .env

  # Generate secrets
  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
  ADMIN_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
  WHATSAPP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

  # Update .env with generated values
  sed -i "s|APP_ENV=.*|APP_ENV=${MODE}|" .env
  sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}|" .env
  sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|" .env
  sed -i "s|ADMIN_JWT_SECRET_KEY=.*|ADMIN_JWT_SECRET_KEY=${ADMIN_JWT_SECRET}|" .env
  sed -i "s|WHATSAPP_ENCRYPTION_KEY=.*|WHATSAPP_ENCRYPTION_KEY=${WHATSAPP_KEY}|" .env
  sed -i "s|REDIS_URL=.*|REDIS_URL=redis://127.0.0.1:6379/0|" .env
  sed -i "s|LOG_LEVEL=.*|LOG_LEVEL=INFO|" .env

  if [ -n "$DOMAIN" ]; then
    sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=https://${DOMAIN}|" .env
  fi

  log_ok "Created .env with generated secrets"
  log_warn "Database password: ${DB_PASS}"
  log_warn "Save this password securely. It won't be shown again."
else
  log_ok ".env already exists, skipping"
fi

# Frontend .env.local
cd "$PROJECT_DIR/frontend"
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  if [ -n "$DOMAIN" ]; then
    sed -i "s|NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=https://${DOMAIN}/api/v1|" .env.local
  fi
  log_ok "Created frontend .env.local"
else
  log_ok "Frontend .env.local already exists, skipping"
fi

# ─────────────────────────────────────────────────────
# 5. Install backend dependencies
# ─────────────────────────────────────────────────────
log_info "Installing backend dependencies..."
cd "$PROJECT_DIR/backend"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  log_ok "Created Python virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -e ".[dev]" -q
log_ok "Backend dependencies installed"

# ─────────────────────────────────────────────────────
# 6. Install frontend dependencies
# ─────────────────────────────────────────────────────
log_info "Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
npm install --silent 2>/dev/null
log_ok "Frontend dependencies installed"

# ─────────────────────────────────────────────────────
# 7. Run database migrations
# ─────────────────────────────────────────────────────
log_info "Running database migrations..."
cd "$PROJECT_DIR/backend"
source .venv/bin/activate
alembic upgrade head
log_ok "Migrations complete"

# ─────────────────────────────────────────────────────
# 8. Build frontend
# ─────────────────────────────────────────────────────
if [ "$MODE" = "production" ]; then
  log_info "Building frontend for production..."
  cd "$PROJECT_DIR/frontend"
  npm run build
  log_ok "Frontend build complete"
fi

# ─────────────────────────────────────────────────────
# 9. Start services
# ─────────────────────────────────────────────────────
log_info "Starting services..."

cd "$PROJECT_DIR/backend"
source .venv/bin/activate

if [ "$MODE" = "development" ]; then
  # Development: start backend with reload
  nohup uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 > "$PROJECT_DIR/logs/backend.log" 2>&1 &
  BACKEND_PID=$!

  # Development: start frontend
  cd "$PROJECT_DIR/frontend"
  nohup npm run dev > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
  FRONTEND_PID=$!
else
  # Production: start backend with workers
  nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > "$PROJECT_DIR/logs/backend.log" 2>&1 &
  BACKEND_PID=$!

  # Production: start frontend
  cd "$PROJECT_DIR/frontend"
  nohup npm run start > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
  FRONTEND_PID=$!
fi

echo ""
echo "================================================"
echo -e "${GREEN}  Installation Complete${NC}"
echo "================================================"
echo ""
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:3000"
echo "  API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "  Logs: $PROJECT_DIR/logs/"
echo ""
echo "  To create admin user:"
echo "    cd $PROJECT_DIR/backend && source .venv/bin/activate && python scripts/seed_admin.py"
echo ""
echo "  To stop services:"
echo "    kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "================================================"
