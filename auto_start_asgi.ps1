Param(
  [int]$Port = 8000,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv_new',
  [string]$TestModule = 'zkeco_modern.agent.test_core',
  [switch]$SkipTests
)
Write-Host "[ASGI] Using venv: $Venv"
if(!(Test-Path "$Venv\Scripts\python.exe")){
  Write-Host "[ASGI] Creating virtual environment $Venv"; py -3 -m venv $Venv; if($LASTEXITCODE -ne 0){ Write-Error 'venv failed'; exit 1 }
}
$py = Join-Path $Venv 'Scripts/python.exe'
Write-Host "[ASGI] Installing dependencies (ensure daphne)"
& $py -m pip install --upgrade pip *> $null
& $py -m pip install -r requirements.txt
if($LASTEXITCODE -ne 0){ Write-Error 'dependency install failed'; exit 1 }
Write-Host "[ASGI] Migrating"
& $py -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','$Settings'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')"
if(!$SkipTests){
  Write-Host "[ASGI] Running tests"
  & $py zkeco_modern/manage.py test $TestModule --verbosity=1
  if($LASTEXITCODE -ne 0){ Write-Error 'tests failed'; exit 1 }
}
Write-Host "[ASGI] Starting daphne (websocket ready) on port $Port"
# Ensure we run from inside zkeco_modern so 'zkeco_config' package is importable
Push-Location zkeco_modern
& $py -m daphne -b 0.0.0.0 -p $Port zkeco_config.asgi:application
Pop-Location
