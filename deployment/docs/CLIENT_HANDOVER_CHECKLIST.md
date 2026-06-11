# AI Sales Agent SaaS — Client Handover Checklist v1.0

> Lista de verificación previa a la entrega del sistema a un cliente.  
> Versión: 1.0 — Junio 2026

---

## Instructions

Before delivering the system to the client, verify each item.  
Mark each box as you complete it. Unverified items must be resolved before handover.

**Symbols**: ✅ Complete | ❌ Incomplete | ⚠️ Warning | N/A Not applicable

---

## 1. Installation Verification

- [ ] **Server meets requirements**
  - CPU: 4 cores minimum
  - RAM: 8 GB minimum
  - Disk: 50 GB SSD minimum
  - OS: Ubuntu 24.04 LTS or Windows Server 2022

- [ ] **Prerequisites installed**
  - PostgreSQL 15+ (running, enabled on boot)
  - Redis 7+ (running, enabled on boot)
  - Python 3.11+
  - Node.js 18.x+
  - Nginx (Linux)

- [ ] **Application deployed**
  - Code is in `/opt/ai-sales-agent-saas/` (Linux) or `C:\AI-Sales-Agent\` (Windows)
  - Backend virtual environment created and working
  - Frontend dependencies installed

- [ ] **Database created**
  - Database `ai_sales_agent_saas` exists
  - User `aisa_admin` exists with proper permissions
  - Migrations ran successfully (`alembic upgrade head`)

- [ ] **Backend running**
  - `curl /api/v1/health` returns `status: "ok"`
  - `curl /api/v1/system/status` returns `status: "healthy"`
  - Backend runs with 4 workers
  - Logs directory exists and is writable

- [ ] **Frontend built**
  - `npm run build` completed without errors
  - Frontend serves correctly at port 3000

---

## 2. Security Verification

- [ ] **JWT secrets generated and configured**
  - `JWT_SECRET_KEY` is a random 64-char string
  - `ADMIN_JWT_SECRET_KEY` is a different random 64-char string
  - Both differ from each other

- [ ] **JWT configuration**
  - `ACCESS_TOKEN_EXPIRE_MINUTES=15` (or shorter)
  - `REFRESH_TOKEN_EXPIRE_DAYS=30` (or shorter)
  - `JWT_ALGORITHM=HS256`

- [ ] **WhatsApp encryption key configured**
  - `WHATSAPP_ENCRYPTION_KEY` is set to a random hex string
  - WhatsApp tokens are encrypted at rest via Fernet

- [ ] **CORS configured**
  - `BACKEND_CORS_ORIGINS` points to the production frontend URL
  - No `localhost` entries in production

- [ ] **Security headers verified**
  - `Content-Security-Policy` is set
  - `Strict-Transport-Security` is set (max-age=31536000)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`

- [ ] **Rate limiting active**
  - Login: 10 requests/minute/IP
  - Admin login: 5 requests/minute/IP
  - Global: 100 requests/minute/IP
  - Redis fallback to in-memory is documented

- [ ] **Database connection secure**
  - `DATABASE_URL` uses `127.0.0.1` (not public IP)
  - PostgreSQL port 5432 is not exposed externally
  - Database password is strong and unique

- [ ] **API documentation disabled in production**
  - Swagger UI (`/docs`) disabled in production
  - ReDoc (`/redoc`) disabled in production

---

## 3. User Management Verification

- [ ] **Super admin created**
  - Admin user exists with super_admin role
  - Default password has been changed

- [ ] **Company (Tenant) created**
  - At least one company exists
  - Company status is `active`
  - Correct plan assigned (`enterprise`, `professional`, or `starter`)

- [ ] **Users created as needed**
  - Owner user created
  - Admin user(s) created
  - Sales agents created with proper roles

- [ ] **Roles verified**
  - Roles match the permission matrix in the onboarding guide
  - Each user has correct module access

- [ ] **Password policy**
  - Minimum password length: 10 characters
  - Users can reset their own passwords

---

## 4. Backup Verification

- [ ] **Backup script installed**
  - `deployment/scripts/backup.sh` or `backup.ps1` is in place
  - Backup directory exists: `/var/backups/ai-sales-agent-saas/`
  - Backup directory has correct permissions (750)

- [ ] **Backup scheduled**
  - Cron job or scheduled task configured for daily 3:00 AM
  - Backup runs successfully without errors

- [ ] **Backup test**
  - Run a manual backup: `sudo ./backup.sh`
  - Verify backup file was created: `ls -la /var/backups/`
  - Verify backup file is not empty
  - Test restore on a staging environment

- [ ] **Retention policy configured**
  - Backups older than 30 days are automatically deleted
  - Notification configured for backup failures (optional)

---

## 5. Domain & SSL Verification

- [ ] **Domain configured**
  - Domain resolves to the server IP
  - `A` record or `CNAME` is configured
  - Domain propagation verified

- [ ] **SSL certificate installed**
  - Let's Encrypt or commercial SSL installed
  - Certificate valid for at least 60 days
  - Auto-renewal configured (certbot)

- [ ] **Nginx configured**
  - HTTP to HTTPS redirect active
  - API proxy configured for `/api/`
  - Frontend proxy configured for `/`
  - WebSocket support configured for AI Live

- [ ] **Domain in configuration**
  - `BACKEND_CORS_ORIGINS` uses the production domain
  - `NEXT_PUBLIC_API_BASE_URL` uses `https://` domain

---

## 6. WhatsApp Verification

- [ ] **WhatsApp Business API account**
  - Meta Business Account is verified
  - WhatsApp Business phone number is registered
  - Phone number is not sandbox (production number)

- [ ] **WhatsApp connected in the system**
  - Connection flow completed successfully
  - Status shows "Connected" in WhatsApp settings
  - Webhook URL is configured and verified

- [ ] **WhatsApp test**
  - Send a test message from the system
  - Receive a test message (customer → system)
  - Verify message appears in conversations panel

- [ ] **WhatsApp metrics**
  - `/api/v1/whatsapp/metrics` returns valid data
  - `is_configured: true`

---

## 7. AI Verification

- [ ] **OpenAI API key configured**
  - `OPENAI_API_KEY` is set in `.env`
  - Key has access to `gpt-4o-mini` model
  - Billing is active with sufficient credits

- [ ] **AI Features enabled**
  - Sales Insights enabled
  - Smart Recommendations enabled
  - AI reply suggestions enabled (if desired)
  - Sentiment Analysis enabled
  - Intent Detection enabled

- [ ] **AI test**
  - Open a conversation → AI suggests a reply
  - Create a pipeline deal → AI scores it automatically
  - Navigate to AI Sales dashboard → data is displayed

---

## 8. Reports Verification

- [ ] **Sales Report (PDF)**
  - Generate via UI: Reports → Sales → PDF
  - Verify PDF contains tables and charts

- [ ] **Sales Report (Excel)**
  - Generate via UI: Reports → Sales → Excel
  - Verify Excel contains data with correct columns

- [ ] **Pipeline Report (PDF)**
  - Generate via UI: Reports → Pipeline → PDF
  - Verify funnel data is present

- [ ] **Pipeline Report (Excel)**
  - Generate via UI: Reports → Pipeline → Excel
  - Verify data is correct

- [ ] **CRM Report** (PDF and Excel)
- [ ] **Inventory Report** (PDF and Excel)
- [ ] **Executive Dashboard** loads with real data

---

## 9. Automation Verification

- [ ] **Automation engine running**
  - Scheduler is active
  - `GET /api/v1/automation/metrics` returns data

- [ ] **At least one automation rule active**
  - Rule exists and is enabled
  - Trigger condition is configured
  - Action is configured

- [ ] **Automation test**
  - Create a rule (e.g., "follow-up after 3 days")
  - Verify rule appears in the rules list
  - Verify scheduled tasks are created

---

## 10. Final Verification

- [ ] **Smoke test passed**
  - Run `deployment/scripts/smoke_test.sh`
  - All 31 API checks pass
  - 0 failures

- [ ] **Performance baseline recorded**
  - `/api/v1/health` response time < 50ms
  - `/api/v1/system/status` response time < 50ms
  - Backend memory usage < 500 MB

- [ ] **Error log is clean**
  - `logs/error.log` has no unexpected errors
  - No repeated error patterns

- [ ] **Documentation delivered**
  - `CUSTOMER_INSTALLATION_GUIDE.md`
  - `ADMIN_OPERATIONS_MANUAL.md`
  - `CUSTOMER_ONBOARDING.md`
  - `CLIENT_HANDOVER_CHECKLIST.md` (this document)

- [ ] **Source code delivered**
  - Delivery package (zip/tar)
  - All configuration templates
  - Installation scripts

- [ ] **Customer contact established**
  - Technical contact name and email
  - Support email: support@ai-sales-agent.com
  - Escalation process defined

---

## Handover Summary

| Section | Status | Notes |
|---------|--------|-------|
| 1. Installation | ⬜ | |
| 2. Security | ⬜ | |
| 3. Users | ⬜ | |
| 4. Backup | ⬜ | |
| 5. Domain & SSL | ⬜ | |
| 6. WhatsApp | ⬜ | |
| 7. AI | ⬜ | |
| 8. Reports | ⬜ | |
| 9. Automation | ⬜ | |
| 10. Final | ⬜ | |

**Handover approved by**: _________________  
**Date**: _________________  
**Customer signature**: _________________

---

*Documentation v1.0 — AI Sales Agent SaaS Enterprise*
