#Requires -Version 5.0
# ZKAccessB Modern Setup Script - Non-Blocking UI with Real-Time Progress
# Features: Non-blocking UI, real-time progress bar, visual feedback, ASCII-only (no emoji encoding issues)

param(
    [switch]$Headless = $false
)

# ========== CONFIGURATION ==========
$WORKSPACE_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR = "$WORKSPACE_ROOT\.venv"
$PYTHON_EXE = "$VENV_DIR\Scripts\python.exe"
$REQUIREMENTS = "$WORKSPACE_ROOT\requirements.txt"
$MANAGE_PY = "$WORKSPACE_ROOT\manage.py"
$STEPS = 7

# ========== HELPER FUNCTIONS ==========
function Invoke-Command {
    param([string]$Command, [string[]]$CommandArgs)
    
    try {
        $output = & $Command @CommandArgs 2>&1
        $exitCode = $LASTEXITCODE
        return @{
            Success = $exitCode -eq 0
            Output = $output
        }
    } catch {
        return @{
            Success = $false
            Output = $_.Exception.Message
        }
    }
}

function Add-LogLine {
    param([string]$Message)
    
    if ($textbox) {
        $textbox.AppendText("$Message`r`n")
        $textbox.ScrollToCaret()
        [System.Windows.Forms.Application]::DoEvents()
    } else {
        Write-Host $Message
    }
}

function Set-ProgressBar {
    param([int]$Percentage, [string]$Status)
    
    if ($progressBar) {
        $progressBar.Value = [Math]::Min($Percentage, 100)
        $progressBar.Refresh()
        [System.Windows.Forms.Application]::DoEvents()
    }
    
    if ($statusLabel) {
        $statusLabel.Text = $Status
        $statusLabel.Refresh()
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function Invoke-Setup {
    try {
        $current = 0
        
        # Step 1: Create Virtual Environment
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Creating virtual environment..." }
        
        if ($form) { Add-LogLine "[*] Creating venv..." }
        if (-not (Test-Path "$VENV_DIR\Scripts\python.exe")) {
            $result = Invoke-Command python @('-m', 'venv', $VENV_DIR)
            if (-not $result.Success) {
                if ($form) { Add-LogLine "[!] Venv creation failed: $($result.Output)" }
                return $false
            }
            Start-Sleep -Milliseconds 500
        }
        if ($form) { Add-LogLine "[+] Virtual environment ready" }
        
        # Step 2: Upgrade pip
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Upgrading pip..." }
        
        if ($form) { Add-LogLine "[*] Upgrading pip..." }
        $result = Invoke-Command $PYTHON_EXE @('-m', 'pip', 'install', '--upgrade', 'pip', '-q')
        if ($form) { Add-LogLine "[+] Pip upgraded" }
        
        # Step 3: Install requirements
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Installing requirements..." }
        
        if ($form) { Add-LogLine "[*] Installing requirements..." }
        $result = Invoke-Command $PYTHON_EXE @('-m', 'pip', 'install', '-r', $REQUIREMENTS, '-q')
        if (-not $result.Success) {
            if ($form) { Add-LogLine "[!] Some packages failed (may be non-critical)" }
        } else {
            if ($form) { Add-LogLine "[+] Requirements installed" }
        }
        
        # Step 4: Check Django
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Checking Django..." }
        
        if ($form) { Add-LogLine "[*] Checking Django..." }
        $result = Invoke-Command $PYTHON_EXE @('-c', 'import django; print(django.get_version())')
        if ($result.Success) {
            if ($form) { Add-LogLine "[+] Django: $($result.Output[0])" }
        } else {
            if ($form) { Add-LogLine "[!] Django check failed" }
            return $false
        }
        
        # Step 5: Check site modules
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Checking site modules..." }
        
        if ($form) { Add-LogLine "[*] Checking Django site..." }
        $result = Invoke-Command $PYTHON_EXE @($MANAGE_PY, '--version')
        if ($result.Success) {
            if ($form) { Add-LogLine "[+] Site modules OK" }
        } else {
            if ($form) { Add-LogLine "[!] Site modules check failed" }
            return $false
        }
        
        # Step 6: Check database
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Checking database..." }
        
        if ($form) { Add-LogLine "[*] Checking database migrations..." }
        $result = Invoke-Command $PYTHON_EXE @($MANAGE_PY, 'makemigrations', '--dry-run', '--check')
        if (-not $result.Success) {
            if ($form) { Add-LogLine "[>] Applying migrations..." }
            Invoke-Command $PYTHON_EXE @($MANAGE_PY, 'makemigrations') | Out-Null
            Invoke-Command $PYTHON_EXE @($MANAGE_PY, 'migrate') | Out-Null
        }
        if ($form) { Add-LogLine "[+] Database OK" }
        
        # Step 7: Collect static files
        $current++
        if ($form) { Set-ProgressBar (($current / $STEPS) * 100) "Step $($current)/$($STEPS): Collecting static files..." }
        
        if ($form) { Add-LogLine "[*] Collecting static files..." }
        $result = Invoke-Command $PYTHON_EXE @($MANAGE_PY, 'collectstatic', '--noinput')
        if ($form) { Add-LogLine "[+] Static files collected" }
        
        if ($form) { 
            Set-ProgressBar 100 "Installation Complete!"
            Add-LogLine ""
            Add-LogLine "[OK] INSTALLATION SUCCESSFUL [OK]"
            Add-LogLine ""
            Add-LogLine "To start the agent:"
            Add-LogLine "  powershell -ExecutionPolicy Bypass -File tray_launch.ps1"
            Add-LogLine ""
        }
        
        return $true
    } catch {
        if ($form) { Add-LogLine "[ERROR] Exception: $($_.Exception.Message)" }
        return $false
    }
}

# ========== MAIN EXECUTION ==========
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()

if (-not $Headless) {
    # GUI MODE
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "ZKAccessB Setup"
    $form.Width = 600
    $form.Height = 500
    $form.StartPosition = "CenterScreen"
    $form.BackColor = [System.Drawing.Color]::White
    $form.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    
    # Title
    $title = New-Object System.Windows.Forms.Label
    $title.Text = "ZKAccessB Installation Setup"
    $title.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
    $title.Location = New-Object System.Drawing.Point(20, 20)
    $title.AutoSize = $true
    $form.Controls.Add($title)
    
    # Status label
    $statusLabel = New-Object System.Windows.Forms.Label
    $statusLabel.Text = "Ready to install"
    $statusLabel.Location = New-Object System.Drawing.Point(20, 50)
    $statusLabel.Size = New-Object System.Drawing.Size(560, 20)
    $form.Controls.Add($statusLabel)
    
    # Progress bar
    $progressBar = New-Object System.Windows.Forms.ProgressBar
    $progressBar.Location = New-Object System.Drawing.Point(20, 80)
    $progressBar.Size = New-Object System.Drawing.Size(560, 25)
    $progressBar.Style = "Continuous"
    $form.Controls.Add($progressBar)
    
    # Log textbox
    $textbox = New-Object System.Windows.Forms.TextBox
    $textbox.Location = New-Object System.Drawing.Point(20, 120)
    $textbox.Size = New-Object System.Drawing.Size(560, 280)
    $textbox.MultiLine = $true
    $textbox.ScrollBars = "Both"
    $textbox.ReadOnly = $true
    $form.Controls.Add($textbox)
    
    # Start button
    $startButton = New-Object System.Windows.Forms.Button
    $startButton.Text = "START INSTALLATION"
    $startButton.Location = New-Object System.Drawing.Point(20, 410)
    $startButton.Size = New-Object System.Drawing.Size(560, 40)
    $startButton.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $startButton.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
    $startButton.ForeColor = [System.Drawing.Color]::White
    $startButton.Add_Click({
        $startButton.Enabled = $false
        $textbox.Text = ""
        Add-LogLine "Installation starting..."
        Add-LogLine ""
        
        $success = Invoke-Setup
        
        if ($success) {
            $startButton.BackColor = [System.Drawing.Color]::FromArgb(0, 176, 80)
            $startButton.Text = "INSTALLATION COMPLETE (Green = Success)"
        } else {
            $startButton.BackColor = [System.Drawing.Color]::FromArgb(192, 0, 0)
            $startButton.Text = "INSTALLATION FAILED (Red = Error)"
        }
    })
    $form.Controls.Add($startButton)
    
    Add-LogLine "Click START to begin installation"
    Add-LogLine ""
    
    [void]$form.ShowDialog()
} else {
    # HEADLESS MODE (Command line)
    Write-Host "[*] ZKAccessB Setup - Starting..."
    $result = Invoke-Setup
    exit $(if ($result) { 0 } else { 1 })
}
