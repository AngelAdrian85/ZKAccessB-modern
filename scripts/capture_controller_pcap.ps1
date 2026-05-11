param(
  [string]$ControllerIp = '192.168.1.235',
  [int[]]$Ports = @(4370, 14370, 8091),
  [int]$Seconds = 20,
  [string]$Interface = '',
  [string]$OutputPath = '',
  [string]$TsharkPath = '',
  [switch]$ListInterfaces,
  [switch]$SkipAnalysis,
  [switch]$OpenFolder
)

$ErrorActionPreference = 'Stop'

function Resolve-TsharkPath {
  param([string]$PreferredPath = '')

  $candidates = @()
  if ($PreferredPath) { $candidates += $PreferredPath }
  try {
    $cmd = Get-Command tshark -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { $candidates += $cmd.Source }
  } catch {}
  $candidates += @(
    'C:\Program Files\Wireshark\tshark.exe',
    'C:\Program Files (x86)\Wireshark\tshark.exe'
  )

  foreach ($candidate in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw 'tshark.exe was not found. Install Wireshark with TShark or pass -TsharkPath.'
}

function Get-TsharkInterfaces {
  param([string]$BinaryPath)

  $rows = & $BinaryPath -D 2>$null
  $parsed = @()
  foreach ($row in $rows) {
    if ($row -match '^\s*(\d+)\.\s+(.*)$') {
      $parsed += [pscustomobject]@{
        Index = [int]$Matches[1]
        Label = $Matches[2].Trim()
      }
    }
  }
  return $parsed
}

function Resolve-TsharkInterface {
  param(
    [array]$Interfaces,
    [string]$Requested = ''
  )

  if (-not $Interfaces -or $Interfaces.Count -eq 0) {
    throw 'No tshark capture interfaces were found.'
  }

  if ($Requested) {
    if ($Requested -match '^\d+$') {
      $match = $Interfaces | Where-Object { $_.Index -eq [int]$Requested } | Select-Object -First 1
      if ($match) { return $match }
    }

    $match = $Interfaces | Where-Object {
      $_.Label -like "*$Requested*"
    } | Select-Object -First 1
    if ($match) { return $match }

    throw "Requested interface '$Requested' was not found in tshark -D output."
  }

  $preferred = $Interfaces | Where-Object {
    $_.Label -match 'Ethernet' -and $_.Label -notmatch 'Loopback|Adapter for loopback|Npcap Loopback'
  } | Select-Object -First 1
  if ($preferred) { return $preferred }

  $fallback = $Interfaces | Where-Object {
    $_.Label -notmatch 'Loopback|Adapter for loopback|Npcap Loopback'
  } | Select-Object -First 1
  if ($fallback) { return $fallback }

  return $Interfaces | Select-Object -First 1
}

function Resolve-PythonPath {
  param([string]$RepoRoot)

  $venvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
  if (Test-Path $venvPython) {
    return @($venvPython)
  }

  try {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
      return @($py.Source, '-3')
    }
  } catch {}

  try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
      return @($python.Source)
    }
  } catch {}

  throw 'No Python interpreter was found for the analyzer.'
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$tshark = Resolve-TsharkPath -PreferredPath $TsharkPath
$interfaces = @(Get-TsharkInterfaces -BinaryPath $tshark)

if ($ListInterfaces) {
  $interfaces | Format-Table -AutoSize | Out-String | Write-Host
  return
}

$selectedInterface = Resolve-TsharkInterface -Interfaces $interfaces -Requested $Interface

$captureFilter = "host $ControllerIp"
if ($Ports -and $Ports.Count -gt 0) {
  $tcpFilter = ($Ports | ForEach-Object { "tcp port $_" }) -join ' or '
  if ($tcpFilter) {
    $captureFilter = "$captureFilter and ($tcpFilter)"
  }
}

$captureDir = Join-Path $repoRoot 'captures\wireshark'
if (-not (Test-Path $captureDir)) {
  New-Item -ItemType Directory -Path $captureDir -Force | Out-Null
}

if (-not $OutputPath) {
  $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $safeIp = $ControllerIp.Replace('.', '_')
  $OutputPath = Join-Path $captureDir ("controller_${safeIp}_$timestamp.pcapng")
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir -and -not (Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "[TSHARK] Binary: $tshark"
Write-Host "[TSHARK] Interface: $($selectedInterface.Index) [$($selectedInterface.Label)]"
Write-Host "[TSHARK] Capture filter: $captureFilter"
Write-Host "[TSHARK] Duration: $Seconds s"
Write-Host "[TSHARK] Output: $OutputPath"

& $tshark -i $selectedInterface.Index -f $captureFilter -a "duration:$Seconds" -w $OutputPath

if ($LASTEXITCODE -ne 0) {
  throw "tshark capture failed with exit code $LASTEXITCODE"
}

Write-Host "[TSHARK] Capture completed: $OutputPath"

if (-not $SkipAnalysis) {
  $pythonCmd = @(Resolve-PythonPath -RepoRoot $repoRoot)
  $analyzer = Join-Path $repoRoot 'scripts\analyze_controller_pcap.py'
  $pythonExe = $pythonCmd[0]
  $pythonArgs = @()
  if ($pythonCmd.Count -gt 1) {
    $pythonArgs += $pythonCmd[1..($pythonCmd.Count - 1)]
  }
  $pythonArgs += @($analyzer, '--pcap', $OutputPath, '--controller-ip', $ControllerIp)
  if ($Ports -and $Ports.Count -gt 0) {
    foreach ($port in $Ports) {
      $pythonArgs += @('--port', "$port")
    }
  }

  Write-Host "[ANALYZE] Running analyzer..."
  & $pythonExe @pythonArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Analyzer failed with exit code $LASTEXITCODE"
  }
}

if ($OpenFolder) {
  Start-Process explorer.exe $outputDir
}
