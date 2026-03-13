param(
  [string]$Ip = '192.168.1.235',
  [int]$Port = 14370,
  [int]$MachineNumber = 1,
  [string]$CommPassword = 'Zk@123',
  [int]$Seconds = 600,
  [string]$LogPath = ''
)

$ErrorActionPreference = 'Stop'

if (-not $LogPath) {
  $LogPath = Join-Path (Get-Location) 'tmp_controller22_hid_poll.log'
}

Remove-Item $LogPath -ErrorAction SilentlyContinue

function Write-LogLine {
  param([string]$Line)
  $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $full = "$stamp $Line"
  Write-Host $full
  Add-Content -Path $LogPath -Value $full -Encoding UTF8
}

$zk = $null
try {
  $zk = New-Object -ComObject 'zkemkeeper.ZKEM.1'
  $okPwd = $zk.SetCommPasswordEx($CommPassword)
  Write-LogLine "PWD=$okPwd"

  $okConn = $zk.Connect_Net($Ip, $Port)
  Write-LogLine "CONNECT=$okConn IP=$Ip PORT=$Port"
  if (-not $okConn) {
    exit 2
  }

  $prevSignature = ''
  for ($i = 1; $i -le $Seconds; $i++) {
    $strCard = ''
    $hidCard = ''
    $cardProp = ''
    $strProp = ''
    $okStr = $false
    $okHid = $false

    try { $null = $zk.ReadRTLog($MachineNumber) } catch {}
    try { $null = $zk.GetRTLog($MachineNumber) } catch {}
    try { $okStr = [bool]$zk.GetStrCardNumber([ref]$strCard) } catch { $okStr = $false }
    try { $okHid = [bool]$zk.GetHIDEventCardNumAsStr([ref]$hidCard) } catch { $okHid = $false }
    try { $cardProp = [string]($zk.CardNumber($MachineNumber)) } catch { $cardProp = '' }
    try { $strProp = [string]($zk.STR_CardNumber($MachineNumber)) } catch { $strProp = '' }

    $signature = "OKSTR=$okStr|STR=[$strCard]|OKHID=$okHid|HID=[$hidCard]|CARDPROP=[$cardProp]|STRPROP=[$strProp]"
    $interesting = ($strCard -and $strCard -ne '0') -or ($hidCard -and $hidCard -ne '0') -or ($cardProp -and $cardProp -ne '0') -or ($strProp -and $strProp -ne '0')

    if ($interesting -or $signature -ne $prevSignature -or ($i % 10) -eq 0) {
      Write-LogLine "TICK=$i $signature"
      $prevSignature = $signature
    }

    Start-Sleep -Seconds 1
  }
}
finally {
  if ($zk) {
    try { $zk.Disconnect() | Out-Null } catch {}
  }
  Write-LogLine 'DISCONNECT=done'
}