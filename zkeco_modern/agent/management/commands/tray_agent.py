import os
import sys
import threading
import webbrowser
import time
from pathlib import Path
import signal
import configparser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import hashlib
import logging
import subprocess
from datetime import datetime

import django
from django.core.management.base import BaseCommand
from django.conf import settings
import importlib
import importlib

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    pystray = None
    Image = None

_CENTER = None
_SERVER_PROC = None
_CENTER_THREAD = None
_LAST_ICON_STATE = None  # (server_running, center_running)
_LAST_ICON_STATE = None  # (server_running, center_running)

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8000
CONFIG_PATH = Path.home() / 'zkeco_tray_config.ini'
_CONFIG = configparser.ConfigParser()
if CONFIG_PATH.exists():
    try:
        _CONFIG.read(CONFIG_PATH)
    except Exception:
        pass
if not _CONFIG.has_section('tray'):
    _CONFIG.add_section('tray')
if not _CONFIG.has_option('tray','port'):
    _CONFIG.set('tray','port', str(DEFAULT_PORT))
if not _CONFIG.has_option('tray','server_mode'):
    _CONFIG.set('tray','server_mode', 'asgi')  # asgi or wsgi
if not _CONFIG.has_option('tray','license_cipher'):
    _CONFIG.set('tray','license_cipher', '')  # encrypted license storage
if not _CONFIG.has_option('tray','backup_dir'):
    _CONFIG.set('tray','backup_dir', str(Path.home() / 'zkeco_backups'))
if not _CONFIG.has_option('tray','log_file'):
    _CONFIG.set('tray','log_file', str(Path.home() / 'zkeco_tray_errors.log'))

def _save_config():
    try:
        with open(CONFIG_PATH, 'w') as fp:
            _CONFIG.write(fp)
    except Exception:
        pass

def _derive_key() -> bytes:
    base = (settings.SECRET_KEY + '::TRAY_SALT').encode()
    return hashlib.sha256(base).digest()

def _fernet():
    try:
        from cryptography.fernet import Fernet
        import base64
        return Fernet(base64.urlsafe_b64encode(_derive_key()))
    except Exception:
        return None

def _encrypt(raw: str) -> str:
    f = _fernet()
    if not f:
        return raw[::-1]
    return f.encrypt(raw.encode()).decode()

def _decrypt(cipher: str) -> str:
    if not cipher:
        return ''
    f = _fernet()
    if not f:
        return cipher[::-1]
    try:
        return f.decrypt(cipher.encode()).decode()
    except Exception:
        return ''

def _license_valid(raw: str) -> bool:
    # Placeholder HMAC spec: PROD-EDITION-YYYYMMDD-SEQ-RAND-HMAC8
    if not raw:
        return False
    parts = raw.strip().split('-')
    if len(parts) < 6:
        return False
    hmac_part = parts[-1].upper()
    body = '-'.join(parts[:-1])
    digest = hashlib.sha256((settings.SECRET_KEY + body).encode()).hexdigest()[:8].upper()
    return hmac_part == digest

def _license_status() -> str:
    key = _decrypt(_CONFIG.get('tray','license_cipher', fallback=''))
    return 'VALID' if _license_valid(key) else 'MISSING'

def _masked_license() -> str:
    raw = _decrypt(_CONFIG.get('tray','license_cipher', fallback=''))
    return 'NONE' if not raw else raw[:4] + '-****'

def _init_logging():
    log_path = Path(_CONFIG.get('tray','log_file', fallback=str(Path.home()/ 'zkeco_tray_errors.log')))
    try:
        logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    except Exception:
        pass
    def _hook(exctype, value, tb):
        try:
            import traceback
            logging.error('Uncaught exception', exc_info=(exctype, value, tb))
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = _hook

def _progress_copy(src: Path, dest: Path, title: str = 'Copying'):
    """Copy a file with a simple Tk progress bar. Falls back to shutil.copy2 on error."""
    try:
        total = os.path.getsize(src)
        chunk = 1024 * 256
        root = tk.Tk(); root.title(title); root.geometry('420x140'); root.resizable(False, False)
        tk.Label(root, text=f'{title}:').pack(pady=6)
        bar = ttk.Progressbar(root, length=360, maximum=total)
        bar.pack(pady=4)
        status = tk.Label(root, text='Starting...')
        status.pack(pady=4)
        root.update_idletasks()
        copied = 0
        with open(src, 'rb') as fsrc, open(dest, 'wb') as fdst:
            while True:
                buf = fsrc.read(chunk)
                if not buf:
                    break
                fdst.write(buf)
                copied += len(buf)
                bar['value'] = copied
                pct = (copied / total) * 100 if total else 100
                status.configure(text=f'{copied//1024} / {total//1024} KB  ({pct:0.1f}%)')
                root.update_idletasks()
        status.configure(text='Completed.')
        root.update_idletasks()
        time.sleep(0.4)
        root.destroy()
        return True
    except Exception:
        try:
            shutil.copy2(src, dest)
            return True
        except Exception:
            return False

def _build_icon(color=(52, 152, 219)):
    if Image is None:
        return None
    img = Image.new('RGB', (64, 64), color=(25, 25, 25))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    d.text((20, 24), 'AC', fill=(255,255,255))
    return img

def _choose_icon_color(server_running: bool, center_running: bool):
    if server_running and center_running:
        return (46, 204, 113)      # green
    if server_running or center_running:
        return (241, 196, 15)      # yellow
    return (231, 76, 60)          # red

def _show_help_ro():
    """Display a window with Romanian explanations for each tray action."""
    try:
        win = tk.Tk(); win.title('Ajutor – Explicația butoanelor'); win.geometry('620x560')
        txt = tk.Text(win, wrap='word')
        txt.pack(fill='both', expand=True)
        info = [
            ('Dashboard', 'Deschide pagina principală de monitorizare.'),
            ('Server WSGI', 'Pornește serverul web în modul WSGI (fără WebSockets, simplu).'),
            ('Server ASGI', 'Pornește serverul în modul ASGI (WebSockets). Dacă lipsește Daphne, cade automat pe WSGI.'),
            ('Restart Server', 'Oprește și repornește serverul folosind modul configurat.'),
            ('Stop Server', 'Oprește serverul web.'),
            ('CommCenter Start', 'Pornește serviciul de comunicație cu dispozitivele (polling evenimente).'),
            ('CommCenter Stop', 'Oprește serviciul de comunicație cu dispozitivele.'),
            ('Configure Server Port', 'Setează portul și modul (ASGI/WSGI) pentru server și salvează în config.'),
            ('Configure Database', 'Afișează detalii despre motorul bazei de date folosit.'),
            ('Database Backup Location', 'Alege directorul unde se salvează copiile de siguranță ale bazei de date.'),
            ('Video File Location', 'Definește directorul pentru fișiere video asociate sistemului.'),
            ('Picture File Location', 'Definește directorul pentru fișiere imagine (poze utilizatori, etc).'),
            ('Restore Database', 'Restaurează baza de date dintr-un fișier backup selectat.'),
            ('Backup Database', 'Creează o copie de siguranță a bazei de date curente.'),
            ('Start Services', 'Pornește serverul și CommCenter împreună.'),
            ('Restart Services', 'Repornește serverul și CommCenter (stop + start).'),
            ('Stop Services', 'Oprește atât serverul cât și CommCenter.'),
            ('License Activation', 'Activează licența cu cheia furnizată (validare HMAC).'),
            ('View Server Log', 'Deschide fișierul server.log pentru depanare.'),
            ('Quit', 'Închide agentul tray și oprește serviciile active.'),
        ]
        for title, desc in info:
            txt.insert('end', f"• {title}: {desc}\n\n")
        txt.config(state='disabled')
        tk.Button(win, text='Închide', command=win.destroy).pack(pady=6)
        win.mainloop()
    except Exception:
        pass

def _server_log_path() -> Path:
    return Path(getattr(settings, 'BASE_DIR', Path.cwd())) / 'server.log'

def _read_first_error_from_log(max_bytes: int = 32768) -> str:
    """Return a concise last-error summary from server.log.
    Prefers the final line of the last Traceback block if present,
    otherwise returns the last ERROR/Exception line or the last non-empty line.
    """
    try:
        p = _server_log_path()
        if not p.exists():
            return ''
        with open(p, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = f.read().decode(errors='ignore')
        lines = [ln.rstrip() for ln in data.splitlines() if ln.strip()]
        if not lines:
            return ''
        # Find last Traceback block; if found, return its last line
        tb_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if 'Traceback (most recent call last):' in lines[i]:
                tb_idx = i
                break
        if tb_idx is not None:
            return lines[-1]
        # Else pick nearest ERROR/Exception line from the end
        for ln in reversed(lines):
            up = ln.upper()
            if 'ERROR' in up or 'EXCEPTION' in up or 'TRACEBACK' in up:
                return ln
        return lines[-1]
    except Exception:
        return ''

def _start_comm_center(poll_interval=1.5, driver='stub'):
    """Start the ModernCommCenter thread if not already running."""
    global _CENTER
    if _CENTER is not None:
        return _CENTER
    from zkeco_modern.agent.modern_comm_center import build_and_run_stub
    _CENTER = build_and_run_stub(poll_interval=poll_interval, driver=driver)
    return _CENTER

def _stop_comm_center():
    global _CENTER
    try:
        if _CENTER is not None:
            _CENTER.stop()
    except Exception:
        pass
    _CENTER = None

def _is_server_running(host='127.0.0.1', port=DEFAULT_PORT):
    import socket
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()

def _start_server(host=DEFAULT_HOST, port=DEFAULT_PORT, asgi=False):
    global _SERVER_PROC
    if _SERVER_PROC and _SERVER_PROC.poll() is None:
        return True
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
    # Ensure parent of project folder is on PYTHONPATH so 'import zkeco_modern' works
    try:
        base_dir = Path(settings.BASE_DIR)
        parent_dir = base_dir.parent
        existing = env.get('PYTHONPATH','')
        paths = [p for p in existing.split(os.pathsep) if p]
        # Add parent directory if not present (needed when manage.py resides inside project subfolder)
        if str(parent_dir) not in paths:
            paths.insert(0, str(parent_dir))
        # Also ensure base_dir itself present for relative imports
        if str(base_dir) not in paths:
            paths.insert(0, str(base_dir))
        env['PYTHONPATH'] = os.pathsep.join(paths)
    except Exception:
        pass
    # If ASGI requested, ensure Daphne is available; otherwise fallback and persist
    if asgi:
        try:
            importlib.import_module('daphne')
        except Exception:
            asgi = False
            try:
                _CONFIG.set('tray','server_mode','wsgi')
                _save_config()
            except Exception:
                pass
    cmd = (
        [sys.executable, '-m', 'daphne', '-b', host, '-p', str(port), 'zkeco_config.asgi:application']
        if asgi else
        [sys.executable, str(Path(settings.BASE_DIR) / 'manage.py'), 'runserver', f'{host}:{port}', '--noreload']
    )
    try:
        log_path = _server_log_path()
        logf = open(log_path, 'ab')
        _SERVER_PROC = subprocess.Popen(cmd, env=env, stdout=logf, stderr=subprocess.STDOUT, cwd=str(settings.BASE_DIR))
        logging.info('Server started (%s) pid=%s', 'ASGI' if asgi else 'WSGI', _SERVER_PROC.pid)
        time.sleep(1.0)
        if _SERVER_PROC.poll() is not None:
            err = _read_first_error_from_log()
            try:
                messagebox.showerror('Server start failed', err or 'Server exited immediately. See server.log')
            except Exception:
                pass
            return False
        return True
    except Exception as e:
        logging.error('Server start failed: %s', e)
        # Fallback once from ASGI to WSGI on failure
        if asgi:
            try:
                return _start_server(host=host, port=port, asgi=False)
            except Exception:
                pass
        try:
            err = _read_first_error_from_log()
            detail = err or f'{e.__class__.__name__}: {e}'
            messagebox.showerror('Start Server', detail)
        except Exception:
            pass
        return False

def _stop_server():
    global _SERVER_PROC
    try:
        if _SERVER_PROC and _SERVER_PROC.poll() is None:
            try:
                _SERVER_PROC.send_signal(signal.SIGINT)
                _SERVER_PROC.wait(timeout=5)
            except Exception:
                _SERVER_PROC.terminate()
            try:
                _SERVER_PROC.wait(timeout=5)
            except Exception:
                _SERVER_PROC.kill()
    except Exception:
        pass
    _SERVER_PROC = None

def _open_dashboard():
    try:
        port = int(_CONFIG.get('tray','port', fallback=str(DEFAULT_PORT)))
    except Exception:
        port = DEFAULT_PORT
    webbrowser.open(f'http://127.0.0.1:{port}/agent/dashboard/')

def _shutdown(icon):
    _stop_server()
    try:
        import threading
        _STOP_EVENT.set()
    except Exception:
        pass
    icon.stop()

def _build_menu(icon, host, port):
    # Legacy-like actions -------------------------------------------------
    def _configure_port():
        def _save():
            try:
                new_port = int(entry_port.get())
                mode = mode_var.get()
                _CONFIG.set('tray','port', str(new_port))
                _CONFIG.set('tray','server_mode', mode)
                _save_config()
                messagebox.showinfo('Port','Saved. Restarting server...')
                _stop_server(); _start_server(host=host, port=new_port, asgi=(mode=='asgi'))
            except Exception as e:
                messagebox.showerror('Error', str(e))
        root = tk.Tk(); root.title('Server Configuration'); root.geometry('340x220')
        tk.Label(root,text='Port:', anchor='w').pack(pady=6)
        entry_port = tk.Entry(root)
        entry_port.pack()
        current = _CONFIG.get('tray','port', fallback=str(port))
        entry_port.delete(0,'end'); entry_port.insert(0,current)
        tk.Label(root,text='Mode:', anchor='w').pack(pady=6)
        mode_var = tk.StringVar(value=_CONFIG.get('tray','server_mode', fallback='asgi'))
        frm = tk.Frame(root); frm.pack()
        for val,label in [('asgi','ASGI (WebSockets)'),('wsgi','WSGI')]:
            tk.Radiobutton(frm, text=label, variable=mode_var, value=val).pack(anchor='w')
        tk.Button(root,text='Save', command=_save).pack(pady=12)
        tk.Button(root,text='Close', command=root.destroy).pack()
        root.mainloop()

    def _select_path(key, title):
        root = tk.Tk(); root.withdraw()
        path = filedialog.askdirectory(title=title)
        if path:
            _CONFIG.set('tray', key, path)
            _save_config()
            messagebox.showinfo('Saved', f'{title} set to {path}')
        root.destroy()

    def _restore_db():
        db_path = Path(settings.DATABASES['default']['NAME'])
        engine = settings.DATABASES['default']['ENGINE']
        is_sqlite = engine == 'django.db.backends.sqlite3'
        root = tk.Tk(); root.withdraw()
        backup_file = filedialog.askopenfilename(title='Select backup file', filetypes=[('All','*.*')])
        root.destroy()
        if not backup_file:
            return
        try:
            _stop_server()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if is_sqlite:
                if db_path.exists():
                    shutil.copy2(db_path, db_path.with_suffix(f'.pre_restore_{timestamp}.bak'))
                ok = _progress_copy(Path(backup_file), db_path, title='Restoring SQLite DB')
                if not ok:
                    raise RuntimeError('Copy failed')
            else:
                engine_lower = 'mysql' if 'mysql' in engine else ('postgres' if 'postgresql' in engine else 'unknown')
                if engine_lower == 'mysql':
                    cfg = settings.DATABASES['default']
                    restore_cmd = [
                        'mysql',
                        '-h', cfg.get('HOST') or '127.0.0.1',
                        '-P', str(cfg.get('PORT') or 3306),
                        '-u', cfg.get('USER') or 'root',
                        f"-p{cfg.get('PASSWORD') or ''}",
                        cfg.get('NAME')
                    ]
                    proc = subprocess.Popen(restore_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    with open(backup_file, 'rb') as fsrc:
                        chunk = fsrc.read(8192)
                        while chunk:
                            proc.stdin.write(chunk)
                            chunk = fsrc.read(8192)
                    proc.stdin.close()
                    rc = proc.wait()
                    if rc != 0:
                        raise RuntimeError(proc.stderr.read().decode() or 'MySQL restore failed')
                elif engine_lower == 'postgres':
                    cfg = settings.DATABASES['default']
                    restore_cmd = [
                        'psql',
                        '-h', cfg.get('HOST') or '127.0.0.1',
                        '-p', str(cfg.get('PORT') or 5432),
                        '-U', cfg.get('USER') or 'postgres',
                        cfg.get('NAME')
                    ]
                    env = os.environ.copy()
                    if cfg.get('PASSWORD'):
                        env['PGPASSWORD'] = cfg.get('PASSWORD')
                    proc = subprocess.Popen(restore_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                    with open(backup_file, 'rb') as fsrc:
                        chunk = fsrc.read(8192)
                        while chunk:
                            proc.stdin.write(chunk)
                            chunk = fsrc.read(8192)
                    proc.stdin.close()
                    rc = proc.wait()
                    if rc != 0:
                        raise RuntimeError(proc.stderr.read().decode() or 'Postgres restore failed')
                else:
                    raise RuntimeError('Unsupported engine for restore')
            messagebox.showinfo('Restore','Database restore completed. Restarting server.')
            new_port = int(_CONFIG.get('tray','port', fallback=str(port)))
            mode = _CONFIG.get('tray','server_mode','asgi')
            _start_server(host=host, port=new_port, asgi=(mode=='asgi'))
        except Exception as e:
            messagebox.showerror('Restore', f'Failed: {e}')

    def _license_activation():
        def _save_key():
            key = entry.get().strip()
            if _license_valid(key):
                _CONFIG.set('tray','license_cipher', _encrypt(key))
                _save_config()
                messagebox.showinfo('License','License activated.')
                win.destroy()
            else:
                messagebox.showerror('License','Invalid key or HMAC mismatch.')
        win = tk.Tk(); win.title('License Activation'); win.geometry('420x180')
        tk.Label(win, text='License Key (PROD-EDITION-YYYYMMDD-SEQ-RAND-HMAC8)').pack(pady=8)
        entry = tk.Entry(win, width=40); entry.pack()
        existing = _decrypt(_CONFIG.get('tray','license_cipher', fallback=''))
        if existing:
            entry.insert(0, existing)
        tk.Label(win, text=f'Current: {_masked_license()}').pack(pady=4)
        tk.Button(win, text='Activate', command=_save_key).pack(pady=10)
        tk.Button(win, text='Close', command=win.destroy).pack()
        win.mainloop()

    def _backup_db():
        db_path = Path(settings.DATABASES['default']['NAME'])
        engine = settings.DATABASES['default']['ENGINE']
        is_sqlite = engine == 'django.db.backends.sqlite3'
        backup_dir = Path(_CONFIG.get('tray','backup_dir', fallback=str(Path.home()/ 'zkeco_backups')))
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest = backup_dir / (f'db_{timestamp}.sqlite' if is_sqlite else f'db_{timestamp}.sql')
        try:
            if is_sqlite:
                ok = _progress_copy(db_path, dest, title='Backing Up SQLite')
                if ok:
                    messagebox.showinfo('Backup', f'Backup saved: {dest}')
                else:
                    messagebox.showerror('Backup', 'Backup copy failed')
            else:
                engine_lower = 'mysql' if 'mysql' in engine else ('postgres' if 'postgresql' in engine else 'unknown')
                if engine_lower == 'mysql':
                    cfg = settings.DATABASES['default']
                    dump_cmd = [
                        'mysqldump',
                        '-h', cfg.get('HOST') or '127.0.0.1',
                        '-P', str(cfg.get('PORT') or 3306),
                        '-u', cfg.get('USER') or 'root',
                        f"-p{cfg.get('PASSWORD') or ''}",
                        cfg.get('NAME')
                    ]
                    with open(dest, 'wb') as fdst:
                        proc = subprocess.Popen(dump_cmd, stdout=fdst, stderr=subprocess.PIPE)
                        rc = proc.wait()
                        if rc != 0:
                            raise RuntimeError(proc.stderr.read().decode() or 'mysqldump failed')
                    messagebox.showinfo('Backup', f'MySQL backup saved: {dest}')
                elif engine_lower == 'postgres':
                    cfg = settings.DATABASES['default']
                    dump_cmd = [
                        'pg_dump',
                        '-h', cfg.get('HOST') or '127.0.0.1',
                        '-p', str(cfg.get('PORT') or 5432),
                        '-U', cfg.get('USER') or 'postgres',
                        cfg.get('NAME')
                    ]
                    env = os.environ.copy()
                    if cfg.get('PASSWORD'):
                        env['PGPASSWORD'] = cfg.get('PASSWORD')
                    with open(dest, 'wb') as fdst:
                        proc = subprocess.Popen(dump_cmd, stdout=fdst, stderr=subprocess.PIPE, env=env)
                        rc = proc.wait()
                        if rc != 0:
                            raise RuntimeError(proc.stderr.read().decode() or 'pg_dump failed')
                    messagebox.showinfo('Backup', f'Postgres backup saved: {dest}')
                else:
                    raise RuntimeError('Unsupported engine for backup')
        except Exception as e:
            messagebox.showerror('Backup', f'Failed: {e}')

    legacy_menu = pystray.Menu(
        pystray.MenuItem('Configure Server Port', lambda: threading.Thread(target=_configure_port, daemon=True).start()),
        pystray.MenuItem('Configure Database', lambda: messagebox.showinfo('Configure DB','Using SQLite file at %s' % (Path(settings.BASE_DIR)/'db.sqlite3'))),
        pystray.MenuItem('Database Backup Location', lambda: threading.Thread(target=_select_path, args=('backup_dir','Backup Location'), daemon=True).start()),
        pystray.MenuItem('Video File Location', lambda: threading.Thread(target=_select_path, args=('video_dir','Video Files'), daemon=True).start()),
        pystray.MenuItem('Picture File Location', lambda: threading.Thread(target=_select_path, args=('picture_dir','Picture Files'), daemon=True).start()),
        pystray.MenuItem('Restore Database', lambda: threading.Thread(target=_restore_db, daemon=True).start()),
        pystray.MenuItem('Backup Database', lambda: threading.Thread(target=_backup_db, daemon=True).start()),
        pystray.MenuItem('Start Services', lambda: threading.Thread(target=lambda: (_start_server(host=host, port=port, asgi=True), _start_comm_center()), daemon=True).start()),
        pystray.MenuItem('Restart Services', lambda: threading.Thread(target=lambda: (_stop_server(), _stop_comm_center(), _start_server(host=host, port=port, asgi=_CONFIG.get('tray','server_mode', fallback='asgi')=="asgi"), _start_comm_center()), daemon=True).start()),
        pystray.MenuItem('Stop Services', lambda: threading.Thread(target=lambda: (_stop_server(), _stop_comm_center()), daemon=True).start()),
        pystray.MenuItem('License Activation', lambda: threading.Thread(target=_license_activation, daemon=True).start()),
        pystray.MenuItem('View Server Log', lambda: webbrowser.open(str(Path(getattr(settings, 'BASE_DIR', Path.cwd())) / 'server.log'))),
    )

    return pystray.Menu(
        pystray.MenuItem('Dashboard', lambda: _open_dashboard()),
        pystray.MenuItem('Server WSGI', lambda: threading.Thread(target=_start_server, args=(host, port, False), daemon=True).start()),
        pystray.MenuItem('Server ASGI', lambda: threading.Thread(target=_start_server, args=(host, port, True), daemon=True).start()),
        pystray.MenuItem('Restart Server', lambda: threading.Thread(target=lambda: (_stop_server(), _start_server(host=host, port=port, asgi=_CONFIG.get('tray','server_mode', fallback='asgi')=="asgi")), daemon=True).start()),
        pystray.MenuItem('Stop Server', lambda: threading.Thread(target=_stop_server, daemon=True).start()),
        pystray.MenuItem('CommCenter Start', lambda: threading.Thread(target=_start_comm_center, daemon=True).start()),
        pystray.MenuItem('CommCenter Stop', lambda: threading.Thread(target=_stop_comm_center, daemon=True).start()),
        pystray.MenuItem('Ajutor (RO)', lambda: threading.Thread(target=_show_help_ro, daemon=True).start()),
        pystray.MenuItem('Legacy Menu', legacy_menu),
        pystray.MenuItem('Quit', lambda: _shutdown(icon)),
    )

class Command(BaseCommand):
    help = 'Launch system tray agent with CommCenter + server controls.'

    def add_arguments(self, parser):
        parser.add_argument('--no-server', action='store_true', help='Do not auto start server')
        parser.add_argument('--asgi', action='store_true', help='Auto start Daphne ASGI server (WebSockets)')
        parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Bind host')
        parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Bind port')
        parser.add_argument('--poll', type=float, default=1.5, help='CommCenter poll interval seconds')
        parser.add_argument('--driver', type=str, default='stub', choices=['stub','socket','sdk','auto'], help='CommCenter driver mode')
        parser.add_argument('--no-commcenter', action='store_true', help='Skip auto start of CommCenter')
        parser.add_argument('--status-interval', type=float, default=2.5, help='Tray tooltip update interval seconds')
        parser.add_argument('--auto-restart', action='store_true', help='Auto-restart server if process exits')
        parser.add_argument('--progress-test', action='store_true', help='Show a short demo progress window then exit')
        parser.add_argument('--self-test', action='store_true', help='Run tray diagnostics and exit')

    def handle(self, *args, **options):
        if pystray is None:
            self.stderr.write('pystray not available; install Pillow + pystray.')
            return 1
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
        django.setup()
        _init_logging()
        host = options['host']; port = options['port']
        # Override port/mode from persisted config
        try:
            port_cfg = int(_CONFIG.get('tray','port', fallback=str(port)))
            mode_cfg = _CONFIG.get('tray','server_mode', fallback=('asgi' if options.get('asgi') else 'wsgi'))
            port = port_cfg
            options['asgi'] = (mode_cfg == 'asgi') or options.get('asgi')
        except Exception:
            pass
        # Downgrade to WSGI if ASGI requested but Daphne missing
        if options.get('asgi'):
            try:
                importlib.import_module('daphne')
            except Exception:
                options['asgi'] = False
                self.stdout.write('Daphne not found; starting WSGI instead.')
        if not options.get('no_server') and not _is_server_running(host=host, port=port):
            if _start_server(host=host, port=port, asgi=options.get('asgi')):
                mode = 'ASGI' if options.get('asgi') else 'WSGI'
                self.stdout.write(f'Started {mode} server on {host}:{port}.')
        if not options.get('no_commcenter'):
            threading.Thread(target=_start_comm_center, args=(options['poll'], options['driver']), daemon=True).start()
            self.stdout.write('CommCenter thread starting...')
        if options.get('progress_test'):
            # Demo progress: create temp file ~5MB and copy to another temp location
            import tempfile
            tmp_src = Path(tempfile.gettempdir()) / 'progress_demo_src.bin'
            tmp_dst = Path(tempfile.gettempdir()) / 'progress_demo_dst.bin'
            if not tmp_src.exists():
                with open(tmp_src, 'wb') as f:
                    f.write(os.urandom(5 * 1024 * 1024))
            _progress_copy(tmp_src, tmp_dst, title='Progress Demo Copy')
            self.stdout.write('Progress demo completed.')
        if options.get('self_test'):
            import socket
            # Free port selection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 0)); s.listen(1)
                free_port = s.getsockname()[1]
            ok_srv = _start_server(host='127.0.0.1', port=free_port, asgi=False)
            time.sleep(1.2)
            srv_up = ok_srv and (_SERVER_PROC is not None) and (_SERVER_PROC.poll() is None)
            _stop_server()
            _stop_comm_center()
            cm = _start_comm_center()
            time.sleep(0.8)
            cm_up = cm is not None
            _stop_comm_center()
            try:
                messagebox.showinfo('Diagnostics', f"Server started: {srv_up}\nCommCenter started: {cm_up}\nLog: {Path(getattr(settings, 'BASE_DIR', Path.cwd())) / 'server.log'}")
            except Exception:
                pass
            return 0

        # Status & auto-restart threads
        global _STOP_EVENT
        _STOP_EVENT = threading.Event()

        def _status_loop(icon_ref):
            global _LAST_ICON_STATE
            while not _STOP_EVENT.is_set():
                try:
                    server_running = _SERVER_PROC is not None and _SERVER_PROC.poll() is None
                    center_running = _CENTER is not None
                    tip = []
                    if center_running and _CENTER:
                        total = len(_CENTER.sessions)
                        online = sum(1 for s in _CENTER.sessions.values() if s.connected)
                        tip.append(f"Dispozitive {online}/{total}")
                        tip.append(f"Cicluri {_CENTER.cycles}")
                        tip.append(f"RT {_CENTER.total_rtlog_lines}")
                    tip.append('Server:' + ('PORNEȘTE' if server_running else 'OPRIT'))
                    tip.append('CommCenter:' + ('PORNEȘTE' if center_running else 'OPRIT'))
                    tip.append(f'Licență:{_license_status()}')
                    tip.append('Click dreapta: meniu')
                    icon_ref.title = ' | '.join(tip)
                    state = (server_running, center_running)
                    if state != _LAST_ICON_STATE:
                        color = _choose_icon_color(server_running, center_running)
                        new_img = _build_icon(color=color)
                        if new_img is not None:
                            icon_ref.icon = new_img
                        _LAST_ICON_STATE = state
                except Exception:
                    pass
                _STOP_EVENT.wait(options['status_interval'])

        def _restart_loop():
            while not _STOP_EVENT.is_set():
                try:
                    if options.get('auto_restart'):
                        if (not _SERVER_PROC) or (_SERVER_PROC and _SERVER_PROC.poll() is not None):
                            _start_server(host=host, port=port, asgi=options.get('asgi'))
                    _STOP_EVENT.wait(5.0)
                except Exception:
                    _STOP_EVENT.wait(5.0)

        icon = pystray.Icon('zkeco_access', _build_icon(color=_choose_icon_color(False, False)), 'Access Control', menu=_build_menu(None, host, port))
        icon.menu = _build_menu(icon, host, port)
        threading.Thread(target=_status_loop, args=(icon,), daemon=True).start()
        if options.get('auto_restart'):
            threading.Thread(target=_restart_loop, daemon=True).start()
        self.stdout.write('Tray icon active. Right-click for menu.')
        icon.run()
        self.stdout.write('Tray agent exited.')
        return 0