Param(
  [string]$RedisUrl = 'redis://127.0.0.1:6379/0',
  [switch]$Docker
)

function Write-Info([string]$msg){ Write-Host "[REDIS] $msg" }
function Write-Warn([string]$msg){ Write-Warning "[REDIS] $msg" }

function Test-TcpPort {
  param(
    [string]$Host = '127.0.0.1',
    [int]$Port = 6379,
    [int]$TimeoutMs = 250
  )
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($Host, $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
    if(-not $ok){ try{ $client.Close() }catch{}; return $false }
    $client.EndConnect($iar)
    try{ $client.Close() }catch{}
    return $true
  } catch {
    try{ if($client){ $client.Close() } }catch{}
    return $false
  }
}

# Parse host/port (best-effort for redis://host:port/0)
$host = '127.0.0.1'
$port = 6379
try {
  if($RedisUrl -match '^redis://([^/]+)'){
    $hp = $Matches[1]
    if($hp -match '^(.*):(\d+)$'){
      $host = $Matches[1]
      $port = [int]$Matches[2]
    } else {
      $host = $hp
    }
  }
} catch {}

if(Test-TcpPort -Host $host -Port $port -TimeoutMs 250){
  Write-Info "Already listening on ${host}:${port}. Set REDIS_URL=${RedisUrl} and start tray_launch.ps1."
  exit 0
}

# 1) Try local redis-server.exe / redis-server on PATH
$redisCmd = $null
try { $redisCmd = (Get-Command redis-server -ErrorAction SilentlyContinue) } catch { $redisCmd = $null }
if($redisCmd){
  Write-Info "Starting redis-server from PATH..."
  try {
    Start-Process -FilePath $redisCmd.Source -ArgumentList @('--port', "$port") -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
  } catch {
    Write-Warn "Failed to start redis-server: $($_.Exception.Message)"
  }

  if(Test-TcpPort -Host $host -Port $port -TimeoutMs 400){
    Write-Info "Started. Use: `$env:REDIS_URL='${RedisUrl}'"
    exit 0
  }
}

# 2) Try Docker (opt-in or if -Docker passed)
$dockerCmd = $null
try { $dockerCmd = (Get-Command docker -ErrorAction SilentlyContinue) } catch { $dockerCmd = $null }
if($dockerCmd -and $Docker){
  Write-Info "Starting Redis via Docker (container name: zkaccessb_redis)..."
  try {
    $name = 'zkaccessb_redis'
    $exists = & docker ps -a --format "{{.Names}}" 2>$null | Where-Object { $_ -eq $name }
    if($exists){
      & docker start $name | Out-Null
    } else {
      & docker run -d --name $name -p ${port}:6379 redis:7-alpine | Out-Null
    }
    Start-Sleep -Milliseconds 600
  } catch {
    Write-Warn "Docker Redis start failed: $($_.Exception.Message)"
  }

  if(Test-TcpPort -Host $host -Port $port -TimeoutMs 700){
    Write-Info "Started. Use: `$env:REDIS_URL='${RedisUrl}'"
    exit 0
  }
}

Write-Warn "Redis is not running on ${host}:${port}."
Write-Info "Options:"
Write-Info "  A) Install a local Redis service and ensure redis-server is on PATH, then re-run this script"
Write-Info "  B) If you have Docker Desktop: re-run with -Docker"
Write-Info "After Redis is running, set: `$env:REDIS_URL='${RedisUrl}' and launch tray_launch.ps1"
exit 1
