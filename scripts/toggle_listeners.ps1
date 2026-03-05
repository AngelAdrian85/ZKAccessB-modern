param(
  [ValidateSet('acp','elatec')][string]$Target,
  [ValidateSet('enable','disable','set')][string]$Action,
  [string]$Value
)
$cfgPath = Join-Path $PSScriptRoot 'card_readers.json'
if(!(Test-Path $cfgPath)){
  Write-Host "[TOGGLE] Config not found, creating default"
  '{"acp":{"enabled":true,"port":9001},"elatec":{"enabled":true,"port":"COM3"}}' | Set-Content -Path $cfgPath -Encoding UTF8
}
try {
  $cfg = Get-Content $cfgPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
} catch {
  $msg = $_.Exception.Message
  Write-Warning "[TOGGLE] Invalid JSON in $cfgPath ($msg)"
  try {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    Copy-Item -LiteralPath $cfgPath -Destination "${cfgPath}.badjson.${ts}" -Force
  } catch {}
  Write-Host "[TOGGLE] Recreating default card_readers.json" -ForegroundColor Yellow
  '{"acp":{"enabled":true,"port":9001},"elatec":{"enabled":true,"port":"COM3"}}' | Set-Content -Path $cfgPath -Encoding UTF8
  $cfg = Get-Content $cfgPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
}
if($null -eq $cfg.$Target){ $cfg | Add-Member -NotePropertyName $Target -NotePropertyValue (@{}) }
if($Action -eq 'enable'){ $cfg.$Target.enabled = $true }
elseif($Action -eq 'disable'){ $cfg.$Target.enabled = $false }
elseif($Action -eq 'set'){
  if($Target -eq 'acp'){ $cfg.$Target.port = [int]$Value }
  else { $cfg.$Target.port = [string]$Value }
}
$cfg | ConvertTo-Json -Depth 3 | Set-Content -Path $cfgPath -Encoding UTF8
Write-Host "[TOGGLE] Updated $Target => $(($cfg.$Target | ConvertTo-Json -Compress))"
Write-Host "[TOGGLE] Restart tray to apply changes: tray_launch.ps1"
