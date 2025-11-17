<#
installs dependencies into the project's venv and runs lint/tests.
Usage:
  .\scripts\install_deps_and_test.ps1 [-VenvPath <path-to-venv>] [-UpgradePip]

If -VenvPath is not provided the script will try common venv folders in the repo.
#>
param(
    [string]$VenvPath = "",
    [switch]$UpgradePip
)

function Find-Venv {
    param()
    $candidates = @("venv311", "venv", "fresh_venv", "new_venv", ".venv", "env")
    foreach ($c in $candidates) {
        $p = Join-Path -Path $PSScriptRoot -ChildPath "..\$c"
        $p = [System.IO.Path]::GetFullPath($p)
        if (Test-Path (Join-Path $p 'Scripts\Activate.ps1')) { return $p }
    }
    # also check project root Scripts folder
    $p = Join-Path -Path $PSScriptRoot -ChildPath '..\Scripts'
    $p = [System.IO.Path]::GetFullPath($p)
    if (Test-Path (Join-Path $p 'Activate.ps1')) { return (Split-Path $p -Parent) }
    return $null
}

if (-not $VenvPath -or $VenvPath -eq '') {
    $found = Find-Venv
    if ($found) { $VenvPath = $found } else {
        Write-Host "No venv detected automatically. Please pass -VenvPath <path> to this script." -ForegroundColor Yellow
        exit 2
    }
}

$activate = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (-not (Test-Path $activate)) {
    Write-Error "Activate.ps1 not found under $VenvPath\Scripts. Ensure the venv path is correct."
    exit 3
}

Write-Host "Using venv: $VenvPath"

# Activate the venv in this shell
. $activate

# Upgrade pip optionally
if ($UpgradePip) {
    python -m pip install --upgrade pip
}

# Install main requirements
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$reqMain = Join-Path $root 'requirements.txt'
$reqDev = Join-Path $root 'requirements-dev.txt'
$reqLock = Join-Path $root 'requirements-lock.txt'

if (Test-Path $reqLock) {
    Write-Host "Installing pinned requirements from requirements-lock.txt"
    python -m pip install -r $reqLock
} elseif (Test-Path $reqMain) {
    Write-Host "Installing requirements from requirements.txt"
    python -m pip install -r $reqMain
}

if (Test-Path $reqDev) {
    Write-Host "Installing dev requirements from requirements-dev.txt"
    python -m pip install -r $reqDev
}

# Run linters and tests if available
Write-Host "Running linter (ruff) if installed..."
try {
    & python -m ruff check .
} catch {
    Write-Host "ruff not available or linting failed (it's optional). Continue to tests." -ForegroundColor Yellow
}

Write-Host "Running pytest (quick run)..."
try {
    & python -m pytest -q
} catch {
    Write-Host "pytest failed or not installed. Install dev requirements and re-run this script." -ForegroundColor Red
    exit 4
}

Write-Host "Done. If tests passed you can continue porting or run the full test suite/staging step." -ForegroundColor Green
