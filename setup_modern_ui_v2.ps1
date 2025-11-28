#Requires -RunAsAdministrator
# ZKAccessB Modern Setup - v2 (Non-blocking, Real-time Progress)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$PROJECT_ROOT = Split-Path -Parent $PSCommandPath
$PYTHON_EXE = "$PROJECT_ROOT\.venv\Scripts\python.exe"
$MANAGE_PY = "$PROJECT_ROOT\zkeco_modern\manage.py"

# ============================================================================
# UI COMPONENTS
# ============================================================================

function New-StatusBitmap($status) {
    # $status: 0=pending, 1=checking, 2=installing, 3=success, 4=error
    $bmp = New-Object System.Drawing.Bitmap 20,20
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    
    $colors = @(
        [System.Drawing.Color]::FromArgb(200,200,200),  # pending - gray
        [System.Drawing.Color]::FromArgb(52,152,219),   # checking - blue
        [System.Drawing.Color]::FromArgb(241,196,15),   # installing - yellow
        [System.Drawing.Color]::FromArgb(46,204,113),   # success - green
        [System.Drawing.Color]::FromArgb(231,76,60)     # error - red
    )
    
    $brush = New-Object System.Drawing.SolidBrush $colors[$status]
    $g.FillEllipse($brush, 0,0,20,20)
    
    $g.Dispose()
    return $bmp
}

# ============================================================================
# MAIN UI
# ============================================================================

$form = New-Object System.Windows.Forms.Form
$form.Text = 'ZKAccessB - Instalare Automata'
$form.Size = New-Object System.Drawing.Size(900, 700)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(240,242,245)

# Header
$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Dock = 'Top'
$headerPanel.Height = 60
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(30,120,200)
$form.Controls.Add($headerPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = 'Instalare automata pentru ZKAccessB-modern'
$titleLabel.Font = New-Object System.Drawing.Font('Segoe UI', 14, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::White
$titleLabel.Dock = 'Fill'
$titleLabel.TextAlign = 'MiddleCenter'
$headerPanel.Controls.Add($titleLabel)

# Progress bar area
$progressPanel = New-Object System.Windows.Forms.Panel
$progressPanel.Dock = 'Top'
$progressPanel.Height = 50
$progressPanel.Padding = New-Object System.Windows.Forms.Padding(20,10,20,5)
$form.Controls.Add($progressPanel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Dock = 'Top'
$progressBar.Height = 20
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$progressBar.ForeColor = [System.Drawing.Color]::FromArgb(46,204,113)
$progressPanel.Controls.Add($progressBar)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = 'Progres: 0%'
$statusLabel.Dock = 'Bottom'
$statusLabel.Height = 20
$statusLabel.TextAlign = 'MiddleCenter'
$statusLabel.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$progressPanel.Controls.Add($statusLabel)

# Content area (split)
$splitContainer = New-Object System.Windows.Forms.SplitContainer
$splitContainer.Dock = 'Fill'
$splitContainer.SplitterDistance = 250
$form.Controls.Add($splitContainer)

# Left: Steps with checkboxes
$stepsPanel = New-Object System.Windows.Forms.Panel
$stepsPanel.Dock = 'Fill'
$stepsPanel.AutoScroll = $true
$stepsPanel.BackColor = [System.Drawing.Color]::White
$stepsPanel.Padding = New-Object System.Windows.Forms.Padding(10)
$splitContainer.Panel1.Controls.Add($stepsPanel)

# Right: Log
$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Dock = 'Fill'
$logBox.ReadOnly = $true
$logBox.Font = New-Object System.Drawing.Font('Consolas', 9)
$logBox.BackColor = [System.Drawing.Color]::FromArgb(30,30,30)
$logBox.ForeColor = [System.Drawing.Color]::FromArgb(0,255,0)
$logBox.Multiline = $true
$splitContainer.Panel2.Controls.Add($logBox)

# Bottom buttons
$bottomPanel = New-Object System.Windows.Forms.Panel
$bottomPanel.Dock = 'Bottom'
$bottomPanel.Height = 50
$bottomPanel.BackColor = [System.Drawing.Color]::FromArgb(240,242,245)
$bottomPanel.Padding = New-Object System.Windows.Forms.Padding(10)
$form.Controls.Add($bottomPanel)

$startButton = New-Object System.Windows.Forms.Button
$startButton.Text = 'Start Installation'
$startButton.Width = 150
$startButton.Height = 35
$startButton.Location = New-Object System.Drawing.Point(10,10)
$startButton.BackColor = [System.Drawing.Color]::FromArgb(46,204,113)
$startButton.ForeColor = [System.Drawing.Color]::White
$startButton.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$startButton.FlatStyle = 'Flat'
$startButton.Enabled = $true
$bottomPanel.Controls.Add($startButton)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Text = 'Close'
$closeButton.Width = 150
$closeButton.Height = 35
$closeButton.Location = New-Object System.Drawing.Point(170,10)
$closeButton.BackColor = [System.Drawing.Color]::FromArgb(231,76,60)
$closeButton.ForeColor = [System.Drawing.Color]::White
$closeButton.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$closeButton.FlatStyle = 'Flat'
$bottomPanel.Controls.Add($closeButton)

# ============================================================================
# STEP DEFINITIONS
# ============================================================================

$steps = @(
    @{ Name = "Activate Virtual Environment"; Icon = 0 },
    @{ Name = "Install Requirements (pip)"; Icon = 0 },
    @{ Name = "Check Django"; Icon = 0 },
    @{ Name = "Check ASGI (uvicorn)"; Icon = 0 },
    @{ Name = "Check Django Site Modules"; Icon = 0 },
    @{ Name = "Check Database & Migrations"; Icon = 0 },
    @{ Name = "Collect Static Files"; Icon = 0 }
)

# Create UI rows for steps
$stepControls = @()
$yPos = 0
foreach ($i in 0..($steps.Count-1)) {
    $row = New-Object System.Windows.Forms.Panel
    $row.Height = 35
    $row.Width = $stepsPanel.Width - 20
    $row.Location = New-Object System.Drawing.Point(0, $yPos)
    $row.Dock = 'Top'
    
    $icon = New-Object System.Windows.Forms.PictureBox
    $icon.Image = New-StatusBitmap(0)
    $icon.SizeMode = 'AutoSize'
    $icon.Location = New-Object System.Drawing.Point(5, 8)
    $row.Controls.Add($icon)
    
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $steps[$i].Name
    $label.Font = New-Object System.Drawing.Font('Segoe UI', 10)
    $label.Location = New-Object System.Drawing.Point(35, 8)
    $label.AutoSize = $true
    $row.Controls.Add($label)
    
    $stepsPanel.Controls.Add($row)
    $stepControls += @{ Panel = $row; Icon = $icon; Label = $label; Status = 0 }
    
    $yPos += 35
}

# ============================================================================
# LOG FUNCTION
# ============================================================================

function Add-Log($message) {
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $message"
    
    if ($logBox.InvokeRequired) {
        $logBox.Invoke([Action]{
            $logBox.AppendText($line + "`r`n")
            $logBox.SelectionStart = $logBox.Text.Length
            $logBox.ScrollToCaret()
        })
    } else {
        $logBox.AppendText($line + "`r`n")
        $logBox.SelectionStart = $logBox.Text.Length
        $logBox.ScrollToCaret()
    }
}

function Update-StepStatus($index, $status) {
    # status: 0=pending, 1=checking, 2=installing, 3=success, 4=error
    $stepControls[$index].Status = $status
    
    if ($stepControls[$index].Icon.InvokeRequired) {
        $stepControls[$index].Icon.Invoke([Action]{
            $stepControls[$index].Icon.Image = New-StatusBitmap($status)
        })
    } else {
        $stepControls[$index].Icon.Image = New-StatusBitmap($status)
    }
}

function Update-Progress($percent, $message) {
    if ($progressBar.InvokeRequired) {
        $progressBar.Invoke([Action]{
            $progressBar.Value = [Math]::Min(100, $percent)
            $statusLabel.Text = "Progres: $percent% - $message"
        })
    } else {
        $progressBar.Value = [Math]::Min(100, $percent)
        $statusLabel.Text = "Progres: $percent% - $message"
    }
}

# ============================================================================
# INSTALLATION LOGIC (RUN IN BACKGROUND)
# ============================================================================

function Run-Installation {
    param([int]$dryRun = 0)
    
    $stepIndex = 0
    $totalSteps = $steps.Count
    
    try {
        # Step 1: Activate Venv
        $stepIndex = 0
        Update-StepStatus $stepIndex 1
        Update-Progress (($stepIndex / $totalSteps) * 100) "Checking virtual environment..."
        Add-Log "Checking venv..."
        
        if (-not (Test-Path "$PROJECT_ROOT\.venv\Scripts\python.exe")) {
            Add-Log "Creating venv..."
            Update-StepStatus $stepIndex 2
            & python -m venv "$PROJECT_ROOT\.venv" 2>&1 | ForEach-Object { Add-Log $_ }
        }
        
        & "$PROJECT_ROOT\.venv\Scripts\Activate.ps1" 2>&1 | Out-Null
        Add-Log "✓ Virtual environment activated"
        Update-StepStatus $stepIndex 3
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Installing requirements..."
        
        # Step 2: Install Requirements
        Add-Log "Installing requirements..."
        Update-StepStatus $stepIndex 2
        & $PYTHON_EXE -m pip install --upgrade pip -q 2>&1 | Out-Null
        & $PYTHON_EXE -m pip install -r "$PROJECT_ROOT\requirements.txt" -q 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ Requirements installed"
            Update-StepStatus $stepIndex 3
        } else {
            Add-Log "✗ Requirements installation failed"
            Update-StepStatus $stepIndex 4
            return $false
        }
        
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Checking Django..."
        
        # Step 3: Check Django
        Add-Log "Checking Django..."
        Update-StepStatus $stepIndex 1
        & $PYTHON_EXE -c "import django; print(django.get_version())" 2>&1 | ForEach-Object { Add-Log $_; }
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ Django OK"
            Update-StepStatus $stepIndex 3
        } else {
            Add-Log "✗ Django check failed"
            Update-StepStatus $stepIndex 4
            return $false
        }
        
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Checking ASGI..."
        
        # Step 4: Check ASGI (uvicorn)
        Add-Log "Checking ASGI (uvicorn)..."
        Update-StepStatus $stepIndex 1
        $uvResult = & $PYTHON_EXE -c "import uvicorn" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ ASGI available"
        } else {
            Add-Log "⚠ ASGI optional (will use WSGI)"
        }
        Update-StepStatus $stepIndex 3
        
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Checking site modules..."
        
        # Step 5: Check Django Site
        Add-Log "Checking Django site modules..."
        Update-StepStatus $stepIndex 1
        & $PYTHON_EXE $MANAGE_PY --version 2>&1 | ForEach-Object { Add-Log $_; }
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ Site modules OK"
            Update-StepStatus $stepIndex 3
        } else {
            Add-Log "✗ Site modules check failed"
            Update-StepStatus $stepIndex 4
            return $false
        }
        
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Checking database..."
        
        # Step 6: Database migrations
        Add-Log "Checking database and migrations..."
        Update-StepStatus $stepIndex 1
        & $PYTHON_EXE $MANAGE_PY makemigrations --dry-run --check 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Add-Log "Applying migrations..."
            & $PYTHON_EXE $MANAGE_PY makemigrations 2>&1 | ForEach-Object { Add-Log $_; }
            & $PYTHON_EXE $MANAGE_PY migrate 2>&1 | ForEach-Object { Add-Log $_; }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ Database OK"
            Update-StepStatus $stepIndex 3
        } else {
            Add-Log "✗ Database check failed (non-critical)"
            Update-StepStatus $stepIndex 3
        }
        
        Update-Progress (((++$stepIndex) / $totalSteps) * 100) "Collecting static files..."
        
        # Step 7: Collect static
        Add-Log "Collecting static files..."
        Update-StepStatus $stepIndex 2
        & $PYTHON_EXE $MANAGE_PY collectstatic --noinput 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Add-Log "✓ Static files collected"
            Update-StepStatus $stepIndex 3
        } else {
            Add-Log "✗ Static file collection failed (non-critical)"
            Update-StepStatus $stepIndex 3
        }
        
        Update-Progress 100 "Installation complete!"
        Add-Log ""
        Add-Log "✓✓✓ Instalatie completata cu succes! ✓✓✓"
        Add-Log ""
        Add-Log "Pentru a porni agentul, rulati:"
        Add-Log "  powershell -ExecutionPolicy Bypass -File tray_launch.ps1"
        Add-Log ""
        
        return $true
        
    } catch {
        Add-Log "✗ Installation error: $($_.Exception.Message)"
        return $false
    }
}

# ============================================================================
# EVENT HANDLERS
# ============================================================================

$startButton.Add_Click({
    if ($startButton.Text -eq 'Start Installation') {
        $startButton.Enabled = $false
        $startButton.Text = 'Installing...'
        
        # Run in background job to prevent blocking UI
        $job = Start-Job -ScriptBlock {
            param($root, $py, $mgmt, $logFunc, $updateFunc, $progFunc)
            
            . ([scriptblock]::Create($logFunc))
            . ([scriptblock]::Create($updateFunc))
            . ([scriptblock]::Create($progFunc))
            
            Run-Installation -dryRun 0
        } -ArgumentList $PROJECT_ROOT, $PYTHON_EXE, $MANAGE_PY, `
            (Get-Content -Path $PROFILE -ErrorAction SilentlyContinue), `
            ${function:Add-Log}, ${function:Update-StepStatus}, ${function:Update-Progress}
        
        # Monitor job completion without blocking UI
        $timer = New-Object System.Windows.Forms.Timer
        $timer.Interval = 500
        
        $timer.Add_Tick({
            if ($job.State -eq 'Completed' -or $job.State -eq 'Failed') {
                $timer.Stop()
                $timer.Dispose()
                
                $result = Receive-Job $job
                Remove-Job $job
                
                $startButton.Text = 'Complete'
                $startButton.BackColor = [System.Drawing.Color]::FromArgb(46,204,113)
                Add-Log "You can now close this window."
                
                $closeButton.Focus()
            }
        })
        
        $timer.Start()
    }
})

$closeButton.Add_Click({
    $form.Close()
})

# ============================================================================
# SHOW FORM
# ============================================================================

Add-Log "ZKAccessB Setup initialized. Click 'Start Installation' to begin."
Add-Log ""

[void]$form.ShowDialog()
