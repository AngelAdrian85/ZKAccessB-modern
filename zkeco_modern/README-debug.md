**OAuth Debug (development only)**

- **Purpose:** Quick steps to debug OAuth redirect/callbacks locally using the development server.
- **Debug endpoint:** `http://127.0.0.1:8000/oauth-debug/` (available when `DEBUG` is True)

Steps

1. Start the Django development server from the `zkeco_modern` folder with your virtualenv activated and `INCLUDE_LEGACY=1` if needed:

```powershell
# activate venv (if not already active)
& .\.venv\Scripts\Activate.ps1
cd zkeco_modern
# start devserver (example)
$env:INCLUDE_LEGACY = '1'
python manage.py runserver
```

2. Register the redirect URI in your OAuth provider (or CLI) as:

```
http://127.0.0.1:8000/oauth-debug/
```

3. Start the auth flow (the provider will redirect back to the URL above).

4. When the browser hits the redirect, you will see a simple HTML page listing the query parameters (e.g. `code` and `state`). The dev server log will also show the request.

Troubleshooting

- If a different local helper (CLI) opens an ephemeral port (e.g. `http://127.0.0.1:58914/?code=...`), that helper consumed the callback — inspect which process opened the port with:

```powershell
netstat -aon | Select-String ':58914' ; Get-Process -Id <PID>
```

- Or monitor ephemeral listeners while reproducing the flow:

```powershell
while ($true) {
  netstat -aon | Select-String 'LISTENING' | Select-String ':(58914|58885)' | ForEach-Object {
    $pid = ($_ .Line.Trim() -split '\s+')[-1]
    Get-Process -Id $pid -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path
  }
  Start-Sleep -Seconds 1
}
```

Notes

- `oauth-debug/` is development-only and added to `zkeco_modern/zkeco_config/urls.py` under `DEBUG`.
- This file is intended as a short local reference; do not ship to production.
