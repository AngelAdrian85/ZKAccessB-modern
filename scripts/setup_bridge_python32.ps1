Param(
  [string]$Version = '3.11.9',
  [string]$DestDir = 'tools\\python32'
)

$ErrorActionPreference = 'Stop'

function Info($m){ Write-Host "[PY32] $m" -ForegroundColor Cyan }
function Warn($m){ Write-Warning "[PY32] $m" }

$root = (Resolve-Path $PSScriptRoot\..).Path
$dest = Join-Path $root $DestDir

# Python embeddable package (x86) – no install, just unzip.
# Example: https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip
$zipName = "python-$Version-embed-win32.zip"
$url = "https://www.python.org/ftp/python/$Version/python-$Version-embed-win32.zip"

Info "Destination: $dest"

if(Test-Path (Join-Path $dest 'python.exe')){
  Info "Already present: $(Join-Path $dest 'python.exe')"
  exit 0
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null

$tmpZip = Join-Path $env:TEMP $zipName
Info "Downloading $url"
try {
  Invoke-WebRequest -Uri $url -OutFile $tmpZip -UseBasicParsing
} catch {
  throw "Download failed. Check internet/proxy/TLS. URL=$url Error=$($_.Exception.Message)"
}

Info "Extracting to $dest"
try {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::ExtractToDirectory($tmpZip, $dest)
} catch {
  throw "Extract failed: $($_.Exception.Message)"
}

if(-not (Test-Path (Join-Path $dest 'python.exe'))){
  throw "python.exe missing after extract. Dest=$dest"
}

# Quick validation: must be 32-bit + python3
Info "Validating interpreter"
$out = & (Join-Path $dest 'python.exe') -S -c "import struct,sys; print(struct.calcsize('P')*8); print(sys.version_info[0])"
if($LASTEXITCODE -ne 0){ throw "Validation command failed" }
$lines = @($out)
$bits = [int]$lines[0]
$major = [int]$lines[1]
if($bits -ne 32){ throw "Expected 32-bit, got $bits" }
if($major -lt 3){ throw "Expected Python 3, got $major" }

Info "OK. You can now run tray_launch; it will auto-pick tools/python32/python.exe for plcommpro bridge."
Info "Optional env override: set ZKACCESS_PYBRIDGE=$((Join-Path $dest 'python.exe'))"
