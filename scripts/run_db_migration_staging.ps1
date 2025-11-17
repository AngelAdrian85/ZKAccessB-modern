<#
Helper: run_db_migration_staging.ps1

What it does:
- Uses the repository's `zkeco_modern/docker-compose.yml` to bring up a Postgres staging DB and the web service.
- Waits for Postgres to accept connections, runs Django migrations in the `web` container context, then runs the example user-migration script from the runbook.

Preconditions:
- Docker and docker-compose (or Docker Desktop) must be installed and running on the host.
- You should run this from the repo root in PowerShell.

Usage:
  .\scripts\run_db_migration_staging.ps1

Notes:
- The script attempts to be non-destructive and uses the credentials declared in `zkeco_modern/docker-compose.yml`.
- You can edit the script to change the path to the sample ETL script or adjust wait timeouts.
#>

Set-StrictMode -Version Latest

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "docker is not installed or not in PATH. Install Docker Desktop and re-run this script."
    exit 1
}

$composeFile = "zkeco_modern/docker-compose.yml"
if (-not (Test-Path $composeFile)) {
    Write-Error "docker-compose.yml not found at $composeFile"
    exit 1
}

Write-Host "Bringing up Postgres + web containers (detached)..."
docker-compose -f $composeFile up -d --build

Write-Host "Waiting for Postgres to become available on db:5432..."
# Poll Postgres from host via docker exec
function Wait-ForPostgres($containerName, $timeoutSeconds = 120) {
    $start = Get-Date
    while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSeconds)) {
        $res = docker exec $containerName pg_isready -U zkeco -d zkeco_db 2>&1
        if ($LASTEXITCODE -eq 0) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

# Get Postgres container name
$dbContainer = (docker ps --filter "ancestor=postgres:15" --format "{{.Names}}" | Select-Object -First 1)
if (-not $dbContainer) {
    Write-Warning "Could not determine Postgres container by image name; trying service name 'zkeco_modern_db_1'"
    $dbContainer = "zkeco_modern_db_1"
}

if (-not (Wait-ForPostgres $dbContainer 180)) {
    Write-Error "Postgres did not become ready in time. Check docker logs: docker logs $dbContainer"
    exit 1
}

Write-Host "Postgres ready. Running Django migrations inside the web container..."

# Run migrations via docker-compose exec (allow for Django settings env var in compose)
docker-compose -f $composeFile exec -T web sh -c "python manage.py migrate --noinput"

Write-Host "Creating admin user (if ADMIN_* env vars provided in compose) and collecting static..."
docker-compose -f $composeFile exec -T web sh -c "python manage.py collectstatic --noinput || true"

# Optional: run the example migration script from runbook (if present)
$etlScript = "zkeco_modern/scripts/migrate_mysql_to_postgres_example.py"
if (Test-Path $etlScript) {
    Write-Host "Running example ETL script inside the web container: $etlScript"
    docker-compose -f $composeFile exec -T web sh -c "python manage.py shell < $etlScript"
} else {
    Write-Host "ETL example script not found at $etlScript — skipping."
}

Write-Host "Staging DB and migrations finished. Run tests against Postgres with:"
Write-Host "  DJANGO_SETTINGS_MODULE=zkeco_config.settings python -m pytest -q"
