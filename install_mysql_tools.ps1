# Install MySQL Tools (mysqldump) and update agent configuration
# Usage: powershell -ExecutionPolicy Bypass -File .\install_mysql_tools.ps1
# Optional: -ForceReinstall to reinstall even if mysqldump exists
param(
  [switch]$ForceReinstall,
  [switch]$EnableRoutinesEvents
)
$ErrorActionPreference = 'Stop'
Function Info($m){ Write-Host $m -ForegroundColor Cyan }
Function Warn($m){ Write-Host $m -ForegroundColor Yellow }
Function Fail($m){ Write-Host $m -ForegroundColor Red }

# 1. Detect existing mysqldump
$existing = Get-ChildItem -Path (Join-Path $PSScriptRoot 'mysql') -Filter mysqldump.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $existing) {
  # search common program files locations
  foreach ($base in @($env:ProgramFiles, $env:ProgramFilesx86)) {
    if ($base -and (Test-Path $base)) {
      $candidate = Get-ChildItem -Path $base -Filter mysqldump.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($candidate) { $existing = $candidate; break }
    }
  }
}
if ($existing -and -not $ForceReinstall) {
  Info "Found mysqldump: $($existing.FullName)"
} else {
  Info 'mysqldump not found or reinstall forced.'
  # 2. Attempt winget install of MySQL Server minimal tools
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($winget) {
    Info 'Installing MySQL Server via winget (may take a while)...'
    try { winget install --accept-source-agreements --accept-package-agreements Oracle.MySQL -h } catch { Warn 'winget install failed or requires elevation.' }
  } else {
    Warn 'winget not available; please install MySQL manually from https://dev.mysql.com/downloads/.'
  }
  # re-scan after install
  $existing = $null
  foreach ($base in @($env:ProgramFiles, $env:ProgramFilesx86)) {
    if ($base -and (Test-Path $base)) {
      $candidate = Get-ChildItem -Path $base -Filter mysqldump.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($candidate) { $existing = $candidate; break }
    }
  }
}
if (-not $existing) { Fail 'mysqldump.exe still not found. Aborting.'; exit 2 }
Info "Using mysqldump: $($existing.FullName)"

# 3. Update agent_controller.ini mysql_bin path (robust whitespace-insensitive key handling)
$iniDir = Join-Path $PSScriptRoot 'zkeco_modern'
$iniPath = Join-Path $iniDir 'agent_controller.ini'
if (-not (Test-Path $iniPath)) { Fail "Config file not found: $iniPath"; exit 3 }
Function Set-IniValue {
  param($Lines, [string]$Key, [string]$Value)
  $pattern = "^\s*$Key\s*="
  $found = $false
  $out = @()
  foreach ($l in $Lines) {
    if ($l -match $pattern) {
      $out += "$Key=$Value"
      $found = $true
    } else { $out += $l }
  }
  if (-not $found) { $out += "$Key=$Value" }
  return $out
}

$cfgLines = Get-Content $iniPath
$binDir = Split-Path $existing.FullName -Parent
$cfgLines = Set-IniValue -Lines $cfgLines -Key 'mysql_bin' -Value $binDir
# Also repair any accidental nested mysql under zkeco_modern (prefer root-level mysql paths)
$cfgLines = ($cfgLines | ForEach-Object {
  if ($_ -match '^\s*mysql_bin\s*=') { $_ -replace 'zkeco_modern\\mysql\\bin','mysql\\bin' }
  elseif ($_ -match '^\s*database_path\s*=') { $_ -replace 'zkeco_modern\\mysql\\data','mysql\\data' }
  else { $_ }
})
if ($EnableRoutinesEvents) {
  $cfgLines = Set-IniValue -Lines $cfgLines -Key 'dump_flags' -Value '--routines --events'
  Info 'Enabled routines/events dump flags.'
} else {
  # Ensure key exists (empty) if not present
  $hasDump = $false
  foreach ($l in $cfgLines) { if ($l -match '^\s*dump_flags\s*=') { $hasDump = $true; break } }
  if (-not $hasDump) { $cfgLines = Set-IniValue -Lines $cfgLines -Key 'dump_flags' -Value '' }
}
$cfgLines | Set-Content $iniPath -Encoding UTF8
Info "Updated mysql_bin (whitespace-safe) in agent_controller.ini to $binDir"

# 4. Quick version test
$version = (& $existing.FullName --version) 2>&1 | Select-Object -First 1
Info "mysqldump version: $version"

# 5. Optional immediate backup test (headless tray invocation)
Info 'Testing backup via tray agent headless...' 
& .\.venv\Scripts\python.exe .\zkeco_modern\tray_agent.py --headless --auto --run-server --backup-interval=0 --set=backup_retention=5 | Out-Null

# 6. Show last 3 backups (PowerShell 5 Join-Path supports only two segments per call)
$modernDir = Join-Path $PSScriptRoot 'zkeco_modern'
$backupDir = Join-Path $modernDir 'backups'
if (Test-Path $backupDir) {
  Get-ChildItem $backupDir -Filter db_backup_*.sql | Sort-Object LastWriteTime -Desc | Select-Object -First 3 | ForEach-Object { Info "Backup: $($_.Name)" }
}

Info 'Install + integration complete.'
if ($EnableRoutinesEvents) { Info 'Note: routines/events may fail on legacy MySQL 5.0.' }
exit 0
