<#
Automate common dev tasks for this repository on Windows PowerShell.

What it does:
- Ensures Git is available (attempts winget install if missing).
- Runs ruff linter.
- Runs pytest (with DJANGO settings for `zkeco_modern`).
- Runs Django migrations for `zkeco_modern`.
- Creates a non-interactive admin user via `scripts/create_ci_admin.py`.
- Starts the Django dev server in the background.
- Waits for the server to become available and runs `scripts/smoke_check.py`.
- Optionally creates a git branch, commits staged changes, pushes and opens a PR (if `gh` CLI is available).

Usage (from repo root):
    powershell -ExecutionPolicy Bypass -File .\scripts\automate_all.ps1

Notes:
- Script assumes a Python virtualenv at `./venv311` and a Django project at `./zkeco_modern`.
- If your environment differs, set the variables below accordingly.
#>

#!/usr/bin/env pwsh
# Parameters (can be passed when invoking the script)
param(
    [string] $BranchName = 'ci/precommit-ruff-pytest',
    [string] $RemoteUrl = '', # e.g. https://github.com/owner/repo.git
    [switch] $CiMode,        # if present, run headless CI (stop server after smoke checks)
    [switch] $ApplyPatch,    # if present, produce a ZIP of the changed files instead of git operations
    [switch] $CreatePRWithToken # if present, attempt to create a PR using GITHUB_TOKEN env var
)

Set-StrictMode -Version Latest

# Configuration (edit if your setup differs)
$PythonExe = Join-Path -Path $PSScriptRoot -ChildPath '..\venv311\Scripts\python.exe'
$DjangoProjPath = Join-Path -Path $PSScriptRoot -ChildPath '..\zkeco_modern'
$DJANGO_SETTINGS = 'zkeco_config.settings'
$FilesToStage = @(
    '.github/workflows/ci.yml',
    '.pre-commit-config.yaml',
    'scripts/create_ci_admin.py',
    'scripts/smoke_check.py',
    'PR_DESCRIPTION.md',
    'zkeco_modern/tests/test_e2e_login_create_user.py'
)

function Ensure-Git {
    Write-Host "Checking for git..."
    $g = Get-Command git -ErrorAction SilentlyContinue
    if ($null -ne $g) {
        Write-Host "git found: $($g.Path)"
        return $true
    }

    Write-Host "git not found. Attempting to install via winget (requires interactive elevation)."
    try {
        winget install --id Git.Git -e --source winget -h
        Start-Sleep -Seconds 2
    } catch {
        Write-Warning "winget install failed or not available. Please install Git for Windows and re-run this script."
        return $false
    }

    # Try to pick up git in current session by checking common install paths
    $possible = @('C:\Program Files\Git\cmd\git.exe','C:\Program Files (x86)\Git\cmd\git.exe')
    foreach ($p in $possible) {
        if (Test-Path $p) {
            $env:PATH = $env:PATH + ';' + (Split-Path $p)
            Write-Host "Added $p to PATH for this session"
            return $true
        }
    }

    Write-Warning "Git install may require a new shell to pick up PATH. Please restart PowerShell and re-run the script if git is still not available."
    return (Get-Command git -ErrorAction SilentlyContinue) -ne $null
}

function Run-Command($exe, $args) {
    Write-Host "Running: $exe $args"
    & $exe $args
    $ec = $LASTEXITCODE
    if ($ec -ne 0) { Write-Warning "Command returned exit code $ec" }
    return $ec
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe. Update the script to point to your venv's python.exe."; exit 2
}

Write-Host "Using Python: $PythonExe"

# Set Django environment for subsequent python runs
$env:PYTHONPATH = (Resolve-Path $DjangoProjPath).Path
$env:DJANGO_SETTINGS_MODULE = $DJANGO_SETTINGS

Write-Host "Running ruff (lint)..."
& $PythonExe -m ruff check .
if ($LASTEXITCODE -ne 0) { Write-Warning "ruff reported issues (exit code $LASTEXITCODE). Please fix before continuing." }

Write-Host "Running pytest (zkeco_modern tests)..."
& $PythonExe -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Warning "pytest failed (exit code $LASTEXITCODE)." }

Write-Host "Applying Django migrations for zkeco_modern..."
& $PythonExe $DjangoProjPath\manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { Write-Warning "migrate returned exit code $LASTEXITCODE." }

Write-Host "Creating CI admin user (if missing)..."
& $PythonExe $PSScriptRoot\create_ci_admin.py

Write-Host "Starting development server in background..."
$serverProc = Start-Process -FilePath $PythonExe -ArgumentList '-u', "$DjangoProjPath\manage.py", 'runserver', '0.0.0.0:8000', '--noreload' -NoNewWindow -PassThru
Write-Host "Started server PID $($serverProc.Id)"

Write-Host "Waiting for server to become available on http://127.0.0.1:8000/ ..."
$ok = $false
for ($i=0; $i -lt 15; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 3
        Write-Host "HTTP / returned $($resp.StatusCode)"
        $ok = $true; break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ok) { Write-Warning "Server didn't respond on port 8000 after wait. Check server logs and ensure it started correctly." }

Write-Host "Running smoke_check.py..."
& $PythonExe $PSScriptRoot\smoke_check.py

Write-Host "Preparing git operations..."
function Create-Repo-IfMissing($remote) {
    if (-not (Test-Path -Path (Join-Path -Path (Get-Location) -ChildPath '.git'))) {
        Write-Host "No .git directory found. Initializing repository locally..."
        & git init
        if ($LASTEXITCODE -ne 0) { Write-Warning "git init failed (code $LASTEXITCODE)"; return $false }
        # Ensure minimal identity so commits will succeed
        & git config user.email "ci@example.com" 2>$null
        & git config user.name "auto-ci" 2>$null
        if ($remote) {
            & git remote add origin $remote
            if ($LASTEXITCODE -ne 0) { Write-Warning "git remote add failed (code $LASTEXITCODE)" }
        }
        return $true
    }
    return $true
}

function Create-Pr-With-Token($remoteUrl, $branch, $title, $bodyFile, $base='main') {
    $token = $env:GITHUB_TOKEN
    if (-not $token) { Write-Warning "GITHUB_TOKEN not set; cannot create PR via API."; return $false }

    # Parse owner/repo from remoteUrl
    if ($remoteUrl -match 'github.com[:/]+([^/]+)/([^/.]+)') {
        $owner = $matches[1]; $repo = $matches[2]
    } else {
        Write-Warning "Could not parse GitHub owner/repo from $remoteUrl"; return $false
    }

    $body = Get-Content -Raw -Path $bodyFile
    $payload = @{ title = $title; head = $branch; base = $base; body = $body } | ConvertTo-Json
    $url = "https://api.github.com/repos/$owner/$repo/pulls"
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Post -Body $payload -Headers @{ Authorization = "token $token"; 'User-Agent'='automate_all' } -ContentType 'application/json'
        Write-Host "Created PR: $($resp.html_url)"
        return $true
    } catch {
        Write-Warning "Failed to create PR via API: $($_.Exception.Message)"
        return $false
    }
}

Write-Host "Preparing git operations..."

if ($ApplyPatch) {
    Write-Host "ApplyPatch mode: creating ZIP of changed files instead of git operations..."
    $zipName = Join-Path -Path $PSScriptRoot -ChildPath '..\changes_bundle.zip'
    if (Test-Path $zipName) { Remove-Item $zipName }
    $files = $FilesToStage | Where-Object { Test-Path $_ }
    if ($files.Count -eq 0) { Write-Warning "No files found to include in ZIP." } else { Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::CreateFromDirectory((Get-Location), $zipName) }
    Write-Host "Wrote $zipName"; exit 0
}

if (-not (Ensure-Git)) {
    Write-Warning "Git unavailable: skipping git commit/push. You can create branch and push manually later."; exit 0
}

# Ensure repo exists or init if missing (use RemoteUrl if provided)
if ($RemoteUrl) { Create-Repo-IfMissing -remote $RemoteUrl } else { Create-Repo-IfMissing -remote $null }

Write-Host "Creating branch $BranchName (if not exists)..."
& git rev-parse --abbrev-ref HEAD 2>$null | Out-Null
& git checkout -b $BranchName 2>$null

Write-Host "Staging files..."
& git add --all

Write-Host "Committing..."
& git commit -m "CI: add ruff+pytest pre-commit, smoke checks and small e2e test; add PR description" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "No changes to commit or commit failed (code $LASTEXITCODE)." }

Write-Host "Pushing branch..."
# If GITHUB_TOKEN is available and remote is HTTPS, use it to push non-interactively
$remoteUrlActual = (& git remote get-url origin) 2>$null
if ($env:GITHUB_TOKEN -and $remoteUrlActual -and $remoteUrlActual -match '^https://') {
    $token = $env:GITHUB_TOKEN
    if ($remoteUrlActual -match '^https://(.*)$') {
        $tail = $matches[1]
        $authUrl = "https://x-access-token:$token@$tail"
        & git remote set-url origin $authUrl
        & git push -u origin $BranchName
        $pushCode = $LASTEXITCODE
        # restore original remote url
        & git remote set-url origin $remoteUrlActual
        if ($pushCode -ne 0) { $LASTEXITCODE = $pushCode }
    } else {
        & git push -u origin $BranchName
    }
} else {
    & git push -u origin $BranchName
}
if ($LASTEXITCODE -ne 0) { Write-Warning "git push failed with code $LASTEXITCODE. Check authentication or remote." }

if ($CreatePRWithToken) {
    if (-not $RemoteUrl) { Write-Warning "RemoteUrl required to create PR via token." } else { Create-Pr-With-Token -remoteUrl $RemoteUrl -branch $BranchName -title "CI: add ruff + pytest pre-commit, smoke checks and small e2e test" -bodyFile (Resolve-Path "$PSScriptRoot\..\PR_DESCRIPTION.md") }
} elseif (Get-Command gh -ErrorAction SilentlyContinue) {
    gh pr create --title "CI: add ruff + pytest pre-commit, smoke checks and small e2e test" --body-file (Resolve-Path "$PSScriptRoot\..\PR_DESCRIPTION.md") --base main
} else {
    Write-Host "gh CLI not found. Open a PR manually using GitHub web UI and use PR_DESCRIPTION.md for the body."
}

Write-Host "Automation script finished. Server still running in background (PID $($serverProc.Id)). To stop it, find the process and kill or press CTRL-BREAK in the original server terminal." 
