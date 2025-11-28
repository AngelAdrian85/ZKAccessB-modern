[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
[System.Reflection.Assembly]::LoadWithPartialName("System.Drawing") | Out-Null

$form = New-Object System.Windows.Forms.Form
$form.Text = "Instalare ZKAccessB - Professional Setup"
$form.Width = 1400
$form.Height = 900
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::White

# TOP SECTION
$topPanel = New-Object System.Windows.Forms.Panel
$topPanel.Dock = "Top"
$topPanel.Height = 100
$topPanel.BackColor = [System.Drawing.Color]::White
$topPanel.BorderStyle = "FixedSingle"
$form.Controls.Add($topPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Instalare automatata pentru ZKAccessB-modern"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$titleLabel.Location = [System.Drawing.Point]::new(10, 5)
$titleLabel.Size = New-Object System.Drawing.Size(1350, 25)
$titleLabel.ForeColor = [System.Drawing.Color]::Black
$topPanel.Controls.Add($titleLabel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = [System.Drawing.Point]::new(10, 35)
$progressBar.Size = New-Object System.Drawing.Size(1350, 25)
$progressBar.Style = "Continuous"
$progressBar.ForeColor = [System.Drawing.Color]::Green
$topPanel.Controls.Add($progressBar)

$percentLabel = New-Object System.Windows.Forms.Label
$percentLabel.Text = "Progres: 0%"
$percentLabel.Location = [System.Drawing.Point]::new(10, 65)
$percentLabel.Size = New-Object System.Drawing.Size(1350, 20)
$percentLabel.ForeColor = [System.Drawing.Color]::Black
$topPanel.Controls.Add($percentLabel)

# BOTTOM SECTION - BUTTONS
$bottomPanel = New-Object System.Windows.Forms.Panel
$bottomPanel.Dock = "Bottom"
$bottomPanel.Height = 60
$bottomPanel.BackColor = [System.Drawing.Color]::WhiteSmoke
$bottomPanel.BorderStyle = "FixedSingle"
$form.Controls.Add($bottomPanel)

$btnStart = New-Object System.Windows.Forms.Button
$btnStart.Text = "Instaleaza"
$btnStart.Location = [System.Drawing.Point]::new(1160, 12)
$btnStart.Size = New-Object System.Drawing.Size(100, 34)
$btnStart.BackColor = [System.Drawing.Color]::FromArgb(52, 152, 219)
$btnStart.ForeColor = [System.Drawing.Color]::White
$btnStart.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$bottomPanel.Controls.Add($btnStart)

$btnExit = New-Object System.Windows.Forms.Button
$btnExit.Text = "Iesire"
$btnExit.Location = [System.Drawing.Point]::new(1270, 12)
$btnExit.Size = New-Object System.Drawing.Size(100, 34)
$btnExit.BackColor = [System.Drawing.Color]::FromArgb(192, 57, 43)
$btnExit.ForeColor = [System.Drawing.Color]::White
$btnExit.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$bottomPanel.Controls.Add($btnExit)

# LEFT PANEL - STEPS (600px wide)
$stepsTextBox = New-Object System.Windows.Forms.TextBox
$stepsTextBox.Location = [System.Drawing.Point]::new(0, 100)
$stepsTextBox.Size = New-Object System.Drawing.Size(600, 740)
$stepsTextBox.BackColor = [System.Drawing.Color]::White
$stepsTextBox.ForeColor = [System.Drawing.Color]::Black
$stepsTextBox.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$stepsTextBox.Multiline = $true
$stepsTextBox.ScrollBars = "Vertical"
$stepsTextBox.ReadOnly = $true
$stepsTextBox.Text = ""
$form.Controls.Add($stepsTextBox)

# RIGHT PANEL - LOG (795px wide)
$logTextBox = New-Object System.Windows.Forms.TextBox
$logTextBox.Location = [System.Drawing.Point]::new(605, 100)
$logTextBox.Size = New-Object System.Drawing.Size(795, 740)
$logTextBox.BackColor = [System.Drawing.Color]::White
$logTextBox.ForeColor = [System.Drawing.Color]::Black
$logTextBox.Font = New-Object System.Drawing.Font("Consolas", 8)
$logTextBox.Multiline = $true
$logTextBox.ScrollBars = "Both"
$logTextBox.ReadOnly = $true
$form.Controls.Add($logTextBox)

# Initialize steps text
$stepsText = @"
Step 1: Creating Virtual Environment
[pending]

Step 2: Upgrading Pip
[pending]

Step 3: Installing Requirements
[pending]

Step 4: Verifying Django
[pending]

Step 5: Verifying Site Modules
[pending]

Step 6: Configuring Database
[pending]

Step 7: Collecting Static Files
[pending]

Step 8: Server Configuration
[pending]

Step 9: Launching Tray Agent
[pending]
"@

$stepsTextBox.Text = $stepsText

# Button handlers
$btnExit.Add_Click({
    $form.Close()
    [System.Windows.Forms.Application]::Exit()
})

$btnStart.Add_Click({
    $btnStart.Enabled = $false
    
    # Simulate installation
    for ($i = 1; $i -le 9; $i++) {
        $pct = [Math]::Min(($i / 9) * 100, 100)
        $progressBar.Value = $pct
        $percentLabel.Text = "Progres: $([Math]::Round($pct))%"
        
        $ts = Get-Date -Format "HH:mm:ss"
        $logTextBox.AppendText("[$ts] Step $i``:  Executing...`r`n")
        
        # Update steps display
        $newStepsText = $stepsText -replace "Step $i``: \w+`r`n\[pending\]", "Step $i``: Completed`r`n[OK]"
        $stepsTextBox.Text = $newStepsText
        
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 500
    }
    
    $progressBar.Value = 100
    $percentLabel.Text = "Progres: 100%"
    $ts = Get-Date -Format "HH:mm:ss"
    $logTextBox.AppendText("[$ts] SETUP COMPLETE!`r`n")
    $btnStart.Text = "Completed!"
    $btnStart.BackColor = [System.Drawing.Color]::FromArgb(46, 204, 113)
})

# Show form
$form.Show()

# Keep application alive
while ($form.Visible) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 100
}

$form.Dispose()
