# AI Sales Agent SaaS — Production Readiness Checklist

Use this checklist before deploying to production.

---

## 1. Security

- [ ] **JWT Secret Rotated**: Run `python -c "import secrets; print(secrets.token_urlsafe(64))"` and update `JWT_SECRET_KEY` in `.env`
- [ ] **Default Credentials Removed**: Change `admin@fashionsales.ai` and `demo@fashionsales.ai` passwords
- [ ] **Auto-Login Disabled**: Remove or gate `/auto-login` page in production
- [ ] **Rate Limiting**: Verify rate limiting is active on `/auth/login` (10 req/min) and `/admin/auth/login` (5 req/min)
- [ ] **Account Lockout**: Confirm 5 failed attempts lock accounts for 5 minutes
- [ ] **Password Policy**: Ensure passwords require uppercase, lowercase, digit, and special character (min 10 chars)
- [ ] **CORS**: Verify `BACKEND_CORS_ORIGINS` is set to your production frontend domain only
- [ ] **API Docs Disabled**: Swagger UI (`/docs`, `/redoc`) are disabled when `APP_ENV=production`
- [ ] **Security Headers**: Verify CSP, HSTS, X-Frame-Options, and X-Content-Type-Options are present in all responses
- [ ] **HTTPS Only**: Ensure all traffic goes through HTTPS with a valid SSL certificate
- [ ] **SQL Injection**: All queries use SQLAlchemy ORM (parameterized queries)
- [ ] **XSS Prevention**: No `dangerouslySetInnerHTML` in frontend code
- [ ] **Dependency Audit**: Run `npm audit` in frontend and `pip-audit` in backend

---

## 2. Authentication & Authorization

- [ ] **JWT Algorithm**: HS256 is configured (consider RS256 for higher security)
- [ ] **Access Token TTL**: 15 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- [ ] **Refresh Token TTL**: 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- [ ] **Refresh Token Rotation**: Token rotation with family-based revocation is active
- [ ] **RBAC**: All endpoints enforce role-based permissions
- [ ] **Tenant Isolation**: All tenant-scoped queries filter by `empresa_id`
- [ ] **Admin Auth**: Admin uses separate JWT with distinct `typ` claim (`admin_access`)

---

## 3. Database

- [ ] **PostgreSQL Running**: `pg_isready` returns successfully
- [ ] **Migrations Applied**: `alembic upgrade head` completed without errors
- [ ] **Connection Pooling**: `pool_pre_ping=True` is active (prevents stale connections)
- [ ] **Database Backups**: Automated daily backups configured (see `backup_database.ps1`)
- [ ] **Backup Retention**: Backups retained for at least 30 days
- [ ] **Restore Tested**: Restore procedure verified from backup file
- [ ] **Connection String**: Password in `DATABASE_URL` is strong and not the default

---

## 4. Monitoring & Health

- [ ] **Health Endpoint**: `GET /api/v1/health` returns all checks:
  - [ ] Database: `connected`
  - [ ] Redis: `connected` or `not_configured`
  - [ ] OpenAI: `configured` or `not_configured`
  - [ ] Uptime: numeric value in seconds
  - [ ] Version: `0.1.0`
- [ ] **Logging Configured**: Logs are written to `logs/` directory with rotation (10 MB per file, 5 backups)
- [ ] **Log Levels**: `LOG_LEVEL=INFO` in production
- [ ] **Error Tracking**: Unhandled exceptions are logged and return sanitized 500 responses
- [ ] **Uptime Monitoring**: External monitoring service configured to check `/api/v1/health`

---

## 5. Audit

- [ ] **Admin Audit Log**: All admin actions are recorded:
  - [ ] Admin login/logout
  - [ ] Company created/updated/suspended/activated/expired
  - [ ] Plan changes
- [ ] **Audit Fields**: Each entry includes:
  - [ ] User (admin_user_id)
  - [ ] Company (target_empresa_id)
  - [ ] Action
  - [ ] Date (created_at)
  - [ ] IP address
  - [ ] Entity modified (details)
- [ ] **User Audit**: User login/register/logout actions are logged with IP

---

## 6. Backup & Restore

- [ ] **Backup Script**: `backup_database.ps1` is tested and working
- [ ] **Restore Script**: `restore_database.ps1` is tested and working
- [ ] **Scheduled Backup**: A scheduled task runs backup daily:
  ```powershell
  # Example: Daily at 2:00 AM
  schtasks /create /tn "AISalesAgentBackup" /tr "powershell.exe -File C:\path\to\backup_database.ps1" /sc daily /st 02:00
  ```
- [ ] **Offsite Backup**: Backup files are copied to a separate location or cloud storage
- [ ] **DR Test**: Full restore test performed in staging environment

---

## 7. Deployment

- [ ] **Backend**: Running behind reverse proxy (Nginx/Caddy) with SSL
- [ ] **Frontend**: Built with `npm run build` and served via `npm start`
- [ ] **Workers**: Backend running with 4+ uvicorn workers
- [ ] **Environment Files**: `.env` is not in version control (in `.gitignore`)
- [ ] **No Secrets in Code**: No API keys, passwords, or secrets hardcoded
- [ ] **Health Check**: Uptime monitoring pings `/api/v1/health` every 60 seconds

---

## 8. Performance

- [ ] **Database Indexes**: All foreign keys and commonly queried columns are indexed
- [ ] **Connection Pool**: Database connection pool sized appropriately (default is fine for most cases)
- [ ] **Static Assets**: Frontend static assets are served via CDN or compressed
- [ ] **API Response Times**: Average API response time < 500ms

---

## 9. Update Procedure

When updating to a new version:

```bash
# 1. Backup database
.\backup_database.ps1

# 2. Pull latest code
git pull origin main

# 3. Install new dependencies
cd backend && pip install -e .
cd frontend && npm install

# 4. Apply database migrations
cd backend && alembic upgrade head

# 5. Rebuild frontend
cd frontend && npm run build

# 6. Restart services
Restart-Service ai-sales-agent-api
Restart-Service ai-sales-agent-frontend

# 7. Verify
curl http://localhost:8000/api/v1/health
```

---

## 10. Final Sign-Off

- [ ] All security items checked
- [ ] Backups configured and tested
- [ ] Monitoring active
- [ ] Audit logging verified
- [ ] SSL/HTTPS configured
- [ ] CORS restricted to production domain
- [ ] Default credentials changed
- [ ] JWT secret rotated
- [ ] Smoke test passed
- [ ] Stakeholder approval obtained

---

**Date:** _________________ **Signed off by:** _________________
