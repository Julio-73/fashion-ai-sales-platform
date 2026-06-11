#!/usr/bin/env bash
# =============================================================================
# AI Sales Agent SaaS — Automated Backup Script
# =============================================================================
# Creates PostgreSQL + Redis backups with rotation.
#
# Setup (run once):
#   sudo ./backup.sh --install
#
# Manual run:
#   sudo ./backup.sh
#
# Cron (daily at 3am):
#   0 3 * * * /opt/ai-sales-agent-saas/scripts/backup.sh --quiet
# =============================================================================

set -euo pipefail

BACKUP_DIR="/var/backups/ai-sales-agent-saas"
DB_NAME="ai_sales_agent_saas"
DB_USER="aisa_admin"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
QUIET=false

log() { [ "$QUIET" = false ] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --quiet) QUIET=true; shift ;;
    --install)
      mkdir -p "$BACKUP_DIR"
      chmod 750 "$BACKUP_DIR"
      echo "Backup directory created: $BACKUP_DIR"
      echo "Add to crontab:"
      echo "  0 3 * * * $(realpath "$0") --quiet"
      exit 0
      ;;
    *) echo "Usage: $0 [--quiet] [--install]"; exit 1 ;;
  esac
done

mkdir -p "$BACKUP_DIR"

# ── PostgreSQL Backup ────────────────────────────────
log "Starting PostgreSQL backup..."
DB_FILE="${BACKUP_DIR}/postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"
pg_dump -U "$DB_USER" -h 127.0.0.1 "$DB_NAME" | gzip > "$DB_FILE"
log "  Created: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"

# ── Redis Backup ─────────────────────────────────────
log "Starting Redis backup..."
REDIS_FILE="${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"
cp /var/lib/redis/dump.rdb "$REDIS_FILE" 2>/dev/null || log "  SKIP: Redis RDB not found"
log "  Created: $REDIS_FILE"

# ── Config Backup ────────────────────────────────────
log "Starting config backup..."
CONFIG_FILE="${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz"
tar czf "$CONFIG_FILE" \
  /opt/ai-sales-agent-saas/backend/.env \
  /opt/ai-sales-agent-saas/frontend/.env.local \
  2>/dev/null || log "  WARN: Some config files not found"

# ── Retention ────────────────────────────────────────
log "Cleaning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "redis_*.rdb" -mtime "+$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime "+$RETENTION_DAYS" -delete

log "Backup complete: ${BACKUP_DIR}"
