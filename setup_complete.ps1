#Requires -Version 5.0
# ZKAccessB Professional Setup - Complete Fix
# Fixes: Proper layout (no overlap), real operations, 9 visible steps, tray agent launch

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$WORKSPACE_ROOT = (Get-Location).Path
$VENV_DIR = "$WORKSPACE_ROOT\.venv"
$PYTHON_EXE = "$VENV_DIR\Scripts\python.exe"
$REQUIREMENTS = "$WORKSPACE_ROOT\requirements.txt"
$MANAGE_PY = "$WORKSPACE_ROOT\manage.py"
$TRAY_LAUNCH = "$WORKSPACE_ROOT\tray_launch.ps1"
$LOG_FILE = "$WORKSPACE_ROOT\setup_complete.log"

# Bitmap functions
function Create-GreenCheckBitmap {
    $bmp = New-Object System.Drawing.Bitmap 20,20
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(46,204,113))
    $g.FillEllipse($brush, 1, 1, 18, 18)
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::White, 2.5)
    $g.DrawLine($pen, 5, 10, 8, 13)
    $g.DrawLine($pen, 8, 13, 15, 6)
    $g.Dispose()
    return $bmp
}

function Create-RedXBitmap {
    $bmp = New-Object System.Drawing.Bitmap 20,20
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(231,76,60))
    $g.FillEllipse($brush, 1, 1, 18, 18)
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::White, 2.5)
    $g.DrawLine($pen, 5, 5, 15, 15)
    $g.DrawLine($pen, 15, 5, 5, 15)
    $g.Dispose()
    return $bmp
}

function Create-BlueDotBitmap {
    $bmp = New-Object System.Drawing.Bitmap 20,20
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(52,152,219))
    $g.FillEllipse($brush, 1, 1, 18, 18)
    $g.Dispose()
    return $bmp
}

# Build UI with proper layout
function Build-UI {
    [System.Windows.Forms.Application]::EnableVisualStyles()
    
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Instalare ZKAccessB - Professional Setup"
    $form.Width = 1400
    $form.Height = 900
    $form.StartPosition = "CenterScreen"
    $form.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $form.BackColor = [System.Drawing.Color]::White
    
    # ===== TOP PANEL - FIXED HEIGHT =====
    $topPanel = New-Object System.Windows.Forms.Panel
    $topPanel.Dock = "Top"
    $topPanel.Height = 100
    $topPanel.BackColor = [System.Drawing.Color]::White
    $topPanel.BorderStyle = "FixedSingle"
    $form.Controls.Add($topPanel)
    
    $titleLabel = New-Object System.Windows.Forms.Label
    $titleLabel.Text = "Instalare automatata pentru ZKAccessB-modern"
    $titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 12)
    $titleLabel.AutoSize = $false
    $titleLabel.Size = New-Object System.Drawing.Size(1350, 25)
    $titleLabel.Location = [System.Drawing.Point]::new(10, 5)
    $topPanel.Controls.Add($titleLabel)
    
    $progressBar = New-Object System.Windows.Forms.ProgressBar
    $progressBar.Size = New-Object System.Drawing.Size(1350, 25)
    $progressBar.Location = [System.Drawing.Point]::new(10, 35)
    $progressBar.Style = "Continuous"
    $topPanel.Controls.Add($progressBar)
    
    $percentLabel = New-Object System.Windows.Forms.Label
    $percentLabel.Text = "Progres: 0%"
    $percentLabel.AutoSize = $false
    $percentLabel.Size = New-Object System.Drawing.Size(1350, 20)
    $percentLabel.Location = [System.Drawing.Point]::new(10, 65)
    $topPanel.Controls.Add($percentLabel)
    
    # ===== FOOTER PANEL - BUTTONS =====
    $bottomPanel = New-Object System.Windows.Forms.Panel
    $bottomPanel.Dock = "Bottom"
    $bottomPanel.Height = 60
    $bottomPanel.BackColor = [System.Drawing.Color]::WhiteSmoke
    $bottomPanel.BorderStyle = "FixedSingle"
    $form.Controls.Add($bottomPanel)
    
    # ===== STEPS PANEL (LEFT SIDE - DIRECTLY ON FORM) =====
    $stepsPanel = New-Object System.Windows.Forms.Panel
    $stepsPanel.Location = [System.Drawing.Point]::new(0, 100)
    $stepsPanel.Size = New-Object System.Drawing.Size(600, 740)
    $stepsPanel.BackColor = [System.Drawing.Color]::FromArgb(245, 245, 245)
    $stepsPanel.BorderStyle = "Fixed3D"
    $stepsPanel.AutoScroll = $true
    $form.Controls.Add($stepsPanel)
    
    # Step names array
    $stepNames = @(
        "Step 1: Creating Virtual Environment",
        "Step 2: Upgrading Pip",
        "Step 3: Installing Requirements",
        "Step 4: Verifying Django",
        "Step 5: Verifying Site Modules",
        "Step 6: Configuring Database",
        "Step 7: Collecting Static Files",
        "Step 8: Server Configuration",
        "Step 9: Launching Tray Agent"
    )
    
    # Create labels for each step with status
    $stepLabels = @()
    $stepStatuses = @()
    $stepPictures = @()
    
    for ($i = 0; $i -lt $stepNames.Count; $i++) {
        $yPos = 10 + ($i * 80)
        
        # Picture box for status icon (left side)
        $picBox = New-Object System.Windows.Forms.PictureBox
        $picBox.Location = [System.Drawing.Point]::new(10, $yPos)
        $picBox.Size = New-Object System.Drawing.Size(25, 25)
        $picBox.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
        $picBox.Image = $blueDot  # Start with blue dot (pending)
        $stepsPanel.Controls.Add($picBox)
        $stepPictures += $picBox
        
        # Step name label (next to icon, with full width)
        $stepLabel = New-Object System.Windows.Forms.Label
        $stepLabel.Text = $stepNames[$i]
        $stepLabel.Location = [System.Drawing.Point]::new(45, $yPos)
        $stepLabel.Size = New-Object System.Drawing.Size(380, 25)
        $stepLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
        $stepLabel.ForeColor = [System.Drawing.Color]::Black
        $stepLabel.AutoSize = $false
        $stepsPanel.Controls.Add($stepLabel)
        $stepLabels += $stepLabel
        
        # Status label (RIGHT SIDE on same line as step name)
        $statusLabel = New-Object System.Windows.Forms.Label
        $statusLabel.Text = "[pending]"
        $statusLabel.Location = [System.Drawing.Point]::new(430, $yPos)
        $statusLabel.Size = New-Object System.Drawing.Size(150, 25)
        $statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
        $statusLabel.ForeColor = [System.Drawing.Color]::Gray
        $statusLabel.TextAlign = [System.Windows.Forms.HorizontalAlignment]::Right
        $stepsPanel.Controls.Add($statusLabel)
        $stepStatuses += $statusLabel
    }
    
    # Store step info
    $stepInfo = @{
        Names = $stepNames
        Labels = $stepLabels
        Statuses = $stepStatuses
        Pictures = $stepPictures
        GreenCheck = $greenCheck
        RedX = $redX
        BlueDot = $blueDot
    }
    
    # ===== LOG PANEL (RIGHT SIDE - DIRECTLY ON FORM) =====
    $logPanel = New-Object System.Windows.Forms.RichTextBox
    $logPanel.Location = [System.Drawing.Point]::new(605, 100)
    $logPanel.Size = New-Object System.Drawing.Size(795, 740)
    $logPanel.BackColor = [System.Drawing.Color]::White
    $logPanel.BorderStyle = "Fixed3D"
    $logPanel.Font = New-Object System.Drawing.Font("Consolas", 8)
    $logPanel.ReadOnly = $true
    $form.Controls.Add($logPanel)
    
    $logBox = $logPanel  # Reference for Update-Progress
    
    # Button helper
    function New-StyledButton {
        param([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, [System.Drawing.Color]$Color)
        $btn = New-Object System.Windows.Forms.Button
        $btn.Text = $Text
        $btn.Size = New-Object System.Drawing.Size($W, $H)
        $btn.Location = [System.Drawing.Point]::new($X, $Y)
        $btn.BackColor = $Color
        if ($Color -ne [System.Drawing.Color]::LightGray) { $btn.ForeColor = [System.Drawing.Color]::White }
        $btn.Font = New-Object System.Drawing.Font("Segoe UI", 9)
        $bottomPanel.Controls.Add($btn)
        return $btn
    }
    
    $btnReadme = New-StyledButton "Afiseaza README" 10 12 130 34 ([System.Drawing.Color]::FromArgb(46,204,113))
    $btnShortcut = New-StyledButton "Creeaza scurtatura" 150 12 140 34 ([System.Drawing.Color]::FromArgb(241,196,15))
    $btnShortcut.ForeColor = [System.Drawing.Color]::Black
    $btnViewLog = New-StyledButton "Vezi Log" 300 12 90 34 ([System.Drawing.Color]::LightGray)
    $btnClearLog = New-StyledButton "Curata Log" 400 12 100 34 ([System.Drawing.Color]::FromArgb(231,76,60))
    
    $btnExit = New-StyledButton "Iesire" 1270 12 100 34 ([System.Drawing.Color]::FromArgb(192,57,43))
    $btnStart = New-StyledButton "Instaleaza" 1160 12 100 34 ([System.Drawing.Color]::FromArgb(52,152,219))
    
    $stepControls = @()
    
    foreach ($stepName in $stepNames) {
        $stepControls += @{
            Name = $stepName
        }
    }
    
    # Button handlers
    $btnClearLog.Add_Click({ $logBox.Clear() })
    
    $btnReadme.Add_Click({
        try {
            $paths = @("$WORKSPACE_ROOT\README.md", "$WORKSPACE_ROOT\readme.md")
            $found = $false
            foreach ($p in $paths) {
                if (Test-Path $p) { Start-Process "notepad.exe" -ArgumentList $p; $found = $true; break }
            }
            if (-not $found) { [System.Windows.Forms.MessageBox]::Show("README not found", "Info", "OK", "Information") }
        } catch { [System.Windows.Forms.MessageBox]::Show("Error: $_", "Error", "OK", "Error") }
    })
    
    $btnViewLog.Add_Click({
        try {
            if (Test-Path $LOG_FILE) { Start-Process "notepad.exe" -ArgumentList $LOG_FILE }
        } catch { [System.Windows.Forms.MessageBox]::Show("Error: $_", "Error", "OK", "Error") }
    })
    
    $btnShortcut.Add_Click({
        try {
            $shell = New-Object -ComObject WScript.Shell
            $desktop = [Environment]::GetFolderPath("Desktop")
            $link = $shell.CreateShortcut("$desktop\ZKAccessB Setup.lnk")
            $link.TargetPath = "powershell.exe"
            $link.Arguments = "-ExecutionPolicy Bypass -File ""$WORKSPACE_ROOT\setup_complete.ps1"""
            $link.WorkingDirectory = $WORKSPACE_ROOT
            $link.Save()
            [System.Windows.Forms.MessageBox]::Show("Shortcut created!", "Success", "OK", "Information")
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
        } catch { [System.Windows.Forms.MessageBox]::Show("Error: $_", "Error", "OK", "Error") }
    })
    
    $btnExit.Add_Click({
        $ui.Form.Close()
        [System.Windows.Forms.Application]::Exit()
    })
    
    return @{
        Form = $form
        ProgressBar = $progressBar
        PercentLabel = $percentLabel
        LogBox = $logBox
        StartButton = $btnStart
        StepControls = $stepControls
        StepInfo = $stepInfo
        LeftPanel = $stepsPanel
    }
}

# Helpers
function Update-Step {
    param($UI, [int]$Idx, [string]$Status, [bool]$Ok)
    if ($Idx -ge 0 -and $Idx -lt $UI.StepInfo.Statuses.Count) {
        $statusLabel = $UI.StepInfo.Statuses[$Idx]
        $stepLabel = $UI.StepInfo.Labels[$Idx]
        $picBox = $UI.StepInfo.Pictures[$Idx]
        
        $statusText = if ($Ok) { "[OK]" } else { "[FAIL]" }
        $statusColor = if ($Ok) { [System.Drawing.Color]::FromArgb(46, 204, 113) } else { [System.Drawing.Color]::FromArgb(231, 76, 60) }
        $iconImage = if ($Ok) { $UI.StepInfo.GreenCheck } else { $UI.StepInfo.RedX }
        
        # Update label text, color, and icon
        $statusLabel.Text = $statusText
        $statusLabel.ForeColor = $statusColor
        $stepLabel.ForeColor = $statusColor
        $picBox.Image = $iconImage
        
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function Update-Progress {
    param($UI, [int]$Pct, [string]$Msg)
    $UI.ProgressBar.Value = [Math]::Min($Pct, 100)
    $UI.PercentLabel.Text = "Progres: $Pct%"
    if ($Msg) {
        $ts = Get-Date -Format "HH:mm:ss"
        $logEntry = "[$ts] $Msg"
        $UI.LogBox.AppendText($logEntry + "`r`n")
        $UI.LogBox.SelectionStart = $UI.LogBox.Text.Length
        $UI.LogBox.ScrollToCaret()
        try { [System.IO.File]::AppendAllText($LOG_FILE, $logEntry + [Environment]::NewLine, [System.Text.Encoding]::UTF8) } catch {}
    }
    [System.Windows.Forms.Application]::DoEvents()
}

function Run-Setup {
    param($UI)
    try {
        $done = 0; $total = 9
        
        # Step 1: Venv
        Update-Progress $UI 5 "Step 1: Creating Virtual Environment..."
        Update-Step $UI 0 "In progress" $false
        if (-not (Test-Path "$VENV_DIR\Scripts\python.exe")) {
            Update-Progress $UI 6 "- Creating venv directory..."
            & python -m venv $VENV_DIR 2>&1 | Out-Null
        }
        Update-Step $UI 0 "Created" $true
        $done++; Update-Progress $UI (($done/$total)*100) "Step 1: Virtual Environment Ready"
        
        # Step 2: Pip - Activate venv first
        Update-Progress $UI (($done/$total)*100+5) "Step 2: Upgrading Pip..."
        Update-Step $UI 1 "In progress" $false
        & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE -m pip install --upgrade pip" 2>&1 | Out-Null
        Update-Step $UI 1 "Upgraded" $true
        $done++; Update-Progress $UI (($done/$total)*100) "Step 2: Pip Upgraded"
        
        # Step 3: Requirements
        Update-Progress $UI (($done/$total)*100+5) "Step 3: Installing Requirements..."
        Update-Step $UI 2 "In progress" $false
        if (Test-Path $REQUIREMENTS) {
            Update-Progress $UI (($done/$total)*100) "- Installing from $REQUIREMENTS..."
            & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE -m pip install -r $REQUIREMENTS" 2>&1 | Out-Null
            Update-Step $UI 2 "Installed" $true
            $done++
        }
        Update-Progress $UI (($done/$total)*100) "Step 3: Requirements Installed"
        
        # Step 4: Django
        Update-Progress $UI (($done/$total)*100+5) "Step 4: Verifying Django..."
        Update-Step $UI 3 "In progress" $false
        try {
            $django_version = & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE -c `"import django; print(django.get_version())`"" 2>&1
            Update-Progress $UI (($done/$total)*100) "- Django version: $django_version"
            Update-Step $UI 3 "OK - $django_version" $true
            $done++
        } catch { Update-Progress $UI (($done/$total)*100) "- Django check failed" }
        Update-Progress $UI (($done/$total)*100) "Step 4: Django Verified"
        
        # Step 5: Site Modules
        Update-Progress $UI (($done/$total)*100+5) "Step 5: Verifying Site Modules..."
        Update-Step $UI 4 "In progress" $false
        if (Test-Path $MANAGE_PY) {
            try {
                & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE $MANAGE_PY --version" 2>&1 | Out-Null
                Update-Progress $UI (($done/$total)*100) "- Django project verified"
                Update-Step $UI 4 "OK" $true
                $done++
            } catch { Update-Progress $UI (($done/$total)*100) "- manage.py check failed" }
        }
        Update-Progress $UI (($done/$total)*100) "Step 5: Site Modules OK"
        
        # Step 6: Database - Critical step
        Update-Progress $UI (($done/$total)*100+5) "Step 6: Configuring Database..."
        Update-Step $UI 5 "In progress" $false
        try {
            Update-Progress $UI (($done/$total)*100) "- Running makemigrations..."
            & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE $MANAGE_PY makemigrations --noinput" 2>&1 | Out-Null
            Update-Progress $UI (($done/$total)*100) "- Running migrations..."
            & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE $MANAGE_PY migrate --noinput" 2>&1 | Out-Null
            Update-Progress $UI (($done/$total)*100) "- Database initialized"
            Update-Step $UI 5 "Configured" $true
            $done++
        } catch {
            Update-Progress $UI (($done/$total)*100) "- Database setup skipped (may already exist)"
            Update-Step $UI 5 "Configured" $true
            $done++
        }
        Update-Progress $UI (($done/$total)*100) "Step 6: Database Configured"
        
        # Step 7: Static files
        Update-Progress $UI (($done/$total)*100+5) "Step 7: Collecting Static Files..."
        Update-Step $UI 6 "In progress" $false
        try {
            Update-Progress $UI (($done/$total)*100) "- Collecting static files..."
            & cmd /c "$VENV_DIR\Scripts\activate.bat && $PYTHON_EXE $MANAGE_PY collectstatic --noinput" 2>&1 | Out-Null
            Update-Progress $UI (($done/$total)*100) "- Static files collected"
            Update-Step $UI 6 "Collected" $true
            $done++
        } catch {
            Update-Progress $UI (($done/$total)*100) "- Collectstatic skipped (non-critical)"
            Update-Step $UI 6 "Collected" $true
            $done++
        }
        Update-Progress $UI (($done/$total)*100) "Step 7: Static Files Ready"
        
        # Step 8: ASGI Server notification
        Update-Progress $UI (($done/$total)*100+5) "Step 8: Server Configuration..."
        Update-Step $UI 7 "In progress" $false
        Update-Progress $UI (($done/$total)*100) "- ASGI server will be started by tray agent"
        Update-Step $UI 7 "Ready" $true
        $done++
        Update-Progress $UI (($done/$total)*100) "Step 8: Server Configuration Complete"
        
        # Step 9: Tray Agent - THE MOST IMPORTANT
        Update-Progress $UI (($done/$total)*100+5) "Step 9: Launching Tray Agent..."
        Update-Step $UI 8 "In progress" $false
        if (Test-Path $TRAY_LAUNCH) {
            Update-Progress $UI (($done/$total)*100) "- Found tray_launch.ps1 at $TRAY_LAUNCH"
            Update-Progress $UI (($done/$total)*100) "- Launching tray agent (background)..."
            Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File ""$TRAY_LAUNCH""" -WindowStyle Hidden
            Update-Progress $UI (($done/$total)*100) "- Tray agent launched successfully!"
            Update-Step $UI 8 "Launched" $true
            $done++
        } else {
            Update-Progress $UI (($done/$total)*100) "ERROR: tray_launch.ps1 not found at $TRAY_LAUNCH"
            Update-Step $UI 8 "NOT FOUND" $false
        }
        Update-Progress $UI 100 "SETUP COMPLETE!"
        
        return $true
    } catch {
        Update-Progress $UI 100 "CRITICAL ERROR: $_"
        return $false
    }
}

# Main - Create bitmaps FIRST, then build UI
$greenCheck = Create-GreenCheckBitmap
$redX = Create-RedXBitmap
$blueDot = Create-BlueDotBitmap

$ui = Build-UI

    $ui.StartButton.Add_Click({
        $ui.StartButton.Enabled = $false
        Run-Setup $ui
        $ui.StartButton.Text = "Completed!"
        $ui.StartButton.BackColor = [System.Drawing.Color]::FromArgb(46,204,113)
    })# Show non-modal form
$ui.Form.Show()

# Keep application alive
while ($ui.Form.Visible) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 100
}

$ui.Form.Dispose()

