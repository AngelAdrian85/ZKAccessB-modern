# Attempt to download original vendor assets into the legacy media folder.
# Run from workspace root PowerShell (Windows PowerShell v5.1):
#   Set-Location 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB'
#   .venv\Scripts\Activate.ps1
#   .\zkeco_modern\scripts\fetch_vendor_assets.ps1

$errors = @()
$root = (Get-Location).ProviderPath
$media = Join-Path $root 'zkeco\units\adms\mysite\media'
Write-Host "MEDIA root: $media"

# Ensure directories exist
New-Item -ItemType Directory -Path (Join-Path $media 'jslib') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $media 'themes\hot-sneaks') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $media 'images\login') -Force | Out-Null

# Map of target relative paths -> candidate URLs (checked in order)
$targets = @{
    'jslib\jquery-ui-1.7.2.custom.js' = @(
        'https://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js',
        'https://code.jquery.com/ui/1.7.2/jquery-ui.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js'
    )
    'jslib\jquery.perciformes.js' = @(
        # This appears to be a custom plugin; no obvious CDN. Try common guesses (may fail).
        'https://cdn.jsdelivr.net/npm/jquery-perciformes@latest/dist/jquery.perciformes.js'
    )
    'jslib\scrollable.js' = @(
        # jQuery Tools scrollable plugin locations (best-effort)
        'https://cdn.jsdelivr.net/gh/jquerytools/jquery-tools@master/src/scrollable/scrollable.js',
        'https://cdnjs.cloudflare.com/ajax/libs/jquery-tools/1.2.7/scrollable.js'
    )
    'themes\hot-sneaks\jquery-ui-1.7.2.custom.css' = @(
        # Theme CSS may not exist on CDN; try theme roll archives (best-effort)
        'https://raw.githubusercontent.com/jquery/jquery-ui/master/themes/hot-sneaks/jquery-ui.css'
    )
}

Function Try-Download($url, $dest) {
    try {
        Write-Host "Trying: $url -> $dest"
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
        Write-Host "Downloaded: $dest"
        return $true
    } catch {
        Write-Host "Failed: $url ($($_.Exception.Message))"
        return $false
    }
}

foreach ($rel in $targets.Keys) {
    $candidates = $targets[$rel]
    $dest = Join-Path $media $rel
    $ok = $false
    foreach ($u in $candidates) {
        if (Try-Download $u $dest) { $ok = $true; break }
    }
    if (-not $ok) {
        $errors += @{ path = $rel; note = 'No candidate downloaded; leave existing placeholder or add manually' }
    }
}

if ($errors.Count -eq 0) {
    Write-Host "All candidate downloads completed or targets already existed."
    exit 0
} else {
    Write-Host "Some targets were not downloaded:" -ForegroundColor Yellow
    foreach ($e in $errors) { Write-Host " - $($e.path): $($e.note)" }
    exit 2
}
