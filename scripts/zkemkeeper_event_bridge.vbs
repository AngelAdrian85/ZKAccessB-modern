Option Explicit

Dim g_ip, g_port, g_machineNumber, g_serverUrl, g_deviceId, g_doorId, g_doorPk
Dim g_source, g_dumpFile, g_commPassword, g_reconnectDelaySeconds, g_repoRoot
Dim g_heartbeatPath, g_pushUrl, g_bridgeTag, g_activePort, g_registeredEvents
Dim g_eventCount, g_lastEvent, g_lastCard, g_lastPin, g_progId, g_connectedSince
Dim g_running, g_zk, g_fso, g_activePassword

Set g_fso = CreateObject("Scripting.FileSystemObject")

g_ip = GetNamedArg("Ip", "")
g_port = CLng(GetNamedArg("Port", "4370"))
g_machineNumber = CLng(GetNamedArg("MachineNumber", "1"))
g_serverUrl = GetNamedArg("ServerUrl", "http://127.0.0.1:8000")
g_deviceId = CLng(GetNamedArg("DeviceId", "0"))
g_doorId = GetNamedArg("DoorId", "")
g_doorPk = GetNamedArg("DoorPk", "")
g_source = GetNamedArg("Source", "zkemkeeper-event")
g_dumpFile = GetNamedArg("DumpFile", "")
g_commPassword = GetEffectiveCommPassword(GetNamedArg("CommPassword", ""))
g_reconnectDelaySeconds = CLng(GetNamedArg("ReconnectDelaySeconds", "5"))
g_repoRoot = g_fso.GetParentFolderName(WScript.ScriptFullName)
g_repoRoot = g_fso.GetParentFolderName(g_repoRoot)
If Len(g_dumpFile) = 0 Then
  If g_deviceId > 0 Then
    g_dumpFile = g_repoRoot & "\zkemkeeper_event_dump_controller" & CStr(g_deviceId) & ".jsonl"
  Else
    g_dumpFile = g_repoRoot & "\zkemkeeper_event_dump_events.jsonl"
  End If
End If
g_heartbeatPath = ExpandEnv("%USERPROFILE%") & "\zkeco_reader_heartbeat_zkemkeeper.json"
g_pushUrl = TrimTrailingSlash(g_serverUrl) & "/agent/api/cards/read/push/"
g_bridgeTag = "zkemkeeper:" & g_ip & ":" & CStr(g_port)
g_activePort = g_port
g_registeredEvents = "[""OnConnected"",""OnDisConnected"",""OnHIDNum"",""OnAttTransactionEx"",""OnVerify""]"
g_eventCount = 0
g_lastEvent = ""
g_lastCard = ""
g_lastPin = ""
g_progId = "zkemkeeper.ZKEM.1"
g_connectedSince = ""
g_activePassword = ""
g_running = True

If Len(g_ip) = 0 Then
  WScript.Echo "[ZKEM-VBS] ERROR: missing -Ip"
  WScript.Quit 2
End If

MainLoop

Sub MainLoop()
  Dim connectMessage
  Do While g_running
    Set g_zk = Nothing
    connectMessage = ""

    On Error Resume Next
    Set g_zk = CreateObject(g_progId)
    If Err.Number <> 0 Then
      connectMessage = "CreateObject failed: " & Err.Description
      Err.Clear
      On Error GoTo 0
      WriteHeartbeat "error", connectMessage
      WScript.Echo "[ZKEM-VBS] ERROR: " & connectMessage
      WScript.Sleep MaxInt(2, g_reconnectDelaySeconds) * 1000
    Else
      On Error GoTo 0
      If ConnectDevice(connectMessage) Then
        On Error Resume Next
        g_zk.RegEvent g_machineNumber, 65535
        Err.Clear
        WScript.ConnectObject g_zk, "zk_"
        Err.Clear
        On Error GoTo 0

        g_connectedSince = IsoNow()
        WScript.Echo "[ZKEM-VBS] Connected to " & g_ip & ":" & CStr(g_activePort) & "; waiting for events"
        WriteHeartbeat "connected", "connected to " & g_ip & ":" & CStr(g_activePort)

        Do While g_running
          On Error Resume Next
          PumpRealtime
          WriteHeartbeat "connected", "idle"
          If Err.Number <> 0 Then
            WScript.Echo "[ZKEM-VBS] LOOP warning: " & Err.Description
            Err.Clear
          End If
          On Error GoTo 0
          WScript.Sleep 1000
        Loop
      Else
        WriteHeartbeat "error", connectMessage
        WScript.Echo "[ZKEM-VBS] ERROR: " & connectMessage
        SafeDisconnect
        WScript.Sleep MaxInt(2, g_reconnectDelaySeconds) * 1000
      End If
    End If
  Loop
End Sub

Function ConnectDevice(ByRef outMessage)
  Dim ok, authMessage
  ConnectDevice = False
  outMessage = ""
  authMessage = ""

  ok = TryConnectWithPasswordCandidate(g_commPassword, authMessage)
  If (Not ok) And Len(Trim(g_commPassword)) > 0 Then
    ok = TryConnectWithPasswordCandidate("", authMessage)
  End If
  If (Not ok) And Trim(CStr(g_commPassword)) <> "0" Then
    ok = TryConnectWithPasswordCandidate("0", authMessage)
  End If

  If ok Then
    ConnectDevice = True
  Else
    outMessage = authMessage
    If Len(outMessage) = 0 Then
      outMessage = "Connect_Net failed for attempted ports: " & CStr(g_port)
      If g_port <> 4370 Then
        outMessage = outMessage & ", 4370"
      End If
    End If
  End If
End Function

Function TryConnectWithPasswordCandidate(passwordValue, ByRef outMessage)
  Dim ok, label
  TryConnectWithPasswordCandidate = False
  label = DescribePassword(passwordValue)
  outMessage = ""

  If ApplyCommPasswordValue(passwordValue) Then
    WScript.Echo "[ZKEM-VBS] Trying Connect_Net with comm password " & label
  ElseIf Len(Trim(CStr(passwordValue))) > 0 Then
    WScript.Echo "[ZKEM-VBS] Comm password setup failed for " & label & "; trying connect anyway"
  Else
    WScript.Echo "[ZKEM-VBS] Trying Connect_Net without comm password"
  End If

  ok = TryConnectPort(g_port)
  If (Not ok) And (g_port <> 4370) Then
    ok = TryConnectPort(4370)
  End If

  If ok Then
    g_activePassword = CStr(passwordValue)
    WScript.Echo "[ZKEM-VBS] Connect_Net succeeded with comm password " & label
    TryConnectWithPasswordCandidate = True
  Else
    outMessage = "Connect_Net failed for attempted passwords/ports; last password=" & label & " ports=" & CStr(g_port)
    If g_port <> 4370 Then
      outMessage = outMessage & ", 4370"
    End If
  End If
End Function

Function TryConnectPort(portValue)
  On Error Resume Next
  g_activePort = CLng(portValue)
  g_bridgeTag = "zkemkeeper:" & g_ip & ":" & CStr(g_activePort)
  TryConnectPort = CBool(g_zk.Connect_Net(g_ip, g_activePort))
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] Connect_Net error for " & g_ip & ":" & CStr(g_activePort) & " -> " & Err.Description
    Err.Clear
    TryConnectPort = False
  ElseIf Not TryConnectPort Then
    WScript.Echo "[ZKEM-VBS] Connect_Net failed for " & g_ip & ":" & CStr(g_activePort)
  End If
  On Error GoTo 0
End Function

Function ApplyCommPasswordValue(passwordValue)
  Dim ok
  ApplyCommPasswordValue = False
  If Len(Trim(CStr(passwordValue))) = 0 Then
    ApplyCommPasswordValue = True
    Exit Function
  End If

  On Error Resume Next
  ok = CBool(g_zk.SetCommPasswordEx(CStr(passwordValue)))
  If Err.Number = 0 And ok Then
    ApplyCommPasswordValue = True
    On Error GoTo 0
    Exit Function
  End If
  Err.Clear

  If IsNumeric(passwordValue) Then
    ok = CBool(g_zk.SetCommPassword(CLng(passwordValue)))
    If Err.Number = 0 And ok Then
      ApplyCommPasswordValue = True
      On Error GoTo 0
      Exit Function
    End If
    Err.Clear
  End If
  On Error GoTo 0
End Function

Function DescribePassword(passwordValue)
  Dim txt
  txt = CStr(passwordValue)
  If Len(Trim(txt)) = 0 Then
    DescribePassword = "<blank>"
  Else
    DescribePassword = "[len=" & CStr(Len(txt)) & "]"
  End If
End Function

Sub PumpRealtime()
  Dim ok, iterations
  On Error Resume Next
  g_zk.ReadRTLog g_machineNumber
  Err.Clear
  iterations = 0
  Do While iterations < 128
    ok = g_zk.GetRTLog(g_machineNumber)
    If Err.Number <> 0 Then
      Err.Clear
      Exit Do
    End If
    If Not CBool(ok) Then
      Exit Do
    End If
    iterations = iterations + 1
  Loop
  On Error GoTo 0
End Sub

Sub zk_OnConnected(ByVal MachineNumber)
  On Error Resume Next
  g_connectedSince = IsoNow()
  WriteHeartbeat "connected", "OnConnected machine=" & CStr(MachineNumber)
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] OnConnected warning: " & Err.Description
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Sub zk_OnDisConnected(ByVal MachineNumber)
  On Error Resume Next
  WriteHeartbeat "error", "OnDisConnected machine=" & CStr(MachineNumber)
  SafeDisconnect
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] OnDisConnected warning: " & Err.Description
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Sub zk_OnHIDNum(ByVal CardNumber)
  Dim hidCard, rawCard, chosenCard, propertiesJson, argsJson, payloadJson, dumpJson
  On Error Resume Next
  rawCard = Trim(CStr(CardNumber))
  hidCard = GetHidCardString()
  chosenCard = hidCard
  If Len(chosenCard) = 0 Then
    chosenCard = NormalizeCard(rawCard)
  End If

  g_eventCount = g_eventCount + 1
  g_lastEvent = "OnHIDNum"
  g_lastCard = chosenCard
  g_lastPin = ""

  propertiesJson = "{" & JsonPair("CardNumber", rawCard) & "," & JsonPair("HIDCard", hidCard) & "}"
  argsJson = "[" & JsonString(rawCard) & "]"
  payloadJson = BuildBasePayload(chosenCard, "", "OnHIDNum", propertiesJson, argsJson, hidCard)
  dumpJson = BuildDumpJson("OnHIDNum", chosenCard, "", propertiesJson, argsJson, rawCard)
  AppendLine g_dumpFile, dumpJson
  PostJson g_pushUrl, payloadJson
  WriteHeartbeat "event", "OnHIDNum card=" & chosenCard
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] OnHIDNum warning: " & Err.Description
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Sub zk_OnAttTransactionEx(ByVal EnrollNumber, ByVal IsInValid, ByVal AttState, ByVal VerifyMethod, ByVal Year, ByVal Month, ByVal Day, ByVal Hour, ByVal Minute, ByVal Second, ByVal WorkCode)
  Dim pinText, propertiesJson, argsJson, payloadJson, dumpJson
  On Error Resume Next
  pinText = Trim(CStr(EnrollNumber))

  g_eventCount = g_eventCount + 1
  g_lastEvent = "OnAttTransactionEx"
  g_lastCard = ""
  g_lastPin = pinText

  propertiesJson = "{" _
    & JsonPair("EnrollNumber", pinText) & "," _
    & JsonPair("IsInValid", CStr(IsInValid)) & "," _
    & JsonPair("AttState", CStr(AttState)) & "," _
    & JsonPair("VerifyMethod", CStr(VerifyMethod)) & "," _
    & JsonPair("Year", CStr(Year)) & "," _
    & JsonPair("Month", CStr(Month)) & "," _
    & JsonPair("Day", CStr(Day)) & "," _
    & JsonPair("Hour", CStr(Hour)) & "," _
    & JsonPair("Minute", CStr(Minute)) & "," _
    & JsonPair("Second", CStr(Second)) & "," _
    & JsonPair("WorkCode", CStr(WorkCode)) _
    & "}"
  argsJson = "[" _
    & JsonString(pinText) & "," _
    & JsonString(CStr(IsInValid)) & "," _
    & JsonString(CStr(AttState)) & "," _
    & JsonString(CStr(VerifyMethod)) & "," _
    & JsonString(CStr(Year)) & "," _
    & JsonString(CStr(Month)) & "," _
    & JsonString(CStr(Day)) & "," _
    & JsonString(CStr(Hour)) & "," _
    & JsonString(CStr(Minute)) & "," _
    & JsonString(CStr(Second)) & "," _
    & JsonString(CStr(WorkCode)) _
    & "]"
  payloadJson = BuildBasePayload("", pinText, "OnAttTransactionEx", propertiesJson, argsJson, "")
  dumpJson = BuildDumpJson("OnAttTransactionEx", "", pinText, propertiesJson, argsJson, pinText)
  AppendLine g_dumpFile, dumpJson
  PostJson g_pushUrl, payloadJson
  WriteHeartbeat "event", "OnAttTransactionEx pin=" & pinText
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] OnAttTransactionEx warning: " & Err.Description
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Sub zk_OnVerify(ByVal UserID)
  Dim pinText, propertiesJson, argsJson, payloadJson, dumpJson
  On Error Resume Next
  pinText = Trim(CStr(UserID))

  g_eventCount = g_eventCount + 1
  g_lastEvent = "OnVerify"
  g_lastCard = ""
  g_lastPin = pinText

  propertiesJson = "{" & JsonPair("UserID", pinText) & "}"
  argsJson = "[" & JsonString(pinText) & "]"
  payloadJson = BuildBasePayload("", pinText, "OnVerify", propertiesJson, argsJson, "")
  dumpJson = BuildDumpJson("OnVerify", "", pinText, propertiesJson, argsJson, pinText)
  AppendLine g_dumpFile, dumpJson
  PostJson g_pushUrl, payloadJson
  WriteHeartbeat "event", "OnVerify pin=" & pinText
  If Err.Number <> 0 Then
    WScript.Echo "[ZKEM-VBS] OnVerify warning: " & Err.Description
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Function BuildBasePayload(cardValue, pinValue, eventName, propertiesJson, argsJson, hidCard)
  Dim parts
  parts = JsonPair("source", g_source) _
    & "," & JsonBoolPair("verify_access", True) _
    & "," & JsonBoolPair("remote_open", False) _
    & "," & JsonPair("card_number", cardValue) _
    & "," & JsonPair("card_number_raw", cardValue) _
    & "," & JsonPair("controller_pin", pinValue) _
    & "," & JsonPair("zkemkeeper_event", eventName) _
    & "," & JsonRawPair("zkemkeeper_properties", propertiesJson) _
    & "," & JsonRawPair("zkemkeeper_source_args", argsJson) _
    & "," & JsonPair("zkemkeeper_hid_card", hidCard)
  If g_deviceId > 0 Then
    parts = parts & "," & JsonNumberPair("device_id", g_deviceId)
  End If
  If Len(g_doorId) > 0 Then
    parts = parts & "," & JsonPair("door_id", g_doorId)
  End If
  If Len(g_doorPk) > 0 Then
    parts = parts & "," & JsonPair("door_pk", g_doorPk)
  End If
  BuildBasePayload = "{" & parts & "}"
End Function

Function BuildDumpJson(eventName, cardValue, pinValue, propertiesJson, argsJson, rawText)
  BuildDumpJson = "{" _
    & JsonPair("ts_iso", IsoNow()) & "," _
    & JsonPair("bridge_tag", g_bridgeTag) & "," _
    & JsonNumberPair("event_index", g_eventCount) & "," _
    & JsonPair("event_name", eventName) & "," _
    & JsonPair("ip", g_ip) & "," _
    & JsonNumberPair("port", g_activePort) & "," _
    & JsonNumberPair("machine_number", g_machineNumber) & "," _
    & JsonPair("prog_id", g_progId) & "," _
    & JsonNumberPair("device_id", g_deviceId) & "," _
    & JsonPair("door_id", g_doorId) & "," _
    & JsonPair("door_pk", g_doorPk) & "," _
    & JsonPair("resolved_card", cardValue) & "," _
    & JsonPair("resolved_pin", pinValue) & "," _
    & JsonPair("raw_text", rawText) & "," _
    & JsonRawPair("event_properties", propertiesJson) & "," _
    & JsonRawPair("source_args", argsJson) _
    & "}"
End Function

Sub PostJson(url, payload)
  Dim http
  On Error Resume Next
  Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  If Err.Number <> 0 Then
    Err.Clear
    Set http = CreateObject("MSXML2.XMLHTTP")
  End If
  If Err.Number = 0 Then
    http.Open "POST", url, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send payload
  End If
  Err.Clear
  On Error GoTo 0
End Sub

Sub WriteHeartbeat(statusValue, messageValue)
  Dim json
  On Error Resume Next
  json = "{" _
    & JsonNumberPair("ts", UnixTs()) & "," _
    & JsonPair("ts_iso", IsoNow()) & "," _
    & JsonPair("source", "zkemkeeper") & "," _
    & JsonPair("bridge_tag", g_bridgeTag) & "," _
    & JsonPair("ip", g_ip) & "," _
    & JsonNumberPair("port", g_activePort) & "," _
    & JsonNumberPair("machine_number", g_machineNumber) & "," _
    & JsonPair("status", statusValue) & "," _
    & JsonPair("message", messageValue) & "," _
    & JsonPair("prog_id", g_progId) & "," _
    & JsonNumberPair("device_id", g_deviceId) & "," _
    & JsonPair("door_id", g_doorId) & "," _
    & JsonPair("door_pk", g_doorPk) & "," _
    & JsonPair("dump_file", g_dumpFile) & "," _
    & JsonNumberPair("event_count", g_eventCount) & "," _
    & JsonPair("last_event", g_lastEvent) & "," _
    & JsonPair("last_card", g_lastCard) & "," _
    & JsonPair("last_pin", g_lastPin) & "," _
    & JsonPair("connected_since", g_connectedSince) & "," _
    & JsonRawPair("registered_events", g_registeredEvents) _
    & "}"
  WriteTextFile g_heartbeatPath, json
  Err.Clear
  On Error GoTo 0
End Sub

Sub SafeDisconnect()
  On Error Resume Next
  If Not g_zk Is Nothing Then
    g_zk.Disconnect
  End If
  Set g_zk = Nothing
  g_connectedSince = ""
  On Error GoTo 0
End Sub

Function GetHidCardString()
  Dim hidValue, ok
  hidValue = ""
  On Error Resume Next
  ok = g_zk.GetHIDEventCardNumAsStr(hidValue)
  If Err.Number <> 0 Then
    Err.Clear
    GetHidCardString = ""
  ElseIf CBool(ok) Then
    GetHidCardString = NormalizeCard(CStr(hidValue))
  Else
    GetHidCardString = ""
  End If
  On Error GoTo 0
End Function

Function NormalizeCard(value)
  Dim txt
  txt = Trim(CStr(value))
  If txt = "0" Or txt = "00000000" Then
    txt = ""
  End If
  NormalizeCard = txt
End Function

Function GetNamedArg(name, defaultValue)
  If WScript.Arguments.Named.Exists(name) Then
    GetNamedArg = CStr(WScript.Arguments.Named.Item(name))
  Else
    GetNamedArg = defaultValue
  End If
End Function

Function GetEffectiveCommPassword(explicitValue)
  Dim shell, envProc, envUser, value
  value = Trim(CStr(explicitValue))
  If Len(value) > 0 Then
    GetEffectiveCommPassword = value
    Exit Function
  End If

  Set shell = CreateObject("WScript.Shell")
  Set envProc = shell.Environment("PROCESS")
  Set envUser = shell.Environment("USER")

  value = Trim(CStr(envProc("ZKACCESS_ZKEMKEEPER_COMM_PASSWORD")))
  If Len(value) = 0 Then
    value = Trim(CStr(envProc("ZKACCESS_DEFAULT_COMM_PASSWORD")))
  End If
  If Len(value) = 0 Then
    value = Trim(CStr(envUser("ZKACCESS_ZKEMKEEPER_COMM_PASSWORD")))
  End If
  If Len(value) = 0 Then
    value = Trim(CStr(envUser("ZKACCESS_DEFAULT_COMM_PASSWORD")))
  End If
  GetEffectiveCommPassword = value
End Function

Function TrimTrailingSlash(value)
  Dim txt
  txt = CStr(value)
  Do While Right(txt, 1) = "/"
    txt = Left(txt, Len(txt) - 1)
  Loop
  TrimTrailingSlash = txt
End Function

Function ExpandEnv(value)
  Dim shell
  Set shell = CreateObject("WScript.Shell")
  ExpandEnv = shell.ExpandEnvironmentStrings(value)
End Function

Sub EnsureParentFolder(pathValue)
  Dim folderPath
  folderPath = g_fso.GetParentFolderName(pathValue)
  If Len(folderPath) > 0 Then
    If Not g_fso.FolderExists(folderPath) Then
      g_fso.CreateFolder folderPath
    End If
  End If
End Sub

Sub WriteTextFile(pathValue, content)
  Dim handle
  On Error Resume Next
  EnsureParentFolder pathValue
  Set handle = g_fso.CreateTextFile(pathValue, True, False)
  If Err.Number = 0 Then
    handle.Write content
    handle.Close
  Else
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Sub AppendLine(pathValue, content)
  Dim handle
  On Error Resume Next
  EnsureParentFolder pathValue
  Set handle = g_fso.OpenTextFile(pathValue, 8, True, False)
  If Err.Number = 0 Then
    handle.WriteLine content
    handle.Close
  Else
    Err.Clear
  End If
  On Error GoTo 0
End Sub

Function JsonString(value)
  JsonString = """" & JsonEscape(CStr(value)) & """"
End Function

Function JsonPair(name, value)
  JsonPair = JsonString(name) & ":" & JsonString(value)
End Function

Function JsonNumberPair(name, value)
  JsonNumberPair = JsonString(name) & ":" & CStr(value)
End Function

Function JsonBoolPair(name, value)
  If CBool(value) Then
    JsonBoolPair = JsonString(name) & ":true"
  Else
    JsonBoolPair = JsonString(name) & ":false"
  End If
End Function

Function JsonRawPair(name, rawValue)
  JsonRawPair = JsonString(name) & ":" & rawValue
End Function

Function JsonEscape(value)
  Dim text
  text = CStr(value)
  text = Replace(text, "\", "\\")
  text = Replace(text, """", "\""")
  text = Replace(text, vbCrLf, "\n")
  text = Replace(text, vbCr, "\n")
  text = Replace(text, vbLf, "\n")
  JsonEscape = text
End Function

Function Pad2(value)
  If Len(CStr(value)) < 2 Then
    Pad2 = "0" & CStr(value)
  Else
    Pad2 = CStr(value)
  End If
End Function

Function IsoNow()
  Dim current
  current = Now
  IsoNow = Year(current) & "-" & Pad2(Month(current)) & "-" & Pad2(Day(current)) & "T" & Pad2(Hour(current)) & ":" & Pad2(Minute(current)) & ":" & Pad2(Second(current))
End Function

Function UnixTs()
  UnixTs = DateDiff("s", "01/01/1970 00:00:00", Now)
End Function

Function MaxInt(leftValue, rightValue)
  If CLng(leftValue) > CLng(rightValue) Then
    MaxInt = CLng(leftValue)
  Else
    MaxInt = CLng(rightValue)
  End If
End Function