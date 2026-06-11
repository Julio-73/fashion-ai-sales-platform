# AI Sales Agent SaaS — Customer Installation Guide v1.0

> Documento para el equipo técnico del cliente.  
> Versión: 1.0 — Junio 2026

---

## Table of Contents

1. [Server Requirements](#1-server-requirements)
2. [Prerequisites Installation](#2-prerequisites-installation)
3. [Automated Installation](#3-automated-installation)
4. [Manual Installation](#4-manual-installation)
5. [Environment Configuration](#5-environment-configuration)
6. [Create Company (Tenant)](#6-create-company-tenant)
7. [Create Admin User](#7-create-admin-user)
8. [Configure WhatsApp](#8-configure-whatsapp)
9. [Configure OpenAI](#9-configure-openai)
10. [Backup Configuration](#10-backup-configuration)
11. [System Update](#11-system-update)
12. [Verification Checklist](#12-verification-checklist)

---

## 1. Server Requirements

### Minimum (demo / low traffic)

| Resource | Requirement |
|----------|-------------|
| CPU | 2 cores |
| RAM | 4 GB |
| Disk | 20 GB SSD |
| OS | Ubuntu 22.04 LTS+ or Windows Server 2019+ |
| PostgreSQL | 15+ |
| Redis | 7+ |
| Python | 3.11+ |
| Node.js | 18.x+ |

### Recommended (production — up to 10 companies)

| Resource | Requirement |
|----------|-------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 50 GB SSD |
| OS | Ubuntu 24.04 LTS |
| PostgreSQL | 16 |
| Redis | 7 |

### Network

| Port | Service | Access |
|------|---------|--------|
| 443 | HTTPS (Frontend + API) | Public |
| 80 | HTTP (redirect to 443) | Public |
| 5432 | PostgreSQL | Localhost only |
| 6379 | Redis | Localhost only |
| 8000 | Backend API (internal) | Localhost only |
| 3000 | Frontend Next.js (internal) | Localhost only |

### Domain & SSL

- A valid domain (e.g., `app.miempresa.com`)
- SSL certificate (Let's Encrypt or commercial)

---

## 2. Prerequisites Installation

### Ubuntu 24.04 LTS

```bash
# System update
sudo apt update && sudo apt upgrade -y

# PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Redis
sudo apt install -y redis-server
sudo systemctl enable redis
sudo systemctl start redis

# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Verify
python3.11 --version
node --version
npm --version
psql --version
redis-cli --version
```

### Windows Server 2022

```powershell
# PostgreSQL — download installer from https://www.postgresql.org/download/windows/
# Redis — download from https://github.com/microsoftarchive/redis/releases
# Python — download from https://www.python.org/downloads/
# Node.js — download from https://nodejs.org/

# Verify installations
python --version
node --version
npm --version
psql --version
```

---

## 3. Automated Installation

The installer creates the database, configures environment variables, installs dependencies, runs migrations, builds the frontend, and starts services.

### Linux

```bash
# Download the delivery package
# (provided by the implementation team)

# Unzip
unzip ai-sales-agent-saas-enterprise-v1.zip -d /opt/ai-sales-agent-saas
cd /opt/ai-sales-agent-saas

# Run installer
chmod +x install.sh
sudo ./install.sh --domain app.miempresa.com
```

The installer will:

1. Check prerequisites (Python, Node, PostgreSQL, Redis)
2. Create database `ai_sales_agent_saas` and user `aisa_admin`
3. Generate secure secrets (JWT, encryption keys, DB password)
4. Configure `.env` files with production values
5. Create Python virtual environment and install dependencies
6. Install frontend dependencies
7. Run database migrations
8. Build frontend for production
9. Start backend (4 workers) and frontend services

After installation, follow the on-screen instructions to create the admin user.

### Windows

```powershell
# Extract delivery package
Expand-Archive -Path ai-sales-agent-saas-enterprise-v1.zip -DestinationPath C:\AI-Sales-Agent

# Run installer (as Administrator)
cd C:\AI-Sales-Agent
powershell -ExecutionPolicy Bypass -File install.ps1 -Domain "app.miempresa.com"
```

---

## 4. Manual Installation

If the automated installer is not suitable for your environment, follow these steps.

### 4.1 Database Setup

```bash
# Create PostgreSQL user and database
sudo -u postgres psql -c "CREATE USER aisa_admin WITH PASSWORD 'your-strong-password-here';"
sudo -u postgres psql -c "CREATE DATABASE ai_sales_agent_saas OWNER aisa_admin;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_sales_agent_saas TO aisa_admin;"

# Verify
psql -U aisa_admin -d ai_sales_agent_saas -h 127.0.0.1 -c "\conninfo"
```

### 4.2 Backend Installation

```bash
cd /opt/ai-sales-agent-saas/backend

# Virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
nano .env  # Edit with production values (see section 5)
```

### 4.3 Frontend Installation

```bash
cd /opt/ai-sales-agent-saas/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
nano .env.local  # Edit API URL

# Build
npm run build
```

### 4.4 Run Migrations

```bash
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
alembic upgrade head
```

### 4.5 Start Services

```bash
# Backend (production)
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > /var/log/aisales/backend.log 2>&1 &

# Frontend (production)
cd /opt/ai-sales-agent-saas/frontend
nohup npm run start > /var/log/aisales/frontend.log 2>&1 &
```

### 4.6 Nginx Configuration

```nginx
server {
    listen 80;
    server_name app.miempresa.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.miempresa.com;

    ssl_certificate /etc/letsencrypt/live/app.miempresa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.miempresa.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for AI Live
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable SSL
sudo certbot --nginx -d app.miempresa.com

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

---

## 5. Environment Configuration

### Backend (`backend/.env`)

```ini
# Environment: local | testing | production
APP_ENV=production
APP_NAME="AI Sales Agent SaaS"
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=https://app.miempresa.com
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://aisa_admin:your-password@127.0.0.1:5432/ai_sales_agent_saas

# Redis (required for production)
REDIS_URL=redis://127.0.0.1:6379/0

# JWT — generate secrets with:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=<generate-random-64-char>
ADMIN_JWT_SECRET_KEY=<generate-different-64-char>
JWT_ISSUER=ai-sales-agent-saas
JWT_AUDIENCE=ai-sales-agent-dashboard
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# OpenAI — required for AI Sales Agent features
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=512
OPENAI_TEMPERATURE=0.7

# WhatsApp encryption key
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
WHATSAPP_ENCRYPTION_KEY=<generate-random-64-char-hex>
```

### Frontend (`frontend/.env.local`)

```ini
NEXT_PUBLIC_APP_NAME="AI Sales Agent SaaS"
NEXT_PUBLIC_API_BASE_URL=https://app.miempresa.com/api/v1
NEXT_PUBLIC_ENABLE_AUTO_LOGIN=false
```

### Configuration Validation

On startup, the application validates all critical variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Always | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Always | JWT signing key |
| `ADMIN_JWT_SECRET_KEY` | Production | Separate admin JWT key |
| `OPENAI_API_KEY` | Production | AI features |
| `REDIS_URL` | Production | Caching, rate limiting, queues |
| `WHATSAPP_ENCRYPTION_KEY` | Production | WhatsApp token encryption |
| `BACKEND_CORS_ORIGINS` | Production | Frontend URL |

If any critical variable is missing or invalid, the application will log the error and exit immediately.

---

## 6. Create Company (Tenant)

After installation, create the first company through the Admin Panel:

```bash
# Create admin user first (see section 7)
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
python scripts/seed_admin.py

# Default credentials:
#   Email: admin@miempresa.com
#   Password: Admin@2024!
```

Then:

1. Open `https://app.miempresa.com/admin/login`
2. Log in with admin credentials
3. Navigate to **Tenants**
4. Click **"Create Company"**
5. Fill in:
   - **Company Name**: Legal business name
   - **Slug**: URL-friendly identifier (e.g., `mi-empresa`)
   - **Plan**: `enterprise`, `professional`, or `starter`
   - **Status**: `active`
   - **Max Users**: Number of allowed users
6. Click **Save**

---

## 7. Create Admin User

### Using the seed script

```bash
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
python scripts/seed_admin.py
```

This creates a super admin with:
- Email: `admin@miempresa.com`
- Password: `Admin@2024!`

**Important**: Change the password after first login.

### Using the Admin Panel

1. Go to **Settings → Users**
2. Click **"Invite User"**
3. Enter email, full name, and role
4. The user receives an email with login instructions

---

## 8. Configure WhatsApp

### Prerequisites

- Meta Business Account with WhatsApp Business API access
- A verified WhatsApp Business phone number
- Meta App with WhatsApp messaging permissions

### Steps

1. Log in to the User Dashboard
2. Go to **WhatsApp → Settings**
3. Click **"Connect WhatsApp"**
4. You will be redirected to Meta's authorization page
5. Log in with your Meta Business account
6. Select the WhatsApp phone number
7. Grant the required permissions
8. You will be redirected back to the platform

### Verify Connection

```bash
curl https://app.miempresa.com/api/v1/whatsapp/metrics \
  -H "Authorization: Bearer <admin-token>"
```

Expected response includes `is_configured: true` and account details.

---

## 9. Configure OpenAI

### Prerequisites

- OpenAI API key with access to GPT-4o-mini
- Billing enabled on the OpenAI account

### Configuration

The OpenAI API key is set in the backend `.env` file:

```ini
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=512
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
```

### Verify AI Features

1. Go to **AI Settings** in the dashboard
2. Verify that AI features show as enabled
3. Create a conversation and verify AI replies work

### Cost Estimates

| Feature | Tokens per request | Estimated cost |
|---------|-------------------|----------------|
| Sales reply generation | ~300-800 tokens | ~$0.001/msg |
| Intent detection | ~200-400 tokens | ~$0.0005/msg |
| Lead scoring | ~500-1000 tokens | ~$0.002/eval |
| Smart recommendations | ~400-800 tokens | ~$0.001/rec |

---

## 10. Backup Configuration

### Automated Daily Backups

The backup script creates:

- Full PostgreSQL dump (compressed)
- Configuration files (.env)
- Rotates backups older than 30 days

### Linux Setup

```bash
# Run once to configure
sudo /opt/ai-sales-agent-saas/deployment/scripts/backup.sh --install

# This installs a cron job at /etc/cron.d/aisales-backup
# Backups run daily at 3:00 AM
# Backup location: /var/backups/ai-sales-agent-saas/
```

### Windows Setup

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File C:\AI-Sales-Agent\deployment\scripts\backup.ps1 -Install
```

### Manual Backup

```bash
# Database
pg_dump -U aisa_admin -h 127.0.0.1 ai_sales_agent_saas | gzip > backup_$(date +%Y%m%d).sql.gz

# Configuration
tar czf config_$(date +%Y%m%d).tar.gz /opt/ai-sales-agent-saas/backend/.env /opt/ai-sales-agent-saas/frontend/.env.local

# Restore
gunzip -c backup_20260101.sql.gz | psql -U aisa_admin -h 127.0.0.1 ai_sales_agent_saas
```

---

## 11. System Update

### Step-by-step update process

```bash
# 1. Stop services
sudo systemctl stop aisales-backend
sudo systemctl stop aisales-frontend

# 2. Backup
sudo /opt/ai-sales-agent-saas/deployment/scripts/backup.sh

# 3. Update code
cd /opt/ai-sales-agent-saas
# (replace with new delivery package)
# or: git pull (if using git)

# 4. Update backend dependencies
cd backend
source .venv/bin/activate
pip install -e ".[dev]" --upgrade

# 5. Run new migrations
alembic upgrade head

# 6. Update frontend
cd ../frontend
npm install
npm run build

# 7. Restart services
sudo systemctl start aisales-backend
sudo systemctl start aisales-frontend

# 8. Verify
curl https://app.miempresa.com/api/v1/system/status
```

### Version compatibility

Always check the changelog (`CHANGELOG_V1.0.0.md`) before updating. Major version updates may require additional migration steps.

---

## 12. Verification Checklist

After installation, verify the following:

- [ ] `curl https://app.miempresa.com/api/v1/health` → `status: "ok"`
- [ ] `curl https://app.miempresa.com/api/v1/system/status` → `status: "healthy"`
- [ ] Login page loads at `https://app.miempresa.com/login`
- [ ] Admin panel loads at `https://app.miempresa.com/admin/login`
- [ ] Can create a new company (tenant)
- [ ] Can create users
- [ ] WhatsApp shows "Connected"
- [ ] AI features respond (AI Sales page loads)
- [ ] Pipeline board loads with stages
- [ ] Reports generate (PDF and Excel)
- [ ] Automation engine responds
- [ ] Executive Dashboard loads
- [ ] Backup script runs successfully

---

*Documentation v1.0 — AI Sales Agent SaaS Enterprise*
