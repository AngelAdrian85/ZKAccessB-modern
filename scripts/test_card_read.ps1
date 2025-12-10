param(
  [string]$Card = 'TESTCARD123'
)
$python = ".\.venv\Scripts\python.exe"
if(!(Test-Path $python)){ throw "Python venv not found" }
Write-Host "[TEST] Pushing card $Card"
& $python -c "import requests; requests.post('http://127.0.0.1:8000/agent/api/cards/read/push/', json={'card_number':'$Card','source':'ps1'}, timeout=3)" | Out-Null
Write-Host "[TEST] Waiting for card..."
& $python -c "import requests,sys; r=requests.get('http://127.0.0.1:8000/agent/api/cards/read/wait/', timeout=12); print(r.status_code); print(r.text)"