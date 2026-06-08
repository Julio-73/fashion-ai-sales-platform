param(
    [string]$OutputDir = ".\backups",
    [string]$DbName = "ai_sales_agent_saas",
    [string]$DbUser = "postgres",
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 5432,
    [switch]$Compress = $true,
    [int]$KeepDays = 30
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path -Path $OutputDir -ChildPath "${DbName}_${timestamp}.dump"

if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "[BACKUP] Created output directory: $OutputDir"
}

$env:PGPASSWORD = $env:PGPASSWORD
if (-not $env:PGPASSWORD) {
    $env:PGPASSWORD = "postgres"
    Write-Host "[BACKUP] WARNING: Using default PGPASSWORD. Set env:PGPASSWORD for production."
}

Write-Host "[BACKUP] Starting database backup: $DbName@$DbHost`:$DbPort"
Write-Host "[BACKUP] Output: $backupFile"

$args = @(
    "-h", $DbHost,
    "-p", $DbPort,
    "-U", $DbUser,
    "-F", "c",
    "-f", $backupFile,
    "-d", $DbName,
    "-v"
)

try {
    & "pg_dump" $args 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[BACKUP] SUCCESS: Backup completed successfully."
        Write-Host "[BACKUP] File: $backupFile"

        if ($Compress) {
            $compressedFile = "${backupFile}.gz"
            try {
                if (Get-Command "gzip" -ErrorAction SilentlyContinue) {
                    & gzip -f $backupFile
                    Write-Host "[BACKUP] Compressed to: $compressedFile"
                } else {
                    Write-Host "[BACKUP] gzip not found, skipping compression."
                }
            } catch {
                Write-Host "[BACKUP] Compression skipped: $($_.Exception.Message)"
            }
        }
    } else {
        Write-Host "[BACKUP] FAILED: pg_dump exited with code $LASTEXITCODE"
        exit 1
    }
} catch {
    Write-Host "[BACKUP] ERROR: $($_.Exception.Message)"
    Write-Host "[BACKUP] Ensure PostgreSQL tools (pg_dump) are installed and in PATH."
    exit 1
}

$oldFiles = Get-ChildItem -Path $OutputDir -Filter "${DbName}_*.dump*" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays)
}
foreach ($f in $oldFiles) {
    Remove-Item -Path $f.FullName -Force
    Write-Host "[BACKUP] Cleaned up old backup: $($f.Name)"
}

Write-Host "[BACKUP] Done. Backups retained for $KeepDays days."
