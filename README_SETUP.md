# 🚀 ZKAccessB Installation & Setup Guide

## 📌 Quick Start (5 Minutes)

### For Windows 10/11 Users:

```powershell
# Open PowerShell as Administrator, then run:
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1
```

**That's it!** A window will open showing real-time installation progress.

---

## 🎯 What The Setup Does

The automated setup script performs 7 verification and installation steps:

| # | Step | What It Does | Status |
|---|------|------------|--------|
| 1 | Virtual Environment | Creates isolated Python environment | ✅ |
| 2 | Pip Upgrade | Updates package manager | ✅ |
| 3 | Requirements | Installs all Python dependencies | ✅ |
| 4 | Django Check | Verifies Django framework | ✅ |
| 5 | Site Modules | Confirms manage.py works | ✅ |
| 6 | Database | Applies migrations | ✅ |
| 7 | Static Files | Collects static assets | ✅ |

---

## 🎨 Setup Interface Explanation

### Progress Bar
- Shows overall installation progress (0-100%)
- Updates in real-time as each step completes

### Log Display
- **Green text on black background**
- Shows detailed output from each step
- **Auto-scrolls** to show latest activity
- **Timestamps** for every operation

### Status Indicators
- 🟢 **Green Checkmark (✅)** = Success
- 🔴 **Red X (❌)** = Failed
- 🔵 **Blue Spinner (🔍)** = Checking
- 🟡 **Yellow Gear (⏳)** = Installing

### Buttons
- **▶ Start** - Begins installation (green button)
- **✕ Close** - Closes the window (red button)

---

## 📋 After Installation

### 1. Verify Everything Works
```powershell
powershell -ExecutionPolicy Bypass -File verify_dependencies.ps1
```

Expected output:
```
✅ ALL CHECKS PASSED (7/7)
You can now start the agent:
  powershell -ExecutionPolicy Bypass -File tray_launch.ps1
```

### 2. Start the System Tray Agent
```powershell
powershell -ExecutionPolicy Bypass -File tray_launch.ps1
```

The system tray icon will appear. Right-click it for menu options.

### 3. Open Web Interface
- Navigate to: `http://localhost:8000/agent/dashboard/`
- Default port: **8000** (configurable)

---

## 🛠️ Script Options

### GUI Mode (Default)
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1
```
Shows interactive window with progress.

### Headless Mode (No GUI)
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1 -Headless
```
Runs installation in console without GUI (useful for CI/CD).

### Advanced Multi-threaded Version
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_ui_v2.ps1
```
Alternative with background job execution (for advanced users).

---

## ❓ Troubleshooting

### "Python not found"
**Solution:**
1. Download Python 3.10+ from https://www.python.org/
2. During installation, **check** "Add Python to PATH"
3. Restart PowerShell
4. Run setup again

### "Script won't run"
**Solution:**
1. Open PowerShell **as Administrator**
2. Use the full `-ExecutionPolicy Bypass` flag
3. Ensure you're in the project directory

### "Installation hangs/freezes"
**Solution (FIXED!):**
- New version doesn't block the UI
- UI stays responsive during installation
- Never got stuck before? Check the log box for progress
- If truly stuck (5+ mins), close and try again

### "Some packages failed"
**Status:** This is OK! Non-critical packages might fail.
- Most core packages install fine
- System will still work
- Check `setup_modern_run.log` for details

### "Database errors"
**Solution:**
1. Installation creates SQLite database automatically
2. If migration fails, run manually:
   ```powershell
   $python = ".\.venv\Scripts\python.exe"
   & $python .\zkeco_modern\manage.py migrate
   ```

---

## 📁 Project Structure After Setup

```
ZKAccessB/
├── .venv/                          # Virtual environment (created)
├── zkeco_modern/                   # Main Django project
│   ├── manage.py
│   ├── db.sqlite3                  # Database (created)
│   ├── static/                     # Static files (created)
│   └── ...
├── requirements.txt                # Python dependencies
├── setup_modern_simple.ps1         # Main setup script ⭐
├── verify_dependencies.ps1         # Verification script
├── tray_launch.ps1                 # Start tray agent
└── SETUP_GUIDE.md                  # This guide
```

---

## 📊 Log Files

The setup creates these log files for reference:

| File | Purpose |
|------|---------|
| `setup_modern_run.log` | All operations performed |
| `setup_modern_error.log` | Errors only (if any) |
| `zkeco_modern/server.log` | Web server logs (when running) |

**To view logs:**
```powershell
Get-Content setup_modern_run.log -Tail 50   # Last 50 lines
Get-Content setup_modern_error.log          # Errors only
```

---

## 🔧 Manual Operations

### Activate Virtual Environment (Manual)
```powershell
.\.venv\Scripts\Activate.ps1
```

### Run Django Commands
```powershell
$python = ".\.venv\Scripts\python.exe"
& $python .\zkeco_modern\manage.py migrate
& $python .\zkeco_modern\manage.py createsuperuser
```

### Start Web Server Manually
```powershell
$python = ".\.venv\Scripts\python.exe"
& $python .\zkeco_modern\manage.py runserver 0.0.0.0:8000
```

---

## ⚡ Performance Tips

1. **First run takes longer** (5-10 min) - Normal, lots to install
2. **Subsequent runs faster** - Uses existing environment
3. **Close unused programs** - Frees resources for installation
4. **Check internet connection** - Needed for pip downloads

---

## 🔐 Security Notes

1. Virtual environment is **isolated** - separate from system Python
2. Local database - no external connections
3. Admin credentials - set during first Django run
4. All operations logged - review logs if needed

---

## 📞 Support

**Issue?** Check in this order:
1. Review the **UI log** (green text on black) - shows exactly what failed
2. Check **setup_modern_run.log** file
3. Run **verify_dependencies.ps1** to see what's missing
4. Try **Headless mode** to isolate GUI issues

---

## 🎓 Learning More

- **Django:** https://docs.djangoproject.com/
- **Python:** https://docs.python.org/
- **uvicorn:** https://www.uvicorn.org/
- **Project Docs:** Check `zkeco_modern/` folder

---

## ✨ Features of New Setup System

✅ **Non-blocking UI** - No freezing during installation
✅ **Real-time progress** - See every step as it happens
✅ **Color-coded output** - Easy to spot success/errors
✅ **Detailed logging** - Everything saved for review
✅ **Error recovery** - Can resume if something fails
✅ **Dependency check** - Verifies each component
✅ **Cross-platform ready** - Works on Windows 10/11

---

## 🎉 You're All Set!

After successful installation:
1. Click **Close** in setup window
2. Run: `powershell -ExecutionPolicy Bypass -File tray_launch.ps1`
3. Open browser to `http://localhost:8000/agent/dashboard/`
4. Enjoy! 🚀

---

**Last Updated:** November 27, 2025
**Setup Version:** 2.0 (Non-blocking, Real-time UI)
