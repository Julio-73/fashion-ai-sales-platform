# AI Sales Agent SaaS — Installation Guide for Enterprise Clients

> Version 1.0 — Enterprise Customer Delivery

---

## Table of Contents

1. [Server Requirements](#1-server-requirements)
2. [PostgreSQL Installation](#2-postgresql-installation)
3. [Redis Installation](#3-redis-installation)
4. [Backend Installation](#4-backend-installation)
5. [Frontend Installation](#5-frontend-installation)
6. [Environment Configuration](#6-environment-configuration)
7. [Database Migrations](#7-database-migrations)
8. [Admin User Creation](#8-admin-user-creation)
9. [Initial Data Load](#9-initial-data-load)
10. [Starting Services](#10-starting-services)
11. [Verification](#11-verification)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Server Requirements

### Minimum (demo / low traffic)
| Resource | Requirement |
|----------|-------------|
| CPU | 2 cores |
| RAM | 4 GB |
| Disk | 20 GB SSD |
| OS | Ubuntu 22.04+ or Windows Server 2019+ |

### Recommended (production — up to 10 companies)
| Resource | Requirement |
|----------|-------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 50 GB SSD |
| OS | Ubuntu 24.04 LTS |

### Software
| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | >= 3.11 | Backend runtime |
| Node.js | >= 18.x | Frontend runtime |
| PostgreSQL | >= 15 | Primary database |
| Redis | >= 7 | Cache, rate limiting, queues |
| Nginx | Latest | Reverse proxy + SSL (Linux) |

### Network
- Port 8000 (backend API — internal only)
- Port 3000 (frontend — behind reverse proxy)
- Port 443 (HTTPS — public facing)
- Outbound HTTPS access to: `api.openai.com` (if using AI features)

---

## 2. PostgreSQL Installation

### Ubuntu 22.04 / 24.04

```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start and enable
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER aisa_admin WITH PASSWORD 'your-strong-password-here';"
sudo -u postgres psql -c "CREATE DATABASE ai_sales_agent_saas OWNER aisa_admin;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_sales_agent_saas TO aisa_admin;"

# Test connection
psql -U aisa_admin -d ai_sales_agent_saas -h 127.0.0.1
```

### Windows Server

```powershell
# Download PostgreSQL installer from https://www.postgresql.org/download/windows/
# Run installer, remember the admin password
# During installation, set port to 5432

# Open psql command line
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres

# In psql:
CREATE USER aisa_admin WITH PASSWORD 'your-strong-password-here';
CREATE DATABASE ai_sales_agent_saas OWNER aisa_admin;
GRANT ALL PRIVILEGES ON DATABASE ai_sales_agent_saas TO aisa_admin;
\q
```

---

## 3. Redis Installation

### Ubuntu

```bash
sudo apt install -y redis-server
sudo systemctl enable redis
sudo systemctl start redis

# Verify
redis-cli ping
# Should respond: PONG
```

### Windows

Download from https://github.com/microsoftarchive/redis/releases and install.
Redis will run as a Windows service by default on port 6379.

---

## 4. Backend Installation

### Clone / Copy the project

```bash
# If using git:
git clone https://your-repo-url/ai-sales-agent-saas.git
cd ai-sales-agent-saas

# Or copy the deployment package to the server
```

### Create virtual environment

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate  # Linux
# OR
.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### Install dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### Configure environment

```bash
cp .env.example .env
# Edit .env with your production values (see section 6)
nano .env
```

---

## 5. Frontend Installation

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with production values
nano .env.local
```

### Build for production

```bash
npm run build
```

---

## 6. Environment Configuration

### Backend (`backend/.env`)

```ini
# Environment: local | testing | production
APP_ENV=production
APP_NAME="AI Sales Agent SaaS"
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO

# Database — use the credentials from section 2
DATABASE_URL=postgresql+asyncpg://aisa_admin:your-strong-password-here@127.0.0.1:5432/ai_sales_agent_saas

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# JWT — generate secrets with:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=<generate-a-random-64-char-secret>
ADMIN_JWT_SECRET_KEY=<generate-a-different-random-64-char-secret>
JWT_ISSUER=ai-sales-agent-saas
JWT_AUDIENCE=ai-sales-agent-dashboard
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# OpenAI — required for AI features
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=512
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2

# WhatsApp encryption key
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
WHATSAPP_ENCRYPTION_KEY=<generate-a-random-64-char-hex-string>
```

### Frontend (`frontend/.env.local`)

```ini
NEXT_PUBLIC_APP_NAME="AI Sales Agent SaaS"
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api/v1
```

### Critical variable validation

On startup, the application validates critical variables:

| Variable | Required | Production Only |
|----------|----------|-----------------|
| `DATABASE_URL` | Yes | — |
| `JWT_SECRET_KEY` | Yes | — |
| `ADMIN_JWT_SECRET_KEY` | Production | Yes |
| `OPENAI_API_KEY` | Recommended | Yes |
| `REDIS_URL` | Production | Yes |
| `WHATSAPP_ENCRYPTION_KEY` | Production | Yes |
| `BACKEND_CORS_ORIGINS` | Production | Yes |

If any critical variable is missing, the application will log the error and exit immediately.

---

## 7. Database Migrations

```bash
cd backend
source .venv/bin/activate  # Linux
# OR
.venv\Scripts\Activate.ps1  # Windows

# Run all pending migrations
alembic upgrade head

# Verify
alembic current
# Should show the latest revision
```

---

## 8. Admin User Creation

```bash
cd backend
source .venv/bin/activate

# Create the initial super admin user
python -c "
from app.database.session import AsyncSessionFactory
from app.modules.admin.repository import AdminUserRepository
from app.modules.admin.service import AdminService
import asyncio

async def create_admin():
    repo = AdminUserRepository()
    admin = await repo.create(
        email='admin@your-company.com',
        password_hash='',  # will be set by service
        rol='super_admin',
        is_active=True,
    )
    print(f'Admin created: {admin.id}')

asyncio.run(create_admin())
"
```

Or use the seed script:
```bash
python scripts/seed_admin.py
```

Default credentials (change immediately):
- Email: `admin@your-company.com`
- Password: `Admin@2024!`

---

## 9. Initial Data Load

### Option A: Demo seed data (testing)

```bash
cd backend
source .venv/bin/activate
python scripts/demo_seed.py
```

This creates:
- 1 demo company
- 1 admin user
- 2 sales agents
- 100 customers
- 20 products with variants
- 50 pipeline deals
- 100 orders
- 200 conversations
- 50 automation tasks
- Inventory items

### Option B: Fresh start (production)

No seed data needed. Create your company and users through the admin panel:
1. Login at `/admin/login`
2. Go to "Tenants" section
3. Click "Create Company"
4. Configure company details, plan, status

---

## 10. Starting Services

### Option A: Using the install script

```bash
# Linux
chmod +x scripts/install.sh
./scripts/install.sh
```

### Option B: Manual start

**Backend (production):**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

**Backend (development with auto-reload):**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend (production):**
```bash
cd frontend
npm run start
```

**Frontend (development):**
```bash
cd frontend
npm run dev
```

### Option C: Systemd service (Linux — recommended for production)

Create `/etc/systemd/system/aisales-backend.service`:

```ini
[Unit]
Description=AI Sales Agent SaaS Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-sales-agent-saas/backend
Environment=PATH=/opt/ai-sales-agent-saas/backend/.venv/bin
ExecStart=/opt/ai-sales-agent-saas/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable aisales-backend
sudo systemctl start aisales-backend
sudo systemctl status aisales-backend
```

---

## 11. Verification

### Health check
```bash
curl http://127.0.0.1:8000/api/v1/health
# Expected: {"status":"ok","service":"ai-sales-agent-saas-api","version":"0.1.0",...}
```

### System status
```bash
curl http://127.0.0.1:8000/api/v1/system/status
# Expected: {"status":"healthy","database":"connected","redis":"connected",...}
```

### Frontend
Open `https://your-domain.com` in a browser.

### Login test
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@your-company.com","password":"Admin@2024!"}'
# Expected: {"access_token":"...","refresh_token":"...","user":{...}}
```

---

## 12. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Backend won't start | Missing env vars | Check `backend/.env` — run `python -c "from app.core.config import get_settings; get_settings()"` to see errors |
| Database connection failed | PostgreSQL not running or bad credentials | Verify: `psql -U aisa_admin -d ai_sales_agent_saas -h 127.0.0.1` |
| Redis connection failed | Redis not running | Verify: `redis-cli ping` |
| Frontend shows 500 | Backend not running or port mismatch | Check backend is on port 8000, frontend .env.local has correct API URL |
| Migrations fail | Alembic can't connect to DB | Check `DATABASE_URL` in .env |
| AI features not working | Missing API key | Set `OPENAI_API_KEY` in .env and restart |
| CORS errors in browser | Wrong `BACKEND_CORS_ORIGINS` | Set to your frontend URL |
| Slow queries | Missing indexes | Run: `python scripts/check_db.py` to analyze |

### Getting support
- Open an issue in the project repository
- Include the output of `curl http://127.0.0.1:8000/api/v1/system/status`
- Include the backend logs from `logs/error.log`
