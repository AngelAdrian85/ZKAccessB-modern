<#
Helper: push_and_open_pr.ps1

What it does:
- Creates a branch (if not present), stages all changes, commits with a sensible message, pushes to origin, and opens a PR.
- If `gh` (GitHub CLI) is available, it will use it to open the PR interactively using the prepared PR body file (if present).
- If `gh` is not available, it will print a URL you can open in your browser to create the PR.

Usage (PowerShell):
  .\scripts\push_and_open_pr.ps1 -BranchName "port/python3/commands-and-migrations" -CommitMessage "port(commands+ci+db): modernize management commands, tests, CI, DB runbook"

Notes:
- Requires `git` installed and available in PATH.
- Optional: `gh` for direct PR creation. If `gh` is missing the script will construct the PR URL.
#>

param(
    [string]$BranchName = "port/python3/commands-and-migrations",
    [string]$CommitMessage = "port(commands+ci+db): modernize management commands, expand tests, improve CI, add DB migration plan",
    [string]$PrBodyFile = "port_plan/PR_DESCRIPTION.md"
)

function Exec-Git {
    param($args)
    Write-Host "git $args"
    git $args
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not installed or not in PATH. Install git and re-run this script."
    exit 1
}

# 1) Ensure branch exists (create if necessary)
$current = (git rev-parse --abbrev-ref HEAD).Trim()
if ($current -ne $BranchName) {
    # if branch exists locally, check it out; otherwise create from current
    $exists = git show-ref --verify --quiet refs/heads/$BranchName; if ($LASTEXITCODE -eq 0) { 
        Exec-Git "checkout $BranchName"
    } else {
        Exec-Git "checkout -b $BranchName"
    }
}

# 2) Stage all changes and commit
Exec-Git "add -A"

$status = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($status)) {
    Exec-Git "commit -m \"$CommitMessage\""
} else {
    Write-Host "No changes to commit."
}

# 3) Push
Exec-Git "push -u origin $BranchName"

# 4) Open PR via gh if available
if (Get-Command gh -ErrorAction SilentlyContinue) {
    if (Test-Path $PrBodyFile) {
        gh pr create --fill --body-file $PrBodyFile --base main --head $BranchName
    } else {
        gh pr create --fill --base main --head $BranchName
    }
} else {
    # Construct a GitHub URL for a new PR (opens browser)
    $remoteUrl = (git remote get-url origin).Trim()
    # convert git@github.com:owner/repo.git -> https://github.com/owner/repo
    if ($remoteUrl -match '^git@github.com:(.+)/(.+)\.git$') {
        $owner = $Matches[1]; $repo = $Matches[2]
        $prUrl = "https://github.com/$owner/$repo/compare/main...$BranchName?expand=1"
    } elseif ($remoteUrl -match '^https://github.com/(.+)/(.+)') {
        $owner = $Matches[1]; $repo = $Matches[2]
        $prUrl = "https://github.com/$owner/$repo/compare/main...$BranchName?expand=1"
    } else {
        $prUrl = "(unknown remote url: $remoteUrl)"
    }

    Write-Host "gh CLI not found. Open the following URL in your browser to create the PR:"
    Write-Host $prUrl
    if ($prUrl -like 'https://*') { Start-Process $prUrl }
}

Write-Host "Done. If the script created a PR, check GitHub for CI results."
