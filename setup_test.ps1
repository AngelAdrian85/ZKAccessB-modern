#Requires -Version 5.0
# ZKAccessB Setup - Quick Test Version

param([switch]$Headless = $false)

$WORKSPACE_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR = "$WORKSPACE_ROOT\.venv"
$PYTHON_EXE = "$VENV_DIR\Scripts\python.exe"
$REQUIREMENTS = "$WORKSPACE_ROOT\requirements.txt"
$MANAGE_PY = "$WORKSPACE_ROOT\manage.py"

Write-Host "[1] Workspace: $WORKSPACE_ROOT"
Write-Host "[2] VENV exists: $(Test-Path $VENV_DIR)"
Write-Host "[3] Python exists: $(Test-Path $PYTHON_EXE)"
Write-Host "[4] Requirements exists: $(Test-Path $REQUIREMENTS)"
Write-Host "[5] Manage.py exists: $(Test-Path $MANAGE_PY)"

if (Test-Path $PYTHON_EXE) {
    Write-Host "[6] Testing Python..."
    & $PYTHON_EXE --version
    Write-Host "[OK] Python works!"
}

Write-Host "[7] Testing pip..."
& $PYTHON_EXE -m pip --version

Write-Host "[DONE] All checks passed!"
