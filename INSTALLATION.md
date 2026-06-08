# AI Sales Agent SaaS — Installation Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Environment Variables](#environment-variables)
3. [PostgreSQL Setup](#postgresql-setup)
4. [Redis Setup](#redis-setup)
5. [Backend Installation](#backend-installation)
6. [Frontend Installation](#frontend-installation)
7. [SSL Configuration](#ssl-configuration)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows Server 2019+, Ubuntu 22.04+, macOS 14+ |
| **Python** | >= 3.11 |
| **Node.js** | >= 18.0.0 |
| **PostgreSQL** | >= 15.0 |
| **Redis** | >= 7.0 (recommended for multi-instance deployments) |
| **RAM** | 4 GB minimum (8 GB recommended) |
| **Disk** | 10 GB free minimum |

---

## Environment Variables

### Backend (`backend/.env`)

```ini
# --- Application ---
APP_ENV=production
APP_NAME="AI Sales Agent SaaS"
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO

# --- Database ---
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/ai_sales_agent_saas

# --- Redis (optional) ---
REDIS_URL=redis://:password@host:6379/0

# --- JWT ---
JWT_ISSUER=ai-sales-agent-saas
JWT_AUDIENCE=ai-sales-agent-dashboard
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=<generate-a-random-64-char-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# --- OpenAI ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=512
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
```

### Frontend (`frontend/.env.local`)

```ini
NEXT_PUBLIC_APP_NAME="AI Sales Agent SaaS"
NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com/api/v1
```

### Generate a Secure JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## PostgreSQL Setup

### Windows

1. Download PostgreSQL 15+ from [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
2. Run installer, remember the password for the `postgres` user
3. Add `C:\Program Files\PostgreSQL\15\bin` to your PATH
4. Create the database:

```powershell
psql -U postgres -c "CREATE DATABASE ai_sales_agent_saas;"
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "CREATE DATABASE ai_sales_agent_saas OWNER app_user;"
```

### Run Migrations

```bash
cd backend
alembic upgrade head
```

### Seed Demo Data (Optional)

```bash
cd backend
python -m seed_admin           # Admin user: admin@fashionsales.ai
python -m seed                 # Demo user: demo@fashionsales.ai / Demo@2024!
python -m seed_crm_demo        # CRM sample orders
```

---

## Redis Setup

Redis is optional. Without it, rate limiting uses in-memory storage (fine for single-instance deployments).

### Windows

Download Redis from [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases) or use WSL:

```powershell
wsl --install -d Ubuntu
sudo apt install redis-server
sudo systemctl start redis-server
```

### Linux

```bash
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis
```

---

## Backend Installation

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd ai-sales-agent-saas
```

### 2. Create Virtual Environment

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate   # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -e .
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
Copy-Item .env.example .env  # Windows
# Edit .env with your settings
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start Server

```bash
# Development
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

### 7. Verify

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","service":"ai-sales-agent-saas-api","version":"0.1.0",...}
```

---

## Frontend Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
Copy-Item .env.example .env.local  # Windows
# Edit .env.local with API URL
```

### 3. Build for Production

```bash
npm run build
```

### 4. Start

```bash
# Development
npm run dev

# Production
npm start
```

The frontend runs on `http://localhost:3000`.

---

## SSL Configuration

### Option 1: Reverse Proxy (Nginx - Recommended)

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name app.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Caddy (Automatic SSL)

```caddyfile
api.your-domain.com {
    reverse_proxy 127.0.0.1:8000
}

app.your-domain.com {
    reverse_proxy 127.0.0.1:3000
}
```

---

## Production Deployment

### Quick Start with PowerShell (Windows)

```powershell
.\start.ps1 -BackendPort 8000 -FrontendPort 3000
```

### Systemd Service (Linux)

**Backend service** (`/etc/systemd/system/ai-sales-agent-api.service`):

```ini
[Unit]
Description=AI Sales Agent SaaS API
After=network.target postgresql.service

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/ai-sales-agent-saas/backend
ExecStart=/opt/ai-sales-agent-saas/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
EnvironmentFile=/opt/ai-sales-agent-saas/backend/.env

[Install]
WantedBy=multi-user.target
```

**Frontend service** (`/etc/systemd/system/ai-sales-agent-frontend.service`):

```ini
[Unit]
Description=AI Sales Agent SaaS Frontend
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/ai-sales-agent-saas/frontend
ExecStart=/usr/bin/node /opt/ai-sales-agent-saas/frontend/node_modules/.bin/next start
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-sales-agent-api ai-sales-agent-frontend
sudo systemctl start ai-sales-agent-api ai-sales-agent-frontend
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Database connection refused** | Ensure PostgreSQL is running and DATABASE_URL is correct |
| **Alembic migration fails** | Check database exists: `psql -U postgres -c "\l"` |
| **Frontend shows blank page** | Check NEXT_PUBLIC_API_BASE_URL in .env.local |
| **CORS errors in browser** | Verify BACKEND_CORS_ORIGINS includes the frontend URL |
| **OpenAI errors** | Verify OPENAI_API_KEY is set and has sufficient credits |
| **Port already in use** | Change port in .env or stop existing process |
| **Module not found errors** | Run `pip install -e .` in backend and `npm install` in frontend |

---

## Support

For production support, contact your system administrator or open an issue at the project repository.
