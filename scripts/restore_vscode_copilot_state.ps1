[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceFile,

    [Parameter(Mandatory=$false)]
    [string]$BackupFolder,

    [Parameter(Mandatory=$false)]
    [string]$VscodeAppDataRoot = "${env:APPDATA}\Code"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($WorkspaceFile)) {
    $WorkspaceFile = Join-Path $PSScriptRoot '..\ZKAccessB.code-workspace'
}

function Resolve-FullPath([string]$Path) {
    return (Resolve-Path -LiteralPath $Path).Path
}

function Find-WorkspaceStorageFolder([string]$workspaceFileFullPath, [string]$vscodeAppDataRoot) {
    $storageRoot = Join-Path $vscodeAppDataRoot 'User\workspaceStorage'
    if (!(Test-Path -LiteralPath $storageRoot)) {
        throw "workspaceStorage root not found: $storageRoot"
    }

    $workspaceFileFullPath = (Resolve-Path -LiteralPath $workspaceFileFullPath).Path

    foreach ($dir in Get-ChildItem -LiteralPath $storageRoot -Directory -ErrorAction SilentlyContinue) {
        $workspaceJson = Join-Path $dir.FullName 'workspace.json'
        if (!(Test-Path -LiteralPath $workspaceJson)) { continue }

        try {
            $json = Get-Content -LiteralPath $workspaceJson -Raw | ConvertFrom-Json
            if (!$json.workspace) { continue }

            $uri = [System.Uri]$json.workspace
            $localPath = $uri.GetComponents([System.UriComponents]::Path, [System.UriFormat]::Unescaped)
            $localPath = $localPath -replace '/', '\\'

            if (!$localPath) { continue }
            $resolved = Resolve-Path -LiteralPath $localPath -ErrorAction SilentlyContinue
            if ($resolved -and $resolved.Path -eq $workspaceFileFullPath) {
                return $dir.FullName
            }
        } catch {
            continue
        }
    }

    return $null
}

$workspaceFileFullPath = Resolve-FullPath $WorkspaceFile
$storageFolder = Find-WorkspaceStorageFolder -workspaceFileFullPath $workspaceFileFullPath -vscodeAppDataRoot $VscodeAppDataRoot

if (!$storageFolder) {
    Write-Host "Could not find workspaceStorage folder for: $workspaceFileFullPath" -ForegroundColor Yellow
    exit 2
}

if ([string]::IsNullOrWhiteSpace($BackupFolder)) {
    $tmpDir = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tmp') -ErrorAction SilentlyContinue
    if (!$tmpDir) {
        throw "tmp folder not found under repo. Provide -BackupFolder explicitly."
    }

    $backupCandidates = Get-ChildItem -LiteralPath $tmpDir.Path -Directory -Filter 'vscode_workspaceStorage_backup_*' | Sort-Object LastWriteTime -Descending
    if (!$backupCandidates -or $backupCandidates.Count -eq 0) {
        throw "No backup folder found in $($tmpDir.Path). Provide -BackupFolder explicitly."
    }

    $BackupFolder = $backupCandidates[0].FullName
}

$BackupFolder = (Resolve-Path -LiteralPath $BackupFolder).Path

Write-Host "Workspace: $workspaceFileFullPath" -ForegroundColor Cyan
Write-Host "workspaceStorage: $storageFolder" -ForegroundColor Cyan
Write-Host "BackupFolder: $BackupFolder" -ForegroundColor Cyan

$targets = @(
    'GitHub.copilot-chat',
    'chatSessions',
    'chatEditingSessions'
)

foreach ($name in $targets) {
    $src = Join-Path $BackupFolder $name
    if (!(Test-Path -LiteralPath $src)) { continue }

    $dest = Join-Path $storageFolder $name
    if (Test-Path -LiteralPath $dest) {
        $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
        $bak = Join-Path $storageFolder ("$name.restorebak-$ts")
        if ($PSCmdlet.ShouldProcess($dest, "Move aside to $bak")) {
            try {
                Move-Item -LiteralPath $dest -Destination $bak -Force
            } catch {
                Write-Host "Could not move existing ${name}: $($_.Exception.Message)" -ForegroundColor Yellow
                Write-Host "Close VS Code completely and re-run." -ForegroundColor Yellow
                continue
            }
        }
    }

    if ($PSCmdlet.ShouldProcess($dest, "Restore from $src")) {
        try {
            Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
            Write-Host "Restored: $name" -ForegroundColor Green
        } catch {
            Write-Host "Restore failed for ${name}: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Close VS Code completely and re-run." -ForegroundColor Yellow
        }
    }
}

Write-Host "" 
Write-Host "Done." -ForegroundColor Green
Write-Host "Reopen VS Code workspace now." -ForegroundColor Cyan
