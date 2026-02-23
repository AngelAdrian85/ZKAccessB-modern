[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceFile,

    [Parameter(Mandatory=$false)]
    [switch]$AlsoResetWorkspaceStateDb,

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
    Write-Host "Hint: open this workspace once, then re-run." -ForegroundColor Yellow
    exit 2
}

Write-Host "Workspace: $workspaceFileFullPath" -ForegroundColor Cyan
Write-Host "workspaceStorage: $storageFolder" -ForegroundColor Cyan

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = Join-Path $PSScriptRoot ("..\\tmp\\vscode_workspaceStorage_backup_$timestamp")
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$targets = @(
    'GitHub.copilot-chat',
    'chatSessions',
    'chatEditingSessions'
)

foreach ($name in $targets) {
    $path = Join-Path $storageFolder $name
    if (!(Test-Path -LiteralPath $path)) {
        continue
    }

    $dest = Join-Path $backupDir $name
    Write-Host "Backing up $name -> $dest" -ForegroundColor Gray
    try {
        Copy-Item -LiteralPath $path -Destination $dest -Recurse -Force
    } catch {
        Write-Host "Backup failed for ${name}: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Close VS Code completely and re-run this script." -ForegroundColor Yellow
        continue
    }

    $bakName = "$name.bak-$timestamp"
    $bakPath = Join-Path $storageFolder $bakName

    if ($PSCmdlet.ShouldProcess($path, "Move to $bakPath")) {
        try {
            Move-Item -LiteralPath $path -Destination $bakPath -Force
            Write-Host "Reset state: $name" -ForegroundColor Green
        } catch {
            Write-Host "Reset failed for ${name}: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Close VS Code completely and re-run this script." -ForegroundColor Yellow
        }
    }
}

if ($AlsoResetWorkspaceStateDb) {
    foreach ($db in @('state.vscdb','state.vscdb.backup')) {
        $dbPath = Join-Path $storageFolder $db
        if (!(Test-Path -LiteralPath $dbPath)) { continue }

        $dest = Join-Path $backupDir $db
        Write-Host "Backing up $db -> $dest" -ForegroundColor Gray
        try {
            Copy-Item -LiteralPath $dbPath -Destination $dest -Force
        } catch {
            Write-Host "Backup failed for ${db}: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Close VS Code completely and re-run this script." -ForegroundColor Yellow
            continue
        }

        $bakPath = Join-Path $storageFolder ("$db.bak-$timestamp")
        if ($PSCmdlet.ShouldProcess($dbPath, "Move to $bakPath")) {
            try {
                Move-Item -LiteralPath $dbPath -Destination $bakPath -Force
                Write-Host "Reset workspace DB: $db" -ForegroundColor Green
            } catch {
                Write-Host "Reset failed for ${db}: $($_.Exception.Message)" -ForegroundColor Yellow
                Write-Host "Close VS Code completely and re-run this script." -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "" 
Write-Host "Done." -ForegroundColor Green
Write-Host "Next: close all VS Code windows, then reopen this workspace." -ForegroundColor Cyan
Write-Host "If resets persist: disable 'GitHub Copilot Chat' for this workspace or update it." -ForegroundColor Cyan
