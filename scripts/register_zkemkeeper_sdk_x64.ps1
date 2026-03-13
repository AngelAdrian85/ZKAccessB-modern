Param(
  [string]$SdkDir = 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\Resurse\Standalone SDK-6.3.1.55\SDK\x64',
  [switch]$Json
)

$ErrorActionPreference = 'Stop'

function Resolve-RepoSdkDir {
  try {
    $repoRoot = Split-Path -Path $PSScriptRoot -Parent
    $resurseRoot = Join-Path $repoRoot 'Resurse'
    if(-not (Test-Path $resurseRoot)){
      return $null
    }
    $dllMatch = Get-ChildItem -Path $resurseRoot -Recurse -Filter 'zkemkeeper.dll' -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match '[\\/](x64|64bits)[\\/]zkemkeeper\.dll$' } |
      Sort-Object FullName |
      Select-Object -First 1
    if($dllMatch){
      return $dllMatch.DirectoryName
    }
  } catch {}
  return $null
}

function Write-Result {
  param(
    [bool]$Ok,
    [string]$Message,
    [string]$ProgId = '',
    [bool]$AlreadyRegistered = $false,
    [bool]$NeedsAdmin = $false
  )

  $payload = [ordered]@{
    ok = $Ok
    message = $Message
    sdk_dir = $SdkDir
    prog_id = $ProgId
    already_registered = $AlreadyRegistered
    needs_admin = $NeedsAdmin
  }
  if ($Json) {
    $payload | ConvertTo-Json -Depth 4 -Compress
  } elseif ($Ok) {
    if ($AlreadyRegistered) {
      Write-Host "[ZKEM] Already registered via $ProgId"
    } else {
      Write-Host "[ZKEM] Registered successfully via $ProgId from $SdkDir"
    }
  } else {
    Write-Error $Message
  }
}

function Resolve-ProgId {
  foreach ($candidate in @('zkemkeeper.CZKEM', 'zkemkeeper.ZKEM.1')) {
    try {
      if ([type]::GetTypeFromProgID($candidate)) {
        return $candidate
      }
    } catch {}
  }
  return $null
}

function Test-Admin {
  try {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($current)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

try {
  if ((-not [string]::IsNullOrWhiteSpace($SdkDir)) -and (-not (Test-Path $SdkDir))) {
    $resolvedSdkDir = Resolve-RepoSdkDir
    if ($resolvedSdkDir) {
      $SdkDir = $resolvedSdkDir
    }
  }
  if (-not (Test-Path $SdkDir)) {
    throw "SDK directory not found: $SdkDir"
  }

  $zkemPath = Join-Path $SdkDir 'zkemkeeper.dll'
  if (-not (Test-Path $zkemPath)) {
    throw "Missing zkemkeeper.dll in: $SdkDir"
  }

  $existingProgId = Resolve-ProgId
  if ($existingProgId) {
    Write-Result -Ok $true -Message 'Already registered.' -ProgId $existingProgId -AlreadyRegistered $true
    exit 0
  }

  if (-not (Test-Admin)) {
    Write-Result -Ok $false -Message 'Administrator privileges are required to register zkemkeeper.dll.' -NeedsAdmin $true
    exit 1
  }

  $env:Path = "$SdkDir;" + $env:Path
  $regsvr32 = Join-Path $env:WINDIR 'System32\regsvr32.exe'
  $proc = Start-Process -FilePath $regsvr32 -ArgumentList @('/s', $zkemPath) -Wait -PassThru -WindowStyle Hidden
  if ($proc.ExitCode -ne 0) {
    throw "regsvr32 failed with exit code $($proc.ExitCode)"
  }

  $progId = Resolve-ProgId
  if (-not $progId) {
    throw 'zkemkeeper COM registration still not visible after regsvr32.'
  }

  Write-Result -Ok $true -Message 'Registered successfully.' -ProgId $progId
  exit 0
} catch {
  if ($Json) {
    Write-Result -Ok $false -Message $_.Exception.Message
    exit 1
  }
  throw
}
