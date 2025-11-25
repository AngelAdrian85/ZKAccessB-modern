Param(
  [int]$Port = 8000,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv_new',
  [string]$TestModule = 'zkeco_modern.agent.test_core'
)

Write-Host "[INFO] Using venv: $Venv"
if(Test-Path .venv){ Write-Host "[INFO] Ignoring legacy '.venv' (corrupt)" }
if(!(Test-Path "$Venv\Scripts\python.exe")){
  Write-Host "[INFO] Creating virtual environment $Venv"
  py -3 -m venv $Venv
  if($LASTEXITCODE -ne 0){ Write-Error "[ERROR] venv creation failed"; exit 1 }
}
$py = Join-Path $Venv 'Scripts/python.exe'

Write-Host "[INFO] Installing dependencies"
& $py -m pip install --upgrade pip *> $null
& $py -m pip install -r requirements.txt
if($LASTEXITCODE -ne 0){ Write-Error "[ERROR] Dependency install failed"; exit 1 }

Write-Host "[INFO] Applying migrations"
& $py -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','$Settings'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')"
if($LASTEXITCODE -ne 0){ Write-Error "[ERROR] migrate failed"; exit 1 }

Write-Host "[INFO] Ensuring admin user"
& $py -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','$Settings'); import django; django.setup(); from django.contrib.auth import get_user_model; U=get_user_model(); import sys; ae=U.objects.filter(username='admin').exists(); print('Admin exists:', ae); import traceback; import sys;\nimport django" 
if($LASTEXITCODE -ne 0){ Write-Warning "[WARN] Admin check script failed" }

Write-Host "[INFO] Running tests: $TestModule"
& $py zkeco_modern/manage.py test $TestModule --verbosity=1
if($LASTEXITCODE -ne 0){ Write-Error "[ERROR] Tests failed"; exit 1 }

Write-Host "[INFO] Starting server on $Port"
& $py zkeco_modern/manage.py runserver 0.0.0.0:$Port
