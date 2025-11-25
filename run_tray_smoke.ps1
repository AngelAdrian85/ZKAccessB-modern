# Runs the non-GUI tray smoke tests with the workspace venv
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host 'Cannot find .venv Python, falling back to system python'
  $python = 'python'
}
& $python (Join-Path $root 'tray_smoke_test.py')
