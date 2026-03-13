Param(
  [Parameter(Mandatory = $true)][string]$Ip,
  [int]$Port = 4370,
  [int]$MachineNumber = 1,
  [string]$ServerUrl = 'http://127.0.0.1:8000',
  [int]$DeviceId = 0,
  [string]$DoorId = '',
  [string]$DoorPk = '',
  [string]$Source = 'zkemkeeper-event',
  [string]$SdkDir = 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\Resurse\Standalone SDK-6.3.1.55\SDK\x64',
  [string]$DumpFile = '',
  [string]$CommPassword = '',
  [switch]$AutoRegister,
  [int]$ReconnectDelaySeconds = 5
)

$ErrorActionPreference = 'Stop'
$script:RepoRoot = Split-Path -Path $PSScriptRoot -Parent

function Resolve-RepoSdkDir {
  try {
    $resurseRoot = Join-Path $script:RepoRoot 'Resurse'
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

if ((-not [string]::IsNullOrWhiteSpace($SdkDir)) -and (-not (Test-Path $SdkDir))) {
  $resolvedSdkDir = Resolve-RepoSdkDir
  if ($resolvedSdkDir) {
    $SdkDir = $resolvedSdkDir
  }
}
if ([string]::IsNullOrWhiteSpace($DumpFile)) {
  $suffix = if ($DeviceId -gt 0) { "controller$DeviceId" } else { 'events' }
  $DumpFile = Join-Path $script:RepoRoot "zkemkeeper_event_dump_$suffix.jsonl"
}
$script:HeartbeatPath = Join-Path $env:USERPROFILE 'zkeco_reader_heartbeat_zkemkeeper.json'
$script:PushUrl = ($ServerUrl.TrimEnd('/')) + '/agent/api/cards/read/push/'
$script:ErrorUrl = ($ServerUrl.TrimEnd('/')) + '/agent/api/listeners/error/'
$script:BridgeTag = "zkemkeeper:$Ip`:$Port"
$script:ActivePort = $Port
$script:EventIds = @()
$script:RegisteredEventNames = @()
$script:EventCount = 0
$script:LastEventName = ''
$script:LastCard = ''
$script:LastPin = ''
$script:ProgId = ''
$script:ConnectedSince = ''
$script:EventDumpFile = $DumpFile

function Get-EffectiveCommPassword {
  if (-not [string]::IsNullOrWhiteSpace($CommPassword)) {
    return [string]$CommPassword
  }
  foreach ($envName in @('ZKACCESS_ZKEMKEEPER_COMM_PASSWORD', 'ZKACCESS_DEFAULT_COMM_PASSWORD')) {
    try {
      $candidate = [string](Get-Item -Path ("Env:{0}" -f $envName) -ErrorAction SilentlyContinue).Value
      if (-not [string]::IsNullOrWhiteSpace($candidate)) {
        return $candidate
      }
    } catch {}
  }
  return ''
}

$script:EffectiveCommPassword = Get-EffectiveCommPassword

function Merge-Hashtable {
  param(
    [hashtable]$Target,
    [hashtable]$Updates
  )
  if ($null -eq $Updates) { return }
  foreach ($entry in $Updates.GetEnumerator()) {
    $Target[$entry.Key] = $entry.Value
  }
}

function Write-JsonUtf8NoBom {
  param(
    [string]$Path,
    [string]$Json
  )
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Json, $utf8)
}

function Update-TrayStatusSnapshot {
  param(
    [string]$Status,
    [string]$Message
  )
  try {
    $trayStatusPath = Join-Path $script:RepoRoot 'tray_status.json'
    $current = [ordered]@{}
    if (Test-Path $trayStatusPath) {
      try {
        $loaded = Get-Content $trayStatusPath -Raw | ConvertFrom-Json
        if ($loaded) {
          foreach ($prop in $loaded.PSObject.Properties) {
            $current[$prop.Name] = $prop.Value
          }
        }
      } catch {}
    }
    $trayState = 'PORNESTE'
    if ($Status -in @('connected', 'event')) {
      $trayState = 'ON'
    } elseif ($Status -eq 'error') {
      $trayState = 'EROARE'
    }
    $current['zkemkeeper_enabled'] = $true
    $current['zkemkeeper'] = $trayState
    $current['zkemkeeper_status'] = $Status
    $current['zkemkeeper_message'] = $Message
    $current['zkemkeeper_target'] = "${Ip}:$($script:ActivePort)"
    $current['zkemkeeper_prog_id'] = $script:ProgId
    $current['zkemkeeper_device_id'] = $DeviceId
    $current['zkemkeeper_door_id'] = $DoorId
    $current['zkemkeeper_door_pk'] = $DoorPk
    $current['zkemkeeper_dump_file'] = $script:EventDumpFile
    $current['zkemkeeper_event_count'] = $script:EventCount
    $current['zkemkeeper_last_event'] = $script:LastEventName
    $current['zkemkeeper_last_card'] = $script:LastCard
    $current['zkemkeeper_last_pin'] = $script:LastPin
    $current['zkemkeeper_connected_since'] = $script:ConnectedSince
    $current['zkemkeeper_registered_events'] = @($script:RegisteredEventNames)
    Write-JsonUtf8NoBom -Path $trayStatusPath -Json ($current | ConvertTo-Json -Depth 8)
  } catch {}
}

function Write-Heartbeat {
  param(
    [string]$Status,
    [string]$Message = '',
    [hashtable]$Extra = @{}
  )
  try {
    $hb = [ordered]@{
      ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
      ts_iso = [DateTime]::UtcNow.ToString('o')
      source = 'zkemkeeper'
      bridge_tag = $script:BridgeTag
      ip = $Ip
      port = $script:ActivePort
      machine_number = $MachineNumber
      status = $Status
      message = $Message
      prog_id = $script:ProgId
      device_id = $DeviceId
      door_id = $DoorId
      door_pk = $DoorPk
      dump_file = $script:EventDumpFile
      event_count = $script:EventCount
      last_event = $script:LastEventName
      last_card = $script:LastCard
      last_pin = $script:LastPin
      connected_since = $script:ConnectedSince
      registered_events = @($script:RegisteredEventNames)
    }
    Merge-Hashtable -Target $hb -Updates $Extra
    Write-JsonUtf8NoBom -Path $script:HeartbeatPath -Json ($hb | ConvertTo-Json -Depth 4)
    Update-TrayStatusSnapshot -Status $Status -Message $Message
  } catch {}
}

function Report-BridgeError {
  param([string]$Message)
  try {
    Invoke-RestMethod -Method Post -Uri $script:ErrorUrl -ContentType 'application/json' -Body (@{
      name = 'zkemkeeper'
      message = $Message
    } | ConvertTo-Json -Depth 4) | Out-Null
  } catch {}
}

function Normalize-Scalar {
  param($Value)
  if ($null -eq $Value) { return '' }
  try {
    return [string]$Value
  } catch {
    return ''
  }
}

function Convert-ArgRecord {
  param($Value)
  $typeName = ''
  try {
    if ($null -ne $Value) {
      $typeName = $Value.GetType().FullName
    }
  } catch {}
  return [ordered]@{
    type = $typeName
    text = Normalize-Scalar $Value
  }
}

function Get-PropertyMap {
  param($InputObject)
  $map = @{}
  if ($null -eq $InputObject) { return $map }
  try {
    $members = $InputObject | Get-Member -MemberType Property, NoteProperty -ErrorAction SilentlyContinue
    foreach ($m in @($members)) {
      try {
        $map[$m.Name] = Normalize-Scalar ($InputObject.($m.Name))
      } catch {}
    }
  } catch {}
  return $map
}

function Write-EventDump {
  param(
    [string]$EventName,
    [hashtable]$Properties,
    [object[]]$SourceArgs,
    [string]$ResolvedCard,
    [string]$ResolvedPin,
    [string]$EventArgsText,
    [string]$SenderType
  )

  try {
    $dumpDir = Split-Path -Path $script:EventDumpFile -Parent
    if ($dumpDir) {
      New-Item -Path $dumpDir -ItemType Directory -Force | Out-Null
    }
    $entry = [ordered]@{
      ts_iso = [DateTime]::UtcNow.ToString('o')
      bridge_tag = $script:BridgeTag
      event_index = $script:EventCount
      event_name = $EventName
      ip = $Ip
      port = $script:ActivePort
      machine_number = $MachineNumber
      prog_id = $script:ProgId
      device_id = $DeviceId
      door_id = $DoorId
      door_pk = $DoorPk
      resolved_card = $ResolvedCard
      resolved_pin = $ResolvedPin
      comm_password_present = (-not [string]::IsNullOrWhiteSpace($script:EffectiveCommPassword))
      sender_type = $SenderType
      event_args_text = $EventArgsText
      event_properties = $Properties
      source_args = @($SourceArgs | ForEach-Object { Convert-ArgRecord $_ })
    }
    Add-Content -Path $script:EventDumpFile -Value ($entry | ConvertTo-Json -Depth 8 -Compress) -Encoding UTF8
  } catch {}
}

function Try-GetHidCardString {
  param($ComObject)

  if ($null -eq $ComObject) { return '' }
  try {
    $holder = ''
    $ok = $ComObject.GetHIDEventCardNumAsStr([ref]$holder)
    if ($ok) {
      $candidate = (Normalize-Scalar $holder).Trim()
      if ($candidate -and $candidate -notin @('0', '00000000')) {
        return $candidate
      }
    }
  } catch {}
  return ''
}

function Apply-CommPassword {
  param($ComObject)

  $password = [string]$script:EffectiveCommPassword
  if ($null -eq $ComObject -or [string]::IsNullOrWhiteSpace($password)) {
    return @{ attempted = $false; method = ''; ok = $false; message = '' }
  }

  try {
    $ok = $ComObject.SetCommPasswordEx($password)
    return @{ attempted = $true; method = 'SetCommPasswordEx'; ok = [bool]$ok; message = '' }
  } catch {
    $msg = $_.Exception.Message
  }

  try {
    if ($password -match '^\d+$') {
      $ok = $ComObject.SetCommPassword([int]$password)
      return @{ attempted = $true; method = 'SetCommPassword'; ok = [bool]$ok; message = '' }
    }
  } catch {
    if (-not $msg) { $msg = $_.Exception.Message }
  }

  return @{ attempted = $true; method = 'error'; ok = $false; message = ([string]$msg) }
}

function Resolve-CardFromEvent {
  param(
    $ComObject,
    [string]$EventName,
    [hashtable]$Properties,
    [object[]]$SourceArgs
  )

  $explicitKeys = @(
    'CardNumber', 'card_number', 'cardno', 'CardNo', 'HIDNumber', 'HIDNum',
    'dwHIDNum', 'dwHIDNumber', 'EventCardNum', 'EventCardNumber'
  )
  $hidString = ''
  if ($EventName -eq 'OnHIDNum') {
    $hidString = Try-GetHidCardString -ComObject $ComObject
    if ($hidString) {
      return $hidString
    }
  }
  foreach ($key in $explicitKeys) {
    if ($Properties.ContainsKey($key)) {
      $candidate = (Normalize-Scalar $Properties[$key]).Trim()
      if ($candidate -and $candidate -notin @('0', '00000000')) {
        return $candidate
      }
    }
  }

  $numericArgs = @()
  foreach ($arg in @($SourceArgs)) {
    $candidate = (Normalize-Scalar $arg).Trim()
    if ($candidate -match '^\d+$' -and $candidate -notin @([string]$MachineNumber, '0')) {
      $numericArgs += $candidate
    }
  }

  if ($EventName -eq 'OnHIDNum' -and $numericArgs.Count -gt 0) {
    return [string]$numericArgs[-1]
  }
  return ''
}

function Resolve-PinFromEvent {
  param(
    [hashtable]$Properties,
    [object[]]$SourceArgs
  )

  foreach ($key in @('EnrollNumber', 'dwEnrollNumber', 'PIN', 'Pin', 'EnrollNo')) {
    if ($Properties.ContainsKey($key)) {
      $candidate = (Normalize-Scalar $Properties[$key]).Trim()
      if ($candidate) { return $candidate }
    }
  }

  foreach ($arg in @($SourceArgs)) {
    $candidate = (Normalize-Scalar $arg).Trim()
    if ($candidate -and $candidate -match '^\d+$') {
      return $candidate
    }
  }
  return ''
}

function Post-EventPayload {
  param(
    [string]$EventName,
    [hashtable]$Properties,
    [object[]]$SourceArgs,
    [string]$ResolvedCard = '',
    [string]$ResolvedPin = ''
  )

  $card = $ResolvedCard
  $pin = $ResolvedPin
  if (-not $card) {
    $card = Resolve-CardFromEvent -EventName $EventName -Properties $Properties -SourceArgs $SourceArgs
  }
  if (-not $pin) {
    $pin = Resolve-PinFromEvent -Properties $Properties -SourceArgs $SourceArgs
  }
  if (-not $card -and -not $pin) {
    return
  }

  $payload = [ordered]@{
    source = $Source
    verify_access = $true
    remote_open = $false
    card_number = $card
    card_number_raw = $card
    controller_pin = $pin
    zkemkeeper_event = $EventName
    zkemkeeper_properties = $Properties
    zkemkeeper_source_args = @($SourceArgs | ForEach-Object { Normalize-Scalar $_ })
    zkemkeeper_hid_card = if ($EventName -eq 'OnHIDNum') { Try-GetHidCardString -ComObject $Sender } else { '' }
  }
  if ($DeviceId -gt 0) { $payload.device_id = $DeviceId }
  if ($DoorId) { $payload.door_id = $DoorId }
  if ($DoorPk) { $payload.door_pk = $DoorPk }

  try {
    Invoke-RestMethod -Method Post -Uri $script:PushUrl -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 8) | Out-Null
    Write-Heartbeat -Status 'event' -Message ("$EventName card=$card pin=$pin")
  } catch {
    Report-BridgeError ("zkemkeeper push failed: " + $_.Exception.Message)
  }
}

function Ensure-ProgId {
  foreach ($candidate in @('zkemkeeper.CZKEM', 'zkemkeeper.ZKEM.1')) {
    try {
      $type = [type]::GetTypeFromProgID($candidate)
      if ($type) {
        return $candidate
      }
    } catch {}
  }

  if (-not $AutoRegister) {
    throw 'zkemkeeper COM is not registered. Run scripts/register_zkemkeeper_sdk_x64.ps1 as Administrator or use -AutoRegister.'
  }

  $registerScript = Join-Path $PSScriptRoot 'register_zkemkeeper_sdk_x64.ps1'
  if (-not (Test-Path $registerScript)) {
    throw "Missing helper script: $registerScript"
  }
  $registerOutput = & $registerScript -SdkDir $SdkDir -Json
  if ($LASTEXITCODE -ne 0) {
    throw (($registerOutput | Out-String).Trim())
  }

  foreach ($candidate in @('zkemkeeper.CZKEM', 'zkemkeeper.ZKEM.1')) {
    try {
      $type = [type]::GetTypeFromProgID($candidate)
      if ($type) {
        return $candidate
      }
    } catch {}
  }
  throw 'zkemkeeper COM could not be resolved after registration attempt.'
}

function Clear-BridgeEvents {
  foreach ($id in @($script:EventIds)) {
    try { Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue } catch {}
  }
  $script:EventIds = @()
  $script:RegisteredEventNames = @()
}

function Register-BridgeEvent {
  param(
    $ComObject,
    [string]$EventName
  )

  $sourceId = "zkem.$EventName.$Ip.$Port.$MachineNumber"
  $messageData = [pscustomobject]@{
    EventName = $EventName
  }

  Register-ObjectEvent -InputObject $ComObject -EventName $EventName -SourceIdentifier $sourceId -MessageData $messageData -Action {
    try {
      $eventName = [string]$Event.MessageData.EventName
      $properties = Get-PropertyMap -InputObject $EventArgs
      $sourceArgs = @()
      try {
        $sourceArgs = @($Event.SourceArgs | Select-Object -Skip 1)
      } catch {
        $sourceArgs = @()
      }
      $script:EventCount += 1
      $resolvedCard = Resolve-CardFromEvent -ComObject $Sender -EventName $eventName -Properties $properties -SourceArgs $sourceArgs
      $resolvedPin = Resolve-PinFromEvent -Properties $properties -SourceArgs $sourceArgs
      $senderType = ''
      try {
        if ($Sender) {
          $senderType = $Sender.GetType().FullName
        }
      } catch {}
      $script:LastEventName = $eventName
      $script:LastCard = $resolvedCard
      $script:LastPin = $resolvedPin
      Write-EventDump -EventName $eventName -Properties $properties -SourceArgs $sourceArgs -ResolvedCard $resolvedCard -ResolvedPin $resolvedPin -EventArgsText (Normalize-Scalar $EventArgs) -SenderType $senderType
      Write-Heartbeat -Status 'event' -Message ("$eventName raw captured")
      Post-EventPayload -EventName $eventName -Properties $properties -SourceArgs $sourceArgs -ResolvedCard $resolvedCard -ResolvedPin $resolvedPin
    } catch {
      Report-BridgeError ("zkemkeeper event action failed: " + $_.Exception.Message)
    }
  } | Out-Null

  $script:EventIds += $sourceId
  $script:RegisteredEventNames += $EventName
}

function Start-BridgeLoop {
  while ($true) {
    $zk = $null
    try {
      $env:Path = "$SdkDir;" + $env:Path
      $progId = Ensure-ProgId
      $script:ProgId = $progId
      Write-Host "[ZKEM] Using ProgID: $progId"
      $zk = New-Object -ComObject $progId
      $authState = Apply-CommPassword -ComObject $zk
      if ($authState.attempted) {
        if ($authState.ok) {
          Write-Host "[ZKEM] Applied comm password via $($authState.method)"
        } elseif ($authState.message) {
          Write-Host "[ZKEM] Comm password setup failed via $($authState.method): $($authState.message)"
        }
      }
      $portCandidates = New-Object System.Collections.Generic.List[int]
      $null = $portCandidates.Add([int]$Port)
      if ([int]$Port -ne 4370) {
        $null = $portCandidates.Add(4370)
      }
      $connected = $false
      foreach ($candidatePort in $portCandidates) {
        $script:ActivePort = $candidatePort
        $script:BridgeTag = "zkemkeeper:$Ip`:$candidatePort"
        if ($zk.Connect_Net($Ip, $candidatePort)) {
          $connected = $true
          break
        }
        Write-Host "[ZKEM] Connect_Net failed for $Ip`:$candidatePort"
      }
      if (-not $connected) {
        throw ("Connect_Net failed for attempted ports: " + (($portCandidates | Select-Object -Unique) -join ', '))
      }

      try { $null = $zk.RegEvent($MachineNumber, 65535) } catch {}
      foreach ($eventName in @('OnHIDNum', 'OnAttTransactionEx', 'OnVerify')) {
        try {
          Register-BridgeEvent -ComObject $zk -EventName $eventName
          Write-Host "[ZKEM] Registered event: $eventName"
        } catch {
          Write-Host "[ZKEM] Event unavailable: $eventName ($($_.Exception.Message))"
        }
      }

      $script:ConnectedSince = [DateTime]::UtcNow.ToString('o')
      Write-Heartbeat -Status 'connected' -Message "connected to $Ip`:$($script:ActivePort)"
      Write-Host "[ZKEM] Connected to $Ip`:$($script:ActivePort); waiting for events"

      while ($true) {
        $evt = Wait-Event -Timeout 2
        if ($evt) {
          try { Remove-Event -EventIdentifier $evt.EventIdentifier -ErrorAction SilentlyContinue } catch {}
        }
        Write-Heartbeat -Status 'connected' -Message 'idle'
        try {
          $state = $zk.GetConnectState()
          if ($state -is [bool] -and (-not $state)) {
            throw 'GetConnectState returned false.'
          }
        } catch {
          # Some SDK builds may not expose GetConnectState; keep waiting.
        }
      }
    } catch {
      $msg = $_.Exception.Message
      Write-Heartbeat -Status 'error' -Message $msg
      Report-BridgeError ("zkemkeeper bridge error: $msg")
      Write-Host "[ZKEM] ERROR: $msg"
    } finally {
      Clear-BridgeEvents
      if ($zk) {
        try { $zk.Disconnect() | Out-Null } catch {}
      }
      $script:ConnectedSince = ''
    }

    Start-Sleep -Seconds ([Math]::Max(2, $ReconnectDelaySeconds))
  }
}

Start-BridgeLoop
