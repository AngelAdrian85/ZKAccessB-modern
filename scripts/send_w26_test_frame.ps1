param(
  [string]$TargetHost = '127.0.0.1',
  [int]$Port = 9002,
  [string]$Payload = 'BITS:10101010101010101010101010',
  [switch]$NoNewline
)

$ErrorActionPreference = 'Stop'

$client = $null
$stream = $null
try {
  $client = New-Object System.Net.Sockets.TcpClient
  $client.Connect($TargetHost, $Port)
  $stream = $client.GetStream()

  $wire = if ($NoNewline) { $Payload } else { $Payload + "`n" }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($wire)
  $stream.Write($bytes, 0, $bytes.Length)
  $stream.Flush()

  Write-Host "Sent frame to ${TargetHost}:$Port"
  Write-Host "Payload: $Payload"
}
finally {
  if ($stream) {
    try { $stream.Dispose() } catch {}
  }
  if ($client) {
    try { $client.Close() } catch {}
  }
}