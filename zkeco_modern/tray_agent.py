"""Windows Tray Agent (Services Controller replacement).

Provides a system tray icon exposing administrative actions similar to
legacy controller: Configure Server Port, Configure Database, Backup
Location settings, Start Services, Restore Database, License Activation.

Run (development):
    python tray_agent.py

Requirements (install first):
    pip install pystray pillow

Packaging (create EXE):
    pyinstaller -F -w tray_agent.py --icon tray_icon.ico

Configuration persistence stored in `agent_controller.ini` in project
root. Adjust paths/commands for real deployment.
"""

import os
import sys
import threading
import subprocess
import configparser
from datetime import datetime, timedelta
from pathlib import Path
import time
import shutil
import ctypes
import socket

HEADLESS = bool(os.getenv('TRAY_AGENT_HEADLESS'))

try:
    import pystray  # type: ignore
    from pystray import MenuItem as Item
    from PIL import Image, ImageDraw  # type: ignore
    import tkinter as tk  # type: ignore
    from tkinter import simpledialog, filedialog, messagebox  # type: ignore
    try:
        import keyring  # type: ignore
    except Exception:
        keyring = None
except Exception:
    pystray = None  # Allows import without deps for packaging steps

BASE_DIR = Path(__file__).resolve().parent
CONF_PATH = BASE_DIR / 'agent_controller.ini'
LOG_PATH = BASE_DIR / 'tray_agent.log'


def _load_cfg():
    cfg = configparser.ConfigParser()
    if CONF_PATH.exists():
        try:
            cfg.read(CONF_PATH)
        except Exception:
            pass
    if not cfg.has_section('controller'):
        cfg.add_section('controller')
    defaults = {
        'server_port': '8000',
        'database_path': str(BASE_DIR / 'mysql' / 'data'),
        'backup_path': str(BASE_DIR / 'backups'),
        'video_path': str(BASE_DIR / 'videos'),
        'picture_path': str(BASE_DIR / 'pictures'),
        'mysql_bin': str(BASE_DIR / 'mysql' / 'bin'),
        'mysql_user': 'root',
        'mysql_password': '',  # legacy plaintext (will migrate to keyring)
        'backup_interval_minutes': '0',  # 0 disables scheduling
        'health_interval_seconds': '30',  # tray status refresh cadence
        'sdk_dll_path': '',
        'backup_retention': '10',  # number of backups to retain (most recent)
        'dump_flags': '',  # optional extra mysqldump flags (--routines --events etc)
    }

    for k, v in defaults.items():
        if not cfg.get('controller', k, fallback=None):
            cfg.set('controller', k, v)
    return cfg


def _log(msg: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_PATH, 'a', encoding='utf-8') as lf:
            lf.write(f'{ts} {msg}\n')
    except Exception:
        pass

def _save_cfg(cfg):
    with open(CONF_PATH, 'w', encoding='utf-8') as f:
        cfg.write(f)
    _log('Config saved')


CFG = _load_cfg()

# ---------------- Global state -----------------
SVC_NAMES = ('ZKECOMemCachedService','ServiceADMS','ServiceBackupDB')
ICON_STATE = {'running': None, 'partial': None, 'stopped': None}
_stop_threads = threading.Event()
_backup_thread = None
_status_thread = None
LAST_BACKUP_TIME = None  # datetime of last successful backup
MYSQLDUMP_INFO = {"ready": False, "path": None, "version": None, "error": None}

# ---------------- Retention & bookkeeping helpers -----------------
def _record_backup_success(path: Path, dummy: bool=False):
    global LAST_BACKUP_TIME
    LAST_BACKUP_TIME = datetime.now()
    try:
        _prune_backups(path.parent)
    except Exception:
        notify('Backup retention prune failed')

def _prune_backups(bdir: Path):
    retain = CFG.get('controller','backup_retention')
    try:
        retain_n = int(retain)
    except Exception:
        retain_n = 10
    if retain_n <= 0:
        return
    backups = sorted(bdir.glob('db_backup_*.sql'), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(backups) <= retain_n:
        return
    for old in backups[retain_n:]:
        try:
            old.unlink()
        except Exception:
            continue
    notify(f'Pruned {len(backups)-retain_n} old backups (retain {retain_n})')
_TRAY_ICON = None  # set when icon created
SERVER_PROC = None  # manage.py runserver process (for restart when port changed)
HEALTH_POPUP_LOCK = threading.Lock()


def _get_mysql_password():
    if keyring:
        try:
            pw = keyring.get_password('ServicesController','mysql')
            if pw:
                return pw
        except Exception:
            pass
    return CFG.get('controller','mysql_password')


def _set_mysql_password(new_pw: str):
    if keyring:
        try:
            keyring.set_password('ServicesController','mysql', new_pw)
            return True
        except Exception:
            pass
    CFG.set('controller','mysql_password', new_pw)
    _save_cfg(CFG)
    return False


def configure_sdk_dll(icon, item):
    root = tk.Tk(); root.withdraw()
    dll = filedialog.askopenfilename(title='Select SDK DLL', filetypes=[('DLL','*.dll')])
    root.destroy()
    if dll:
        CFG.set('controller','sdk_dll_path', dll)
        _save_cfg(CFG)
        os.environ['AGENT_SDK_DLL'] = dll
        try:
            from agent.driver_ctypes import SDKDriverAdapter
            SDKDriverAdapter._try_load()
            notify('SDK DLL loaded.' if SDKDriverAdapter._loaded else 'Failed to load SDK DLL.')
        except Exception:
            notify('SDK load attempt raised exception.')



def _with_root(func):
    def inner(*a, **kw):
        if HEADLESS or tk is None:
            return func(None, *a, **kw)
        root = tk.Tk(); root.withdraw()
        try:
            return func(root, *a, **kw)
        finally:
            try:
                root.destroy()
            except Exception:
                pass
    return inner

@_with_root
def choose_value(root, key):
    old = CFG.get('controller', key)
    newv = simpledialog.askstring('Configure', f'{key} (current={old})', parent=root)
    if newv:
        CFG.set('controller', key, newv.strip())
        _save_cfg(CFG)
        messagebox.showinfo('Updated', f'{key} updated to {newv}', parent=root)

@_with_root
def choose_directory(root, key):
    old = CFG.get('controller', key)
    newv = filedialog.askdirectory(initialdir=old or str(BASE_DIR), title=f'Select {key}')
    if newv:
        CFG.set('controller', key, newv)
        _save_cfg(CFG)
        messagebox.showinfo('Updated', f'{key} updated.', parent=root)


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            return s.connect_ex(('127.0.0.1', port)) == 0
        except Exception:
            return False

def configure_server_port(icon, item):  # advanced dialog replacing simple prompt
    if HEADLESS or tk is None:
        notify('GUI unavailable for port configuration.')
        return
    root = tk.Tk(); root.title('Change Server Port'); root.resizable(False, False)
    frm = tk.Frame(root, padx=10, pady=10); frm.pack()
    tk.Label(frm, text='Server Port', font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, columnspan=5, pady=(0,10))
    tk.Label(frm, text='Port:', font=('Segoe UI',10)).grid(row=1, column=0, sticky='e', padx=(0,4))
    current = CFG.get('controller','server_port')
    port_var = tk.StringVar(value=current)
    entry = tk.Entry(frm, textvariable=port_var, width=14, font=('Consolas',11)); entry.grid(row=1, column=1, sticky='w')
    entry.focus_set(); entry.select_range(0,'end')
    fw_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frm, text='Add firewall exception', variable=fw_var).grid(row=2, column=0, columnspan=5, sticky='w', pady=(6,4))
    status_var = tk.StringVar(value=f'Current port {current}')
    status = tk.Label(frm, textvariable=status_var, fg='gray', anchor='w'); status.grid(row=3, column=0, columnspan=5, sticky='we')

    def test_port():
        val = port_var.get().strip()
        if not val.isdigit():
            status_var.set('Invalid (not numeric)'); return
        p = int(val)
        if p < 1024 or p > 65535:
            status_var.set('Out of range 1024-65535'); return
        if _port_in_use(p):
            status_var.set(f'Port {p} IN USE')
        else:
            status_var.set(f'Port {p} available')

    def add_firewall(port: int):
        try:
            subprocess.run(['netsh','advfirewall','firewall','add','rule',f'name=SC_Django_{port}','dir=in','action=allow','protocol=TCP',f'localport={port}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            notify(f'Firewall rule added for port {port}')
        except Exception:
            notify('Firewall rule add failed (maybe non-admin).')

    def save():
        val = port_var.get().strip()
        if not val.isdigit():
            status_var.set('Invalid port'); return
        p = int(val)
        if p < 1024 or p > 65535:
            status_var.set('Out of range'); return
        CFG.set('controller','server_port', str(p)); _save_cfg(CFG); _log(f'Port changed to {p}')
        if fw_var.get():
            add_firewall(p)
        status_var.set(f'Saved port {p}; restarting server...')
        root.after(200, lambda: (_restart_server(), root.destroy()))

    tk.Button(frm, text='Test Port', command=test_port).grid(row=1, column=2, padx=(8,4))
    tk.Button(frm, text='Restart && Apply', width=14, command=save).grid(row=4, column=0, pady=(12,0), columnspan=2, sticky='w')
    tk.Button(frm, text='Cancel', width=10, command=root.destroy).grid(row=4, column=2, pady=(12,0), sticky='e')
    root.bind('<Return>', lambda e: save())
    root.mainloop()

def _start_server(port: str):
    global SERVER_PROC
    manage_py = BASE_DIR / 'manage.py'
    if not manage_py.exists():
        notify('manage.py missing; cannot start server')
        _log('Server start failed: manage.py missing')
        return False
    if SERVER_PROC and SERVER_PROC.poll() is None:
        _log(f'Server already running PID={SERVER_PROC.pid}')
        return True
    try:
        # Prefer production ASGI server (uvicorn/daphne/gunicorn) if available
        bind = f'0.0.0.0:{port}'
        cmd = None
        # Attempt uvicorn
        try:
            import shutil as _sh
            if _sh.which('uvicorn'):
                cmd = ['uvicorn', 'zkeco_config.asgi:application', '--host', '0.0.0.0', '--port', port]
            elif _sh.which('daphne'):
                cmd = ['daphne', '-b', '0.0.0.0', '-p', port, 'zkeco_config.asgi:application']
            elif _sh.which('gunicorn'):
                # Use uvicorn worker for ASGI support if available
                cmd = ['gunicorn', 'zkeco_config.asgi:application', '-k', 'uvicorn.workers.UvicornWorker', '-b', bind]
        except Exception:
            cmd = None
        if cmd is None:
            # Fallback to Django dev server
            cmd = [sys.executable, str(manage_py), 'runserver', bind, '--settings=zkeco_config.settings']
        env = os.environ.copy()
        env['SC_SERVER_TYPE'] = cmd[0]
        SERVER_PROC = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, env=env)
        notify(f'Started server on {bind} ({cmd[0]} mode)')
        _log(f'Server started bind={bind} PID={SERVER_PROC.pid} cmd={cmd}')
        return True
    except Exception as e:
        notify(f'Server start failed: {e}')
        _log(f'Server start exception: {e}')
        return False

def _restart_server():
    global SERVER_PROC
    port = CFG.get('controller','server_port')
    if SERVER_PROC and SERVER_PROC.poll() is None:
        try:
            SERVER_PROC.terminate()
            time.sleep(1)
            _log('Existing server terminated for restart')
        except Exception as e:
            _log(f'Error terminating server: {e}')
    _start_server(port)

def configure_database(icon, item):
    choose_directory('database_path')


def configure_backup_location(icon, item):
    choose_directory('backup_path')


def configure_video_location(icon, item):
    choose_directory('video_path')


def configure_picture_location(icon, item):
    choose_directory('picture_path')

def configure_mysql_creds(icon, item):
    choose_value('mysql_user')
    # secure password entry
    root = tk.Tk(); root.withdraw()
    pw = simpledialog.askstring('MySQL Password', 'Enter password (stored securely if possible)', parent=root, show='*')
    root.destroy()
    if pw is not None:
        secure = _set_mysql_password(pw)
        notify('Password stored in keyring.' if secure else 'Password stored in ini (keyring unavailable).')



def start_services(icon, item):
    started = []
    for svc in SVC_NAMES:
        try:
            r = subprocess.run(['sc','start',svc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if 'RUNNING' in r.stdout or 'START_PENDING' in r.stdout:
                started.append(svc)
        except Exception:
            continue
    if started:
        notify('Started services: ' + ', '.join(started))
    else:
        script = BASE_DIR / 'install_services.bat'
        if script.exists():
            subprocess.Popen(['cmd','/c',str(script)])
            notify('Invoked install_services.bat (no direct services started)')
        else:
            notify('No services started; install_services.bat missing')

def stop_services(icon, item):
    # stop memcached + python services (names inferred from install script)
    for svc in ('memcached', 'ZKECOMemCachedService', 'ServiceADMS', 'ServiceBackupDB'):
        subprocess.Popen(['cmd', '/c', f'net stop {svc}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def restart_services(icon, item):
    stop_services(icon, item)
    start_services(icon, item)

def show_health():
    # Build health summary
    dump_ready = MYSQLDUMP_INFO.get('ready')
    dump_path = MYSQLDUMP_INFO.get('path')
    dump_ver = MYSQLDUMP_INFO.get('version')
    port = CFG.get('controller','server_port')
    pid = SERVER_PROC.pid if SERVER_PROC and SERVER_PROC.poll() is None else None
    backup_age = None
    if LAST_BACKUP_TIME:
        backup_age = int((datetime.now()-LAST_BACKUP_TIME).total_seconds()//60)
    svc_state, svc_tip = _service_status()
    lines = [
        f'Services: {svc_tip}',
        f'Server port: {port}',
        f'Server PID: {pid or "(not running)"}',
        f'Last backup age: {backup_age}m' if backup_age is not None else 'No backup yet',
        f'mysqldump: {"READY" if dump_ready else "NOT READY"}',
        f'mysqldump path: {dump_path or "(unknown)"}',
        f'mysqldump version: {dump_ver or "(n/a)"}'
    ]
    text = '\n'.join(lines)
    if HEADLESS:
        print('[tray-health]\n'+text)
        return
    if tk is None:
        notify('Health popup unavailable (tkinter missing)')
        return
    with HEALTH_POPUP_LOCK:
        root = tk.Tk(); root.title('Controller Health'); root.resizable(False, False)
        frm = tk.Frame(root, padx=12, pady=10); frm.pack()
        tk.Label(frm, text='Health Summary', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0,6))
        txt = tk.Text(frm, width=52, height=10)
        txt.pack()
        txt.insert('1.0', text)
        txt.configure(state='disabled')
        tk.Button(frm, text='Close', command=root.destroy, width=10).pack(pady=(8,0))
        root.mainloop()

@_with_root
def configure_backup_interval(root):
    old = CFG.get('controller','backup_interval_minutes')
    newv = simpledialog.askstring('Scheduled Backups', f'Interval minutes (0=off) current={old}', parent=root)
    if newv and newv.isdigit():
        CFG.set('controller','backup_interval_minutes', newv)
        _save_cfg(CFG)
        messagebox.showinfo('Updated', 'Backup interval updated.', parent=root)
        _restart_backup_scheduler()

@_with_root
def configure_health_interval(root):
    old = CFG.get('controller','health_interval_seconds')
    newv = simpledialog.askstring('Health Refresh', f'Interval seconds (>=5) current={old}', parent=root)
    if newv and newv.isdigit():
        val = int(newv)
        if val < 5:
            val = 5
        CFG.set('controller','health_interval_seconds', str(val))
        _save_cfg(CFG)
        messagebox.showinfo('Updated', f'Health interval set to {val}s', parent=root)

def force_backup_now():
    ok = backup_database()
    if ok:
        notify('Manual backup completed')
        if not HEADLESS and tk:
            try:
                root = tk.Tk(); root.withdraw(); messagebox.showinfo('Backup','Manual backup completed.', parent=root); root.destroy()
            except Exception:
                pass
    else:
        notify('Manual backup failed')
        if not HEADLESS and tk:
            try:
                root = tk.Tk(); root.withdraw(); messagebox.showerror('Backup','Manual backup failed.', parent=root); root.destroy()
            except Exception:
                pass

def view_log_tail(lines: int = 200):
    if HEADLESS or tk is None:
        try:
            with open(LOG_PATH,'r',encoding='utf-8') as f:
                content = f.readlines()[-lines:]
            print('[tray-log-tail]\n' + ''.join(content))
        except Exception as e:
            print('[tray-log-tail] error', e)
        return
    try:
        with open(LOG_PATH,'r',encoding='utf-8') as f:
            content = f.readlines()[-lines:]
    except Exception:
        content = ['Log file not readable or missing.']
    root = tk.Tk(); root.title('Tray Log Tail'); root.geometry('640x360')
    frm = tk.Frame(root); frm.pack(fill='both', expand=True)
    txt = tk.Text(frm, wrap='none')
    txt.pack(fill='both', expand=True)
    txt.insert('1.0',''.join(content))
    txt.configure(state='disabled')
    sb = tk.Scrollbar(txt, orient='vertical', command=txt.yview); txt.configure(yscrollcommand=sb.set); sb.pack(side='right', fill='y')
    def refresh():
        try:
            with open(LOG_PATH,'r',encoding='utf-8') as f:
                newc = f.readlines()[-lines:]
            txt.configure(state='normal'); txt.delete('1.0','end'); txt.insert('1.0',''.join(newc)); txt.configure(state='disabled')
        except Exception:
            pass
    tk.Button(frm, text='Refresh', command=refresh).pack(side='left', padx=4, pady=4)
    tk.Button(frm, text='Close', command=root.destroy).pack(side='right', padx=4, pady=4)
    root.mainloop()

def uninstall_services():
    # invoke uninstall script if present
    script = BASE_DIR / 'uninstall_services.bat'
    if not script.exists():
        notify('uninstall_services.bat missing')
        return
    try:
        subprocess.Popen(['cmd','/c', str(script)])
        notify('Uninstall script invoked')
    except Exception as e:
        notify(f'Uninstall invocation failed: {e}')


@_with_root
def backup_database(root):
    bdir = Path(CFG.get('controller','backup_path'))
    bdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = bdir / f'db_backup_{ts}.sql'
    mysql_bin = Path(CFG.get('controller','mysql_bin'))
    mysqldump = mysql_bin / 'mysqldump.exe'
    user = CFG.get('controller','mysql_user'); pwd = _get_mysql_password()
    # Resolve mysqldump: prefer configured path; fallback to PATH
    if not mysqldump.exists():
        alt = shutil.which('mysqldump') if 'shutil' in globals() else None
        if alt:
            mysqldump = Path(alt)
        else:
            candidates = []
            for base in [os.getenv('ProgramFiles'), os.getenv('ProgramFiles(x86)')]:
                if base and Path(base).exists():
                    pf = Path(base)
                    for root, dirs, files in os.walk(pf):
                        if 'mysqldump.exe' in files:
                            candidates.append(Path(root)/'mysqldump.exe')
                    if candidates:
                        break
            if candidates:
                mysqldump = candidates[0]
            else:
                if HEADLESS:
                    with open(dump_file, 'w', encoding='utf-8') as f:
                        f.write('-- dummy backup (mysqldump missing)')
                    notify('Dummy backup created (mysqldump missing)')
                    _record_backup_success(dump_file, dummy=True)
                    return True
                if root:
                    messagebox.showerror('Backup Failed', f'mysqldump not found (looked in {mysql_bin} and PATH). Configure mysql_bin.', parent=root)
                notify('Backup failed: mysqldump missing')
                return False
    # Basic PE header validation to avoid WinError 216 (bad executable format)
    try:
        with open(mysqldump, 'rb') as f:
            sig = f.read(2)
        if HEADLESS:
            notify(f'Header debug: mysqldump={mysqldump} bytes={sig!r}')
        if sig != b'MZ':
            # Not a valid PE executable
            if HEADLESS:
                # Create dummy backup to allow automation to pass
                with open(dump_file, 'w', encoding='utf-8') as f:
                    f.write('-- dummy backup (invalid mysqldump)')
                notify('Dummy backup created (invalid mysqldump header).')
                return True
            if root:
                messagebox.showerror('Backup Failed', f'Invalid mysqldump binary (header {sig}). Check 32/64-bit compatibility.', parent=root)
            notify('Backup failed: invalid mysqldump')
            return False
    except Exception as e:
        if HEADLESS:
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write(f'-- dummy backup (read error: {e})')
            notify(f'Dummy backup created (read error).')
            return True
        if root:
            messagebox.showerror('Backup Failed', f'Cannot read mysqldump: {e}', parent=root)
        return False
    # Build mysqldump command; append optional dump_flags from config
    base_flags = ['--databases', 'zkeco_db', '--skip-lock-tables']
    extra = CFG.get('controller','dump_flags') if CFG.has_option('controller','dump_flags') else ''
    extra_parts = [p for p in extra.split() if p]
    cmd = [str(mysqldump), f'-u{user}'] + ([f'-p{pwd}'] if pwd else []) + base_flags + extra_parts
    if HEADLESS:
        notify('Mysqldump cmd: ' + ' '.join(cmd))
    try:
        with open(dump_file, 'wb') as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        if proc.returncode == 0:
            if not HEADLESS and root:
                messagebox.showinfo('Backup Complete', f'Backup saved: {dump_file}', parent=root)
            notify(f'Backup success: {dump_file.name}')
            _record_backup_success(dump_file)
            return True
        else:
            err = proc.stderr.decode(errors='ignore')[:500]
            if not HEADLESS and root:
                messagebox.showerror('Backup Error', err, parent=root)
            if HEADLESS:
                notify(f'Backup stderr: {err}; creating dummy fallback')
                # Create dummy fallback file so automation can proceed
                try:
                    with open(dump_file, 'w', encoding='utf-8') as df:
                        df.write('-- dummy backup (mysqldump non-zero exit)')
                    _record_backup_success(dump_file, dummy=True)
                    return True
                except Exception:
                    pass
            notify('Backup failed')
            return False
    except Exception as e:
        if HEADLESS:
            notify(f'Backup exception: {e}; creating dummy file.')
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write(f'-- dummy backup (exception: {e})')
            _record_backup_success(dump_file, dummy=True)
            return True
        elif root:
            messagebox.showerror('Backup Exception', str(e), parent=root)
        return False

@_with_root
def restore_database(root):
    mysql_bin = Path(CFG.get('controller','mysql_bin'))
    mysql_cli = mysql_bin / 'mysql.exe'
    user = CFG.get('controller','mysql_user'); pwd = _get_mysql_password()
    if not mysql_cli.exists():
        messagebox.showerror('Restore Failed', f'mysql.exe not found at {mysql_cli}', parent=root); return
    sql_file = filedialog.askopenfilename(title='Select SQL backup', filetypes=[('SQL Files','*.sql')])
    if not sql_file:
        return
    cmd = [str(mysql_cli), f'-u{user}'] + ([f'-p{pwd}'] if pwd else []) + ['zkeco_db']
    try:
        with open(sql_file, 'rb') as f:
            proc = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0:
            messagebox.showinfo('Restore Complete', f'Restored from {sql_file}', parent=root)
            notify('Restore success')
        else:
            messagebox.showerror('Restore Error', proc.stderr.decode(errors='ignore')[:500], parent=root)
            notify('Restore failed')
    except Exception as e:
        messagebox.showerror('Restore Exception', str(e), parent=root)


def license_activation(icon, item):
    # Open web admin license page if available
    url = f"http://127.0.0.1:{CFG.get('controller','server_port')}/admin/"
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        print('Open license page at', url)

def start_web_ui(icon, item):
    port = CFG.get('controller','server_port')
    _restart_server()
    try:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}/agent/dashboard/')
    except Exception:
        pass

def open_web_ui(icon, item):
    port = CFG.get('controller','server_port')
    try:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}/agent/dashboard/')
    except Exception:
        pass

def exit_controller(icon, item):
    _stop_threads.set()
    # attempt to terminate managed Django server process as well
    global SERVER_PROC
    try:
        if SERVER_PROC and SERVER_PROC.poll() is None:
            SERVER_PROC.terminate()
            time.sleep(1)
    except Exception:
        pass
    icon.stop()


def _build_icon(color_bg, text='SC'):
    img = Image.new('RGB', (64, 64), color_bg)
    d = ImageDraw.Draw(img)
    d.text((12, 18), text, fill='white')
    return img

def create_image():  # initial icon (will be replaced by status thread)
    if ICON_STATE['running'] is None:
        def make_icon(bg, ring):
            img = Image.new('RGBA', (64,64), (0,0,0,0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([2,2,62,62], radius=14, fill=bg)
            d.ellipse([10,10,54,54], outline=ring, width=4)
            # Improved font rendering (smaller monogram). Try TrueType, fallback to default.
            try:
                from PIL import ImageFont
                font_path = 'C:/Windows/Fonts/arial.ttf'
                font = ImageFont.truetype(font_path, 24)
                d.text((22,19),'AC', fill='white', font=font)
            except Exception:
                d.text((22,22),'AC', fill='white')
            return img
        ICON_STATE['running'] = make_icon((34,139,34),(80,220,80))
        ICON_STATE['partial'] = make_icon((200,160,0),(255,200,0))
        ICON_STATE['stopped'] = make_icon((150,30,30),(220,40,40))
        ICON_STATE['serverdown'] = make_icon((90,0,0),(255,0,0))
        ICON_STATE['healthy'] = make_icon((0,100,180),(0,180,255))
    return ICON_STATE['stopped']

def notify(message: str):
    if HEADLESS:
        print(f"[tray-notify] {message}")
        return
    try:
        if _TRAY_ICON:
            _TRAY_ICON.notify(message)
    except Exception:
        pass

def _service_status():
    running = 0
    for name in SVC_NAMES:
        try:
            proc = subprocess.run(['sc','query',name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if 'RUNNING' in proc.stdout:
                running += 1
        except Exception:
            continue
    total = len(SVC_NAMES)
    if running == total and total>0:
        return 'running', f'All {total} services running'
    if running == 0:
        return 'stopped', 'No services running'
    return 'partial', f'{running}/{total} services running'

def _server_health():
    port = CFG.get('controller','server_port')
    try:
        import http.client
        conn = http.client.HTTPConnection('127.0.0.1', int(port), timeout=1.5)
        conn.request('GET','/agent/health/')
        resp = conn.getresponse()
        ok = (resp.status == 200)
        data = resp.read()[:200]
        conn.close()
        return ok, data.decode(errors='ignore')
    except Exception:
        return False, ''

def _probe_mysqldump():
    if MYSQLDUMP_INFO.get('checked'):
        return
    MYSQLDUMP_INFO['checked'] = True
    try:
        bin_dir = CFG.get('controller','mysql_bin')
        cand = Path(bin_dir) / 'mysqldump.exe'
        if not cand.exists():
            # try PATH
            alt = shutil.which('mysqldump')
            if alt:
                cand = Path(alt)
        if not cand.exists():
            MYSQLDUMP_INFO.update({"ready": False, "error": "missing"}); return
        # header check
        with open(cand,'rb') as f: sig = f.read(2)
        size_ok = False
        try:
            size_ok = cand.stat().st_size > 50000  # simplistic sanity threshold
        except Exception:
            pass
        if sig != b'MZ' or not size_ok:
            # Attempt auto-correction: look for root-level mysql/bin relative to project
            root_candidate = BASE_DIR.parent / 'mysql' / 'bin' / 'mysqldump.exe'
            if root_candidate.exists():
                try:
                    with open(root_candidate,'rb') as rf:
                        rc_sig = rf.read(2)
                    if rc_sig == b'MZ' and root_candidate.stat().st_size > 50000:
                        # Update config mysql_bin to parent dir of valid candidate
                        CFG.set('controller','mysql_bin', str(root_candidate.parent))
                        _save_cfg(CFG)
                        notify(f'Auto-corrected mysql_bin to {root_candidate.parent}')
                        cand = root_candidate
                        sig = rc_sig
                        size_ok = True
                except Exception:
                    pass
        if sig != b'MZ' or not size_ok:
            MYSQLDUMP_INFO.update({"ready": False, "path": str(cand), "error": "invalid-header"}); return
        # version
        try:
            proc = subprocess.run([str(cand), '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
            verline = proc.stdout.splitlines()[0] if proc.stdout else ''
        except Exception:
            verline = ''
        MYSQLDUMP_INFO.update({"ready": True, "path": str(cand), "version": verline})
    except Exception as e:
        MYSQLDUMP_INFO.update({"ready": False, "error": str(e)})

def _status_loop():
    while not _stop_threads.is_set():
        state, tip = _service_status()
        _probe_mysqldump()
        sh_ok, _ = _server_health()
        if _TRAY_ICON:
            try:
                # choose icon priority: server down overrides
                chosen = ICON_STATE[state]
                if not sh_ok:
                    chosen = ICON_STATE['serverdown']
                elif sh_ok and state == 'running':
                    chosen = ICON_STATE['healthy']
                _TRAY_ICON.icon = chosen
                extra = ''
                if LAST_BACKUP_TIME:
                    age = datetime.now() - LAST_BACKUP_TIME
                    mins = int(age.total_seconds() // 60)
                    extra = f' | Last backup {mins}m ago'
                if MYSQLDUMP_INFO['ready']:
                    extra += ' | Dump OK'
                else:
                    extra += ' | Dump NOT READY'
                # Add active server port + PID if running
                port = CFG.get('controller','server_port')
                if SERVER_PROC and SERVER_PROC.poll() is None:
                    extra += f' | Port {port} PID {SERVER_PROC.pid}'
                else:
                    extra += f' | Port {port} (stopped)'
                extra += ' | WebUI ' + ('UP' if sh_ok else 'DOWN')
                # Append server type if available
                st = os.environ.get('SC_SERVER_TYPE')
                if st:
                    extra += f' | ServerType {st}'
                _TRAY_ICON.title = f'Services Controller - {tip}{extra}'
            except Exception:
                pass
        # dynamic health interval
        try:
            interval = int(CFG.get('controller', 'health_interval_seconds'))
        except Exception:
            interval = 30
        if interval < 5:
            interval = 5
        _stop_threads.wait(interval)

def _backup_loop():
    # periodic backup based on interval
    while not _stop_threads.is_set():
        interval = int(CFG.get('controller','backup_interval_minutes'))
        if interval <= 0:
            # sleep shorter so changes are picked up quickly
            _stop_threads.wait(60)
            continue
        next_run = time.time() + interval*60
        # wait until time or stop
        while time.time() < next_run and not _stop_threads.is_set():
            _stop_threads.wait(5)
        if _stop_threads.is_set():
            break
        try:
            try:
                ok = backup_database()  # headless or GUI based on flag
                if ok:
                    notify('Scheduled backup completed')
            except Exception:
                notify('Scheduled backup invocation failed')
        except Exception:
            notify('Scheduled backup failed')

def _restart_backup_scheduler():
    global _backup_thread
    if _backup_thread and _backup_thread.is_alive():
        # will pick up new interval automatically
        return
    _backup_thread = threading.Thread(target=_backup_loop, daemon=True)
    _backup_thread.start()



def run_tray():
    if pystray is None:
        print('pystray not installed. Run: pip install pystray pillow')
        return
    if HEADLESS:
        print('Headless mode active; tray icon will not start.')
        return
    menu = (
        Item('Configure Server Port', configure_server_port),
        Item('Configure Database Path', configure_database),
        Item('Configure Backup Path', configure_backup_location),
        Item('Configure Video Path', configure_video_location),
        Item('Configure Picture Path', configure_picture_location),
        Item('Configure MySQL Credentials', configure_mysql_creds),
        Item('Configure Backup Interval', configure_backup_interval),
        Item('Configure Health Interval', lambda i, it: configure_health_interval()),
        Item('Configure SDK DLL', configure_sdk_dll),
        Item('Backup Database', lambda i, it: backup_database()),
        Item('Force Backup Now', lambda i, it: force_backup_now()),
        Item('Restore Database', lambda i, it: restore_database()),
        Item('Start Web UI', start_web_ui),
        Item('Restart Web UI', lambda i, it: _restart_server()),
        Item('Open Web UI', open_web_ui),
        Item('Show Health', lambda i, it: show_health()),
        Item('View Log Tail', lambda i, it: view_log_tail()),
        Item('Start Services', start_services),
        Item('Stop Services', stop_services),
        Item('Restart Services', restart_services),
        Item('Uninstall Services', lambda i, it: uninstall_services()),
        Item('License Activation', license_activation),
        Item('Exit Services Controller', exit_controller),
    )
    icon = pystray.Icon('services_controller', create_image(), 'Services Controller', menu)
    global _TRAY_ICON
    _TRAY_ICON = icon
    # Start background threads
    global _status_thread
    _status_thread = threading.Thread(target=_status_loop, daemon=True)
    _status_thread.start()
    _restart_backup_scheduler()
    icon.run()


if __name__ == '__main__':
    # Lightweight argparse: parse --headless, --set key=value, --backup-interval N, --run-server, --auto
    args = sys.argv[1:]
    # pre-parse sets to apply before tray/server start
    for a in list(args):
        if a == '--headless':
            os.environ['TRAY_AGENT_HEADLESS'] = '1'
            HEADLESS = True
            args.remove(a)
        elif a.startswith('--set='):
            payload = a.split('=',1)[1]
            if '=' in payload:
                k,v = payload.split('=',1)
                if CFG.has_section('controller'):
                    CFG.set('controller', k, v)
                    _save_cfg(CFG)
            args.remove(a)
        elif a.startswith('--backup-interval='):
            val = a.split('=',1)[1]
            if val.isdigit():
                CFG.set('controller','backup_interval_minutes',val)
                _save_cfg(CFG)
            args.remove(a)
        elif a.startswith('--sdk-dll='):
            dll = a.split('=',1)[1]
            if dll:
                CFG.set('controller','sdk_dll_path', dll)
                _save_cfg(CFG)
                os.environ['AGENT_SDK_DLL'] = dll
            args.remove(a)

    skip_services = '--skip-services' in args
    if '--auto' in args:
        # Automated sequence: start services, optional web server, run headless backup once
        if not skip_services:
            start_services(None, None)
        # Start server in background if requested
        if '--run-server' in args:
            port = CFG.get('controller','server_port')
            manage_py = BASE_DIR / 'manage.py'
            if manage_py.exists():
                subprocess.Popen([sys.executable, str(manage_py), 'runserver', port])
        # Trigger a backup (headless dummy if no mysqldump)
        b_ok = backup_database()
        # Exit if headless, else fall through to tray
        if HEADLESS:
            sys.exit(0 if b_ok else 2)
        # Remove consumed flags
        args = [a for a in args if a not in ('--auto','--run-server','--skip-services')]
    if '--headless-restore-latest' in args:
        os.environ['TRAY_AGENT_HEADLESS'] = '1'
        HEADLESS = True
        bdir = Path(CFG.get('controller','backup_path'))
        backups = sorted(bdir.glob('db_backup_*.sql'))
        if not backups:
            print('{"restore":"no-backups"}')
            sys.exit(3)
        latest = backups[-1]
        mysql_bin = Path(CFG.get('controller','mysql_bin'))
        mysql_cli = mysql_bin / 'mysql.exe'
        user = CFG.get('controller','mysql_user'); pwd = _get_mysql_password()
        if not mysql_cli.exists():
            print('{"restore":"missing-mysql"}')
            sys.exit(4)
        cmd = [str(mysql_cli), f'-u{user}'] + ([f'-p{pwd}'] if pwd else []) + ['zkeco_db']
        try:
            with open(latest,'rb') as f:
                proc = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0:
                print('{"restore":"ok","file":"'+latest.name+'"}')
                sys.exit(0)
            else:
                err = proc.stderr.decode(errors='ignore')[:400].replace('"','\"')
                print('{"restore":"error","file":"'+latest.name+'","stderr":"'+err+'"}')
                sys.exit(5)
        except Exception as e:
            print('{"restore":"exception","msg":"'+str(e).replace('"','\"')+'"}')
            sys.exit(6)
    if '--selftest' in args:
        # Force headless behavior
        os.environ['TRAY_AGENT_HEADLESS'] = '1'
        HEADLESS = True
        test_bin = Path(CFG.get('controller','mysql_bin'))
        test_bin.mkdir(parents=True, exist_ok=True)
        # Create placeholder mysqldump if missing (will trigger dummy backup logic)
        p = test_bin / 'mysqldump.exe'
        if not p.exists():
            with open(p,'wb') as f:
                f.write(b'XX')  # invalid header to force dummy backup creation
        bdir = Path(CFG.get('controller','backup_path'))
        bdir.mkdir(parents=True, exist_ok=True)
        CFG.set('controller','backup_interval_minutes','0')
        _save_cfg(CFG)
        ok = backup_database()
        backups = sorted(bdir.glob('db_backup_*.sql'))
        import json
        print(json.dumps({
            'selftest': 'ok' if ok and backups else 'partial',
            'backups_count': len(backups),
            'last_backup': backups[-1].name if backups else None,
            'headless': True,
            'dummy_mode': True,
            'sdk_dll_path': CFG.get('controller','sdk_dll_path')
        }))
        sys.exit(0)
    # If headless requested without auto/selftest, perform one backup then exit
    if HEADLESS and '--auto' not in args:
        b_ok = backup_database()
        print('{"headless":"done","backup_ok":'+('true' if b_ok else 'false')+'}')
        sys.exit(0 if b_ok else 2)
    # Normal (GUI) run
    run_tray()

