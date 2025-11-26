function New-CheckProxy {
    param($Label, $Pic)
    # PSCustomObject with a ScriptProperty 'Checked' and ScriptMethod 'Refresh'
    $obj = [PSCustomObject]@{ Label = $Label; Pic = $Pic }
    $obj | Add-Member -MemberType NoteProperty -Name _checked -Value $false -Force
    $get = { return [bool]$this._checked }
    $set = { param($v); $this._checked = [bool]$v; try { if ($this.Label) { $this.Label.Tag = $this._checked } } catch {} }
    $obj | Add-Member -MemberType ScriptProperty -Name Checked -Value @{ get = $get; set = $set } -Force
    $refresh = { try { if ($this.Label -and ($this.Label.Tag -is [bool])) { $this._checked = [bool]$this.Label.Tag } } catch {} }
    $obj | Add-Member -MemberType ScriptMethod -Name Refresh -Value $refresh -Force
    return $obj
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Install application-level handlers to convert unhandled UI thread exceptions
# into logged errors and our in-app result dialog instead of the default .NET crash dialog.
try {
    [System.Windows.Forms.Application]::SetUnhandledExceptionMode([System.Windows.Forms.UnhandledExceptionMode]::CatchException)
    $uiThreadHandler = [System.Threading.ThreadExceptionEventHandler] { param($sender,$e)
        try {
            Write-ErrorLog($e.Exception)
            if (Test-Path variable:global:ui -and $global:ui) {
                try { Show-ResultDialog $global:ui 'Eroare neprevazuta' @{ Success=$false; Message = $e.Exception.ToString() } } catch {}
            } else {
                try { Show-InfoDialog $null 'Unhandled exception' $e.Exception.ToString() $false } catch { try { Write-Host $e.Exception.ToString() } catch {} }
            }
        } catch {}
    }
    [System.Windows.Forms.Application]::add_ThreadException($uiThreadHandler)
} catch {
    # best-effort only; if adding handlers fails, continue without them
}

try {
    $domainHandler = [System.UnhandledExceptionEventHandler] { param($sender,$e)
        try {
            $ex = $e.ExceptionObject
            Write-ErrorLog($ex)
            if (Test-Path variable:global:ui -and $global:ui) {
                try { Show-ResultDialog $global:ui 'Eroare neprevazuta' @{ Success=$false; Message = $ex.ToString() } } catch {}
            } else {
                try { Show-InfoDialog $null 'Eroare neprevazuta' $ex.ToString() $false } catch { try { Write-Host $ex.ToString() } catch {} }
            }
        } catch {}
    }
    [System.AppDomain]::CurrentDomain.add_UnhandledException($domainHandler)
} catch {}

# If a caller (tests) wants to dot-source this file without starting the UI,
# they can set $Script:AutoStartUI = $false before dot-sourcing.
if (-not (Test-Path variable:Script:AutoStartUI)) { $Script:AutoStartUI = $true }

# Ensure we're running in STA (required for Windows Forms). If not, relaunch this script in a new PowerShell process with -STA.
try {
    $apt = [System.Threading.Thread]::CurrentThread.ApartmentState
} catch {
    $apt = $null
}
if ($apt -ne 'STA') {
    Write-Host "PowerShell not running in STA mode; relaunching with -STA..."
    $me = $MyInvocation.MyCommand.Path
    if (-not $me) { $me = Join-Path (Get-Location) 'setup_with_ui.ps1' }
    $args = @('-NoProfile','-ExecutionPolicy','RemoteSigned','-STA','-File', $me)
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList $args -WindowStyle Normal
    exit
}

# CheckProxy is defined at the top of this file (PowerShell class definitions must appear before executable statements)

function New-SetupForm {
    # Minimal, robust UI implementation (keeps previous external contract)
    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'Instalare ZKAccessB'
    $form.Size = [System.Drawing.Size]::new(900,640)
    $form.StartPosition = 'CenterScreen'

    # Simple top label
    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Text = 'Instalare automata pentru ZKAccessB-modern'
    $lblTitle.Font = New-Object System.Drawing.Font('Segoe UI',14,[System.Drawing.FontStyle]::Bold)
    $lblTitle.Dock = 'Top'
    $lblTitle.Height = 50
    $lblTitle.TextAlign = 'MiddleLeft'
    $form.Controls.Add($lblTitle)

    # Progress and percent
    $progress = New-Object System.Windows.Forms.ProgressBar
    $progress.Style = 'Continuous'
    $progress.Minimum = 0; $progress.Maximum = 100; $progress.Value = 0
    $progress.Dock = 'Top'; $progress.Height = 18
    $form.Controls.Add($progress)

    $lblPercent = New-Object System.Windows.Forms.Label
    $lblPercent.Text = 'Progres: 0%'
    $lblPercent.Dock = 'Top'
    $lblPercent.Height = 24
    $form.Controls.Add($lblPercent)

    # Main split: steps left, log right
    $split = New-Object System.Windows.Forms.SplitContainer
    $split.Dock = 'Fill'
    $split.Orientation = 'Vertical'
    $split.SplitterDistance = 360

    # Steps list
    $stepsPanel = New-Object System.Windows.Forms.Panel
    $stepsPanel.Dock = 'Fill'; $stepsPanel.AutoScroll = $true
    $split.Panel1.Controls.Add($stepsPanel)

    $checks = @{}
    $selectors = @{}
    $tasks = @('Verifica Python','Verifica Django','Creeaza/Verifica .venv_clean','Instaleaza dependente','Seteaza DJANGO_SETTINGS_MODULE','Ruleaza migrari','Porneste server (optional)')
    $y = 8
    foreach ($t in $tasks) {
        $pic = New-Object System.Windows.Forms.PictureBox
        $pic.Size = [System.Drawing.Size]::new(22,22)
        $pic.Location = [System.Drawing.Point]::new(8,$y)
        try { $pic.Image = New-StatusBitmap($false) } catch {}
        $stepsPanel.Controls.Add($pic)

    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text = $t
    $lbl.Location = [System.Drawing.Point]::new(40,$y)
    $lbl.AutoSize = $false; $lbl.Size = [System.Drawing.Size]::new(300,24)
        $lbl.TextAlign = 'MiddleLeft'
        $stepsPanel.Controls.Add($lbl)
    # Place selector checkbox to the right of the label so it remains visible when the left panel is resized
    $sel = New-Object System.Windows.Forms.CheckBox
    $sel.Location = [System.Drawing.Point]::new($lbl.Location.X + $lbl.Size.Width + 8, $y)
        $sel.Checked = $false
        $stepsPanel.Controls.Add($sel)

    try { $proxy = New-CheckProxy -Label $lbl -Pic $pic } catch { $proxy = [PSCustomObject]@{ Label=$lbl; Pic=$pic; Checked=$false; Refresh={ } } }
        $checks[$t] = $proxy
        $selectors[$t] = $sel

        $y += 36
    }

    # Right: log
    $log = New-Object System.Windows.Forms.TextBox
    $log.Multiline = $true; $log.ReadOnly = $true; $log.ScrollBars = 'Both'
    $log.Font = New-Object System.Drawing.Font('Consolas',9)
    $log.Dock = 'Fill'
    $split.Panel2.Controls.Add($log)

    # Bottom controls
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock = 'Bottom'; $panel.Height = 56
    # Add the bottom panel before adding the split so the split fills the remaining area above the panel
    $form.Controls.Add($panel)
    $form.Controls.Add($split)

    $btnStart = New-Object System.Windows.Forms.Button
    $btnStart.Text = 'Instaleaza'; $btnStart.Size = [System.Drawing.Size]::new(140,36)
    $btnStart.Location = [System.Drawing.Point]::new($form.ClientSize.Width - 160,10)
    $btnStart.Anchor = ([System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Right)
    $panel.Controls.Add($btnStart)

    $btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Text = 'Iesire'; $btnExit.Size = [System.Drawing.Size]::new(90,36); $btnExit.Location = [System.Drawing.Point]::new($form.ClientSize.Width - 260,10)
    $btnExit.Anchor = ([System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Right)
    $panel.Controls.Add($btnExit)

    $btnReadme = New-Object System.Windows.Forms.Button; $btnReadme.Text='Afiseaza README'; $btnReadme.Size=[System.Drawing.Size]::new(120,28); $btnReadme.Location=[System.Drawing.Point]::new(8,12); $panel.Controls.Add($btnReadme)
    $btnShortcut = New-Object System.Windows.Forms.Button; $btnShortcut.Text='Creeaza scurtatura pe Desktop'; $btnShortcut.Size=[System.Drawing.Size]::new(180,28); $btnShortcut.Location=[System.Drawing.Point]::new(136,12); $panel.Controls.Add($btnShortcut)
    $btnViewLog = New-Object System.Windows.Forms.Button; $btnViewLog.Text='Vezi Log'; $btnViewLog.Size=[System.Drawing.Size]::new(90,28); $btnViewLog.Location=[System.Drawing.Point]::new(328,12); $panel.Controls.Add($btnViewLog)
    $btnClearLog = New-Object System.Windows.Forms.Button; $btnClearLog.Text='Curata Log'; $btnClearLog.Size=[System.Drawing.Size]::new(90,28); $btnClearLog.Location=[System.Drawing.Point]::new(424,12); $panel.Controls.Add($btnClearLog)

    $chkStartServer = New-Object System.Windows.Forms.CheckBox; $chkStartServer.Text='Porneste serverul dupa instalare'; $chkStartServer.Location=[System.Drawing.Point]::new(524,16); $panel.Controls.Add($chkStartServer)
    $chkDryRun = New-Object System.Windows.Forms.CheckBox; $chkDryRun.Text='Mod test (fara comenzi externe)'; $chkDryRun.Location=[System.Drawing.Point]::new(724,16); $panel.Controls.Add($chkDryRun)

    $lblDebug = New-Object System.Windows.Forms.Label; $lblDebug.Text=''; $lblDebug.Visible=$false

    # Return object matching previous contract
    return @{ Form=$form; Progress=$progress; PercentLabel=$lblPercent; StepsLabel=$lblTitle; DebugLabel=$lblDebug; Checks=$checks; Selectors=$selectors; Log=$log; StartButton=$btnStart; StartServerCheck=$chkStartServer; DryRunCheck=$chkDryRun; ReadmeButton=$btnReadme; ShortcutButton=$btnShortcut; ViewLogButton=$btnViewLog; ClearLogButton=$btnClearLog; ExitButton=$btnExit; Panel=$stepsPanel }
}

function Create-DesktopShortcut($targetFile, $shortcutName, $usePowerShell = $false) {
    try {
        $shell = New-Object -ComObject WScript.Shell
        $desktop = [Environment]::GetFolderPath('Desktop')
        $lnkPath = Join-Path $desktop "$shortcutName.lnk"
        $shortcut = $shell.CreateShortcut($lnkPath)
        $fullTarget = (Resolve-Path -LiteralPath $targetFile).Path
        if ($usePowerShell) {
            # Point to powershell.exe and run the PS1 directly
            $psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
            if (-not (Test-Path $psExe)) { $psExe = 'powershell' }
            $ps1 = if ($fullTarget -like '*.ps1') { $fullTarget } else { (Join-Path (Split-Path $fullTarget -Parent) 'setup_with_ui.ps1') }
            $shortcut.TargetPath = $psExe
            $shortcut.Arguments = "-NoProfile -ExecutionPolicy RemoteSigned -File `"$ps1`""
            $shortcut.WorkingDirectory = Split-Path $ps1 -Parent
        } else {
            # Use cmd.exe to launch the batch file reliably; set the batch path as an argument
            $cmd = Join-Path $env:SystemRoot 'System32\cmd.exe'
            $shortcut.TargetPath = $cmd
            $shortcut.Arguments = "/c `"$fullTarget`""
            $shortcut.WorkingDirectory = Split-Path $fullTarget -Parent
        }
        $shortcut.WindowStyle = 1
        $shortcut.Save()
        return @{ Success=$true; Path=$lnkPath }
    } catch {
        return @{ Success=$false; Error=$_.Exception.Message }
    }
}

function Show-ReadmeModal($root, $owner) {
    $path = Join-Path $root 'README.md'
    if (-not (Test-Path $path)) { Show-InfoDialog $null 'Info' 'README.md nu a fost gasit.' ; return }
    $text = Get-Content -Raw -Path $path
    $frm = New-Object System.Windows.Forms.Form
    $txt = New-Object System.Windows.Forms.TextBox
    $txt.Multiline = $true
    $txt.ReadOnly = $true
    $txt.ScrollBars = 'Both'
    $txt.WordWrap = $false
    $txt.Dock = 'Fill'
    $txt.Font = New-Object System.Drawing.Font('Consolas',10)
    $txt.Text = $text
    $frm.Controls.Add($txt)
    try {
        if ($null -ne $owner -and ($owner -is [System.Windows.Forms.Form])) {
            $frm.ShowDialog($owner) | Out-Null
        } else {
            $frm.ShowDialog() | Out-Null
        }
    } catch {
        # Fallback to non-owned dialog
        try { $frm.ShowDialog() | Out-Null } catch {}
    }
}

# Show a detailed modal dialog with full log and per-step status. Useful for errors and final summary.
function Show-ResultDialog($ui, $title, $result) {
    try {
        $frm = New-Object System.Windows.Forms.Form
        $frm.Text = $title
        $frm.Size = [System.Drawing.Size]::new(900,700)
        $frm.StartPosition = 'CenterParent'

        $tbl = New-Object System.Windows.Forms.TableLayoutPanel
        $tbl.Dock = 'Fill'
        $tbl.RowCount = 3
        $tbl.ColumnCount = 1
        $tbl.RowStyles.Add((New-Object System.Windows.Forms.RowStyle([System.Windows.Forms.SizeType]::AutoSize)))
        $tbl.RowStyles.Add((New-Object System.Windows.Forms.RowStyle([System.Windows.Forms.SizeType]::Percent, 100)))
        $tbl.RowStyles.Add((New-Object System.Windows.Forms.RowStyle([System.Windows.Forms.SizeType]::AutoSize)))
        $frm.Controls.Add($tbl)

        $lblSummary = New-Object System.Windows.Forms.Label
        $lblSummary.AutoSize = $false
        $lblSummary.Height = 28
        $lblSummary.Dock = 'Top'
        $lblSummary.TextAlign = 'MiddleLeft'
        $lblSummary.Font = New-Object System.Drawing.Font('Segoe UI',9,[System.Drawing.FontStyle]::Bold)
        $lblSummary.Text = "Result: $($result.Message)  |  Success: $([bool]$result.Success)"
        $tbl.Controls.Add($lblSummary,0,0)

        $txt = New-Object System.Windows.Forms.TextBox
        $txt.Multiline = $true
        $txt.ReadOnly = $true
        $txt.ScrollBars = 'Both'
        $txt.WordWrap = $false
        $txt.Font = New-Object System.Drawing.Font('Consolas',9)
        $txt.Dock = 'Fill'

        # Build detailed text: last persistent log and step-by-step status from UI
        $body = @()
        $body += "=== Summary ==="
        $body += "Message: $($result.Message)"
        $body += "Success: $([bool]$result.Success)"
        $body += ""
        $body += "=== Steps ==="
        try {
            if ($null -ne $ui -and $ui.PSObject.Properties.Match('Checks').Count -gt 0) {
                try {
                    foreach ($k in $ui.Checks.Keys) {
                        $proxy = $null
                        try { $proxy = $ui.Checks[$k] } catch {}
                        $checked = $false
                        try { if ($proxy -ne $null) { $checked = [bool]$proxy.Checked } } catch {}
                        $status = 'UNKNOWN'
                        try { $status = if ($checked) { 'OK' } else { 'NOT OK' } } catch { $status = 'UNKNOWN' }
                        $body += ("{0} : {1}" -f $k, $status)
                    }
                } catch {}
            } else {
                $body += '(no step status available)'
            }
        } catch { $body += '(error enumerating steps)' }
        $body += ""
        $body += "=== UI Log (latest) ==="
        try {
            if ($null -ne $ui -and $ui.PSObject.Properties.Match('Log').Count -gt 0 -and $ui.Log -ne $null) {
                try { $logText = $ui.Log.Text } catch { $logText = $null }
                if ($logText) { $body += $logText } else { $body += '(no ui log available)' }
            } else {
                $body += '(no ui log available)'
            }
        } catch { $body += '(no ui log available)' }
        $body += ""
        $body += "=== Persistent run log (setup_with_ui_run.log) tail ==="
        try {
            $runPath = Join-Path (Get-Location) 'setup_with_ui_run.log'
            if (Test-Path $runPath) {
                $tail = Get-Content $runPath -Tail 200 -ErrorAction SilentlyContinue
                if ($tail) { $body += $tail } else { $body += '(persistent run log empty)' }
            } else { $body += '(no persistent run log found)' }
        } catch { $body += "(error reading persistent log: $($_.Exception.Message))" }

        $txt.Text = ($body -join [Environment]::NewLine)
        $tbl.Controls.Add($txt,0,1)

        $btnPanel = New-Object System.Windows.Forms.FlowLayoutPanel
        $btnPanel.Dock = 'Fill'
        $btnPanel.FlowDirection = 'RightToLeft'
        $btnPanel.AutoSize = $true

        $btnClose = New-Object System.Windows.Forms.Button
        $btnClose.Text = 'Close'
        $btnClose.Size = [System.Drawing.Size]::new(100,32)
        $btnClose.Add_Click({ $frm.Close() })
        $btnPanel.Controls.Add($btnClose)

        $btnSave = New-Object System.Windows.Forms.Button
        $btnSave.Text = 'Save Log'
        $btnSave.Size = [System.Drawing.Size]::new(100,32)
        $btnSave.Add_Click({
            try {
                $path = Join-Path (Get-Location) ("setup_with_ui_result_{0}.log" -f ((Get-Date).ToString('yyyyMMdd_HHmmss')))
                $txt.Text | Out-File -FilePath $path -Encoding utf8
                try { Show-InfoDialog $ui 'Saved' ("Saved: {0}" -f $path) | Out-Null } catch { Write-Host ("Saved: {0}" -f $path) }
            } catch { try { Show-InfoDialog $ui 'Error' ("Save failed: {0}" -f $_.Exception.Message) $false | Out-Null } catch { Write-Host ("Save failed: {0}" -f $_.Exception.Message) } }
        })
        $btnPanel.Controls.Add($btnSave)

    $btnCopy = New-Object System.Windows.Forms.Button
    $btnCopy.Text = 'Copy'
    $btnCopy.Size = [System.Drawing.Size]::new(80,32)
    $btnCopy.Add_Click({ try { [System.Windows.Forms.Clipboard]::SetText($txt.Text); try { Show-InfoDialog $ui 'Info' 'Copied to clipboard' | Out-Null } catch { Write-Host 'Copied to clipboard' } } catch {} })
        $btnPanel.Controls.Add($btnCopy)

        $tbl.Controls.Add($btnPanel,0,2)

        if ($null -ne $ui -and $ui.PSObject.Properties.Match('Form') -and $ui.Form -ne $null) {
            $frm.ShowDialog($ui.Form) | Out-Null
        } else {
            # headless or no-owner case
            $frm.ShowDialog() | Out-Null
        }
    } catch {
        try { Write-Host (("Result: {0} - {1}" -f $result.Success, $result.Message)) } catch {}
    }
}

# Show a short informational dialog using the Result dialog infrastructure when possible.
function Show-InfoDialog($ui, $title, $message, [bool]$success = $true) {
    try {
        $res = @{ Success = [bool]$success; Message = $message }
        if ($null -ne $ui) { Show-ResultDialog $ui $title $res; return }
        # if no UI, try to create a minimal form owner for the dialog
        try {
            $fakeUi = @{ Checks = @{}; Log = [PSCustomObject]@{ Text = $message }; Form = $null }
            Show-ResultDialog $fakeUi $title $res
            return
        } catch {}
        # last resort: write to host (headless fallback)
        try { Write-Host ("{0}: {1}" -f $title, $message) } catch {}
    } catch {
        try { Write-Host ("{0}: {1}" -f $title, $message) } catch {}
    }
}

function New-StatusBitmap($ok) {
    # create a tiny 18x18 bitmap with a colored circle and either a check or cross
    $bmp = New-Object System.Drawing.Bitmap 18,18
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rect = New-Object System.Drawing.Rectangle 0,0,17,17
    if ($ok) {
        $fill = [System.Drawing.Color]::FromArgb(0,150,0)
    } else {
        $fill = [System.Drawing.Color]::FromArgb(200,50,50)
    }
    $brush = New-Object System.Drawing.SolidBrush $fill
    $g.FillEllipse($brush,$rect)
    # draw symbol (use unicode glyphs; fall back to simple lines if not available)
    $font = New-Object System.Drawing.Font('Segoe UI Symbol',10,[System.Drawing.FontStyle]::Bold)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    try {
        $char = if ($ok) { [char]0x2713 } else { [char]0x2717 }
        $g.DrawString($char, $font, [System.Drawing.Brushes]::White, [System.Drawing.RectangleF]::new(0,0,18,18), $sf)
    } catch {
        try {
            if ($ok) {
                $pen = New-Object System.Drawing.Pen([System.Drawing.Brushes]::White,2)
                $g.DrawLine($pen,3,9,7,13)
                $g.DrawLine($pen,7,13,15,5)
            } else {
                $pen = New-Object System.Drawing.Pen([System.Drawing.Brushes]::White,2)
                $g.DrawLine($pen,4,4,14,14)
                $g.DrawLine($pen,14,4,4,14)
            }
        } catch {
            # ignore drawing fallback errors
        }
    }
    $g.Dispose()
    return $bmp
}

function Set-StepStatus($ui, $proxy, [bool]$ok) {
    try {
        # All UI updates must be marshaled to the UI thread; use Safe-UiInvoke to be defensive.
        Safe-UiInvoke $ui {
            try {
                if ($ok) {
                    $proxy.Label.ForeColor = [System.Drawing.Color]::FromArgb(0,90,0)
                    $proxy.Label.Tag = $true
                } else {
                    $proxy.Label.ForeColor = [System.Drawing.Color]::FromArgb(140,30,30)
                    $proxy.Label.Tag = $false
                }
                # ensure proxy.Checked is set (CheckProxy will update Pic.BackColor when set)
                try { $proxy.Checked = [bool]$ok } catch {}
                try { $proxy.Pic.Image = New-StatusBitmap($ok) } catch {}
                try { $proxy.Refresh() } catch {}
            } catch {}
        }
    } catch {}
}

function Write-Log($txt, $logbox) {
    $now = (Get-Date).ToString('HH:mm:ss')
    $line = "[$now] $txt"
    try {
        # update last-activity timestamp (used by watchdog)
        try { $global:lastActivityTime = Get-Date } catch {}
        # Always append to persistent run log for post-mortem debugging
        try { Add-Content -Path (Join-Path (Get-Location) 'setup_with_ui_run.log') -Value $line -ErrorAction SilentlyContinue } catch {}
        if ($null -eq $logbox) { Write-Host $line; return }
        # If called from a non-UI thread, marshal the update to the control's thread
        try {
            if ($logbox.InvokeRequired) {
                # Create an Action delegate to append text safely on the UI thread
                $action = [System.Action]{ param($lb,$ln)
                    try { $lb.AppendText($ln + [Environment]::NewLine); $lb.SelectionStart = $lb.Text.Length; $lb.ScrollToCaret() } catch {}
                }
                $logbox.BeginInvoke($action, @($logbox,$line)) | Out-Null
            } else {
                $logbox.AppendText($line + [Environment]::NewLine)
                $logbox.SelectionStart = $logbox.Text.Length
                $logbox.ScrollToCaret()
            }
        } catch {
            # Fallback to Write-Host if invoking fails
            Write-Host $line
        }
    } catch {}
}

function Safe-UiInvoke($ui, [scriptblock]$action, $args = $null) {
    # Safely invoke an action on the UI thread if the form exists and is valid.
    try {
        if ($null -eq $ui) { return }
        $form = $null
        try { $form = $ui.Form } catch {}
        if ($form -and ($form -is [System.Windows.Forms.Form])) {
            try {
                if ($form.InvokeRequired) {
                    try {
                        if ($null -ne $args) { $form.BeginInvoke($action, @($args)) | Out-Null } else { $form.BeginInvoke($action) | Out-Null }
                    } catch { try { if ($null -ne $args) { $form.BeginInvoke($action) | Out-Null } else { $form.BeginInvoke($action) | Out-Null } } catch {} }
                } else {
                    try { if ($null -ne $args) { & $action $args } else { & $action } } catch {}
                }
            } catch {
                # last resort, run the action directly (best-effort)
                try { & $action } catch {}
            }
        } else {
            try { & $action } catch {}
        }
    } catch {}
}

function Write-ErrorLog($ex) {
    # Minimal-safe logger: append a simple string representation to the error log file.
    try {
        $ts = (Get-Date).ToString('s')
        try { $path = Join-Path (Get-Location) 'setup_with_ui_error.log' } catch { $path = 'setup_with_ui_error.log' }
        # Convert to simple string without calling properties/methods on the object to avoid null/method errors
        try { $s = [string]$ex } catch { $s = '<unserializable>' }
        $line = "[$ts] $s`r`n"
        try { [System.IO.File]::AppendAllText($path, $line, [System.Text.Encoding]::UTF8) } catch { try { Write-Host $line } catch {} }
    } catch {
        try { Write-Host ("[Write-ErrorLog failure at {0}] {1}" -f (Get-Date).ToString('s'), ($_ -as [string])) } catch {}
    }
}

function IncrementProgress($ui) {
    try {
        if ($ui -and $ui.Progress -and ($ui.Progress.Value -lt $ui.Progress.Maximum)) {
            # Update progress on the UI thread if required
            if ($ui.Progress.InvokeRequired) {
                $act = [System.Action]{ param($u)
                    try {
                        $u.Progress.Value = [Math]::Min($u.Progress.Maximum, $u.Progress.Value + 1)
                        if ($u.PercentLabel) { $u.PercentLabel.Text = "Progres: $($u.Progress.Value)%" }
                        [System.Windows.Forms.Application]::DoEvents()
                    } catch {}
                }
                try { $ui.Progress.BeginInvoke($act, @($ui)) | Out-Null } catch { }
            } else {
                try { $ui.Progress.Value = [Math]::Min($ui.Progress.Maximum, $ui.Progress.Value + 1) } catch {}
                try { if ($ui.PercentLabel) { $ui.PercentLabel.Text = "Progres: $($ui.Progress.Value)%" } } catch {}
            }
        }
    } catch {}
}

function Run-CommandCapture($exe, $argArray, [int]$timeoutSeconds = 600) {
    # Resolve executable: prefer absolute path if provided, otherwise try Get-Command
    try {
        if (-not [string]::IsNullOrEmpty($exe) -and -not (Test-Path $exe)) {
            $cmd = Get-Command $exe -ErrorAction SilentlyContinue
            if ($cmd) { $exe = $cmd.Source }
        }
    } catch {}
        # If dry-run mode is enabled, return a successful fake response immediately
    # Allow tests to override default timeout by setting $global:SetupDefaultTimeoutSeconds
    try { if (Test-Path variable:global:SetupDefaultTimeoutSeconds -and $timeoutSeconds -eq 600) { $timeoutSeconds = [int]$global:SetupDefaultTimeoutSeconds } } catch {}
    try { if ($global:ui -and $global:ui.DryRunCheck -and $global:ui.DryRunCheck.Checked) { $tmpArgs = @(); if ($null -ne $argArray) { $tmpArgs = @($argArray) }; Write-Log ("[DRYRUN] Run-CommandCapture {0} {1}" -f $exe, ($tmpArgs -join ' ')) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }); return @{ ExitCode=0; StdOut='[DRYRUN]'; StdErr='' } } } catch {}

        # Prepare ProcessStartInfo and arguments
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exe
    # Quote/escape individual args safely; guard against null $argArray
    $argList = @()
    if ($null -ne $argArray) { $argList = @($argArray) }
    $escaped = @()
    foreach ($a in $argList) {
        if ($a -match '\s') { $escaped += ('"{0}"' -f ($a -replace '"','\\"')) } else { $escaped += $a }
    }
    if ($escaped.Count -gt 0) { $psi.Arguments = [String]::Join(' ', $escaped) } else { $psi.Arguments = '' }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi

    # Diagnostic: log resolved command and args to persistent log
    try { Write-Log ("Run-CommandCapture: Executable=[{0}] Args=[{1}] Timeout={2}" -f $psi.FileName, $psi.Arguments, $timeoutSeconds) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}

    try {
        if (-not (Test-Path $exe) -and -not (Get-Command $exe -ErrorAction SilentlyContinue)) {
            return @{ ExitCode = -1; StdOut=''; StdErr = "Executable not found: $exe" }
        }
        $started = $proc.Start()
        if (-not $started) { return @{ ExitCode = -1; StdOut=''; StdErr='Failed to start process' } }
    } catch {
        return @{ ExitCode = -1; StdOut=''; StdErr=$_.Exception.Message }
    }

    # track PID for watchdog/cleanup
    try { if (-not (Test-Path variable:global:TrackedPIDs)) { $global:TrackedPIDs = @() } ; $global:TrackedPIDs += $proc.Id } catch {}

    # Read output synchronously to avoid async callback deadlocks for short commands
    $out = ''
    $err = ''
    try {
        # Wait for exit with timeout, but poll so the in-process watchdog can abort/kilL the process
        $deadline = (Get-Date).AddSeconds($timeoutSeconds)
        while (-not $proc.HasExited) {
            Start-Sleep -Milliseconds 200
            # If an in-process watchdog is desired, we can also inspect last-activity timestamp
            try {
                if (Test-Path variable:global:lastActivityTime) {
                    $idleSince = (Get-Date) - $global:lastActivityTime
                    if ($idleSince.TotalSeconds -ge $timeoutSeconds) {
                        try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                        try { Write-Log (("[WATCHDOG] Killed process by PID {0} due to inactivity {1}s >= {2}s") -f $proc.Id, [int]$idleSince.TotalSeconds, $timeoutSeconds) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
                        return @{ ExitCode = -1; StdOut=''; StdErr='Killed by watchdog (inactivity)' }
                    }
                }
            } catch {}
            # enforce timeout
            if ((Get-Date) -gt $deadline) {
                try { $proc.Kill() } catch {}
                return @{ ExitCode = -1; StdOut=''; StdErr='Timed out' }
            }
        }
        # Read standard output/error synchronously
        try { $out = $proc.StandardOutput.ReadToEnd() } catch { $out = '' }
        try { $err = $proc.StandardError.ReadToEnd() } catch { $err = '' }
        # Log exit details for diagnostics (helps automated tests and post-mortem)
        try { Write-Log (("Run-CommandCapture finished: ExitCode={0} StdErr={1}") -f $proc.ExitCode, ($err -replace "`r?`n", ' | ')) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
        # Persist the full StdOut/StdErr to the run log for forensic inspection (separate markers)
        try {
            $runLogPath = Join-Path (Get-Location) 'setup_with_ui_run.log'
            if ($out -ne $null -and $out -ne '') {
                Add-Content -Path $runLogPath -Value "--- Run-CommandCapture StdOut ({0}) ---" -f ([DateTime]::Now.ToString('s')) -ErrorAction SilentlyContinue
                Add-Content -Path $runLogPath -Value $out -ErrorAction SilentlyContinue
            }
            if ($err -ne $null -and $err -ne '') {
                Add-Content -Path $runLogPath -Value "--- Run-CommandCapture StdErr ({0}) ---" -f ([DateTime]::Now.ToString('s')) -ErrorAction SilentlyContinue
                Add-Content -Path $runLogPath -Value $err -ErrorAction SilentlyContinue
            }
        } catch {}
    } catch {
        try { $proc.Kill() } catch {}
        return @{ ExitCode = -1; StdOut=''; StdErr = $_.Exception.Message }
    }
    return @{ ExitCode=$proc.ExitCode; StdOut=$out; StdErr=$err }
}

# Start a process with redirected stdout/stderr and stream lines into the provided log textbox.
function Start-ProcessWithStreaming($exe, $argArray, $logbox, [int]$timeoutSeconds = 600) {
    # If dry-run mode is enabled, log and return success immediately
    # Allow tests to override default timeout by setting $global:SetupDefaultTimeoutSeconds
    try { if (Test-Path variable:global:SetupDefaultTimeoutSeconds -and $timeoutSeconds -eq 600) { $timeoutSeconds = [int]$global:SetupDefaultTimeoutSeconds } } catch {}
    try { if ($global:ui -and $global:ui.DryRunCheck -and $global:ui.DryRunCheck.Checked) { $tmpArgs = @(); if ($null -ne $argArray) { $tmpArgs = @($argArray) }; Write-Log (("[DRYRUN] Start-ProcessWithStreaming {0} {1}" -f $exe, ($tmpArgs -join ' '))) $logbox; return 0 } } catch {}

    # Resolve executable similarly to Run-CommandCapture
    try { if (-not [string]::IsNullOrEmpty($exe) -and -not (Test-Path $exe)) { $cmd = Get-Command $exe -ErrorAction SilentlyContinue; if ($cmd) { $exe = $cmd.Source } } } catch {}
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    # Guard against null $argArray
    $argList = @()
    if ($null -ne $argArray) { $argList = @($argArray) }
    $escaped = @()
    foreach ($a in $argList) {
        if ($a -match '\s') { $escaped += ('"{0}"' -f ($a -replace '"','\\"')) } else { $escaped += $a }
    }
    if ($escaped.Count -gt 0) { $psi.Arguments = [String]::Join(' ', $escaped) } else { $psi.Arguments = '' }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.EnableRaisingEvents = $true

    try {
        if (-not (Test-Path $exe) -and -not (Get-Command $exe -ErrorAction SilentlyContinue)) {
            Write-Log (("Executable not found: {0}" -f $exe)) $logbox
            return -1
        }
        $started = $proc.Start()
        if (-not $started) { Write-Log (("Failed to start process {0}" -f $exe)) $logbox ; return -1 }
    } catch {
        Write-Log (("Exception starting process {0}: {1}" -f $exe, $_.Exception.Message)) $logbox
        return -1
    }
    # track PID for watchdog/cleanup
    try { if (-not (Test-Path variable:global:TrackedPIDs)) { $global:TrackedPIDs = @() } ; $global:TrackedPIDs += $proc.Id } catch {}

    # output handlers
    $proc.add_OutputDataReceived({ param($s,$e) if ($e.Data) { Write-Log $e.Data $logbox } })
    $proc.add_ErrorDataReceived({ param($s,$e) if ($e.Data) { Write-Log $e.Data $logbox } })
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not (Test-Path variable:global:lastProcessHeartbeatSeconds)) { $global:lastProcessHeartbeatSeconds = 0 }
    while (-not $proc.HasExited) {
        Start-Sleep -Milliseconds 150
        # periodic heartbeat to persistent log so we can see progress when UI seems stuck
        try {
            $elapsed = [int]$sw.Elapsed.TotalSeconds
            if ($elapsed -gt 0 -and ($elapsed -ge ($global:lastProcessHeartbeatSeconds + 15))) {
                $global:lastProcessHeartbeatSeconds = $elapsed
                Write-Log ("[HEARTBEAT] Process running {0}s: {1} {2}" -f $elapsed, $exe, $psi.Arguments) $logbox
            }
        } catch {}
        if ($sw.Elapsed.TotalSeconds -gt $timeoutSeconds) {
            try { $proc.Kill() } catch {}
            Write-Log (("Process timed out after {0} seconds: {1} {2}" -f $timeoutSeconds, $exe, $psi.Arguments)) $logbox
            return -1
        }
    }
    $proc.WaitForExit()
    # Log exit code for better visibility in the persistent run log
    try { Write-Log (("Process exited: ExitCode={0}  Cmd={1} {2}" -f $proc.ExitCode, $exe, $psi.Arguments)) $logbox } catch {}
    return $proc.ExitCode
}

# Start a process with redirected stdout/stderr and stream lines into the provided log textbox
# but return immediately with the Process object so caller can keep it running in background.
function Start-ProcessWithStreamingBg($exe, $argArray, $logbox, [int]$startTimeoutSeconds = 30) {
    try { if (Test-Path variable:global:SetupDefaultTimeoutSeconds -and $startTimeoutSeconds -eq 30) { $startTimeoutSeconds = [int]$global:SetupDefaultTimeoutSeconds } } catch {}
    try { if ($global:ui -and $global:ui.DryRunCheck -and $global:ui.DryRunCheck.Checked) { $tmpArgs = @(); if ($null -ne $argArray) { $tmpArgs = @($argArray) }; Write-Log (("[DRYRUN] Start-ProcessWithStreamingBg {0} {1}" -f $exe, ($tmpArgs -join ' '))) $logbox; return $null } } catch {}
    try { if (-not [string]::IsNullOrEmpty($exe) -and -not (Test-Path $exe)) { $cmd = Get-Command $exe -ErrorAction SilentlyContinue; if ($cmd) { $exe = $cmd.Source } } } catch {}
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    # Guard against null $argArray
    $argList = @()
    if ($null -ne $argArray) { $argList = @($argArray) }
    $escaped = @()
    foreach ($a in $argList) {
        if ($a -match '\s') { $escaped += ('"{0}"' -f ($a -replace '"','\\"')) } else { $escaped += $a }
    }
    if ($escaped.Count -gt 0) { $psi.Arguments = [String]::Join(' ', $escaped) } else { $psi.Arguments = '' }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.EnableRaisingEvents = $true

    # handlers will write log lines
    $proc.add_OutputDataReceived({ param($s,$e) if ($e.Data) { Write-Log $e.Data $logbox } })
    $proc.add_ErrorDataReceived({ param($s,$e) if ($e.Data) { Write-Log $e.Data $logbox } })

    try {
        if (-not (Test-Path $exe) -and -not (Get-Command $exe -ErrorAction SilentlyContinue)) {
            Write-Log (("Executable not found for background process: {0}" -f $exe)) $logbox
            return $null
        }
        $started = $proc.Start()
        if (-not $started) { Write-Log (("Failed to start background process {0}" -f $exe)) $logbox ; return $null }
    } catch {
        Write-Log (("Exception starting background process {0}: {1}" -f $exe, $_.Exception.Message)) $logbox
        return $null
    }
    # Log background process start (PID may be known after Start())
    try { Write-Log (("Background process started: PID={0} Cmd={1} {2}" -f $proc.Id, $exe, $psi.Arguments)) $logbox } catch {}
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    # wait a short while to ensure process started successfully
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not (Test-Path variable:global:lastProcessHeartbeatSeconds)) { $global:lastProcessHeartbeatSeconds = 0 }
    while ($sw.Elapsed.TotalSeconds -lt $startTimeoutSeconds) {
        if (-not $proc.HasExited) { return $proc }
        Start-Sleep -Milliseconds 100
    }
    # if it exited quickly, return null and log
    if ($proc.HasExited) { Write-Log ("Background process exited prematurely (code {0}): {1} {2}" -f $proc.ExitCode, $exe, $psi.Arguments) $logbox ; return $null }
    return $proc
}

# Kill previously-started or orphaned processes left from earlier test runs.
function Cleanup-OrphanedProcesses() {
    try {
        Write-Log 'Running pre-start cleanup of orphaned processes...' (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null })
    } catch { Write-Host 'Running pre-start cleanup of orphaned processes...' }
    try {
        # Kill any PIDs we tracked from previous runs
        if (Test-Path variable:global:TrackedPIDs) {
            $pids = @($global:TrackedPIDs) | Select-Object -Unique
            foreach ($pid in $pids) {
                try {
                    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($p) {
                        Write-Log ("Cleaning up tracked PID: {0}" -f $pid) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null })
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    }
                } catch {}
            }
            # reset tracked list after attempted cleanup
            try { $global:TrackedPIDs = @() } catch {}
        }
    } catch {
        try { Write-Log ("Cleanup-OrphanedProcesses error: {0}" -f $_.Exception.Message) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
    }
    try {
        # Also attempt to find python processes launched from previous .venv_clean runs
        $found = @()
        try {
            $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and ($_.CommandLine -like "*\\.venv_clean\\Scripts\\python.exe*") }
            foreach ($pp in $procs) {
                $found += $pp.ProcessId
                try { Write-Log ("Killing orphaned venv python PID={0} CmdLine={1}" -f $pp.ProcessId, ($pp.CommandLine -replace "`r?`n"," | ")) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
                try { Stop-Process -Id $pp.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
            }
        } catch {}
        if ($found.Count -gt 0) { Write-Log ("Killed orphaned venv python PIDs: {0}" -f ($found -join ', ')) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) }
    } catch {
        try { Write-Log ("Cleanup-OrphanedProcesses (venv scan) error: {0}" -f $_.Exception.Message) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
    }
}

# Start a lightweight watchdog timer that aborts the running setup if there is no activity for the configured timeout.
# The watchdog runs in-process using System.Threading.Timer so it can access global variables safely.
function Start-SetupWatchdog([int]$timeoutSeconds = 60, $backgroundWorker = $null) {
    try {
        if (-not (Test-Path variable:global:lastActivityTime)) { $global:lastActivityTime = Get-Date }
        if ($timeoutSeconds -le 0) { $timeoutSeconds = 60 }
        # If an existing timer exists, dispose it first
        try { if ($global:SetupWatchdogTimer -ne $null) { $global:SetupWatchdogTimer.Dispose(); $global:SetupWatchdogTimer = $null } } catch {}

        $cb = [System.Threading.TimerCallback]{ param($state)
            try {
                $now = Get-Date
                $last = $global:lastActivityTime
                if (-not $last) { $last = $now }
                $idle = ($now - $last).TotalSeconds
                if ($idle -ge $timeoutSeconds) {
                    # mark watchdog triggered and attempt to cancel background worker
                    try { $global:SetupWatchdogTriggered = $true } catch {}
                    try { Write-Log ("[WATCHDOG] Inactivity {0}s >= {1}s - aborting and cleaning processes" -f [int]$idle, $timeoutSeconds) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
                    # attempt to cancel BackgroundWorker if provided
                    try { if ($backgroundWorker -and $backgroundWorker.WorkerSupportsCancellation) { $backgroundWorker.CancelAsync() } } catch {}
                    # kill any tracked PIDs
                    try {
                        if (Test-Path variable:global:TrackedPIDs) {
                            foreach ($pid in @($global:TrackedPIDs)) {
                                try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue ; Write-Log ("[WATCHDOG] Killed PID {0}" -f $pid) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
                            }
                        }
                    } catch {}
                    # after triggering once, stop the timer
                    try { if ($global:SetupWatchdogTimer -ne $null) { $global:SetupWatchdogTimer.Dispose(); $global:SetupWatchdogTimer = $null } } catch {}
                }
            } catch {}
        }
        # create timer that fires every 3 seconds
        $global:SetupWatchdogTimer = New-Object System.Threading.Timer($cb, $null, 3000, 3000)
        Write-Log ("Watchdog started: timeout {0} seconds" -f $timeoutSeconds) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null })
        # store reference to background worker for potential cancellation
        try { $global:SetupWatchdogBackgroundWorker = $backgroundWorker } catch {}
    } catch {
        try { Write-Log ("Start-SetupWatchdog error: {0}" -f $_.Exception.Message) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
    }
}

function Stop-SetupWatchdog() {
    try {
        if ($global:SetupWatchdogTimer -ne $null) { $global:SetupWatchdogTimer.Dispose(); $global:SetupWatchdogTimer = $null }
        $global:SetupWatchdogTriggered = $false
        $global:SetupWatchdogBackgroundWorker = $null
        Write-Log 'Watchdog stopped.' (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null })
    } catch {
        try { Write-Log ("Stop-SetupWatchdog error: {0}" -f $_.Exception.Message) (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
    }
}

# Individual step runners (exposed so checkboxes can call them)
function Run-Step_CheckPython($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $lbl = $ui.StepsLabel
    $lbl.Text = 'Verificare Python...'
    $pythonArgs = @('-c','import sys; print(sys.executable); print(sys.version.split()[0])')
    try { Write-Log ("Run-Step_CheckPython: invoking python with args: {0}" -f ($pythonArgs -join ' ')) $log } catch {}
    $res = Run-CommandCapture 'python' $pythonArgs
    if ($res.ExitCode -eq 0) {
        Write-Log "OK: $($res.StdOut.Trim())" $log
    Set-StepStatus $ui $checks['Verifica Python'] $true
    } else {
        Write-Log "FAIL: $($res.StdErr)" $log
        Set-StepStatus $ui $checks['Verifica Python'] $false
    }
}

function Run-Step_CheckDjango($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $root = Get-Location
    $venvPython = Join-Path (Join-Path $root '.venv_clean') 'Scripts\python.exe'
    # prefer venv python if present
    $py = if (Test-Path $venvPython) { $venvPython } else { 'python' }
    Write-Log "Checking Django with $py..." $log
    $djangoArgs = @('-c','import django; print(django.get_version())')
    try { Write-Log ("Run-Step_CheckDjango: invoking $py with args: {0}" -f ($djangoArgs -join ' ')) $log } catch {}
    $res = Run-CommandCapture $py $djangoArgs
    if ($res.ExitCode -eq 0 -and ($res.StdOut.Trim() -ne '')) {
        Write-Log "Django present: $($res.StdOut.Trim())" $log
        Set-StepStatus $ui $checks['Verifica Django'] $true
    } else {
        Write-Log "Django not found: $($res.StdErr.Trim())" $log
        Set-StepStatus $ui $checks['Verifica Django'] $false
    }
}

function Run-Step_CreateVenv($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $root = Get-Location
    $venvPath = Join-Path $root '.venv_clean'
    $venvPython = Join-Path $venvPath 'Scripts\python.exe'
    if (Test-Path $venvPython) {
        Write-Log 'venv exists' $log
        Set-StepStatus $ui $checks['Creeaza/Verifica .venv_clean'] $true
        return
    }

    Write-Log 'Creating venv (this may take a moment)...' $log
    # Use streaming helper so output appears in the UI log and UI stays responsive
    $createExit = Start-ProcessWithStreaming (Get-Command python).Source @('-m','venv','.venv_clean','--clear') $log
    if ($createExit -ne 0) { Write-Log "Failed to create venv (exit $createExit)." $log; Set-StepStatus $ui $checks['Creeaza/Verifica .venv_clean'] $false; return }

    # Ensure pip
    $venvPython = Join-Path $venvPath 'Scripts\python.exe'
    Write-Log 'Ensuring pip in venv...' $log
    $ensureExit = Start-ProcessWithStreaming $venvPython @('-m','ensurepip','--default-pip') $log
    if ($ensureExit -ne 0) { Write-Log "ensurepip failed (exit $ensureExit)" $log }
    Set-StepStatus $ui $checks['Creeaza/Verifica .venv_clean'] $true
}

function Run-Step_InstallRequirements($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $root = Get-Location
    $venvPython = Join-Path (Join-Path $root '.venv_clean') 'Scripts\python.exe'
    $reqs = Join-Path $root 'requirements.txt'
    if (-not (Test-Path $reqs)) { Write-Log 'requirements.txt not found' $log; return }
    # Use synchronous Run-CommandCapture for pip install to avoid streaming/DoEvents timing issues
    $ui.Progress.Style = 'Marquee'
    Write-Log 'Installing requirements (this can take several minutes)...' $log
    $reqArgs = @('-m','pip','install','-r',$reqs)
    $res = Run-CommandCapture $venvPython $reqArgs
    $ui.Progress.Style = 'Continuous'
    if ($res.ExitCode -eq 0) {
        # Log a summary of stdout (tail) so long outputs don't clutter the UI
        try {
            $outTail = ($res.StdOut -split "`r?`n" | Select-Object -Last 20) -join [Environment]::NewLine
            if ($outTail) { Write-Log $outTail $log }
        } catch {}
        Write-Log 'Requirements installed' $log
        Set-StepStatus $ui $checks['Instaleaza dependente'] $true
    } else {
        try {
            $errTail = ($res.StdErr -split "`r?`n" | Select-Object -Last 40) -join [Environment]::NewLine
            if ($errTail) { Write-Log ("pip stderr: `n{0}" -f $errTail) $log }
        } catch {}
        Write-Log ("pip install failed (exit {0})." -f $res.ExitCode) $log
        Set-StepStatus $ui $checks['Instaleaza dependente'] $false
    }
}

function Run-Step_SetSettings($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $env:DJANGO_SETTINGS_MODULE = 'zkeco_config.settings'
    Write-Log "session DJANGO_SETTINGS_MODULE=$env:DJANGO_SETTINGS_MODULE" $log
    Set-StepStatus $ui $checks['Seteaza DJANGO_SETTINGS_MODULE'] $true
}

function Run-Step_Migrate($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $venvPython = Join-Path (Join-Path (Get-Location) '.venv_clean') 'Scripts\python.exe'
    Write-Log 'Running migrations...' $log
    $migExit = Start-ProcessWithStreaming $venvPython @('manage.py','migrate','--no-input') $log
    if ($migExit -eq 0) {
        Write-Log 'Migrations applied' $log
        Set-StepStatus $ui $checks['Ruleaza migrari'] $true
    } else {
        Write-Log "migrate failed (exit $migExit)." $log
        Set-StepStatus $ui $checks['Ruleaza migrari'] $false
    }
}

function Run-Step_StartServer($ui) {
    $log = $ui.Log
    $checks = $ui.Checks
    $root = Get-Location
    $venvPython = Join-Path (Join-Path $root '.venv_clean') 'Scripts\python.exe'
    # Prevent double-start: if a server process is already running, don't start another
    try {
        # Prevent concurrent starts
        if ($global:StartingServerLock) {
            Write-Log 'Server start already in progress; skipping.' $log
            return
        }
        $global:StartingServerLock = $true
            if ($global:StartedProcess -and -not $global:StartedProcess.HasExited) {
            Write-Log "Server already running (PID $($global:StartedProcess.Id)); skipping start." $log
            try { Set-StepStatus $ui $checks['Porneste server (optional)'] $true } catch {}
            return
        }
    $serverArgs = @('manage.py','runserver','0.0.0.0:8000','--noreload')
        $proc = $null
        try {
            $proc = Start-ProcessWithStreamingBg $venvPython $serverArgs $log
        } catch {
            Write-Log "Failed to spawn server process: $($_.Exception.Message)" $log
            Set-StepStatus $checks['Porneste server (optional)'] $false
            return
        }
            if ($proc -and -not $proc.HasExited) {
            $global:StartedProcess = $proc
            Write-Log "Started server (PID $($proc.Id))" $log
            Set-StepStatus $ui $checks['Porneste server (optional)'] $true
        } else {
            Write-Log 'Failed to start server' $log
            Set-StepStatus $ui $checks['Porneste server (optional)'] $false
        }
    } catch {
        Write-Log "Exception starting server: $($_.Exception.Message)" $log
        Set-StepStatus $ui $checks['Porneste server (optional)'] $false
    } finally {
        $global:StartingServerLock = $false
    }
}

function Setup-Workflow($ui, $startServer) {
    $checks = $ui.Checks
    $progress = $ui.Progress
    $stepsLabel = $ui.StepsLabel
    $log = $ui.Log
    # $startServer is captured from the UI thread at Start button click time and passed in

    # Progress uses percentage (0..100)
    $weights = @{ 'Verifica Python'=1; 'Verifica Django'=1; 'Creeaza/Verifica .venv_clean'=1; 'Instaleaza dependente'=1; 'Seteaza DJANGO_SETTINGS_MODULE'=1; 'Ruleaza migrari'=1; 'Porneste server (optional)'=1 }
    $current = 0
    $totalSteps = $weights.Keys.Count
    $progress.Maximum = 100
    $progress.Value = 0
    $stepsLabel.Text = "Progres: 0%"
    $stepInc = [Math]::Max(1, [Math]::Floor(100 / $totalSteps))

    # Sequence through implemented step functions and update progress
    $stepsToRun = @('Verifica Python','Verifica Django','Creeaza/Verifica .venv_clean','Instaleaza dependente','Seteaza DJANGO_SETTINGS_MODULE','Ruleaza migrari')
    $root = Get-Location
    foreach ($s in $stepsToRun) {
        # Update small status label + debug label so user sees the currently-running step
        try { Safe-UiInvoke $ui { $ui.StepsLabel.Text = "Ruleaza: $s" } } catch {}
        try { Safe-UiInvoke $ui { if ($ui.DebugLabel) { $ui.DebugLabel.Text = "Running: $s" } } } catch {}

        # If watchdog triggered due to inactivity, abort early
        try {
            if (Test-Path variable:global:SetupWatchdogTriggered -and $global:SetupWatchdogTriggered) {
                Write-Log "[WATCHDOG] Aborting workflow due to inactivity" $log
                return @{ Success=$false; Message='Aborted due to inactivity (watchdog)' }
            }
        } catch {
            # ignore watchdog read errors
        }

        # persistent log mark for diagnostics
        try {
            Write-Log ("START STEP: $s") $log
        } catch {
            # ignore logging failures
        }

        switch ($s) {
            'Verifica Python' { Run-Step_CheckPython $ui }
            'Verifica Django' { Run-Step_CheckDjango $ui }
            'Creeaza/Verifica .venv_clean' { Run-Step_CreateVenv $ui }
            'Instaleaza dependente' { Run-Step_InstallRequirements $ui }
            'Seteaza DJANGO_SETTINGS_MODULE' { Run-Step_SetSettings $ui }
            'Ruleaza migrari' { Run-Step_Migrate $ui }
        }

        try { Write-Log ("END STEP: $s") $log } catch {}
        try { Safe-UiInvoke $ui { if ($ui.DebugLabel) { $ui.DebugLabel.Text = "Completed: $s" } } } catch {}

    # small pause to yield CPU and allow UI thread to process updates
    Start-Sleep -Milliseconds 120

        # verify step marked as completed
        if (-not ($checks[$s].Checked)) {
            try { Write-Log "Pas esuat: $s" $log } catch {}
            return @{ Success=$false; Message="$s failed" }
        }

        $current += $stepInc
        try { Safe-UiInvoke $ui { $ui.Progress.Value = [Math]::Min(100, $current); if ($ui.PercentLabel) { $ui.PercentLabel.Text = "Progres: $($ui.Progress.Value)%" } } } catch {}
        IncrementProgress($ui)
    }

    # Optionally start server
    if ($startServer) {
        Write-Log 'Pornire server dezvoltare...' $log
        Run-Step_StartServer $ui
        if ($checks['Porneste server (optional)'].Checked) {
            Write-Log "Server pornit. Poti deschide http://localhost:8000" $log
        } else {
            Write-Log 'Esec pornire server.' $log
            return @{ Success=$false; Message='Failed to start server' }
        }
    } else {
        Write-Log 'Se sare peste pornirea serverului (nebifat).' $log
    }

    try { Safe-UiInvoke $ui { $ui.Progress.Value = 100; if ($ui.PercentLabel) { $ui.PercentLabel.Text = "Progres: 100%" } ; $ui.StepsLabel.Text = "Progres: 100%" } } catch {}

    return @{ Success=$true; Message='Instalare finalizata' }
}

# If AutoStartUI is disabled (tests/dot-source), don't construct or show the UI.
if (-not $Script:AutoStartUI) {
    Write-Host 'AutoStartUI disabled; setup functions loaded but UI will not be shown.'
    return
}

# Build UI and wire events (synchronous run to avoid BackgroundWorker issues)
$global:StartedProcess = $null
$global:StartingServerLock = $false
try {
    $ui = New-SetupForm
} catch {
    Write-ErrorLog($_)
    try { Show-InfoDialog $null 'Error' ("Failed to construct UI: $($_.Exception.Message)`nSee setup_with_ui_error.log in repository root.") | Out-Null } catch { try { Write-Host ("Failed to construct UI: $($_.Exception.Message)") } catch {} }
    throw
}
$form = $ui.Form
$form.Tag = $ui
$global:ui = $ui

# If python isn't available, automatically enable dry-run so the UI can be tested without launching commands
try {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        try { $ui.DryRunCheck.Checked = $true } catch {}
        Write-Log 'Python not found on PATH - enabling dry-run (no external commands will be executed).' $ui.Log
    }
} catch {}

# Test hook: allow forcing dry-run when running automated tests
try { if ($env:AUTOSTART_DRYRUN -and $env:AUTOSTART_DRYRUN -ne '') { try { $ui.DryRunCheck.Checked = $true } catch {}; Write-Log 'AUTOSTART_DRYRUN: enabled' $ui.Log } } catch {}

# Ensure we kill the started server if the UI is closed unexpectedly
$form.Add_FormClosing({
    param($sender,$e)
    try {
        if ($global:StartedProcess -ne $null) {
            Write-Host "Stopping server process PID $($global:StartedProcess.Id)"
            try {
                Stop-Process -Id $global:StartedProcess.Id -Force -ErrorAction SilentlyContinue
            } catch {
                # ignore
            }
            $global:StartedProcess = $null
        }
    } catch {
        # ignore
    }
    try { Stop-SetupWatchdog } catch {}
})

$ui.StartButton.Add_Click({
    try {
        $btn = $ui.StartButton
        if ($global:SetupRunning) { Write-Log 'Setup already running' $ui.Log ; return }
        $global:SetupRunning = $true
    $btn.Enabled = $false
    # provide immediate visual feedback that the run started
    try { $global:_StartBtn_OrigText = $btn.Text } catch {}
    try { $global:_StartBtn_OrigBack = $btn.BackColor } catch {}
    try { $btn.Text = 'Se instaleaza...'; $btn.BackColor = [System.Drawing.Color]::FromArgb(0,120,215); $btn.Refresh() } catch {}
        # cleanup any orphaned processes from previous runs to avoid PID accumulation
        try { Cleanup-OrphanedProcesses } catch { Write-Log ("Pre-start cleanup error: {0}" -f $_.Exception.Message) $ui.Log }
    $ui.Log.Clear()
    Write-Log 'Incep instalarea...' $ui.Log
    # Capture UI checkbox values on UI thread and pass into background worker to avoid cross-thread reads
    try { $startServer = $ui.StartServerCheck.Checked } catch { $startServer = $false }

        # Run the workflow on a background worker so the UI stays responsive
        $bw = New-Object System.ComponentModel.BackgroundWorker
        $bw.WorkerReportsProgress = $false
        # allow cancellation so the watchdog can request abort
        $bw.WorkerSupportsCancellation = $true

        $bw.DoWork.Add({ param($s,$e)
            try {
                try { Write-Log 'BackgroundWorker: DoWork starting' $ui.Log } catch {}
                # Call Setup-Workflow and capture exceptions with full diagnostics
                try {
                    $res = Setup-Workflow $ui $startServer
                    $e.Result = $res
                } catch {
                    # Log full exception details for post-mortem
                    try { Write-Log ('BackgroundWorker exception: {0}' -f $_.Exception.Message) $ui.Log } catch {}
                    try { Write-ErrorLog($_) } catch {}
                    $e.Result = @{ Success = $false; Message = $_.Exception.Message }
                }
            } catch {
                try { Write-ErrorLog($_) } catch {}
                $e.Result = @{ Success = $false; Message = $_.Exception.Message }
            }
        })

        $bw.RunWorkerCompleted.Add({ param($s,$e)
            try {
                # If the DoWork threw an unhandled exception, e.Error will be non-null
                if ($e.Error) {
                    try { Write-Log ('RunWorkerCompleted: unhandled error: {0}' -f $e.Error.Message) $ui.Log } catch {}
                    try { Write-ErrorLog($e.Error) } catch {}
                    $result = @{ Success = $false; Message = $e.Error.Message }
                } else {
                    $result = $e.Result
                }

                if ($result -and $result.Success) {
                    Write-Log 'Instalare finalizata.' $ui.Log
                    try { Show-ResultDialog $ui 'Instalare finalizata' $result } catch { try { Write-Log ("(Show-ResultDialog failed) $_") $ui.Log } catch {} }
                } else {
                    if ($result) { try { Write-Log (("Setup finished: {0}" -f $result.Message) ) $ui.Log } catch {} }
                    try { Show-ResultDialog $ui 'Instalare esuata' $result } catch { try { Write-Log ("(Show-ResultDialog failed) $_") $ui.Log } catch {} }
                }
            } catch {
                try { Write-Log (("Eroare la finalizare: {0}" -f $_.Exception.Message)) $ui.Log } catch {}
                try { Write-ErrorLog($_) } catch {}
            } finally {
                # stop watchdog when run completes
                try { Stop-SetupWatchdog } catch {}
                # restore start button appearance
                try { if ($null -ne $global:_StartBtn_OrigText) { $btn.Text = $global:_StartBtn_OrigText } else { $btn.Text = 'Instaleaza' } } catch {}
                try { if ($null -ne $global:_StartBtn_OrigBack) { $btn.BackColor = $global:_StartBtn_OrigBack } else { $btn.BackColor = [System.Drawing.SystemColors]::Control } } catch {}
                try { $btn.Enabled = $true } catch {}
                $global:SetupRunning = $false
            }
        })

        try {
            # start the watchdog (60s default inactivity timeout) and pass the BackgroundWorker so it can be cancelled
            try { Start-SetupWatchdog 60 $bw } catch { Write-Log ("Failed to start watchdog: {0}" -f $_.Exception.Message) $ui.Log }
            $bw.RunWorkerAsync() | Out-Null
        } catch {
            Write-Log ("Failed to start background worker: $($_.Exception.Message)") $ui.Log
            # fallback to synchronous run
                try {
                $result = Setup-Workflow $ui ( (try { $ui.StartServerCheck.Checked } catch { $false } ) )
                if ($result -and $result.Success) { Show-ResultDialog $ui 'Instalare finalizata' $result } else { Show-ResultDialog $ui 'Instalare esuata' $result }
            } catch {
                Show-ResultDialog $ui 'Instalare esuata' @{ Success = $false; Message = $_.Exception.Message }
            } finally {
                $btn.Enabled = $true
                $global:SetupRunning = $false
            }
        }
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("StartButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

# (diagnostic click handler removed to avoid double-handling during runs)

# Wire README, Shortcut and Exit buttons directly from UI object
$ui.ReadmeButton.Add_Click({
    try {
        Write-Log 'Afisez README...' $ui.Log
        Show-ReadmeModal (Get-Location) $form
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("ReadmeButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

$ui.ViewLogButton.Add_Click({
    try {
        Write-Log 'Afisez logul curent...' $ui.Log
        Show-ResultDialog $ui 'Log curent' @{ Success=$true; Message='Log curent' }
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("ViewLogButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

$ui.ClearLogButton.Add_Click({
    try {
        try { $ui.Log.Clear() } catch {}
        $path = Join-Path (Get-Location) 'setup_with_ui_run.log'
        if (Test-Path $path) { '' | Out-File -FilePath $path -Encoding utf8 }
        Show-InfoDialog $ui 'Gata' 'Log curatat' | Out-Null
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("ClearLogButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

$ui.ShortcutButton.Add_Click({
    try {
        $bat = Join-Path (Get-Location) 'start_setup.bat'
        $ps1 = Join-Path (Get-Location) 'setup_with_ui.ps1'
        # Shortcut will use the batch launcher by default (no PowerShell checkbox present)
        $usePS = $false
        $target = if ($usePS -and (Test-Path $ps1)) { $ps1 } else { $bat }
        if (-not (Test-Path $target)) {
            Show-InfoDialog $ui 'Eroare' 'Fisier lansator nen gasit in radacina proiectului.' | Out-Null
            return
        }
        $res = Create-DesktopShortcut $target 'ZKAccessB Setup' $usePS
        if ($res.Success) {
            Write-Log "Created shortcut: $($res.Path)" $ui.Log
            Show-InfoDialog $ui 'Gata' ("Scurtatura a fost creata pe Desktop:`n$($res.Path)") | Out-Null
        } else {
            Write-Log "Esec creare scurtatura: $($res.Error)" $ui.Log
            Show-InfoDialog $ui 'Eroare' ("Esec creare scurtatura: $($res.Error)") | Out-Null
        }
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("ShortcutButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

$ui.ExitButton.Add_Click({
    try {
        try {
            if ($global:StartedProcess -ne $null) {
                Write-Log "Stopping server process PID $($global:StartedProcess.Id)" $ui.Log
                try { Stop-Process -Id $global:StartedProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
                $global:StartedProcess = $null
            }
        } catch {}
        try { Stop-SetupWatchdog } catch {}
        try { $form.Close() } catch {}
    } catch {
        try { Write-ErrorLog($_) } catch {}
        try { Show-InfoDialog $null 'Eroare' $_.Exception.Message $false } catch { try { Write-Host ("ExitButton click error: {0}" -f $_.Exception.Message) } catch {} }
    }
})

$form.Topmost = $false
try {
    # Optional test hook: if AUTOSTART_PERFORM_CLICK environment variable is set,
    # perform a programmatic click on the Start button shortly after showing the dialog.
    $doAutoClick = $false
    try { if ($env:AUTOSTART_PERFORM_CLICK -and $env:AUTOSTART_PERFORM_CLICK -ne '') { $doAutoClick = $true } } catch {}
    if ($doAutoClick) {
        # Show dialog non-modally so we can trigger the click without blocking the caller
        $form.Shown.Add({ param($s,$e)
            Start-Sleep -Milliseconds 200
            try { Write-Log 'AUTOSTART_PERFORM_CLICK: performing StartButton.PerformClick()' (if ($global:ui -and $global:ui.Log) { $global:ui.Log } else { $null }) } catch {}
            # Capture ui object into a local variable so the invoked scriptblock uses a stable reference
            $owner = $global:ui
            try {
                # quick diagnostics about owner and StartButton presence
                try {
                    $diagPath = Join-Path (Get-Location) 'setup_with_ui_error_diagnostics.log'
                    $ts = (Get-Date).ToString('s')
                    $status = if ($null -eq $owner) { 'owner=null' } else { ('owner OK; StartButton=' + ([bool]($owner.StartButton -ne $null)).ToString()) }
                    [System.IO.File]::AppendAllText($diagPath, ("[$ts] AUTOSTART DIAG: $status`r`n"), [System.Text.Encoding]::UTF8)
                } catch {}
                Safe-UiInvoke $owner ({ param($o) try { $o.StartButton.PerformClick() } catch { throw } }) $owner
            } catch { try { 
                    $ts = (Get-Date).ToString('s')
                    $msg = try { $_.Exception | Out-String } catch { ($_ | Out-String) }
                    [System.IO.File]::AppendAllText((Join-Path (Get-Location) 'setup_with_ui_error_diagnostics.log'), ("[$ts] AUTOSTART CATCH: $msg`r`n"), [System.Text.Encoding]::UTF8)
                    Write-ErrorLog($_)
                } catch {} }
        })
        [void]$form.ShowDialog()
    } else {
        [void]$form.ShowDialog()
    }
} catch {
    # write exception diagnostics to a dedicated diagnostics file (best-effort, minimal APIs)
    try {
        $diagPath = Join-Path (Get-Location) 'setup_with_ui_error_diagnostics.log'
        $ts = (Get-Date).ToString('s')
        $dump = try { $_.Exception | Out-String } catch { ($_ | Out-String) }
        $psStack = ''
        try { $psStack = (Get-PSCallStack | Out-String) } catch {}
        $entry = "[$ts] DIAG: $dump`r`nPSCallStack:`r`n$psStack`r`n"
        try { [System.IO.File]::AppendAllText($diagPath, $entry, [System.Text.Encoding]::UTF8) } catch {}
    } catch {}
    # write exception to persistent log and show a message so the app doesn't just close
    Write-ErrorLog($_.Exception)
    try { Show-InfoDialog $null 'Eroare' ("Eroare UI setup: $($_.Exception.Message)`nVezi setup_with_ui_error.log in radacina proiectului.") } catch {}
    # keep PowerShell session alive briefly so message can be observed if run from terminal
    Start-Sleep -Seconds 2
}


