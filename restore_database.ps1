param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$DbName = "ai_sales_agent_saas",
    [string]$DbUser = "postgres",
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 5432,
    [switch]$DropExisting = $false,
    [switch]$DryRun = $false
)

if (-not (Test-Path -Path $BackupFile)) {
    Write-Host "[RESTORE] ERROR: Backup file not found: $BackupFile"
    exit 1
}

$env:PGPASSWORD = $env:PGPASSWORD
if (-not $env:PGPASSWORD) {
    $env:PGPASSWORD = "postgres"
    Write-Host "[RESTORE] WARNING: Using default PGPASSWORD. Set env:PGPASSWORD for production."
}

Write-Host "[RESTORE] === DATABASE RESTORE ==="
Write-Host "[RESTORE] Database: $DbName@$DbHost`:$DbPort"
Write-Host "[RESTORE] Backup file: $BackupFile"
Write-Host "[RESTORE] Drop existing: $DropExisting"

if ($DryRun) {
    Write-Host "[RESTORE] DRY RUN: No changes will be made."
    Write-Host "[RESTORE] Would restore: $BackupFile -> $DbName"
    exit 0
}

Write-Host "[RESTORE] WARNING: This will overwrite the database '$DbName'."
Write-Host "[RESTORE] Press Ctrl+C within 5 seconds to cancel..."
Start-Sleep -Seconds 5

if ($DropExisting) {
    Write-Host "[RESTORE] Dropping existing connections to $DbName..."
    $killArgs = @(
        "-h", $DbHost,
        "-p", $DbPort,
        "-U", $DbUser,
        "-d", "postgres",
        "-c", "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DbName' AND pid <> pg_backend_pid();"
    )
    & "psql" $killArgs 2>&1 | Out-Null

    Write-Host "[RESTORE] Dropping database $DbName..."
    $dropArgs = @(
        "-h", $DbHost,
        "-p", $DbPort,
        "-U", $DbUser,
        "-d", "postgres",
        "-c", "DROP DATABASE IF EXISTS $DbName;"
    )
    & "psql" $dropArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[RESTORE] ERROR: Failed to drop database."
        exit 1
    }

    Write-Host "[RESTORE] Creating database $DbName..."
    $createArgs = @(
        "-h", $DbHost,
        "-p", $DbPort,
        "-U", $DbUser,
        "-d", "postgres",
        "-c", "CREATE DATABASE $DbName;"
    )
    & "psql" $createArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[RESTORE] ERROR: Failed to create database."
        exit 1
    }
} else {
    Write-Host "[RESTORE] Restoring into existing database (use -DropExisting for clean restore)..."
}

Write-Host "[RESTORE] Starting restore..."

$restoreArgs = @(
    "-h", $DbHost,
    "-p", $DbPort,
    "-U", $DbUser,
    "-d", $DbName,
    "-F", "c",
    "-v"
)

if ($BackupFile -like "*.gz") {
    $tempFile = [System.IO.Path]::GetTempFileName()
    try {
        if (Get-Command "gzip" -ErrorAction SilentlyContinue) {
            & gzip -d -c $BackupFile -f > $tempFile
            $restoreArgs += @("-f", $tempFile)
        } else {
            Write-Host "[RESTORE] ERROR: gzip not found, cannot decompress."
            exit 1
        }
    } catch {
        Write-Host "[RESTORE] ERROR decompressing: $($_.Exception.Message)"
        exit 1
    }
} else {
    $restoreArgs += @("-f", $BackupFile)
}

try {
    & "pg_restore" $restoreArgs 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[RESTORE] SUCCESS: Database restored successfully."
    } else {
        Write-Host "[RESTORE] WARNING: pg_restore completed with warnings (exit code $LASTEXITCODE)."
        Write-Host "[RESTORE] This is often normal. Verify data integrity manually."
    }
} catch {
    Write-Host "[RESTORE] ERROR: $($_.Exception.Message)"
    Write-Host "[RESTORE] Ensure PostgreSQL tools (pg_restore) are installed and in PATH."
    exit 1
} finally {
    if ($tempFile -and (Test-Path $tempFile)) {
        Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[RESTORE] Restore complete."
