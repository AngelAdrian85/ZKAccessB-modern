# ZKAccessB Modern UI - Automated Setup with Real-time Progress
# No blocking, live updates, full dependency checking

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============================================================================
# UI BITMAPS
# ============================================================================

function New-StatusBitmap($ok) {
    $bmp = New-Object System.Drawing.Bitmap 22,22
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rect = New-Object System.Drawing.Rectangle 0,0,17,17
    if ($ok) { $fill = [System.Drawing.Color]::FromArgb(46,204,113) } else { $fill = [System.Drawing.Color]::FromArgb(231,76,60) }
    $brush = New-Object System.Drawing.SolidBrush $fill
    $g.FillEllipse($brush,$rect)
    try {
        $font = New-Object System.Drawing.Font('Segoe UI Symbol',12,[System.Drawing.FontStyle]::Bold)
        $sf = New-Object System.Drawing.StringFormat
        $sf.Alignment = [System.Drawing.StringAlignment]::Center
        $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
        $char = if ($ok) { [char]0x2713 } else { [char]0x2717 }
        $g.DrawString($char, $font, [System.Drawing.Brushes]::White, [System.Drawing.RectangleF]::new(0,0,22,22), $sf)
    } catch {
        try {
            if ($ok) { $pen = New-Object System.Drawing.Pen([System.Drawing.Brushes]::White,2); $g.DrawLine($pen,4,11,9,16); $g.DrawLine($pen,9,16,18,6) } else { $pen = New-Object System.Drawing.Pen([System.Drawing.Brushes]::White,2); $g.DrawLine($pen,5,5,17,17); $g.DrawLine($pen,17,5,5,17) }
        } catch {}
    }
    $g.Dispose()
    return $bmp
}

function New-ProcessingBitmap() {
    $bmp = New-Object System.Drawing.Bitmap 22,22
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $fill = [System.Drawing.Color]::FromArgb(52,152,219)
    $brush = New-Object System.Drawing.SolidBrush $fill
    $g.FillEllipse($brush, 2,2,18,18)
    $pen = New-Object System.Drawing.Pen([System.Drawing.Brushes]::White,2)
    $g.DrawArc($pen, 4,4,14,14, -90, 120)
    $g.Dispose()
    return $bmp
}

# Minimal modern setup UI inspired by provided screenshot
# Features: centered header, progress bar, left steps with icons, right log, bottom colored action buttons
# Steps: check python, venv activation, requirements, django, asgi, site modules, db, start agent

function Write-LogSimple($path, $text) {
    try { [System.IO.File]::AppendAllText($path, $text + [Environment]::NewLine, [System.Text.Encoding]::UTF8) } catch {}
}

$RunLog = Join-Path (Get-Location) 'setup_modern_run.log'
$ErrLog = Join-Path (Get-Location) 'setup_modern_error.log'

function Run-CommandCapture($exe, $args, [int]$timeout=600) {
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exe
        if ($args) { $psi.Arguments = $args }
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $psi
        $started = $proc.Start()
        if (-not $started) { return @{ ExitCode=-1; StdOut=''; StdErr='Start failed' } }
        $out = $proc.StandardOutput.ReadToEnd()
        $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit($timeout*1000) | Out-Null
    if ($proc.HasExited) { $code = $proc.ExitCode } else { $code = -1 }
    try { Write-LogSimple $RunLog ("[Run-Command] $exe $args => exit $code") } catch {}
        return @{ ExitCode=$code; StdOut=$out; StdErr=$err }
    } catch {
        Write-LogSimple $ErrLog ("Run-Command exception: $($_.Exception.Message)")
        return @{ ExitCode=-1; StdOut=''; StdErr=$_.Exception.Message }
    }
}

# Stream process output line-by-line to Append-UiLog (and return exit code)
function Start-ProcessWithStreaming($exe, $argArray, $logbox = $null, [int]$timeoutSeconds = 600) {
    try {
        # Resolve binary
        if (-not [string]::IsNullOrEmpty($exe) -and -not (Test-Path $exe)) {
            $c = Get-Command $exe -ErrorAction SilentlyContinue
            if ($c) { $exe = $c.Source }
        }
    } catch {}
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $args = @()
    if ($null -ne $argArray) { $args = @($argArray) }
    $escaped = @()
    foreach ($a in $args) { if ($a -match '\s') { $escaped += ('"{0}"' -f ($a -replace '"','\\"')) } else { $escaped += $a } }
    if ($escaped.Count -gt 0) { $psi.Arguments = [String]::Join(' ', $escaped) } else { $psi.Arguments = '' }
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.EnableRaisingEvents = $true

    $outSb = New-Object System.Text.StringBuilder
    $stdoutHandler = [System.Diagnostics.DataReceivedEventHandler]{ param($s,$e) if ($e.Data) { Append-UiLog $e.Data } }
    $stderrHandler = [System.Diagnostics.DataReceivedEventHandler]{ param($s,$e) if ($e.Data) { Append-UiLog $e.Data } }
    $proc.add_OutputDataReceived($stdoutHandler)
    $proc.add_ErrorDataReceived($stderrHandler)

    try {
        if (-not (Test-Path $exe) -and -not (Get-Command $exe -ErrorAction SilentlyContinue)) { Append-UiLog ("Executable not found: $exe"); return -1 }
        $started = $proc.Start()
        if (-not $started) { Append-UiLog ("Failed to start: $exe"); return -1 }
    } catch { Append-UiLog ("Exception starting process: $($_.Exception.Message)"); return -1 }

    try { $proc.BeginOutputReadLine(); $proc.BeginErrorReadLine() } catch {}

    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    while (-not $proc.HasExited) {
        Start-Sleep -Milliseconds 150
        try { [System.Windows.Forms.Application]::DoEvents() } catch {}
        if ((Get-Date) -gt $deadline) { try { $proc.Kill() } catch {}; Append-UiLog ("Process timeout: $exe $($psi.Arguments)"); return -1 }
    }
    try { return $proc.ExitCode } catch { return -1 }
}

# Append a line both to UI log (if available) and to persistent run log
function Append-UiLog($text) {
    try {
        $ts = (Get-Date).ToString('HH:mm:ss')
        $line = "[$ts] $text"
        Write-LogSimple $RunLog $line
        if ($global:ui -and $global:ui.Log) {
            try {
                $form = $global:ui.Form
                if ($form -and $form.InvokeRequired) {
                    $form.BeginInvoke({ param($u,$l) try { $u.Log.AppendText($l + [Environment]::NewLine); $u.Log.SelectionStart = $u.Log.Text.Length; $u.Log.ScrollToCaret() } catch {} }, @($global:ui,$line)) | Out-Null
                } else {
                    try { $global:ui.Log.AppendText($line + [Environment]::NewLine); $global:ui.Log.SelectionStart = $global:ui.Log.Text.Length; $global:ui.Log.ScrollToCaret() } catch {}
                }
            } catch {
                # fallback to Ui-Invoke if direct begin-invoke fails
                try { Ui-Invoke $global:ui { param($u,$l) try { $u.Log.AppendText($l + [Environment]::NewLine); $u.Log.SelectionStart = $u.Log.Text.Length; $u.Log.ScrollToCaret() } catch {} } -args @($global:ui,$line) } catch {}
            }
        }
    } catch {}
}

# Ensure STA
try { $apt = [System.Threading.Thread]::CurrentThread.ApartmentState } catch { $apt = $null }
if ($apt -ne 'STA') {
    $me = $MyInvocation.MyCommand.Path
    if (-not $me) { $me = Join-Path (Get-Location) 'setup_modern_ui.ps1' }
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',$me) -WindowStyle Normal
    exit
}

function New-ModernForm {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'Instalare ZKAccessB - Modern UI'
    $form.Size = [System.Drawing.Size]::new(980,680)
    $form.StartPosition = 'CenterScreen'

    # Top: progress bar area
    $topPanel = New-Object System.Windows.Forms.Panel
    $topPanel.Dock = 'Top'; $topPanel.Height = 70
    $form.Controls.Add($topPanel)

    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Text = 'Instalare automata pentru ZKAccessB-modern'
    $lblTitle.Font = New-Object System.Drawing.Font('Segoe UI',12,[System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(30,120,200)
    $lblTitle.AutoSize = $false; $lblTitle.TextAlign = 'MiddleCenter'
    $lblTitle.Dock = 'Top'; $lblTitle.Height = 40
    $topPanel.Controls.Add($lblTitle)

    $progress = New-Object System.Windows.Forms.ProgressBar
    $progress.Style = 'Continuous'; $progress.Dock = 'Top'; $progress.Height = 18; $progress.Value = 0
    $topPanel.Controls.Add($progress)

    $lblPercent = New-Object System.Windows.Forms.Label
    $lblPercent.Text = 'Progres: 0%'; $lblPercent.Dock='Top'; $lblPercent.Height=18; $lblPercent.TextAlign='MiddleCenter'
    $topPanel.Controls.Add($lblPercent)

    # Main split
    $split = New-Object System.Windows.Forms.SplitContainer
    $split.Dock = 'Fill'; $split.SplitterDistance = 260
    $form.Controls.Add($split)

    # Left: steps area (with icons)
    # Create a selector panel that sits above the bottom action buttons so all selectors are visible there
    $chkPanel = New-Object System.Windows.Forms.Panel; $chkPanel.Dock='Bottom'; $chkPanel.Height = 140; $chkPanel.AutoScroll = $true; $chkPanel.Padding = [System.Windows.Forms.Padding]::new(8)
    # Add selector panel to the form (so it appears above the bottom action bar)
    $form.Controls.Add($chkPanel)

    # Main container for step rows
    $chkContainer = New-Object System.Windows.Forms.Panel; $chkContainer.Dock='Fill'; $chkContainer.AutoScroll = $true
    $split.Panel1.Controls.Add($chkContainer)

    # We'll build checkbox rows dynamically later and keep hashtables for access
    $global:StepCheckboxes = @{}
    $global:StepPics = @{}
    $global:StepLabels = @{}
    $global:StepStatusLabels = @{}

    # Right: log
    $log = New-Object System.Windows.Forms.TextBox
    $log.Multiline = $true; $log.ReadOnly = $true; $log.ScrollBars = 'Both'; $log.Font = New-Object System.Drawing.Font('Consolas',9)
    $log.Dock = 'Fill'
    $split.Panel2.Controls.Add($log)

    # Bottom action bar
    $bottom = New-Object System.Windows.Forms.Panel; $bottom.Dock='Bottom'; $bottom.Height = 100
    $form.Controls.Add($bottom)

    # Buttons with colors
    $btnReadme = New-Object System.Windows.Forms.Button; $btnReadme.Text='Afiseaza README'; $btnReadme.BackColor = [System.Drawing.Color]::FromArgb(46,204,113); $btnReadme.ForeColor=[System.Drawing.Color]::White
    $btnReadme.Size = [System.Drawing.Size]::new(140,34); $btnReadme.Location = [System.Drawing.Point]::new(12,14)
    $bottom.Controls.Add($btnReadme)

    $btnShortcut = New-Object System.Windows.Forms.Button; $btnShortcut.Text='Creeaza scurtatura'; $btnShortcut.BackColor=[System.Drawing.Color]::FromArgb(241,196,15); $btnShortcut.ForeColor=[System.Drawing.Color]::Black
    $btnShortcut.Size=[System.Drawing.Size]::new(150,34); $btnShortcut.Location=[System.Drawing.Point]::new(164,14); $bottom.Controls.Add($btnShortcut)

    $btnViewLog = New-Object System.Windows.Forms.Button; $btnViewLog.Text='Vezi Log'; $btnViewLog.BackColor=[System.Drawing.Color]::LightGray; $btnViewLog.Size=[System.Drawing.Size]::new(100,34); $btnViewLog.Location=[System.Drawing.Point]::new(326,14); $bottom.Controls.Add($btnViewLog)

    $btnClearLog = New-Object System.Windows.Forms.Button; $btnClearLog.Text='Curata Log'; $btnClearLog.BackColor=[System.Drawing.Color]::FromArgb(231,76,60); $btnClearLog.ForeColor=[System.Drawing.Color]::White; $btnClearLog.Size=[System.Drawing.Size]::new(110,34); $btnClearLog.Location=[System.Drawing.Point]::new(436,14); $bottom.Controls.Add($btnClearLog)

    $btnExit = New-Object System.Windows.Forms.Button; $btnExit.Text='Iesire'; $btnExit.Size=[System.Drawing.Size]::new(100,34); $btnExit.BackColor=[System.Drawing.Color]::FromArgb(192,57,43); $btnExit.ForeColor=[System.Drawing.Color]::White; $btnExit.Location=[System.Drawing.Point]::new($form.ClientSize.Width-340,14); $btnExit.Anchor = 'Right,Bottom'
    $bottom.Controls.Add($btnExit)

    $btnStart = New-Object System.Windows.Forms.Button; $btnStart.Text='Instaleaza'; $btnStart.Size=[System.Drawing.Size]::new(140,36); $btnStart.BackColor=[System.Drawing.Color]::FromArgb(52,152,219); $btnStart.ForeColor=[System.Drawing.Color]::White; $btnStart.Location=[System.Drawing.Point]::new($form.ClientSize.Width-180,12); $btnStart.Anchor='Right,Bottom'
    $bottom.Controls.Add($btnStart)
    # Test-mode checkbox for UI testing (forces steps green)
    $chkTest = New-Object System.Windows.Forms.CheckBox
    $chkTest.Text = 'Mod test vizual (forțează verde)'
    $chkTest.AutoSize = $true
    $chkTest.Checked = $false
    $chkTest.Font = New-Object System.Drawing.Font('Segoe UI',9,[System.Drawing.FontStyle]::Regular)
    # Place checkbox under the bottom buttons (below Start) so it's clearly separated
    try {
        $chkTest.Location = [System.Drawing.Point]::new($btnStart.Location.X, $btnStart.Location.Y + $btnStart.Height + 8)
        $chkTest.Anchor = 'Left,Bottom'
    } catch {
        # fallback: position at fixed offset
        $chkTest.Location = [System.Drawing.Point]::new($form.ClientSize.Width - 340, 58)
        $chkTest.Anchor = 'Right,Bottom'
    }
    $bottom.Controls.Add($chkTest)

    # Return UI object (include check container so callers can add controls)
    return @{ Form=$form; Progress=$progress; PercentLabel=$lblPercent; CheckPanel=$chkPanel; CheckContainer=$chkContainer; Log=$log; StartButton=$btnStart; ExitButton=$btnExit; ReadmeButton=$btnReadme; ShortcutButton=$btnShortcut; ViewLogButton=$btnViewLog; ClearLogButton=$btnClearLog; CheckTest=$chkTest }
}

# Helper: safely invoke on UI thread
function Ui-Invoke($ui, [scriptblock]$action, [Alias('args')] $arglist = $null) {
    try {
        $form = $null
        try { $form = $ui.Form } catch {}
        # If caller didn't supply an arglist, default to passing the UI object
        if ($arglist -eq $null) { $arglist = @($ui) }
            # optional diagnostic toggle
            try { if ($env:DEBUG_UIINVOKE -and $env:DEBUG_UIINVOKE -ne '') { Write-LogSimple $RunLog ("[Ui-Invoke] argcount={0}" -f ($arglist.Count)) } } catch {}
        if ($form -and $form.InvokeRequired) {
            try {
                $form.BeginInvoke($action, $arglist) | Out-Null
            } catch {
                # fallback: try invoking synchronously
                try { & $action @($arglist) } catch {}
            }
        } else {
            try { & $action @($arglist) } catch {}
        }
    } catch {}
}

# Build UI
$ui = New-ModernForm
$form = $ui.Form; $global:ui = $ui

# If an env var requests visual-test autostart, enable the checkbox so Precheck will run the visual test
try { if ($env:AUTOSTART_VISUAL_TEST -and $env:AUTOSTART_VISUAL_TEST -ne '') { if ($global:ui -and $global:ui.CheckTest) { $global:ui.CheckTest.Checked = $true } } } catch {}

# Define steps and mapping to functions
$steps = @(
    @{ Key='Check Python'; Fn='Check-Python' },
    @{ Key='Check/Create Venv'; Fn='Check-Venv' },
    @{ Key='Activate Venv'; Fn='Activate-Venv' },
    @{ Key='Install Requirements'; Fn='Install-Requirements' },
    @{ Key='Check Django'; Fn='Check-Django' },
    @{ Key='Check ASGI (uvicorn)'; Fn='Check-ASGI' },
    @{ Key='Check site modules (manage.py)'; Fn='Check-Manage' },
    @{ Key='Check DB (migrate/check)'; Fn='Check-DB' },
    @{ Key='Start Agent Tray'; Fn='Start-Agent' }
)

# Create rows: picture + label in the main steps area, and selectors (checkboxes)
# reparented into the bottom checkbox panel so selectors remain visible.
$i = 0
foreach ($s in $steps) {
    # PictureBox + Label in the left steps area
    # Small glyph label replacing PictureBox to avoid GDI+/bitmap repaint issues
    $glyphLbl = New-Object System.Windows.Forms.Label
    $glyphLbl.Size = [System.Drawing.Size]::new(26,26)
    $glyphLbl.Location = [System.Drawing.Point]::new(8, 4 + ($i * 32))
    $glyphLbl.TextAlign = 'MiddleCenter'
    try { $glyphLbl.Font = New-Object System.Drawing.Font('Segoe UI Symbol',12,[System.Drawing.FontStyle]::Bold); $glyphLbl.Text = [char]0x2717; $glyphLbl.ForeColor = [System.Drawing.Color]::FromArgb(231,76,60) } catch {}
    try { $ui.CheckContainer.Controls.Add($glyphLbl) } catch {}

    # Use the checkbox's built-in text instead of a separate label to avoid misalignment
    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text = $s.Key
    $lbl.AutoSize = $false
    $lbl.Size = [System.Drawing.Size]::new(360,24)
    $lbl.Location = [System.Drawing.Point]::new(34, 4 + ($i * 32))
    $lbl.TextAlign = 'MiddleLeft'
    try { $lbl.Font = New-Object System.Drawing.Font('Segoe UI',10,[System.Drawing.FontStyle]::Regular) } catch {}

    # Selector checkbox (moved to selector panel above bottom action buttons)
    # Selector checkbox (inline, no visible text)
    $cb = New-Object System.Windows.Forms.CheckBox
    $cb.Checked = $true
    $cb.AutoSize = $true
    # put the step text on the checkbox so the label near the glyph is not needed
    $cb.Text = $s.Key
    try { $cb.FlatStyle = 'Flat' } catch {}
    # align checkbox near the glyph/label
    $cb.Location = [System.Drawing.Point]::new(34, 6 + ($i * 32))
    try { $ui.CheckContainer.Controls.Add($cb) } catch { try { $ui.CheckContainer.Controls.Add($cb) } catch {} }

    # Status label to the right of checkbox (shows text like OK / Error / Running)
    $statLbl = New-Object System.Windows.Forms.Label
    $statLbl.Text = ''
    $statLbl.AutoSize = $false
    $statLbl.Size = [System.Drawing.Size]::new(180,18)
    $statLbl.Location = [System.Drawing.Point]::new(420, 6 + ($i * 32))
    $statLbl.TextAlign = 'MiddleLeft'
    try { $statLbl.Font = New-Object System.Drawing.Font('Segoe UI',9,[System.Drawing.FontStyle]::Regular); $ui.CheckContainer.Controls.Add($statLbl) } catch {}

    $global:StepCheckboxes[$s.Key] = $cb
    $global:StepPics[$s.Key] = $glyphLbl
    $global:StepLabels[$s.Key] = $lbl
    $global:StepStatusLabels[$s.Key] = $statLbl
    $i += 1
}

# Utility to set list status and color
function Set-StepStatus($name, $status, [bool]$ok) {
    try {
        # Debug: log every call so we can trace why icons may not change
        try { Write-LogSimple $RunLog ("[DBG] Set-StepStatus called: $name => $status (ok=$ok)") } catch {}
        # Update checkbox state and color in the left panel
        if (Test-Path variable:global:StepCheckboxes) {
            try {
                $cb = $global:StepCheckboxes[$name]
                $pic = $null; $lbl = $null
                try { $pic = $global:StepPics[$name] } catch {}
                try { $lbl = $global:StepLabels[$name] } catch {}
                $slabel = $null
                try { $slabel = $global:StepStatusLabels[$name] } catch {}
                if ($cb -ne $null) {
                    $action = { param($c,$p,$l,$sName,$s,$ok,$sl)
                        try {
                            # Do NOT change the user's checkbox selection here (precheck should not toggle selectors).
                            # Update visual cue (checkbox background) and the picture/label state instead.
                            try { $c.BackColor = (if ($ok) {[System.Drawing.Color]::FromArgb(46,204,113)} else {[System.Drawing.Color]::FromArgb(231,76,60)}) } catch {}
                        } catch {}
                        try {
                            if ($p -ne $null) {
                                try {
                                    # p is a glyph Label now: set its text and color directly
                                    $glyph = (if ($ok) {[char]0x2713} else {[char]0x2717})
                                    try { $p.Text = $glyph } catch {}
                                    try { $p.ForeColor = (if ($ok) {[System.Drawing.Color]::FromArgb(46,204,113)} else {[System.Drawing.Color]::FromArgb(231,76,60)}) } catch {}
                                    try { $p.Font = New-Object System.Drawing.Font('Segoe UI Symbol',12,[System.Drawing.FontStyle]::Bold) } catch {}
                                } catch {}
                            }
                        } catch {}
                        try {
                            if ($l -ne $null) {
                                $l.ForeColor = (if ($ok) {[System.Drawing.Color]::FromArgb(0,90,0)} else {[System.Drawing.Color]::FromArgb(140,30,30)})
                                try { $l.Text = $sName } catch {}
                            } else {
                                # no separate label: color the checkbox text so user sees the state
                                try { if ($c -ne $null) { $c.ForeColor = (if ($ok) {[System.Drawing.Color]::FromArgb(0,90,0)} else {[System.Drawing.Color]::FromArgb(140,30,30)}); $c.Text = $sName } } catch {}
                            }
                        } catch {}
                        try { if ($sl -ne $null) { $sl.Text = $s; $sl.ForeColor = (if ($ok) {[System.Drawing.Color]::FromArgb(0,120,0)} else {[System.Drawing.Color]::FromArgb(140,30,30)}); $sl.Font = New-Object System.Drawing.Font('Segoe UI',9, (if ($ok) {[System.Drawing.FontStyle]::Bold} else {[System.Drawing.FontStyle]::Regular})) } } catch {}
                    }
                    Ui-Invoke $ui $action @($cb,$pic,$lbl,$name,$status,$ok,$slabel)
                    # Extra debug + force refresh + update image to avoid GDI+ caching issues
                    try {
                        Write-LogSimple $RunLog ("[DBG] After Ui-Invoke refresh for: $name (ok=$ok)")
                        Ui-Invoke $ui { param($u,$p,$l,$s) try { if ($p -ne $null) { $p.Invalidate(); $p.Update(); $p.Refresh() }; if ($l -ne $null) { $l.Invalidate(); $l.Update(); $l.Refresh() }; $u.Form.Invalidate(); $u.Form.Update(); $u.Form.Refresh(); [System.Windows.Forms.Application]::DoEvents() } catch {} } -args @($ui,$pic,$lbl,$slabel)
                    } catch {}
                }
            } catch {}
        }
    } catch {}
}

# Visual test helper: force all steps to green and animate progress (UI-only, non-destructive)
function Run-VisualTest {
    try {
        Append-UiLog 'Visual test: forcing all steps to OK (test mode)'
        $stepCount = $steps.Count
        if ($stepCount -le 0) { return }
        $completed = 0
        foreach ($s in $steps) {
            # mark step OK visually
            Set-StepStatus $s.Key 'OK (test)' $true
            Append-UiLog ("Visual test: $($s.Key) => OK")
            # advance progress based on completed steps
            $completed += 1
            $percent = [int][Math]::Round((($completed / $stepCount) * 100))
            try { Ui-Invoke $ui { param($u,$v) $u.Progress.Value = $v; if ($u.PercentLabel) { $u.PercentLabel.Text = "Progres: $v%" }; [System.Windows.Forms.Application]::DoEvents() } -args @($ui,$percent) } catch {}
            Start-Sleep -Milliseconds 180
        }
        # ensure final 100%
        try { Ui-Invoke $ui { param($u) $u.Progress.Value = 100; if ($u.PercentLabel) { $u.PercentLabel.Text = 'Progres: 100%' } } -args @($ui) } catch {}
        Append-UiLog 'Visual test: completed'
        $global:PrecheckDone = $true
    } catch { Append-UiLog ("Visual test error: $($_.Exception.Message)") }
}

# Step implementations
function Check-Python { param($dry)
    $name='Check Python'
    Set-StepStatus $name 'Running' $false
    try {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if (-not $cmd) { Set-StepStatus $name 'Missing' $false; Write-LogSimple $RunLog "Python not found"; return $false }
        if ($dry) { Set-StepStatus $name 'Found (dry-run)' $true; Write-LogSimple $RunLog "Python found: $($cmd.Source) (dry-run)"; return $true }
        $res = Run-CommandCapture $cmd.Source '-c "import sys;print(sys.executable)"'
        if ($res.ExitCode -eq 0) { Set-StepStatus $name 'OK' $true; Write-LogSimple $RunLog "Python: $($res.StdOut.Trim())"; return $true } else { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog "Python check failed: $($res.StdErr)"; return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Check-Venv { param($dry)
    $name='Check/Create Venv'
    Set-StepStatus $name 'Running' $false
    try {
        $root = Get-Location
        $venvPath = Join-Path $root '.venv_clean'
        $venvPython = Join-Path $venvPath 'Scripts\python.exe'
        if (Test-Path $venvPython) { Set-StepStatus $name 'Exists' $true; return $true }
        if ($dry) { Set-StepStatus $name 'Would create (dry-run)' $true; return $true }
    # create venv (stream output to UI)
    $py = (Get-Command python).Source
    $createExit = Start-ProcessWithStreaming $py @('-m','venv','.venv_clean','--clear') $global:ui.Log
    if ($createExit -eq 0 -and (Test-Path $venvPython)) { Set-StepStatus $name 'Created' $true; return $true } else { Set-StepStatus $name 'Failed' $false; Write-LogSimple $ErrLog "Venv create failed (exit $createExit)"; return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Activate-Venv { param($dry)
    $name='Activate Venv'
    Set-StepStatus $name 'Running' $false
    try {
        $root = Get-Location
        $venvPython = Join-Path (Join-Path $root '.venv_clean') 'Scripts\python.exe'
        if (Test-Path $venvPython) { $global:ActivePython = $venvPython; Set-StepStatus $name 'Activated' $true; return $true }
        # fallback to system python
        $py = (Get-Command python -ErrorAction SilentlyContinue)
        if ($py) { $global:ActivePython = $py.Source; Set-StepStatus $name 'Using system python' $true; return $true }
        Set-StepStatus $name 'Missing' $false; return $false
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Install-Requirements { param($dry)
    $name='Install Requirements'
    Set-StepStatus $name 'Running' $false
    try {
        $reqs = Join-Path (Get-Location) 'requirements.txt'
        if (-not (Test-Path $reqs)) { Set-StepStatus $name 'No requirements.txt' $false; return $false }
        if ($dry) { Set-StepStatus $name 'Would install (dry-run)' $true; return $true }
        $py = $global:ActivePython
        if (-not $py) { Set-StepStatus $name 'No python' $false; return $false }
    $exit = Start-ProcessWithStreaming $py @('-m','pip','install','-r',$reqs) $global:ui.Log
    if ($exit -eq 0) { Set-StepStatus $name 'Installed' $true; return $true } else { Set-StepStatus $name 'Failed' $false; Write-LogSimple $ErrLog ("pip install failed (exit {0})" -f $exit); return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Check-Django { param($dry)
    $name='Check Django'
    Set-StepStatus $name 'Running' $false
    try {
        $py = $global:ActivePython
        if (-not $py) { Set-StepStatus $name 'No python' $false; return $false }
        if ($dry) { Set-StepStatus $name 'Would check (dry-run)' $true; return $true }
    $res = Run-CommandCapture $py '-c "import django; print(django.get_version())"'
        if ($res.ExitCode -eq 0 -and $res.StdOut.Trim()) { Set-StepStatus $name ('Django ' + $res.StdOut.Trim()) $true; return $true } else { Set-StepStatus $name 'Missing' $false; return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Check-ASGI { param($dry)
    $name='Check ASGI (uvicorn)'
    Set-StepStatus $name 'Running' $false
    try {
        $py = $global:ActivePython
        if (-not $py) { Set-StepStatus $name 'No python' $false; return $false }
        if ($dry) { Set-StepStatus $name 'Would check (dry-run)' $true; return $true }
    $res = Run-CommandCapture $py '-c "import uvicorn; print(\'uvicorn\')"'
        if ($res.ExitCode -eq 0) { Set-StepStatus $name 'uvicorn OK' $true; return $true }
        # try daphne
    $res2 = Run-CommandCapture $py '-c "import daphne; print(\'daphne\')"'
        if ($res2.ExitCode -eq 0) { Set-StepStatus $name 'daphne OK' $true; return $true }
        Set-StepStatus $name 'Missing ASGI server' $false; return $false
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Check-Manage { param($dry)
    $name='Check site modules (manage.py)'
    Set-StepStatus $name 'Running' $false
    try {
        $root = Get-Location
        $mg = Join-Path $root 'manage.py'
        if (-not (Test-Path $mg)) { Set-StepStatus $name 'No manage.py' $false; return $false }
        if ($dry) { Set-StepStatus $name 'Would check (dry-run)' $true; return $true }
        $py = $global:ActivePython
        $res = Run-CommandCapture $py "manage.py check"
        if ($res.ExitCode -eq 0) { Set-StepStatus $name 'OK' $true; return $true } else { Set-StepStatus $name 'Check Failed' $false; Write-LogSimple $ErrLog $res.StdErr; return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Check-DB { param($dry)
    $name='Check DB (migrate/check)'
    Set-StepStatus $name 'Running' $false
    try {
        $root = Get-Location
        $mg = Join-Path $root 'manage.py'
        if (-not (Test-Path $mg)) { Set-StepStatus $name 'No manage.py' $false; return $false }
        $py = $global:ActivePython
        if ($dry) { Set-StepStatus $name 'Would migrate (dry-run)' $true; return $true }
    $exit = Start-ProcessWithStreaming $py @('manage.py','migrate','--no-input') $global:ui.Log
    if ($exit -eq 0) { Set-StepStatus $name 'DB OK' $true; return $true } else { Set-StepStatus $name 'DB Issue' $false; Write-LogSimple $ErrLog ("migrate failed (exit {0})" -f $exit); return $false }
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

function Start-Agent { param($dry)
    $name='Start Agent Tray'
    Set-StepStatus $name 'Running' $false
    try {
        $tray = Join-Path (Get-Location) 'tray_launch.ps1'
        if (-not (Test-Path $tray)) { Set-StepStatus $name 'No agent script' $false; return $false }
        if ($dry) { Set-StepStatus $name 'Would start (dry-run)' $true; return $true }
        Start-Process -FilePath 'powershell.exe' -ArgumentList ('-NoProfile','-ExecutionPolicy','Bypass','-File', (Resolve-Path $tray)) -WindowStyle Minimized
        Set-StepStatus $name 'Started' $true; return $true
    } catch { Set-StepStatus $name 'Error' $false; Write-LogSimple $ErrLog $_.Exception.Message; return $false }
}

# Runner
function Run-Workflow($dry) {
    Append-UiLog 'Starting workflow'
    # ensure ActivePython cleared
    $global:ActivePython = $null
    $allOk = $true
    # Determine which steps are selected to run (selectors may be unchecked to skip a step)
    $selected = @()
    foreach ($s in $steps) {
        $sel = $null
        try { $sel = $global:StepCheckboxes[$s.Key] } catch {}
        if ($sel -eq $null -or $sel.Checked) { $selected += $s }
    }
    if ($selected.Count -eq 0) { Append-UiLog 'No steps selected - nothing to do'; return $false }

    $stepCount = $selected.Count
    $stepIndex = 0
    $completed = 0
    $progressSoFar = 0
    foreach ($s in $selected) {
        $stepIndex += 1

        $fn = Get-Item Function:$($s.Fn) -ErrorAction SilentlyContinue
        $ok = $false
        if ($fn) {
            Append-UiLog ("Running step: $($s.Key) ({0}/{1})" -f $stepIndex, $stepCount)
            $ok = & $s.Fn $dry
        } else {
            Set-StepStatus $s.Key 'Missing function' $false
            Append-UiLog ("Missing function for $($s.Key)")
            $ok = $false
        }

            if ($ok) {
                # advance progress only when the step completed successfully
                $completed += 1
                $percent = [int][Math]::Round((($completed / $stepCount) * 100))
                $progressSoFar = [Math]::Min(100, $percent)
                try { Ui-Invoke $ui { param($u,$val) $u.Progress.Value = $val; if ($u.PercentLabel) { $u.PercentLabel.Text = "Progres: $val%" }; [System.Windows.Forms.Application]::DoEvents() } -args @($ui,$progressSoFar) } catch {}
                try { Write-LogSimple $RunLog ("[PROG] Progress updated to {0}%" -f $progressSoFar) } catch {}
        } else {
            $allOk = $false
        }

        # small UI pulse so changes appear progressively
        try { [System.Windows.Forms.Application]::DoEvents() } catch {}
    }
    if ($allOk) { Append-UiLog 'Workflow completed: SUCCESS' } else { Append-UiLog 'Workflow completed: ERRORS - see logs' }
    return $allOk
}

# Precheck (non-destructive) run when UI is shown to populate checkbox states
function Precheck() {
    Append-UiLog 'Starting pre-check (non-destructive)'
    $global:PrecheckDone = $false
    foreach ($s in $steps) {
        Append-UiLog ("Precheck: $($s.Key)")
        $fn = Get-Item Function:$($s.Fn) -ErrorAction SilentlyContinue
        $ok = $false
        if ($fn) { try { $ok = & $s.Fn $true } catch { $ok = $false; Append-UiLog ("Precheck error for $($s.Key): $($_.Exception.Message)") } } else { Set-StepStatus $s.Key 'Missing' $false; Append-UiLog ("Missing function: $($s.Key)") }
        Append-UiLog ("Precheck result: $($s.Key) => $ok")
        Start-Sleep -Milliseconds 120
    }
    Append-UiLog 'Pre-check finished'
    $global:PrecheckDone = $true
    # If visual test checkbox is checked, run the visual test to force green icons
    try { if ($global:ui -and $global:ui.CheckTest -and $global:ui.CheckTest.Checked) { Run-VisualTest } } catch {}
}

# When form is shown, run precheck in background to populate checkbox colors
try {
    # Run a quick precheck synchronously on Show (avoids background runspace issues)
    $ui.Form.Shown.Add({ param($s,$e)
        try {
            Append-UiLog 'Precheck: starting (synchronous)'
            Precheck
        } catch { Append-UiLog ("Precheck start failed: $($_.Exception.Message)") }
    })
} catch {}

# Wire buttons
$ui.ReadmeButton.Add_Click({ try { $p = Join-Path (Get-Location) 'README.md'; if (Test-Path $p) { Start-Process notepad.exe $p } else { [System.Windows.Forms.MessageBox]::Show('README.md not found') } } catch {} })
$ui.ClearLogButton.Add_Click({ try { '' | Out-File -FilePath $RunLog -Encoding utf8; $ui.Log.Clear() } catch {} })
$ui.ViewLogButton.Add_Click({ try { Start-Process notepad.exe $RunLog } catch {} })
$ui.ShortcutButton.Add_Click({ try { [System.Windows.Forms.MessageBox]::Show('Shortcut creation not yet implemented') } catch {} })
$ui.ExitButton.Add_Click({ try { $ui.Form.Close() } catch {} })

# Wire visual-test checkbox change: run visual test when enabled, else re-run precheck
try {
    if ($global:ui -and $global:ui.CheckTest) {
        $global:ui.CheckTest.Add_CheckedChanged({ param($s,$e) try { if ($global:ui.CheckTest.Checked) { Run-VisualTest } else { Append-UiLog 'Visual test disabled - re-running precheck'; Precheck } } catch {} })
    }
} catch {}

$ui.StartButton.Add_Click({
    try {
        Append-UiLog 'Start button clicked'
        # Diagnostic: log UI object presence to help track null-valued issues
        try { Append-UiLog ("StartHandlerDiag: ui=={0} global:ui=={1} startBtn=={2}" -f ([bool]($ui -ne $null)), ([bool]($global:ui -ne $null)), ([bool]($ui.StartButton -ne $null))) } catch {}
        if ($global:SetupRunning) { Append-UiLog 'Setup already running; ignoring start request'; return }
        $global:SetupRunning = $true
        # disable start button directly (we are on UI thread in click handler)
        try { $ui.StartButton.Enabled = $false } catch { Append-UiLog ("DisableStartBtn failed: " + $_.Exception.Message) }
        $dry = $false
        try { if ($env:AUTOSTART_DRYRUN -and $env:AUTOSTART_DRYRUN -ne '') { $dry = $true } } catch {}
    # If visual test mode is enabled, run the visual test instead of the normal workflow
    try { if ($global:ui -and $global:ui.CheckTest -and $global:ui.CheckTest.Checked) { Append-UiLog 'StartHandler: visual test mode enabled - running UI-only test'; Run-VisualTest; Ui-Invoke $ui { param($u) $u.StartButton.Enabled = $true; $u.Progress.Value = 100; if ($u.PercentLabel) { $u.PercentLabel.Text = 'Progres: 100%' } } -args @($ui); $global:SetupRunning = $false; return } } catch {}
    # Run workflow synchronously on UI thread but stream long-running subprocesses;
        # Reset and show progress bar beginning from Install button click
        Append-UiLog 'StartHandler: running workflow synchronously on UI thread'
        try {
            Ui-Invoke $ui { param($u) $u.Progress.Value = 0; if ($u.PercentLabel) { $u.PercentLabel.Text = 'Progres: 0%' } }
            try { Start-SetupWatchdog 60 $null } catch {}
            $res = $false
            try { $res = Run-Workflow $dry } catch { Append-UiLog ("Run-Workflow exception: $($_.Exception.Message)"); Write-LogSimple $ErrLog $_.Exception.Message }
            # Ensure progress shows completion
            if ($res) { Ui-Invoke $ui { param($u) $u.Progress.Value = 100; if ($u.PercentLabel) { $u.PercentLabel.Text = 'Progres: 100%' } } }
            else { Ui-Invoke $ui { param($u) $u.Progress.Value = [Math]::Min(100,$u.Progress.Value); if ($u.PercentLabel) { $u.PercentLabel.Text = ('Progres: ' + $u.Progress.Value + '%') } } }
        } finally {
            try { Stop-SetupWatchdog } catch {}
            $global:SetupRunning = $false
            try { $ui.StartButton.Enabled = $true } catch { Append-UiLog (("EnableStartBtn failed: " + $_.Exception.Message)) }
            Append-UiLog 'StartHandler: synchronous workflow finished'
        }
    } catch {
        $msg = try { $_.Exception.ToString() } catch { ($_ | Out-String) }
        Append-UiLog ("StartButton click handler exception: $msg")
        try { Write-LogSimple $ErrLog $msg } catch {}
        # ensure we clear running flag so user can retry
        try { $global:SetupRunning = $false } catch {}
    }
})

# Auto-click if requested (single handler) - wait for Precheck to finish using a WinForms timer
$global:AutoClicked = $false
try {
    if ($env:AUTOSTART_PERFORM_CLICK -and $env:AUTOSTART_PERFORM_CLICK -ne '') {
        $ui.Form.Shown.Add({
            param($s,$e)
            try {
                $timer = New-Object System.Windows.Forms.Timer
                $timer.Interval = 300
                $attempts = 0
                $timer.Add_Tick({
                    try {
                        $attempts += 1
                            if ($global:PrecheckDone -or $attempts -gt 100) {
                                try { '' | Out-File -FilePath $ErrLog -Encoding utf8 } catch {}
                                if (-not $global:AutoClicked) {
                                    $global:AutoClicked = $true
                                    Ui-Invoke $ui { param($u) if (-not $global:SetupRunning) { $u.StartButton.PerformClick() } }
                                }
                            $timer.Stop()
                            $timer.Dispose()
                        }
                    } catch {}
                })
                $timer.Start()
            } catch {}
        })
    }
} catch {}

# Show form
[void]$ui.Form.ShowDialog()
