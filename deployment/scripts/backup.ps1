# =============================================================================
# AI Sales Agent SaaS — Automated Backup Script (Windows)
# =============================================================================
# Creates PostgreSQL backup with rotation.
#
# Setup scheduled task (daily at 3am):
#   powershell -ExecutionPolicy Bypass -File backup.ps1 -Install
#
# Manual run:
#   powershell -ExecutionPolicy Bypass -File backup.ps1
#
# Prerequisites:
#   - PostgreSQL pg_dump in PATH
#   - %APPDATA%\postgresql\pgpass.conf configured:
#       127.0.0.1:5432:ai_sales_agent_saas:aisa_admin:your_password
# =============================================================================

param(
  [switch]$Install = $false,
  [switch]$Quiet = $false
)

$BackupDir = "C:\ProgramData\AI-Sales-Agent\backups"
$DbName = "ai_sales_agent_saas"
$RetentionDays = 30
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Write-Log { if (-not $Quiet) { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $args" } }

if ($Install) {
  New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
  Write-Host "Backup directory created: $BackupDir"
  Write-Host ""
  Write-Host "Create pgpass.conf at: $env:APPDATA\postgresql\pgpass.conf"
  Write-Host "  Content: 127.0.0.1:5432:ai_sales_agent_saas:aisa_admin:your_password"
  Write-Host ""
  Write-Host "To schedule daily backup at 3am, run as Administrator:"
  Write-Host '  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File backup.ps1 -Quiet"'
  Write-Host '  $trigger = New-ScheduledTaskTrigger -Daily -At 03:00am'
  Write-Host '  Register-ScheduledTask -TaskName "AI-Sales-Agent-Backup" -Action $action -Trigger $trigger -RunLevel Highest'
  exit 0
}

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# ── PostgreSQL Backup ────────────────────────────────
Write-Log "Starting PostgreSQL backup..."
$DbFile = Join-Path $BackupDir "postgres_${DbName}_${Timestamp}.sql"
& pg_dump -U aisa_admin -h 127.0.0.1 $DbName -f $DbFile 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Log "  Created: $DbFile"
} else {
  Write-Log "  FAILED: pg_dump exit code $LASTEXITCODE. Ensure pgpass.conf is configured."
}

# ── Config Backup ────────────────────────────────────
Write-Log "Starting config backup..."
$ConfigFile = Join-Path $BackupDir "config_${Timestamp}.zip"
$BackendEnv = Join-Path $PSScriptRoot "..\backend\.env"
$FrontendEnv = Join-Path $PSScriptRoot "..\frontend\.env.local"
if (Test-Path $BackendEnv) {
  Compress-Archive -Path $BackendEnv, $FrontendEnv -DestinationPath $ConfigFile -Force
  Write-Log "  Created: $ConfigFile"
} else {
  Write-Log "  WARN: .env files not found"
}

# ── Retention ────────────────────────────────────────
Write-Log "Cleaning backups older than ${RetentionDays} days..."
Get-ChildItem $BackupDir -Filter "postgres_*.sql" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } | Remove-Item -Force
Get-ChildItem $BackupDir -Filter "config_*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } | Remove-Item -Force

Write-Log "Backup complete: ${BackupDir}"
