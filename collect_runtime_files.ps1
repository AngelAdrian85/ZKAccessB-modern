<#
collect_runtime_files.ps1

Detects the installed ZKAccess CommCenter service PathName and copies candidate runtime
Python files (.py/.pyc) into the workspace `debug_pyc` folder for offline analysis.

Usage (PowerShell, run as Administrator if required for file access):
  .\collect_runtime_files.ps1            # autodetect service path and copy files
  .\collect_runtime_files.ps1 -InstallPath "C:\Program Files (x86)\ZKTeco\ZKAccessB"

#>
param(
    [string]$InstallPath
)

$svcName = 'ZKECODataCommCenterService'
$dst = Join-Path -Path $PSScriptRoot -ChildPath 'debug_pyc'
New-Item -Path $dst -ItemType Directory -Force | Out-Null

if (-not $InstallPath) {
    try {
        $svc = Get-WmiObject -Class Win32_Service -Filter "Name='$svcName'" -ErrorAction Stop
        if ($svc -and $svc.PathName) {
            Write-Output "Service PathName: $($svc.PathName)"
            # Attempt to extract base install folder (path to executable's parent)
            $pn = $svc.PathName
            # Remove surrounding quotes
            if ($pn.StartsWith('"') -and $pn.EndsWith('"')) { $pn = $pn.Trim('"') }
            # If contains python.exe plus script, take leading folder
            $parts = $pn -split '\\'
            # heuristic: find 'ZKTeco' in path
            $idx = $parts | ForEach-Object { $_ } | Select-Object -Index ((($parts | Select-String -Pattern 'ZKTeco' -AllMatches).Matches | ForEach-Object { $_.Index })[0] ) 2>$null
            # fallback: take first two segments
            $InstallPath = "C:\Program Files (x86)\ZKTeco\ZKAccessB"
            Write-Output "Using fallback InstallPath: $InstallPath"
        } else {
            Write-Output "Service $svcName not found or PathName empty. Falling back to default install path."
            $InstallPath = "C:\Program Files (x86)\ZKTeco\ZKAccessB"
        }
    } catch {
        Write-Output "Failed to query service: $_. Exception. Using fallback install path"
        $InstallPath = "C:\Program Files (x86)\ZKTeco\ZKAccessB"
    }
} else {
    Write-Output "Using provided InstallPath: $InstallPath"
}

# Candidate source paths (relative to $InstallPath)
$paths = @(
    'zkeco\units\adms\mysite\iclock\models\model_device.py',
    'zkeco\units\adms\mysite\iclock\models\model_device.pyc',
    'zkeco\units\adms\mysite\iaccess\devcomm.py',
    'zkeco\units\adms\mysite\iaccess\devcomm.pyc',
    'zkeco\units\adms\mysite\iaccess\dev_comm_center.py',
    'zkeco\units\adms\mysite\iaccess\dev_comm_center.pyc'
)

$copied = @()
foreach ($rel in $paths) {
    $src = Join-Path -Path $InstallPath -ChildPath $rel
    if (Test-Path $src) {
        try {
            Copy-Item -Path $src -Destination $dst -Force
            $copied += $rel
            Write-Output "Copied: $rel"
        } catch {
            Write-Output "Failed to copy $src: $_"
        }
    } else {
        Write-Output "Not found: $rel"
    }
}

Write-Output "--- Done. Files copied into: $dst ---"
Get-ChildItem -Path $dst | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize

if ($copied.Count -eq 0) { Write-Output "No candidate files were copied. If you know the exact path, re-run with -InstallPath '<path>'." }

Write-Output "If you want me to decompile any copied .pyc files, paste the directory listing output here and I'll proceed."