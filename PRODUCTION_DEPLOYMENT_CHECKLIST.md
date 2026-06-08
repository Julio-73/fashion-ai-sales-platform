# Production Deployment Checklist — Enterprise V1

> **Project:** AI Sales Agent SaaS
> **Version:** 1.0.0
> **Last Updated:** 2026-06-08

---

## Phase 0: Pre-Flight Checks

- [ ] Backend server responds at `/api/v1/health` → `status: "ok"`
- [ ] Frontend builds without errors: `npm run build`
- [ ] Database has seed data: `python scripts/demo_seed.py`
- [ ] All environment variables set in `.env` (production values)
- [ ] `APP_ENV` set to `production`
- [ ] `JWT_SECRET_KEY` rotated to a secure random value
- [ ] `OPENAI_API_KEY` configured (if using AI features)

---

## Phase 1: Infrastructure Setup

### Reverse Proxy & SSL
- [ ] Install nginx or Caddy as reverse proxy
- [ ] Configure SSL/TLS with Let's Encrypt (Certbot)
- [ ] Redirect HTTP → HTTPS
- [ ] Set up nginx config with:
  - Rate limiting
  - Request size limits (e.g., `client_max_body_size 10M`)
  - Proxy buffers
  - WebSocket support for live features

### PostgreSQL
- [ ] Set up PostgreSQL 15+ with replication
- [ ] Configure `pg_hba.conf` for SSL-only connections
- [ ] Create database `ai_sales_agent_saas` with proper encoding
- [ ] Create dedicated DB user (not `postgres` superuser)
- [ ] Run migrations: `alembic upgrade head`
- [ ] Set up daily automated backups
- [ ] Verify backup script: `scripts/backup_database.ps1`
- [ ] Verify restore script: `scripts/restore_database.ps1`

### Redis (Recommended)
- [ ] Install Redis 7+
- [ ] Configure with password
- [ ] Set `REDIS_URL` in `.env`
- [ ] Configure persistence (RDB/AOF)
- [ ] Set `maxmemory` policy

### Monitoring
- [ ] Set up Sentry for error tracking
- [ ] Add Prometheus metrics endpoint
- [ ] Configure log rotation (already implemented)
- [ ] Set up uptime monitoring (e.g., UptimeRobot, Pingdom)

---

## Phase 2: Backend Deployment

### Application Server
- [ ] Install Python 3.12+ and create virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set all `.env` variables for production
- [ ] Run with gunicorn + uvicorn workers:
  ```bash
  gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 --workers 4 --timeout 120 \
    --access-logfile - --error-logfile -
  ```
- [ ] Or use systemd service for process management
- [ ] Verify health endpoint returns `status: "ok"`

### Security Hardening
- [ ] JWT secret rotated (use `openssl rand -hex 64`)
- [ ] CORS origins set to production frontend URL
- [ ] Rate limiting configured and tested
- [ ] Swagger/Redoc disabled (auto-disabled when `APP_ENV=production`)
- [ ] File upload limits enforced
- [ ] Database SSL connection verified
- [ ] Security headers verified (CSP, HSTS, X-Frame-Options)
- [ ] All passwords follow complexity policy

---

## Phase 3: Frontend Deployment

### Build & Deploy
- [ ] Set `NEXT_PUBLIC_API_BASE_URL` to production API URL
- [ ] Run `npm run build` — verify zero errors
- [ ] Deploy built artifacts:
  - **Option A:** `npm start` with systemd (self-hosted)
  - **Option B:** Deploy to Vercel (recommended)
  - **Option C:** Static export + nginx (`next.config.mjs` output: 'export')
- [ ] Configure CDN for static assets
- [ ] Set up client-side error tracking (Sentry)

### Frontend Verification
- [ ] Login page renders correctly
- [ ] Admin login works
- [ ] All protected routes redirect to login
- [ ] Dashboard loads with data
- [ ] Pipeline (CRM) displays correctly
- [ ] Customer list loads
- [ ] Order list loads
- [ ] Inventory page loads
- [ ] WhatsApp integration config page loads
- [ ] Reports page loads
- [ ] Mobile responsive design verified

---

## Phase 4: Integration Testing

### API Smoke Tests
- [ ] `GET /api/v1/health` → 200
- [ ] `POST /api/v1/auth/login` → 200 with tokens
- [ ] `GET /api/v1/auth/me` → 200 (with auth header)
- [ ] `GET /api/v1/customers` → 200
- [ ] `POST /api/v1/customers` → 201
- [ ] `GET /api/v1/crm/customers` → 200
- [ ] `GET /api/v1/pipeline` → 200
- [ ] `GET /api/v1/orders` → 200
- [ ] `GET /api/v1/inventory` → 200
- [ ] `GET /api/v1/products` → 200
- [ ] `GET /api/v1/conversations` → 200
- [ ] `GET /api/v1/executive-dashboard/` → 200
- [ ] `GET /api/v1/automation/metrics` → 200

### Business Flow Test
- [ ] User registration → Login → Dashboard loads
- [ ] Create customer → Create pipeline deal → Move through stages
- [ ] Create order → Verify inventory deduction
- [ ] Create conversation → Add messages → AI reply (if configured)
- [ ] Run automation engine → Verify tasks created
- [ ] Generate report → Download PDF/XLSX

---

## Phase 5: Performance & Load Testing

- [ ] Run load test (locust/k6): 100 concurrent users
- [ ] Measure API response times (target: <200ms p95)
- [ ] Check database query performance
- [ ] Verify rate limiting at scale
- [ ] Test Redis cache hit ratios (if configured)
- [ ] Test file upload performance (if applicable)
- [ ] Run Lighthouse audit on frontend (target: 90+)

---

## Phase 6: Database Seeding

- [ ] Run demo seed script:
  ```bash
  cd backend
  python scripts/demo_seed.py
  ```
- [ ] Verify seed counts:
  - Clients: 100
  - Products: 20 (with variants)
  - Pipeline deals: 50
  - Conversations: 200 (with messages)
  - Orders: 100 (with items)
  - Automation rules: 5
  - Automation tasks: 50
  - Inventory items: 20

---

## Phase 7: Monitoring Go-Live

### First 24 Hours
- [ ] Monitor error logs for 500 errors
- [ ] Check slow query log
- [ ] Verify backup ran successfully
- [ ] Monitor server resource usage (CPU, RAM, disk)
- [ ] Check for any auth failures or brute force attempts

### First Week
- [ ] Review all error logs
- [ ] Optimize any slow endpoints
- [ ] Collect user feedback
- [ ] Adjust rate limiting as needed
- [ ] Verify all business flows work end-to-end

---

## Phase 8: Go/No-Go Decision

### Must Pass (Blockers)
- [ ] All API smoke tests pass
- [ ] Frontend builds without errors
- [ ] SSL/HTTPS configured
- [ ] JWT secret rotated from default
- [ ] Database backups automated
- [ ] No critical security vulnerabilities

### Should Pass (Strongly Recommended)
- [ ] Sentry error tracking configured
- [ ] Redis configured for rate limiting
- [ ] Load testing completed
- [ ] Seed data loaded for demo
- [ ] Production CORS origins set
- [ ] Database SSL enabled

### Nice to Have
- [ ] Prometheus metrics
- [ ] CI/CD pipeline
- [ ] Automated end-to-end tests
- [ ] Staging environment
- [ ] Blue-green deployment

---

## Final Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Developer | | | |
| QA Engineer | | | |
| DevOps | | | |
| Product Owner | | | |

---

## VPS Recommendation

| Tier | Provider | Specs | Est. Monthly Cost | Max Users |
|------|----------|-------|-------------------|-----------|
| **Minimum** | Hetzner CX22 | 2 vCPU, 4 GB RAM, 40 GB SSD | ~€8/mo | 50 concurrent |
| **Recommended** | Hetzner CX32 | 4 vCPU, 8 GB RAM, 80 GB SSD | ~€16/mo | 200 concurrent |
| **High Traffic** | Hetzner CX42 | 8 vCPU, 16 GB RAM, 160 GB SSD | ~€32/mo | 500+ concurrent |
| **Alternative** | DigitalOcean Basic | 4 vCPU, 8 GB RAM, 160 GB SSD | ~$48/mo | 200 concurrent |

**Alternative:** Deploy frontend on Vercel (free tier) + backend on Railway/Heroku for easy scaling.
