param(
  [string]$Ip = "192.168.1.235",
  [int]$Port = 4370,
  [string]$Password = "",
  [int]$TimeoutMs = 3000,
  [string]$OutputPath = "probe_controller_direct_4370.latest.txt",
  [ValidateSet('TCP','UDP')]
  [string]$Protocol = 'TCP'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
  throw "Python environment not found at $pythonExe"
}

Push-Location $repoRoot
try {
  $env:DJANGO_SETTINGS_MODULE = 'zkeco_config.settings'
  $cmd = @(
    'manage.py',
    'probe_plcommpro_flow',
    '--ip', $Ip,
    '--port', [string]$Port,
    '--strict-port',
    '--protocol', $Protocol,
    '--timeout-ms', [string]$TimeoutMs,
    '--write-probe'
  )
  if ($Password -ne '') {
    $cmd += @('--password', $Password)
  }
  $stdoutPath = Join-Path $repoRoot 'tmp_probe_controller_direct_4370.stdout.txt'
  $stderrPath = Join-Path $repoRoot 'tmp_probe_controller_direct_4370.stderr.txt'
  Remove-Item $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
  $proc = Start-Process -FilePath $pythonExe -ArgumentList $cmd -WorkingDirectory $repoRoot -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
  $merged = @()
  if (Test-Path $stderrPath) {
    $merged += Get-Content -Path $stderrPath
  }
  if (Test-Path $stdoutPath) {
    $merged += Get-Content -Path $stdoutPath
  }
  $merged | Tee-Object -FilePath $OutputPath
  if ($proc.ExitCode -ne 0) {
    throw "probe_plcommpro_flow exited with code $($proc.ExitCode)"
  }
}
finally {
  Pop-Location
}