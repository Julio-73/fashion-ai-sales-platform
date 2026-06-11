# AI Sales Agent SaaS — Admin Operations Manual v1.0

> Para administradores del sistema.  
> Versión: 1.0 — Junio 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Managing Companies (Tenants)](#2-managing-companies-tenants)
3. [Managing Users](#3-managing-users)
4. [Monitoring System Health](#4-monitoring-system-health)
5. [Reviewing Logs](#5-reviewing-logs)
6. [Error Tracking with Error IDs](#6-error-tracking-with-error-ids)
7. [Backup and Restore](#7-backup-and-restore)
8. [Maintenance Tasks](#8-maintenance-tasks)
9. [Troubleshooting Guide](#9-troubleshooting-guide)
10. [Emergency Procedures](#10-emergency-procedures)

---

## 1. System Overview

### Architecture

```
Internet → Nginx (SSL) → Frontend :3000 / Backend API :8000
                                        ├── PostgreSQL :5432
                                        ├── Redis :6379
                                        └── OpenAI API
```

### Services

| Service | Port | Status Check | Restart Command |
|---------|------|-------------|-----------------|
| Nginx | 443/80 | `sudo systemctl status nginx` | `sudo systemctl restart nginx` |
| PostgreSQL | 5432 | `sudo systemctl status postgresql` | `sudo systemctl restart postgresql` |
| Redis | 6379 | `sudo systemctl status redis` | `sudo systemctl restart redis` |
| Backend API | 8000 | `sudo systemctl status aisales-backend` | `sudo systemctl restart aisales-backend` |
| Frontend | 3000 | `sudo systemctl status aisales-frontend` | `sudo systemctl restart aisales-frontend` |

### File Locations

| Resource | Path |
|----------|------|
| Application code | `/opt/ai-sales-agent-saas/` |
| Backend env | `/opt/ai-sales-agent-saas/backend/.env` |
| Frontend env | `/opt/ai-sales-agent-saas/frontend/.env.local` |
| Logs | `/opt/ai-sales-agent-saas/logs/` |
| Backups | `/var/backups/ai-sales-agent-saas/` |
| Systemd services | `/etc/systemd/system/aisales-*.service` |
| Nginx config | `/etc/nginx/sites-available/aisales` |

---

## 2. Managing Companies (Tenants)

### Create a New Company

1. Log in to the **Admin Panel** at `https://app.miempresa.com/admin/login`
2. Navigate to **Tenants**
3. Click **"Create Company"**
4. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| Company Name | Legal business name | "Fashion Store SAC" |
| Slug | URL-friendly ID | `fashion-store` |
| Plan | Subscription tier | `enterprise` |
| Status | Active / Suspended | `active` |
| Max Users | User limit | `10` |
| Max Storage GB | File storage limit | `5` |

5. Click **Save**

### Suspend a Company

1. **Admin Panel** → **Tenants**
2. Find the company
3. Click **Edit** (or the status toggle)
4. Set **Status** to `suspended`

All users from this company lose access immediately. Active sessions are invalidated within the token expiry window (15 minutes max).

### Delete a Company

Deleting a company is a destructive operation. To permanently remove:

```bash
# Connect to PostgreSQL
sudo -u postgres psql -d ai_sales_agent_saas

# The system uses soft-delete for data integrity.
# Run the following SQL to hard-delete (irreversible):
DELETE FROM empresas WHERE id = '<empresa-uuid>';
-- This cascades to all related data.

# After deletion, reindex:
VACUUM FULL ANALYZE;
```

**Warning**: This deletes all customers, orders, conversations, and settings for the company. Only do this if required by data privacy regulations (e.g., GDPR right to erasure).

### List All Companies

```bash
# API (requires admin token)
curl https://app.miempresa.com/api/v1/admin/tenants \
  -H "Authorization: Bearer <admin-token>"

# Direct database query
sudo -u postgres psql -d ai_sales_agent_saas -c "SELECT id, nombre, slug, plan, status, created_at FROM empresas;"
```

---

## 3. Managing Users

### Create a User

**Via Admin Panel:**
1. **Settings → Users**
2. **"Invite User"**
3. Enter email, name, and role
4. The user receives an invitation email

**Via API:**
```bash
curl -X POST https://app.miempresa.com/api/v1/admin/auth/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@email.com","full_name":"John Doe","rol":"sales_agent"}'
```

### User Roles

| Role | Permissions |
|------|------------|
| `super_admin` | Full system access across all companies |
| `owner` | Full access within their company |
| `admin` | Manage company data, settings, view reports |
| `sales_agent` | Daily operations (CRM, pipeline, orders) |
| `analyst` | Read-only reports and dashboards |

### Reset a Password

1. **Admin Panel → Settings → Users**
2. Find the user
3. Click **"Reset Password"**
4. The user receives a password reset email

### Deactivate a User

1. **Admin Panel → Settings → Users**
2. Find the user
3. Click **"Edit"**
4. Set **Active** to `false`

The user's tokens become invalid within 15 minutes.

---

## 4. Monitoring System Health

### Health Check Endpoint

```bash
curl https://app.miempresa.com/api/v1/health
```

Response:
```json
{
  "status": "ok",
  "service": "ai-sales-agent-saas-api",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 86400.0,
  "database": "connected",
  "redis": "connected",
  "openai": "configured"
}
```

### System Status Endpoint

```bash
curl https://app.miempresa.com/api/v1/system/status
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 86400.0,
  "database": "connected",
  "redis": "connected",
  "openai": "configured",
  "whatsapp": "configured",
  "storage": { "total_gb": 50, "used_gb": 12, "free_gb": 38, "percent_used": 24 },
  "errors_24h": 0,
  "service": "ai-sales-agent-saas-api"
}
```

### Monitoring Commands

```bash
# Service status
sudo systemctl status aisales-backend
sudo systemctl status aisales-frontend
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Resource usage
htop
df -h
free -h

# PostgreSQL connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis info
redis-cli info stats

# Recent errors
tail -f /opt/ai-sales-agent-saas/logs/error.log
```

### Automated Monitoring Setup

For production, configure external monitoring:

| Tool | Integration |
|------|-------------|
| **UptimeRobot** | HTTP GET `/api/v1/health` every 5 minutes |
| **Datadog** | Ingest JSON logs from `/opt/ai-sales-agent-saas/logs/*.log` |
| **Prometheus** | Scrape `/api/v1/system/status` as a target |
| **PagerDuty** | Alert on service downtime or `status: degraded` |

---

## 5. Reviewing Logs

### Log Files

| File | Size Limit | Retention | Content |
|------|-----------|-----------|---------|
| `logs/api.log` | 50 MB | 10 rotated files | All API requests |
| `logs/error.log` | 50 MB | 10 rotated files | ERROR level and above |
| `logs/automation.log` | 10 MB | 5 rotated files | Automation engine |
| `logs/backend.log` | — | — | Backend startup (stdout) |

### Production Mode (JSON format)

In production (`APP_ENV=production`), logs are written as newline-delimited JSON:

```json
{"timestamp": "2026-06-11T10:30:00+0000", "level": "INFO", "logger": "ai_sales_agent.auth", "message": "User logged in", "request_id": "abc-123", "user_id": "uuid-here", "tenant_id": "uuid-here"}
```

These can be ingested directly by Datadog, Splunk, or Logstash.

### Useful Log Queries

```bash
# Last 10 errors
tail -10 /opt/ai-sales-agent-saas/logs/error.log

# Errors from last hour
grep "$(date +%Y-%m-%dT%H)" /opt/ai-sales-agent-saas/logs/error.log

# Track a specific request_id
grep "req-abc-123" /opt/ai-sales-agent-saas/logs/api.log

# Track a specific error_id
grep "ERROR-2026-00001" /opt/ai-sales-agent-saas/logs/error.log

# WhatsApp errors
grep "whatsapp" /opt/ai-sales-agent-saas/logs/error.log

# Authentication failures
grep "not_authenticated" /opt/ai-sales-agent-saas/logs/api.log

# Watch logs in real-time
tail -f /opt/ai-sales-agent-saas/logs/api.log
```

---

## 6. Error Tracking with Error IDs

Every system error is assigned a unique **Error ID**:

```
ERROR-{YEAR}-{SEQUENTIAL_ID}
```

Example: `ERROR-2026-00042`

### What Error IDs look like in practice

**In API responses:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected error occurred. Please check server logs."
  }
}
```
(The Error ID is logged in the error log)

**In logs (production JSON mode):**
```json
{
  "timestamp": "2026-06-11T10:30:00+0000",
  "level": "ERROR",
  "logger": "ai_sales_agent.errors",
  "message": "[ERROR-2026-00042] ValueError | user=uuid-here tenant=uuid-here endpoint=/api/v1/orders",
  "error_id": "ERROR-2026-00042",
  "request_id": "req-abc-123"
}
```

### How to use Error IDs for support

When a customer reports an issue:

1. Ask for the **Error ID** shown in the UI or API response
2. Search the error log:
   ```bash
   grep "ERROR-2026-00042" /opt/ai-sales-agent-saas/logs/error.log
   ```
3. The log entry shows the endpoint, user, tenant, timestamp, and error details
4. Use the Error ID to correlate with the customer's report

---

## 7. Backup and Restore

### Automated Backup

The system includes a backup script that runs daily at 3:00 AM.

**Location**: `/var/backups/ai-sales-agent-saas/`  
**Retention**: 30 days

### Manual Backup

```bash
# Full database backup
sudo -u postgres pg_dump ai_sales_agent_saas | gzip > /var/backups/manual_$(date +%Y%m%d_%H%M%S).sql.gz

# Configuration backup
tar czf /var/backups/config_$(date +%Y%m%d).tar.gz \
  /opt/ai-sales-agent-saas/backend/.env \
  /opt/ai-sales-agent-saas/frontend/.env.local
```

### Restore from Backup

```bash
# 1. Stop services
sudo systemctl stop aisales-backend aisales-frontend

# 2. Find the backup to restore
ls -la /var/backups/postgres_ai_sales_agent_saas_*.sql.gz

# 3. Drop and recreate the database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ai_sales_agent_saas;"
sudo -u postgres psql -c "CREATE DATABASE ai_sales_agent_saas OWNER aisa_admin;"

# 4. Restore
gunzip -c /var/backups/postgres_ai_sales_agent_saas_20260101_030000.sql.gz | \
  sudo -u postgres psql -d ai_sales_agent_saas

# 5. Restore config (if needed)
tar xzf /var/backups/config_20260101.tar.gz -C /

# 6. Restart services
sudo systemctl start aisales-backend aisales-frontend

# 7. Verify
curl https://app.miempresa.com/api/v1/health
```

### Restore to a Different Server

```bash
# On the new server:
# 1. Install prerequisites (section 2 of installation guide)
# 2. Run the installer to create the database structure
# 3. Stop services
# 4. Restore the SQL dump (as above)
# 5. Update .env files with new server's secrets
# 6. Start services
```

---

## 8. Maintenance Tasks

### Daily

- [ ] Check `/api/v1/system/status` returns `healthy`
- [ ] Verify backup ran successfully (`ls -la /var/backups/`)
- [ ] Review error log for new errors

### Weekly

- [ ] Check disk usage (`df -h`)
- [ ] Review PostgreSQL slow queries:
  ```sql
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
  ```
- [ ] Review Redis memory usage (`redis-cli info memory`)
- [ ] Rotate Nginx access logs if needed

### Monthly

- [ ] Update SSL certificate (certbot renew)
- [ ] Analyze database performance:
  ```sql
  VACUUM ANALYZE;
  ```
- [ ] Review user list and deactivate inactive accounts
- [ ] Check for failed WhatsApp webhooks
- [ ] Review OpenAI API usage and costs
- [ ] Test backup restore on a staging environment

### Quarterly

- [ ] Apply system updates (apt update/upgrade)
- [ ] Review and update backup retention policies
- [ ] Security audit: verify all secrets have been rotated
- [ ] Performance benchmark with `/api/v1/system/status`
- [ ] Update documentation

---

## 9. Troubleshooting Guide

### Backend won't start

| Symptom | Cause | Solution |
|---------|-------|----------|
| `Config ERROR: DATABASE_URL is not set` | Missing or invalid .env | Check `backend/.env` exists and has `DATABASE_URL` |
| `Database connection FAILED` | PostgreSQL not running or bad credentials | `sudo systemctl status postgresql`; test with `psql` |
| `ModuleNotFoundError: No module named '...'` | Dependencies not installed | `source .venv/bin/activate && pip install -e ".[dev]"` |
| `Address already in use` | Port 8000 already occupied | `kill $(lsof -ti:8000)` then restart |

### Frontend shows 500 or blank page

| Symptom | Cause | Solution |
|---------|-------|----------|
| Blank page, console shows API errors | Backend not running | `sudo systemctl status aisales-backend` |
| "API URL not configured" | Wrong `NEXT_PUBLIC_API_BASE_URL` | Check `frontend/.env.local` |
| CSS broken | Build not complete | Run `npm run build` in frontend directory |

### WhatsApp not connecting

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Session expired" | Meta access token expired | Reconnect via WhatsApp settings page |
| "Webhook verification failed" | Webhook URL not accessible | Ensure the server is reachable from Meta's servers |
| "Message send failed" | Rate limited by Meta | The system manages rate limits automatically; wait and retry |

### AI features not working

| Symptom | Cause | Solution |
|---------|-------|----------|
| AI replies return empty | OpenAI API key not configured | Set `OPENAI_API_KEY` in `.env` and restart |
| "Insufficient quota" | OpenAI billing exhausted | Check OpenAI account billing |
| Slow AI responses | Network latency or model overload | The system uses GPT-4o-mini for optimal speed |

### Performance degradation

1. Check system resources: `htop`, `df -h`, `free -h`
2. Check PostgreSQL connections: `sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"`
3. Check Redis: `redis-cli ping`
4. Review slow queries: `tail -100 /opt/ai-sales-agent-saas/logs/api.log | grep "duration"`
5. Restart services if needed

---

## 10. Emergency Procedures

### Service Outage

1. **Check if the server is reachable**
   ```bash
   ping app.miempresa.com
   ```

2. **Check all services**
   ```bash
   sudo systemctl status aisales-backend aisales-frontend nginx postgresql redis
   ```

3. **Restart all services**
   ```bash
   sudo systemctl restart aisales-backend aisales-frontend nginx
   ```

4. **Check logs for the root cause**
   ```bash
   tail -50 /opt/ai-sales-agent-saas/logs/error.log
   journalctl -u aisales-backend --no-pager -n 50
   ```

5. **If database is corrupted, restore from backup** (see section 7)

### Security Breach

1. **Immediately suspend all companies**:
   ```sql
   UPDATE empresas SET status = 'suspended';
   ```

2. **Rotate all secrets** in `backend/.env`:
   - JWT_SECRET_KEY
   - ADMIN_JWT_SECRET_KEY
   - WHATSAPP_ENCRYPTION_KEY
   - Database password

3. **Restart services**:
   ```bash
   sudo systemctl restart aisales-backend
   ```

4. **Revoke all active sessions** by changing JWT secrets

5. **Audit logs** for suspicious activity:
   ```bash
   grep -i "error\|failed\|unauthorized" /opt/ai-sales-agent-saas/logs/api.log | head -100
   ```

6. **Contact support** at support@ai-sales-agent.com

### Data Loss

1. **Stop services immediately** to prevent further writes
2. **Identify the latest valid backup** from `/var/backups/`
3. **Restore database** (see section 7.2)
4. **Restore configuration** (see section 7.2)
5. **Verify data integrity** by checking customer count, order count, etc.
6. **Document the incident** including root cause and recovery steps

---

*Documentation v1.0 — AI Sales Agent SaaS Enterprise*
