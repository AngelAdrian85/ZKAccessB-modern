<#
Start the docker-compose development environment for zkeco_modern.
This script builds the images, waits for Postgres, runs migrations and ensures a superuser exists.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Starting docker-compose for zkeco_modern..."
Set-Location $PSScriptRoot

# Check if Docker is available first to avoid hard failure on systems without Docker
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "Docker is not installed or not on PATH."
    Write-Host "If you want to run the application without Docker, use the local venv instructions below."
    Write-Host "Exiting run_docker_dev.ps1."
    return
}

docker compose up --build -d

Write-Host "Waiting for Postgres to be ready..."
for ($i=0; $i -lt 60; $i++) {
    docker compose exec -T db pg_isready -U zkeco -d zkeco_db 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "Postgres ready"; break }
    Start-Sleep -Seconds 2
}

Write-Host "Running migrations inside web container..."
docker compose exec -T web python manage.py migrate --noinput

Write-Host "Ensuring superuser exists (admin/adminpass)..."
# Use a one-line python command to avoid bash/heredoc syntax in PowerShell
$py = 'from django.contrib.auth import get_user_model; User = get_user_model();'
$py += '\nif not User.objects.filter(username="admin").exists():'
$py += ' User.objects.create_superuser("admin", "admin@example.com", "adminpass"); print("Created admin superuser")'
$py += ' else: print("Admin user already exists")'
docker compose exec -T web python -c $py

Write-Host "Logs (web): tailing for 5s..."
docker compose logs --since 5s --no-color web | Select-Object -First 200

Write-Host "Open http://localhost:8000/admin to log in with admin/adminpass"