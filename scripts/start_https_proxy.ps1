Param(
  [Parameter(Mandatory = $true)][int]$UiPort,
  [Parameter(Mandatory = $true)][int]$AdmsPort,
  [Parameter(Mandatory = $true)][int]$HttpsPort,
  [string]$CaddyPath = '',
  [switch]$SkipCaddyBootstrap
)

$ErrorActionPreference = 'Stop'

function Get-CaddyBootstrapDir {
  return (Join-Path $PWD 'tools\caddy')
}

function Resolve-PublicHosts {
  $hosts = New-Object System.Collections.Generic.List[string]

  foreach($candidate in @(
    [string]$env:ZKACCESS_PUSH_PUBLIC_HOST,
    '127.0.0.1',
    'localhost'
  )){
    if(-not [string]::IsNullOrWhiteSpace($candidate) -and -not $hosts.Contains($candidate)){
      $hosts.Add($candidate)
    }
  }

  try {
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
      Where-Object {
        $_.IPAddress -and
        $_.IPAddress -ne '127.0.0.1' -and
        $_.PrefixOrigin -ne 'WellKnown'
      } |
      Sort-Object InterfaceMetric, SkipAsSource |
      ForEach-Object {
        if(-not [string]::IsNullOrWhiteSpace($_.IPAddress) -and -not $hosts.Contains($_.IPAddress)){
          $hosts.Add($_.IPAddress)
        }
      }
  } catch {}

  return @($hosts)
}

function Test-CaddyBinary {
  param([string]$BinaryPath)

  if([string]::IsNullOrWhiteSpace($BinaryPath) -or -not (Test-Path $BinaryPath)){
    return $false
  }

  try {
    $null = & $BinaryPath version 2>$null
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  }
}

function Resolve-CaddyDownloadUrl {
  $override = [string]($env:ZKACCESS_CADDY_DOWNLOAD_URL)
  if(-not [string]::IsNullOrWhiteSpace($override)){
    return $override
  }

  try {
    $resp = Invoke-WebRequest -Uri 'https://github.com/caddyserver/caddy/releases/latest' -UseBasicParsing
    $content = [string]($resp.Content)
    $match = [System.Text.RegularExpressions.Regex]::Match(
      $content,
      '/caddyserver/caddy/releases/download/[^"''<>\s]+/caddy_[^"''<>\s]+_windows_amd64\.zip'
    )
    if($match.Success){
      return ('https://github.com' + $match.Value)
    }
  } catch {}

  return 'https://github.com/caddyserver/caddy/releases/download/v2.11.2/caddy_2.11.2_windows_amd64.zip'
}

function Resolve-CaddyPath {
  param([string]$RequestedPath)

  $candidates = @()
  if($RequestedPath){ $candidates += $RequestedPath }
  if($env:ZKACCESS_CADDY_PATH){ $candidates += [string]$env:ZKACCESS_CADDY_PATH }
  $candidates += @(
    (Join-Path $PWD 'tools\caddy\caddy.exe'),
    (Join-Path $PWD 'caddy.exe'),
    'C:\Program Files\Caddy\caddy.exe',
    'C:\caddy\caddy.exe'
  )

  foreach($candidate in $candidates | Where-Object { $_ }){
    try {
      if(Test-Path $candidate){ return $candidate }
    } catch {}
  }

  try {
    $cmd = Get-Command caddy.exe -ErrorAction SilentlyContinue
    if($cmd -and $cmd.Source){ return [string]$cmd.Source }
  } catch {}

  return ''
}

function Install-CaddyBinary {
  param([string]$TargetDir)

  $downloadUrl = Resolve-CaddyDownloadUrl

  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  $zipPath = Join-Path $TargetDir 'caddy_windows_amd64.zip'
  $exePath = Join-Path $TargetDir 'caddy.exe'
  $tmpExePath = Join-Path $TargetDir 'caddy_download.tmp'

  Write-Host "[HTTPS] Downloading Caddy from $downloadUrl"
  Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

  if(Test-Path $exePath){
    Remove-Item -Force $exePath -ErrorAction SilentlyContinue
  }

  $signature = ''
  try {
    $headerBytes = Get-Content -Path $zipPath -Encoding Byte -TotalCount 2
    if($headerBytes -and $headerBytes.Count -ge 2){
      $signature = [System.Text.Encoding]::ASCII.GetString($headerBytes)
    }
  } catch {}

  if($signature -eq 'MZ'){
    Move-Item -Force $zipPath $exePath
    return $exePath
  }

  $expanded = $false
  try {
    Expand-Archive -Path $zipPath -DestinationPath $TargetDir -Force
    $expanded = $true
  } catch {
    $expanded = $false
  }

  if(-not $expanded){
    Move-Item -Force $zipPath $tmpExePath
    Move-Item -Force $tmpExePath $exePath
  }

  if(-not (Test-Path $exePath)){
    $foundExe = Get-ChildItem -Path $TargetDir -Filter 'caddy*.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if($foundExe){
      Copy-Item -Force $foundExe.FullName $exePath
    }
  }

  if(-not (Test-Path $exePath)){
    throw '[HTTPS] Caddy download completed but caddy.exe was not found in the extracted files.'
  }

  if(-not (Test-CaddyBinary -BinaryPath $exePath)){
    throw '[HTTPS] Downloaded caddy.exe is not runnable on this machine.'
  }

  return $exePath
}

$resolvedCaddy = Resolve-CaddyPath -RequestedPath $CaddyPath
if($resolvedCaddy -and -not (Test-CaddyBinary -BinaryPath $resolvedCaddy)){
  Write-Warning "[HTTPS] Existing caddy.exe is invalid: $resolvedCaddy"
  try {
    Remove-Item -Force $resolvedCaddy -ErrorAction SilentlyContinue
  } catch {}
  $resolvedCaddy = ''
}

if(-not $resolvedCaddy -and -not $SkipCaddyBootstrap){
  try {
    $resolvedCaddy = Install-CaddyBinary -TargetDir (Get-CaddyBootstrapDir)
  } catch {
    Write-Warning "[HTTPS] Failed to bootstrap caddy.exe automatically: $_"
  }
}

if(-not $resolvedCaddy){
  Write-Warning '[HTTPS] caddy.exe not found. HTTPS reverse proxy not started.'
  exit 0
}

$runtimeDir = Join-Path $PWD 'runtime'
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

$caddyFile = Join-Path $runtimeDir 'Caddyfile.zkaccessb'
$stdoutLog = Join-Path $PWD 'https_proxy_stdout.log'
$stderrLog = Join-Path $PWD 'https_proxy_stderr.log'
$siteLabels = @(
  Resolve-PublicHosts | ForEach-Object { "https://${_}:$HttpsPort" }
) -join ', '

if([string]::IsNullOrWhiteSpace($siteLabels)){
  $siteLabels = "https://127.0.0.1:$HttpsPort"
}

$cfg = @"
{
  admin off
  auto_https disable_redirects
  local_certs
}

$siteLabels {
  tls internal
  bind 0.0.0.0

  @iclock path /iclock/*
  handle @iclock {
    reverse_proxy 127.0.0.1:$AdmsPort
  }

  handle {
    reverse_proxy 127.0.0.1:$UiPort
  }
}
"@

Set-Content -Path $caddyFile -Value $cfg -Encoding UTF8

Write-Host "[HTTPS] Starting Caddy reverse proxy on port $HttpsPort (ui=$UiPort adms=$AdmsPort)"
Start-Process -FilePath $resolvedCaddy -ArgumentList @('run', '--config', $caddyFile, '--adapter', 'caddyfile') -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog | Out-Null