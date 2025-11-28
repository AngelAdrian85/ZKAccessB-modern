#Requires -RunAsAdministrator
# Quick test script - verifies all dependencies are installed

$PROJECT_ROOT = Split-Path -Parent $PSCommandPath
$PYTHON_EXE = "$PROJECT_ROOT\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ZKAccessB - Dependency Verification                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$checks = @()

# 1. Python
Write-Host "1️⃣  Python..." -NoNewline
if (Test-Path $PYTHON_EXE) {
    $ver = & $PYTHON_EXE --version 2>&1
    Write-Host " ✅ $ver" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not found" -ForegroundColor Red
    $checks += $false
}

# 2. Django
Write-Host "2️⃣  Django..." -NoNewline
$result = & $PYTHON_EXE -c "import django; print(django.get_version())" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ $result" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    $checks += $false
}

# 3. ASGI (uvicorn)
Write-Host "3️⃣  ASGI (uvicorn)..." -NoNewline
$result = & $PYTHON_EXE -c "import uvicorn; print(uvicorn.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ $result" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ⚠️  Optional (WSGI fallback)" -ForegroundColor Yellow
    $checks += $true
}

# 4. Pillow (for images)
Write-Host "4️⃣  Pillow (images)..." -NoNewline
$result = & $PYTHON_EXE -c "import PIL; print(PIL.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ $result" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    $checks += $false
}

# 5. pystray
Write-Host "5️⃣  pystray (tray agent)..." -NoNewline
$result = & $PYTHON_EXE -c "import pystray; print('available')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ Installed" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    $checks += $false
}

# 6. Requests
Write-Host "6️⃣  Requests (HTTP)..." -NoNewline
$result = & $PYTHON_EXE -c "import requests; print(requests.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ $result" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    $checks += $false
}

# 7. manage.py
Write-Host "7️⃣  Django Site (manage.py)..." -NoNewline
$result = & $PYTHON_EXE "$PROJECT_ROOT\zkeco_modern\manage.py" --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ Working" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " ❌ Not found" -ForegroundColor Red
    $checks += $false
}

Write-Host ""
Write-Host "────────────────────────────────────────────────────────────" -ForegroundColor Gray
$passed = ($checks | Where-Object {$_}).Count
$total = $checks.Count

if ($passed -eq $total) {
    Write-Host "✅ ALL CHECKS PASSED ($passed/$total)" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now start the agent:" -ForegroundColor Green
    Write-Host "  powershell -ExecutionPolicy Bypass -File tray_launch.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "⚠️  SOME CHECKS FAILED ($passed/$total)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run setup first:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
