<#
Run full local automation:
- create/ensure .venv_clean exists
- install requirements and dev requirements
- run ruff (format), mypy, pytest (with coverage)
- if Docker is available: build and run docker-compose for zkeco_modern
#>
param(
    [switch]$SkipDocker
)

Write-Host "=== Full automation runner: start ==="

$venvPath = Join-Path $PSScriptRoot '.venv_clean'
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtualenv .venv_clean..."
    python -m venv .venv_clean --clear --without-pip
    .\.venv_clean\Scripts\python.exe -m ensurepip --default-pip
}

& .\.venv_clean\Scripts\python.exe -m pip install --upgrade pip
& .\.venv_clean\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv_clean\Scripts\python.exe -m pip install -r requirements-dev.txt

# Run format/lint/type/test
& .\.venv_clean\Scripts\python.exe -m ruff format zkeco_modern || Write-Host "ruff format completed"
& .\.venv_clean\Scripts\python.exe -m ruff check zkeco_modern || Write-Host "ruff found issues"
& .\.venv_clean\Scripts\python.exe -m mypy zkeco_modern --config-file "$PSScriptRoot\mypy.ini"

# Run tests with coverage
Set-Location zkeco_modern
$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"
& "$PSScriptRoot\.venv_clean\Scripts\python.exe" -m coverage run -m pytest -q
& "$PSScriptRoot\.venv_clean\Scripts\python.exe" -m coverage report -m

# Optionally start docker compose
if (-not $SkipDocker) {
    docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker detected — starting docker-compose up..."
        Set-Location $PSScriptRoot\zkeco_modern
        docker compose up --build -d
        Write-Host "Waiting for Postgres..."
        for ($i=0; $i -lt 60; $i++) {
            docker compose exec -T db pg_isready -U zkeco -d zkeco_db 2>$null
            if ($LASTEXITCODE -eq 0) { Write-Host "Postgres ready"; break }
            Start-Sleep -Seconds 2
        }
        docker compose exec -T web python manage.py migrate --noinput
        Write-Host "Containers are up; visit http://localhost:8000/admin"
    } else {
        Write-Host "Docker not found — skipping container start."
    }
}

Write-Host "=== Full automation runner: done ==="