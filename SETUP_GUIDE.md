# ZKAccessB Setup Scripts - Updated Versions

## 📋 Available Setup Scripts

### 1. **setup_modern_simple.ps1** (RECOMMENDED - Ultra-Simple, Non-Blocking)
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1
```
**Features:**
- ✅ Real-time progress display (no blocking)
- ✅ Live log output in GUI
- ✅ Color-coded status indicators
- ✅ Simple, clean interface
- ✅ All 7 installation steps with visual feedback
- ✅ Responsive UI during installation
- ✅ Works on Windows 10/11

**Steps Performed:**
1. Create/Activate virtual environment
2. Upgrade pip
3. Install requirements from requirements.txt
4. Verify Django installation
5. Check Django site modules (manage.py)
6. Check and apply database migrations
7. Collect static files

---

### 2. **setup_modern_ui_v2.ps1** (Advanced - Multi-threaded)
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_ui_v2.ps1
```
**Features:**
- ✅ Background job execution
- ✅ Timer-based progress monitoring
- ✅ Split view (left: steps, right: log)
- ✅ Detailed step tracking with icons
- ✅ Non-blocking installation

**Note:** Uses PowerShell jobs for better separation

---

### 3. **setup_modern_ui.ps1** (Original - Kept for backup)
```powershell
powershell -ExecutionPolicy Backup -File setup_modern_ui.backup.ps1
```
Original version saved as backup.

---

## 🚀 Quick Start

### Run Interactive Setup:
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1
```

### Run Headless (No GUI):
```powershell
powershell -ExecutionPolicy Bypass -File setup_modern_simple.ps1 -Headless
```

---

## ✅ What Gets Checked & Installed

1. **Virtual Environment**
   - Creates `.venv` folder if missing
   - Python 3.10+ compatible

2. **Python Packages**
   - Django 4.2+
   - uvicorn (ASGI server)
   - All dependencies from requirements.txt

3. **Django Setup**
   - Verifies manage.py works
   - Runs migrations
   - Collects static files

4. **Database**
   - Checks for pending migrations
   - Applies migrations if needed
   - Uses SQLite by default

---

## 🎨 UI Features

### Progress Indicator
- Blue progress bar fills from left to right
- Shows percentage and current step
- Real-time updates

### Log Display
- Green text on dark background
- Shows detailed operation output
- Auto-scrolls to latest entries
- Timestamps for each operation

### Status Colors
- 🟢 Green = Success (✅)
- 🔴 Red = Error (❌)
- 🟡 Yellow = In Progress (⏳)
- 🔵 Blue = Checking (🔍)

---

## 📋 Installation Output

After successful installation, you'll see:
```
✅✅✅ INSTALLATION SUCCESSFUL ✅✅✅

To start the agent:
  powershell -ExecutionPolicy Bypass -File tray_launch.ps1
```

---

## 🛠️ Troubleshooting

**Issue: Script won't run**
- Run as Administrator
- Use `-ExecutionPolicy Bypass` flag
- Check PowerShell version (5.1+)

**Issue: Python not found**
- Install Python 3.10+ from python.org
- Add Python to PATH
- Restart terminal

**Issue: Stuck/Freezing**
- This is fixed! New version doesn't block UI
- Click Start to begin
- UI remains responsive during installation

**Issue: Requirements installation fails**
- Some packages may be optional
- Non-critical failures are logged but don't stop installation
- Check `setup_modern_run.log` for details

---

## 📝 Log Files

- `setup_modern_run.log` - All operations
- `setup_modern_error.log` - Errors only (if present)
- `setup_modern_ui.backup.ps1` - Original script backup

---

## 💡 Pro Tips

1. **First Time Setup?** Use `setup_modern_simple.ps1` - it's the most reliable
2. **Watch the UI** - It shows exactly what's happening in real-time
3. **Check Logs** - All output is saved to log files for reference
4. **Don't Close During Installation** - Wait for "Complete" status
5. **After Setup** - Run `tray_launch.ps1` to start the agent

---

## Version History

- **v2.0** (NEW) - Simplified, non-blocking, background jobs
- **v1.5** (NEW) - Ultra-simple version with responsive UI
- **v1.0** (Original) - Full-featured but complex

---

## Questions?

Check the log files first, then review the installer output. The UI shows exactly what step failed.
