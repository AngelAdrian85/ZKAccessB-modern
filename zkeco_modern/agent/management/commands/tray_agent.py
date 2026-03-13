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
import json

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
_ADMS_SERVER_PROC = None
_CENTER_THREAD = None
_LAST_ICON_STATE = None  # (server_running, center_running)
_LAST_ICON_STATE = None  # (server_running, center_running)
_LISTENER_PROCS = []  # ACP/Elatec listener processes started by tray agent
_PID_FILE = Path.home() / 'zkeco_tray_agent.pid'
_START_TS = time.time()
_DB_ERR_LAST = {}
_LAST_CONTACT_LAST = {}

# CommCenter defaults (populated from CLI options in Command.handle)
_COMM_DEFAULT_DRIVER = 'auto'
_COMM_DEFAULT_POLL = 0.25
_COMM_LAST_DRIVER = None
_COMM_LAST_BACKEND = None

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 15437
DEFAULT_ADMS_PORT = 8091
CONFIG_PATH = Path.home() / 'zkeco_tray_config.ini'
# Be tolerant to manual edits: allow duplicate keys (keeps last occurrence)
_CONFIG = configparser.ConfigParser(strict=False)
if CONFIG_PATH.exists():
    try:
        # Support UTF-8 BOM (common when edited via PowerShell Out-File)
        _CONFIG.read(CONFIG_PATH, encoding='utf-8-sig')
    except Exception:
        pass
if not _CONFIG.has_section('tray'):
    _CONFIG.add_section('tray')
if not _CONFIG.has_option('tray','port'):
    _CONFIG.set('tray','port', str(DEFAULT_PORT))
if not _CONFIG.has_option('tray','adms_port'):
    _CONFIG.set('tray','adms_port', str(DEFAULT_ADMS_PORT))
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
        # Also echo logs to stdout for terminal visibility
        try:
            sh = logging.StreamHandler(sys.stdout)
            sh.setLevel(logging.INFO)
            sh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            root = logging.getLogger()
            root.addHandler(sh)
        except SystemExit:
            raise
        except Exception:
            pass
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

def _set_icon_title(icon_obj, text: str):
    """Set tray icon tooltip/title with safe truncation for Windows (<=128)."""
    try:
        if not text:
            return
        # Windows NOTIFYICONDATAW szTip max length is 128
        safe = text[:128]
        icon_obj.title = safe
    except Exception:
        try:
            icon_obj.title = 'Access Control'
        except Exception:
            pass

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
            ('Web Server (ASGI)', 'Serverul prim ă cu suport WebSockets. Se pornește automat la deschiderea tray. Dacă lipsește Daphne, cade pe WSGI.'),
            ('CommCenter', 'Serviciul de comunicație cu dispozitivele (polling, sincronizare, cicluri).'),
            ('Admin Menu → Server WSGI', 'Fallback manual la WSGI dacă ASGI are probleme. Fără WebSockets.'),
            ('Configure Server Port', 'Setează portul și modul (ASGI/WSGI) pentru server.'),
            ('Configure Database', 'Afișează detalii despre motorul bazei de date.'),
            ('Database Backup Location', 'Alege directorul pentru copiile de siguranță.'),
            ('Video File Location', 'Definește directorul pentru fișiere video.'),
            ('Picture File Location', 'Definește directorul pentru fișiere imagine (poze utilizatori).'),
            ('Restore Database', 'Restaurează baza de date dintr-un fișier backup.'),
            ('Backup Database', 'Creează o copie de siguranță a bazei de date curente.'),
            ('License Activation', 'Activează licența cu cheia furnizată (validare HMAC).'),
            ('View Server Log', 'Deschide fișierul server.log pentru depanare.'),
            ('Quit', 'Închide agentul tray, oprește serviciile active și distruge procesul.'),
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

def _server_state_path() -> Path:
    """Persist last server PID/port so a new tray_agent can stop orphaned servers.

    This prevents the last used port from remaining bound if tray_agent/server
    crashed or was killed ungracefully.
    """
    try:
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        p = base.parent / 'runtime_logs' / 'last_server_state.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        p = Path('last_server_state.json')
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return p

def _read_server_state() -> dict:
    try:
        p = _server_state_path()
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8')) or {}
    except Exception:
        pass
    return {}

def _write_server_state(pid: int, host: str, port: int, asgi: bool, server_type: str):
    try:
        try:
            from django.utils import timezone

            started_at = timezone.now().isoformat(timespec='seconds')
        except Exception:
            started_at = datetime.now().isoformat(timespec='seconds')
        payload = {
            'pid': int(pid),
            'host': str(host),
            'port': int(port),
            'asgi': bool(asgi),
            'server_type': str(server_type),
            'started_at': started_at,
        }
        p = _server_state_path()
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
        tmp.replace(p)
    except Exception:
        pass

def _windows_get_process_cmdline(pid: int) -> str:
    try:
        cmd = (
            "Get-CimInstance Win32_Process "
            f"-Filter \"ProcessId = {int(pid)}\" "
            "| Select-Object -ExpandProperty CommandLine"
        )
        r = subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
            capture_output=True,
            text=True,
        )
        return (r.stdout or '').strip()
    except Exception:
        return ''

def _looks_like_our_server_cmdline(cmdline: str) -> bool:
    if not cmdline:
        return False
    cl = cmdline.lower()
    # ASGI daphne style
    if ('daphne' in cl) and ('zkeco_config.asgi:application' in cl):
        return True
    # Django runserver fallback style
    if ('manage.py' in cl) and ('runserver' in cl) and ('zkeco_config.settings' in cl or 'zkeco_config' in cl):
        return True
    return False

def _looks_like_our_listener_cmdline(cmdline: str) -> bool:
    if not cmdline:
        return False
    cl = cmdline.lower()
    return any(name in cl for name in ('card_reader_acp.py', 'card_reader_elatec.py', 'wiegand_listener.py'))

def _windows_listening_pids_on_port(port: int) -> set:
    pids = set()
    try:
        r = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True)
        for line in (r.stdout or '').splitlines():
            if 'LISTENING' not in line.upper():
                continue
            if f':{int(port)}' not in line:
                continue
            parts = line.split()
            if not parts:
                continue
            pid = parts[-1]
            if pid.isdigit() and pid != '0':
                pids.add(int(pid))
    except Exception:
        pass
    return pids

def _stop_our_server_on_port(port: int):
    """Stop ZKAccessB server processes listening on a given port.

    Safety: only kills processes whose command line matches our server.
    """
    try:
        if os.name != 'nt':
            return
        port = int(port)
        listen_pids = _windows_listening_pids_on_port(port)
        for pid in sorted(listen_pids):
            try:
                if pid == os.getpid():
                    continue
                cmdline = _windows_get_process_cmdline(pid)
                if not _looks_like_our_server_cmdline(cmdline):
                    continue
                subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F', '/T'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logging.info('Stopped server pid=%s on port %s', pid, port)
            except Exception:
                pass
    except Exception:
        pass

def _stop_our_listener_on_port(port: int):
    """Stop our TCP listener processes on a given port."""
    try:
        if os.name != 'nt':
            return
        port = int(port)
        listen_pids = _windows_listening_pids_on_port(port)
        for pid in sorted(listen_pids):
            try:
                if pid == os.getpid():
                    continue
                cmdline = _windows_get_process_cmdline(pid)
                if not _looks_like_our_listener_cmdline(cmdline):
                    continue
                subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F', '/T'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logging.info('Stopped listener pid=%s on port %s', pid, port)
            except Exception:
                pass
    except Exception:
        pass

def _stop_orphan_server_from_state():
    """Stop previous server instance (if any) recorded in last_server_state.json.

    Uses a safety check on command line so we don't kill unrelated processes.
    """
    try:
        st = _read_server_state() or {}
        port = st.get('port')
        pid = st.get('pid')
        if not port:
            return
        try:
            port = int(port)
        except Exception:
            return
        # Stop anything that looks like our server on the last-used port.
        _stop_our_server_on_port(port)

        listen_pids = _windows_listening_pids_on_port(port) if os.name == 'nt' else set()

        candidate_pids = []
        if pid:
            try:
                candidate_pids.append(int(pid))
            except Exception:
                pass
        if not candidate_pids:
            candidate_pids = list(listen_pids)

        for cand in candidate_pids:
            try:
                # If we can see who is listening, require the PID to actually own the port
                if listen_pids and cand not in listen_pids:
                    continue
                cmdline = _windows_get_process_cmdline(cand) if os.name == 'nt' else ''
                if os.name == 'nt' and not _looks_like_our_server_cmdline(cmdline):
                    continue
                subprocess.run(
                    ['taskkill', '/PID', str(cand), '/F', '/T'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logging.info('Stopped previous server pid=%s on port %s', cand, port)
            except Exception:
                pass
    except Exception:
        pass

def _tray_status_path() -> Path:
    try:
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        return base.parent / 'tray_status.json'
    except Exception:
        return Path('tray_status.json')

def _read_tray_status() -> dict:
    """Read tray_status.json written by tray_launch.ps1. Returns {} if missing/invalid.
    Expected keys: acp (ON/OPRIT), elatec (ON/OPRIT), server (PORNESTE/PORNIT/OPRIT), color (green/yellow/red).
    """
    try:
        p = _tray_status_path()
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8-sig')) or {}
    except Exception:
        pass
    return {}

def _zkemkeeper_heartbeat_path() -> Path:
    return Path.home() / 'zkeco_reader_heartbeat_zkemkeeper.json'

def _read_zkemkeeper_heartbeat() -> dict:
    try:
        p = _zkemkeeper_heartbeat_path()
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8-sig')) or {}
    except Exception:
        pass
    return {}

def _zkemkeeper_process_running() -> bool:
    try:
        out = subprocess.run(
            [
                'powershell',
                '-ExecutionPolicy',
                'Bypass',
                '-Command',
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*zkemkeeper_event_bridge.ps1*' -or $_.CommandLine -like '*zkemkeeper_event_bridge.vbs*' } | Select-Object -First 1 -ExpandProperty ProcessId",
            ],
            capture_output=True,
            text=True,
        )
        return bool((out.stdout or '').strip())
    except Exception:
        return False


def _wiegand_heartbeat_path() -> Path:
    return Path.home() / 'zkeco_reader_heartbeat_wiegand.json'


def _wiegand_trace_path() -> Path:
    try:
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        return base.parent / 'tmp_wiegand_listener_trace.jsonl'
    except Exception:
        return Path('tmp_wiegand_listener_trace.jsonl')


def _read_last_jsonl_event(path: Path, event_name: str) -> dict:
    try:
        if not path.exists():
            return {}
        text = path.read_text(encoding='utf-8', errors='ignore')
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if str(payload.get('event') or '').strip() == event_name:
                return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    return {}


def _collect_capture_health(st: dict) -> dict:
    try:
        cfg = _load_readers_cfg() or {}
    except Exception:
        cfg = {}
    wiegand_cfg = cfg.get('wiegand') or {}
    wiegand_enabled = bool(st.get('wiegand_enabled', wiegand_cfg.get('enabled', False)))
    wiegand_listener = str(st.get('wiegand') or 'OPRIT').strip().upper()
    heartbeat = {}
    try:
        hb_path = _wiegand_heartbeat_path()
        if hb_path.exists():
            heartbeat = json.loads(hb_path.read_text(encoding='utf-8-sig')) or {}
    except Exception:
        heartbeat = {}
    last_frame = _read_last_jsonl_event(_wiegand_trace_path(), 'frame_parsed')

    raw_capture_last_frame_ts = last_frame.get('ts')
    heartbeat_ts = heartbeat.get('ts') if isinstance(heartbeat, dict) else None
    heartbeat_source = str((heartbeat or {}).get('source') or '').strip().lower()
    try:
        if heartbeat_source == 'frame' and heartbeat_ts not in (None, ''):
            if raw_capture_last_frame_ts in (None, '') or float(heartbeat_ts) > float(raw_capture_last_frame_ts):
                raw_capture_last_frame_ts = heartbeat_ts
    except Exception:
        pass

    raw_capture_last_frame_age_s = None
    try:
        if raw_capture_last_frame_ts not in (None, ''):
            raw_capture_last_frame_age_s = max(0, int(time.time() - float(raw_capture_last_frame_ts)))
    except Exception:
        raw_capture_last_frame_age_s = None

    if not wiegand_enabled:
        raw_capture_state = 'disabled'
        raw_capture_message = 'W26 dezactivat'
    elif wiegand_listener != 'ON':
        raw_capture_state = 'listener_down'
        raw_capture_message = 'W26 oprit; nu există captură brută'
    elif raw_capture_last_frame_age_s is None:
        raw_capture_state = 'absent'
        raw_capture_message = 'W26 pornit, dar nu a capturat niciun frame brut'
    elif raw_capture_last_frame_age_s > 120:
        raw_capture_state = 'absent'
        raw_capture_message = f'W26 pornit, dar ultimul frame brut are {raw_capture_last_frame_age_s}s'
    else:
        raw_capture_state = 'active'
        raw_capture_message = f'W26 activ; ultimul frame brut are {raw_capture_last_frame_age_s}s'

    zkem_enabled = bool(st.get('zkemkeeper_enabled', False))
    zkem_label = str(st.get('zkemkeeper') or '').strip().upper()
    zkem_status = str(st.get('zkemkeeper_status') or '').strip().lower()
    zkem_message = str(st.get('zkemkeeper_message') or '').strip()
    if not zkem_enabled:
        zkem_capture_state = 'disabled'
    elif zkem_label == 'EROARE' or zkem_status == 'error':
        zkem_capture_state = 'error'
    elif zkem_label == 'ON':
        zkem_capture_state = 'active'
    elif zkem_label:
        zkem_capture_state = 'inactive'
    else:
        zkem_capture_state = 'unknown'

    warnings = []
    summary_state = 'ok'
    if raw_capture_state in ('listener_down', 'absent'):
        warnings.append('raw capture absent')
        summary_state = 'warn'
    if zkem_capture_state == 'error':
        warnings.append('zkemkeeper error')
        summary_state = 'err'
    if warnings:
        summary_message = '; '.join(warnings)
    elif raw_capture_state == 'disabled' and zkem_capture_state == 'disabled':
        summary_state = 'disabled'
        summary_message = 'capture disabled'
    else:
        summary_message = 'capture active'

    heartbeat_age_s = None
    try:
        if heartbeat_ts not in (None, ''):
            heartbeat_age_s = max(0, int(time.time() - float(heartbeat_ts)))
    except Exception:
        heartbeat_age_s = None

    return {
        'summary_state': summary_state,
        'summary_message': summary_message,
        'warnings': warnings,
        'raw_capture_state': raw_capture_state,
        'raw_capture_message': raw_capture_message,
        'raw_capture_last_frame_ts': raw_capture_last_frame_ts,
        'raw_capture_last_frame_age_s': raw_capture_last_frame_age_s,
        'wiegand_enabled': wiegand_enabled,
        'wiegand_listener': wiegand_listener,
        'wiegand_port': wiegand_cfg.get('port'),
        'wiegand_heartbeat_age_s': heartbeat_age_s,
        'zkemkeeper_state': zkem_capture_state,
        'zkemkeeper_label': zkem_label or 'UNKNOWN',
        'zkemkeeper_error': zkem_capture_state == 'error',
        'zkemkeeper_message': zkem_message,
    }

def _collect_zkemkeeper_status(st_prev: dict | None = None) -> dict:
    st_prev = st_prev or {}
    data = {k: v for k, v in st_prev.items() if k.startswith('zkemkeeper')}
    hb = _read_zkemkeeper_heartbeat()
    if hb:
        hb_status = str(hb.get('status') or '').strip().lower()
        if hb_status in ('connected', 'event'):
            state = 'ON'
        elif hb_status == 'error':
            state = 'EROARE'
        else:
            state = data.get('zkemkeeper', 'PORNESTE')
        data.update(
            {
                'zkemkeeper': state,
                'zkemkeeper_status': hb_status,
                'zkemkeeper_message': hb.get('message') or data.get('zkemkeeper_message'),
                'zkemkeeper_target': hb.get('ip') and f"{hb.get('ip')}:{hb.get('port')}" or data.get('zkemkeeper_target', ''),
                'zkemkeeper_prog_id': hb.get('prog_id') or data.get('zkemkeeper_prog_id', ''),
                'zkemkeeper_dump_file': hb.get('dump_file') or data.get('zkemkeeper_dump_file', ''),
                'zkemkeeper_last_event': hb.get('last_event') or '',
                'zkemkeeper_last_card': hb.get('last_card') or '',
                'zkemkeeper_last_pin': hb.get('last_pin') or '',
                'zkemkeeper_event_count': hb.get('event_count') or 0,
                'zkemkeeper_connected_since': hb.get('connected_since') or '',
                'zkemkeeper_registered_events': hb.get('registered_events') or [],
                'zkemkeeper_enabled': bool(st_prev.get('zkemkeeper_enabled', True)),
            }
        )
    elif data.get('zkemkeeper_enabled'):
        if _zkemkeeper_process_running():
            data.setdefault('zkemkeeper', 'PORNESTE')
        elif data.get('zkemkeeper') == 'ON':
            data['zkemkeeper'] = 'OPRIT'
    return data

def _write_tray_status(acp_on: bool, elatec_on: bool, server_state: str, center_on: bool, wiegand_on: bool = False):
    """Write tray_status.json while preserving enabled flags.
    Treat disabled readers as satisfied for color semantics.
    server_state in { 'PORNIT', 'PORNESTE', 'OPRIT' }.
    """
    try:
        acp_on = bool(acp_on)
        elatec_on = bool(elatec_on)
        center_on = bool(center_on)
        srv = (server_state or '').upper()
        if srv not in ('PORNIT','PORNESTE','OPRIT'):
            srv = 'OPRIT'
        # Preserve existing enabled flags if present
        st_prev = _read_tray_status()
        acp_enabled = bool(st_prev.get('acp_enabled', True))
        elatec_enabled = bool(st_prev.get('elatec_enabled', True))
        wiegand_enabled = bool(st_prev.get('wiegand_enabled', False))
        # Color computation with enabled flags
        all_ok = (srv == 'PORNIT') and center_on and ((not acp_enabled) or acp_on) and ((not elatec_enabled) or elatec_on) and ((not wiegand_enabled) or wiegand_on)
        any_running = (srv == 'PORNIT') or center_on or (acp_enabled and acp_on) or (elatec_enabled and elatec_on) or (wiegand_enabled and wiegand_on)
        color = 'green' if all_ok else ('yellow' if any_running else 'red')
        data = {
            'acp': 'ON' if acp_on else 'OPRIT',
            'elatec': 'ON' if elatec_on else 'OPRIT',
            'wiegand': 'ON' if wiegand_on else 'OPRIT',
            'commcenter': 'ON' if center_on else 'OPRIT',
            'commcenter_driver': _COMM_LAST_DRIVER or _COMM_DEFAULT_DRIVER,
            'commcenter_backend': _COMM_LAST_BACKEND,
            'server': srv,
            'acp_enabled': acp_enabled,
            'elatec_enabled': elatec_enabled,
            'wiegand_enabled': wiegand_enabled,
            'color': color,
        }
        # Preserve blocked flags and other important UI-controlled keys from previous file
        try:
            for k, v in st_prev.items():
                if k.endswith('_blocked') or k.startswith('cmd_'):
                    # keep blocked flags and transient cmd_* flags if present
                    data[k] = v
        except Exception:
            pass
        try:
            data.update(_collect_zkemkeeper_status(st_prev))
        except Exception:
            pass
        try:
            capture_health = _collect_capture_health(data)
            data['capture_health'] = capture_health
            data['raw_capture_state'] = capture_health.get('raw_capture_state')
            data['raw_capture_message'] = capture_health.get('raw_capture_message')
            data['raw_capture_last_frame_age_s'] = capture_health.get('raw_capture_last_frame_age_s')
        except Exception:
            pass
        p = _tray_status_path()
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
        tmp.replace(p)
    except Exception:
        pass

def _update_tray_status_fields(updates: dict):
    """Merge arbitrary fields into existing tray_status.json and write atomically."""
    try:
        st = _read_tray_status() or {}
        for k, v in (updates or {}).items():
            st[k] = v
        p = _tray_status_path()
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(st, ensure_ascii=False), encoding='utf-8')
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
        tmp.replace(p)
    except Exception:
        logging.exception('Failed to update tray_status fields')

def _set_device_online_flag(scanner: str, online: bool):
    """Safely set DeviceStatus.online for devices matching scanner type.
    Tries ORM update first; falls back to direct SQL. Works for sqlite/mysql/postgres.
    """
    # ORM-first path (preferred). Also updates Device.last_contact as a throttled heartbeat
    # when the reader process is alive, so the dashboard has a persisted 'last seen'.
    try:
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Q
        from agent.models import Device, DeviceStatus
        from agent.ws import broadcast_device_status

        now = timezone.now()
        dev_ids = list(
            Device.objects.filter(scanner_type=str(scanner), scanner_linked=True, enabled=True)
            .values_list('id', flat=True)
        )
        if not dev_ids:
            return

        COOLDOWN_SECONDS = 5.0
        if online:
            # Only update DeviceStatus rows that actually change state.
            DeviceStatus.objects.filter(device_id__in=dev_ids).exclude(online=True).update(
                online=True, updated_at=now
            )
        else:
            cutoff = now - timedelta(seconds=COOLDOWN_SECONDS)
            DeviceStatus.objects.filter(device_id__in=dev_ids).exclude(online=False).filter(
                Q(updated_at__lte=cutoff) | Q(updated_at__isnull=True)
            ).update(online=False, updated_at=now)

        # Heartbeat for 'live process' state.
        if online:
            try:
                interval_s = float(os.getenv('TRAY_LAST_CONTACT_INTERVAL', '30'))
            except Exception:
                interval_s = 30.0
            try:
                now_ts = time.time()
                last_ts = float(_LAST_CONTACT_LAST.get(str(scanner), 0.0) or 0.0)
                if interval_s <= 0 or (now_ts - last_ts) >= interval_s:
                    Device.objects.filter(id__in=dev_ids).update(last_contact=now)
                    _LAST_CONTACT_LAST[str(scanner)] = now_ts
            except Exception:
                pass

        # Broadcast current status snapshot (use last_contact when present)
        try:
            for ds in DeviceStatus.objects.select_related('device').filter(device_id__in=dev_ids):
                dev = getattr(ds, 'device', None)
                last_seen = None
                try:
                    last_seen = getattr(dev, 'last_contact', None) or getattr(ds, 'updated_at', None)
                except Exception:
                    last_seen = getattr(ds, 'updated_at', None)
                ua = None
                try:
                    ua = last_seen.isoformat() if last_seen is not None and hasattr(last_seen, 'isoformat') else (str(last_seen) if last_seen is not None else None)
                except Exception:
                    ua = None
                broadcast_device_status(
                    int(ds.device_id),
                    bool(ds.online),
                    door_state=getattr(ds, 'door_state', None),
                    serial=getattr(dev, 'serial_number', None) if dev else None,
                    updated_at=ua,
                )
        except Exception:
            pass
        return
    except Exception as e:
        try:
            logging.getLogger(__name__).exception('ORM DeviceStatus update failed for scanner=%s; falling back to SQL: %s', scanner, e)
        except Exception:
            pass

    try:
        from django.db import connection
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime
        val = 1 if online else 0
        esc = str(scanner).replace("'", "''")
        cur = connection.cursor()
        # Small cooldown: avoid stomping a very recent user-initiated change.
        COOLDOWN_SECONDS = 5.0
        try:
            # Retrieve candidate rows and their timestamps
            vendor = getattr(connection, 'vendor', '')
            if vendor == 'sqlite':
                sel = ("SELECT agent_device.id, agent_devicestatus.online, agent_devicestatus.updated_at "
                       "FROM agent_device JOIN agent_devicestatus ON agent_devicestatus.device_id = agent_device.id "
                       f"WHERE agent_device.scanner_type = '{esc}' AND agent_device.scanner_linked=1 AND agent_device.enabled=1")
                cur.execute(sel)
            else:
                sel = ("SELECT agent_device.id, agent_devicestatus.online, agent_devicestatus.updated_at "
                       "FROM agent_device JOIN agent_devicestatus ON agent_devicestatus.device_id = agent_device.id "
                       f"WHERE agent_device.scanner_type = '{esc}' AND agent_device.scanner_linked = true AND agent_device.enabled = true")
                cur.execute(sel)
            rows = cur.fetchall() or []
            ids_to_update = []
            now_ts = time.time()
            for did, online_db, updated_at in rows:
                try:
                    online_db_bool = bool(online_db)
                except Exception:
                    online_db_bool = bool(online_db)
                # Only consider rows where the online flag actually differs
                if online_db_bool == bool(val):
                    continue
                # If changing to offline, skip rows updated very recently
                if val == 0 and updated_at is not None:
                    try:
                        # Normalize updated_at to timestamp seconds
                        if isinstance(updated_at, str):
                            # Attempt parse ISO-like string
                            try:
                                import datetime as _dt
                                from django.utils.dateparse import parse_datetime
                                d = parse_datetime(updated_at)
                                if d is not None:
                                    updated_ts = d.timestamp()
                                else:
                                    updated_ts = None
                            except Exception:
                                updated_ts = None
                        else:
                            updated_ts = updated_at.timestamp() if hasattr(updated_at, 'timestamp') else None
                        if updated_ts is not None and (now_ts - float(updated_ts)) < COOLDOWN_SECONDS:
                            # Skip this row to avoid overwriting recent user action
                            continue
                    except Exception:
                        pass
                ids_to_update.append(did)

            if not ids_to_update:
                logging.info('No DeviceStatus rows to update for scanner=%s after cooldown filter', scanner)
                # proceed to broadcasting current states below
            else:
                # Perform update for selected device ids
                id_list = ','.join(str(int(x)) for x in ids_to_update)
                updated_at_now = timezone.now()
                try:
                    if vendor == 'sqlite':
                        upd = (f"UPDATE agent_devicestatus SET online=%s, updated_at=%s "
                               f"WHERE device_id IN ({id_list})")
                        cur.execute(upd, [val, updated_at_now])
                    else:
                        upd = (f"UPDATE agent_devicestatus SET online = %s, updated_at = %s WHERE device_id IN ({id_list})")
                        cur.execute(upd, [val, updated_at_now])
                    try:
                        connection.commit()
                    except Exception:
                        pass
                    logging.info('Set DeviceStatus.online=%s for scanner=%s (rows affected=%s)', val, scanner, getattr(cur, 'rowcount', 'unknown'))
                except Exception as e:
                    logging.error('SQL update failed while setting DeviceStatus for %s: %s', scanner, e)
            # Broadcast status for affected devices via channels if available
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                # retrieve affected device ids and current door_state/serial
                cur2 = connection.cursor()
                if vendor == 'sqlite':
                    sel = ("SELECT agent_device.id, agent_device.serial_number, agent_devicestatus.door_state, agent_devicestatus.online, agent_devicestatus.updated_at "
                           "FROM agent_device JOIN agent_devicestatus ON agent_devicestatus.device_id = agent_device.id "
                           f"WHERE agent_device.scanner_type = '{esc}' AND agent_device.scanner_linked=1 AND agent_device.enabled=1")
                    cur2.execute(sel)
                else:
                    sel = ("SELECT agent_device.id, agent_device.serial_number, agent_devicestatus.door_state, agent_devicestatus.online, agent_devicestatus.updated_at "
                           "FROM agent_device JOIN agent_devicestatus ON agent_devicestatus.device_id = agent_device.id "
                           f"WHERE agent_device.scanner_type = '{esc}' AND agent_device.scanner_linked = true AND agent_device.enabled = true")
                    cur2.execute(sel)
                rows = cur2.fetchall() or []
                try:
                    from agent.ws import broadcast_device_status
                    for did, serial, door_state, online_db, updated_at in rows:
                            try:
                                # Normalize updated_at to an *aware* ISO string.
                                # Some DB drivers return naive datetimes; JS will misinterpret them.
                                ua = None
                                try:
                                    import datetime as _dt

                                    def _to_aware_dt(v):
                                        if v is None:
                                            return None
                                        if isinstance(v, _dt.datetime):
                                            dt = v
                                        elif isinstance(v, (int, float)):
                                            dt = _dt.datetime.fromtimestamp(float(v), tz=_dt.timezone.utc)
                                        else:
                                            dt = parse_datetime(str(v))
                                            if dt is None:
                                                return None
                                        if timezone.is_naive(dt):
                                            # Assume UTC to match Django DB timezone handling.
                                            dt = timezone.make_aware(dt, timezone=timezone.utc)
                                        return dt

                                    # If this device was updated in this cycle, prefer the known UTC timestamp.
                                    if 'updated_at_now' in locals() and did in (ids_to_update or []):
                                        dt_aware = updated_at_now
                                    else:
                                        dt_aware = _to_aware_dt(updated_at)
                                    ua = dt_aware.isoformat() if dt_aware is not None else None
                                except Exception:
                                    ua = None
                                try:
                                    import logging
                                    logging.getLogger(__name__).info(
                                        'tray_agent (management cmd) -> broadcasting device=%s online=%s updated_at=%s serial=%s',
                                        did, bool(online_db), ua, serial
                                    )
                                except Exception:
                                    pass
                                try:
                                    print('tray_agent (management cmd) -> broadcasting device=%s online=%s updated_at=%s serial=%s' % (did, bool(online_db), ua, serial), flush=True)
                                except Exception:
                                    pass
                                broadcast_device_status(did, bool(online_db), door_state=door_state, serial=serial, updated_at=ua)
                            except Exception:
                                pass
                except Exception:
                    pass
            except Exception:
                pass
            return
        except Exception as e:
            # Throttle noisy DB errors to once per minute per scanner
            try:
                now = time.time()
                last = _DB_ERR_LAST.get(scanner, 0)
                if (now - last) > 60:
                    logging.error('SQL update failed for DeviceStatus.online for %s: %s', scanner, e)
                    _DB_ERR_LAST[scanner] = now
            except Exception:
                logging.error('SQL update failed for DeviceStatus.online for %s: %s', scanner, e)
            return
    except Exception as e:
        logging.error('DB connection failed while setting DeviceStatus.online for %s: %s', scanner, e)
        return

def _remove_heartbeat(scanner: str):
    try:
        name = 'acp' if scanner == 'acp' else 'elatec'
        hb = Path.home() / f'zkeco_reader_heartbeat_{name}.json'
        if hb.exists():
            try:
                hb.unlink()
            except Exception:
                pass
    except Exception:
        pass

def _set_blocked(name: str, value: bool):
    try:
        st = _read_tray_status()
        prev = bool(st.get(f'{name}_blocked', False))
        val = bool(value)
        if prev == val:
            return
        st[f'{name}_blocked'] = val
        # when blocking, set a cmd_stop marker for other agents
        if val:
            st[f'cmd_stop_{name}'] = True
        else:
            # remove transient stop command when unblocking
            if f'cmd_stop_{name}' in st:
                st.pop(f'cmd_stop_{name}', None)
        # If operator blocks a reader, ensure the enabled flag remains True
        # unless the reader is explicitly disabled in scripts/card_readers.json
        try:
            if val:
                cfg = _read_listeners_config()
                cfg_entry = (cfg or {}).get(name) or {}
                cfg_disabled = (cfg_entry.get('enabled') is False)
                if not cfg_disabled:
                    st[f'{name}_enabled' if name+'_'+'enabled' in st else f'{name}_enabled'] = True
                else:
                    # keep config-driven disabled state
                    pass
        except Exception:
            pass
        _update_tray_status_fields(st)
        logging.info('%s_blocked set to %s', name, val)
        try:
            _recompute_status_once()
        except Exception:
            pass
    except Exception:
        logging.exception('Error setting blocked flag')

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

def _start_comm_center(poll_interval=None, driver=None):
    """Start the ModernCommCenter thread if not already running."""
    global _CENTER
    global _COMM_LAST_DRIVER, _COMM_LAST_BACKEND
    if _CENTER is not None:
        return _CENTER
    from agent.modern_comm_center import build_and_run_stub

    poll = _COMM_DEFAULT_POLL if poll_interval is None else float(poll_interval)
    drv = _COMM_DEFAULT_DRIVER if (driver is None or driver == '') else str(driver)

    # Best-effort: report the effective backend used by auto selection.
    backend = None
    if drv == 'auto':
        try:
            from agent.plcommpro_bridge import bridge_available

            backend = 'plcommpro' if bridge_available() else None
        except Exception:
            backend = None
    else:
        backend = drv

    _COMM_LAST_DRIVER = drv
    _COMM_LAST_BACKEND = backend

    _CENTER = build_and_run_stub(poll_interval=poll, driver=drv)
    return _CENTER

def _stop_comm_center():
    global _CENTER
    try:
        if _CENTER is not None:
            _CENTER.stop()
    except Exception:
        pass
    _CENTER = None

def _read_listeners_config():
    try:
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        cfg = (base.parent / 'scripts' / 'card_readers.json')
        if cfg.exists():
            import json
            return json.loads(cfg.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}

def _start_listener(name: str):
    """Start a single listener based on config."""
    global _LISTENER_PROCS
    try:
        try:
            if _listener_running(name):
                logging.info('Listener %s already running; skipping duplicate start', name)
                return
        except Exception:
            pass
        # Respect explicit UI block flags to avoid unwanted auto-start
        try:
            st = _read_tray_status()
            if st.get(f'{name}_blocked', False):
                logging.info('Start suppressed for %s due to %s_blocked flag', name, name)
                return
        except Exception:
            pass
        cfg = _read_listeners_config()
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        py = sys.executable
        if name == 'acp':
            acp = cfg.get('acp', {'enabled': True, 'port': 9001})
            if acp.get('enabled', True):
                script = str(base.parent / 'scripts' / 'card_reader_acp.py')
                if Path(script).exists():
                    port = str(acp.get('port', 9001))
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen([py, script, port], cwd=str(base.parent), creationflags=cf)
                    _LISTENER_PROCS.append(p)
                    try:
                        # mark devices online for this scanner when listener started
                        _set_device_online_flag(name, True)
                    except Exception:
                        pass
        elif name == 'elatec':
            el = cfg.get('elatec', {'enabled': True, 'port': 'COM3'})
            if el.get('enabled', True):
                script = str(base.parent / 'scripts' / 'card_reader_elatec.py')
                if Path(script).exists():
                    com = str(el.get('port', 'COM3'))
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen([py, script, com], cwd=str(base.parent), creationflags=cf)
                    logging.info('Starting listener process: %s %s', script, port if name=='acp' else com)
                    _LISTENER_PROCS.append(p)
        elif name == 'wiegand':
            wg = cfg.get('wiegand', {'enabled': False, 'listen_host': '0.0.0.0', 'port': 9002, 'format_name': 'Wiegand 26', 'source': 'w26-hardware-tap'})
            if wg.get('enabled', False):
                script = str(base.parent / 'scripts' / 'wiegand_listener.py')
                if Path(script).exists():
                    listen_host = str(wg.get('listen_host', '0.0.0.0') or '0.0.0.0')
                    listen_port = str(wg.get('port', 9002) or 9002)
                    args = [
                        py,
                        script,
                        '--server-url', f"http://127.0.0.1:{int(_CONFIG.get('tray', 'port', fallback=str(DEFAULT_PORT)))}",
                        '--listen-host', listen_host,
                        '--listen-port', listen_port,
                    ]
                    if wg.get('format_name'):
                        args.extend(['--format-name', str(wg.get('format_name') or '').strip()])
                    if wg.get('format_id'):
                        args.extend(['--format-id', str(wg.get('format_id') or '').strip()])
                    if wg.get('device_id') not in (None, ''):
                        args.extend(['--device-id', str(wg.get('device_id') or '').strip()])
                    if wg.get('door_id') not in (None, ''):
                        args.extend(['--door-id', str(wg.get('door_id') or '').strip()])
                    if wg.get('door_pk') not in (None, ''):
                        args.extend(['--door-pk', str(wg.get('door_pk') or '').strip()])
                    if wg.get('source'):
                        args.extend(['--source', str(wg.get('source') or '').strip()])
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen(args, cwd=str(base.parent), creationflags=cf)
                    logging.info('Starting listener process: %s %s:%s', script, listen_host, listen_port)
                    _LISTENER_PROCS.append(p)
    except Exception:
        pass

def _stop_listener(name: str):
    """Stop processes matching a listener script."""
    target = {
        'acp': 'card_reader_acp.py',
        'elatec': 'card_reader_elatec.py',
        'wiegand': 'wiegand_listener.py',
    }.get(name, '')
    if not target:
        return
    try:
        logging.info('Stopping listener: %s', name)
        # Stop tracked ones
        global _LISTENER_PROCS
        keep = []
        for p in _LISTENER_PROCS:
            try:
                if p and (p.poll() is None):
                    p.terminate()
                    try:
                        p.wait(timeout=2)
                    except Exception:
                        p.kill()
                # Do not keep terminated
            except Exception:
                pass
        _LISTENER_PROCS = keep
        # Kill any OS processes by script name, retrying if they reappear
        try:
            attempts = 3
            remaining = None
            for attempt in range(attempts):
                out = subprocess.run(['powershell','-ExecutionPolicy','Bypass','-Command', f"Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -match 'python|pyw') -and $_.CommandLine -like '*{target}*' }} | Select-Object -ExpandProperty ProcessId"], capture_output=True, text=True)
                pids = [l.strip() for l in (out.stdout or '').splitlines() if l.strip()]
                if not pids:
                    remaining = []
                    break
                logging.warning('Processes still present for %s after stop (attempt %d): %s. Attempting forced kill.', target, attempt + 1, pids)
                for pid in pids:
                    try:
                        subprocess.run(['taskkill','/F','/PID', pid, '/T'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass
                time.sleep(0.5 + attempt * 0.2)
            # final check
            out = subprocess.run(['powershell','-ExecutionPolicy','Bypass','-Command', f"Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -match 'python|pyw') -and $_.CommandLine -like '*{target}*' }} | Select-Object -ExpandProperty ProcessId"], capture_output=True, text=True)
            remaining = [l.strip() for l in (out.stdout or '').splitlines() if l.strip()]
            if remaining:
                logging.warning('Processes still present for %s after final stop attempts: %s', target, remaining)
        except Exception:
            pass
        # Ensure heartbeat file removed and DB set to offline for this scanner
        try:
            _remove_heartbeat(name)
        except Exception:
            pass
        try:
            _set_device_online_flag(name, False)
        except Exception:
            pass
    except Exception:
        pass

def _start_listeners():
    global _LISTENER_PROCS
    try:
        # If UI or tray explicitly blocked a listener, do not start it here
        st = _read_tray_status()
        cfg = _read_listeners_config()
        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        py = sys.executable
        # ACP
        try:
            acp = cfg.get('acp', {'enabled': True, 'port': 9001})
            if acp.get('enabled', True) and not bool(st.get('acp_blocked', False)):
                script = str(base.parent / 'scripts' / 'card_reader_acp.py')
                if Path(script).exists():
                    port = str(acp.get('port', 9001))
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen([py, script, port], cwd=str(base.parent), creationflags=cf)
                    _LISTENER_PROCS.append(p)
        except Exception:
            pass
        # Elatec
        try:
            el = cfg.get('elatec', {'enabled': True, 'port': 'COM3'})
            if el.get('enabled', True) and not bool(st.get('elatec_blocked', False)):
                script = str(base.parent / 'scripts' / 'card_reader_elatec.py')
                if Path(script).exists():
                    com = str(el.get('port', 'COM3'))
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen([py, script, com], cwd=str(base.parent), creationflags=cf)
                    _LISTENER_PROCS.append(p)
        except Exception:
            pass
        # Wiegand
        try:
            wg = cfg.get('wiegand', {'enabled': False, 'listen_host': '0.0.0.0', 'port': 9002})
            if wg.get('enabled', False) and not bool(st.get('wiegand_blocked', False)):
                script = str(base.parent / 'scripts' / 'wiegand_listener.py')
                if Path(script).exists():
                    args = [
                        py,
                        script,
                        '--server-url', f"http://127.0.0.1:{int(_CONFIG.get('tray', 'port', fallback=str(DEFAULT_PORT)))}",
                        '--listen-host', str(wg.get('listen_host', '0.0.0.0') or '0.0.0.0'),
                        '--listen-port', str(wg.get('port', 9002) or 9002),
                    ]
                    if wg.get('format_name'):
                        args.extend(['--format-name', str(wg.get('format_name') or '').strip()])
                    if wg.get('format_id'):
                        args.extend(['--format-id', str(wg.get('format_id') or '').strip()])
                    if wg.get('device_id') not in (None, ''):
                        args.extend(['--device-id', str(wg.get('device_id') or '').strip()])
                    if wg.get('door_id') not in (None, ''):
                        args.extend(['--door-id', str(wg.get('door_id') or '').strip()])
                    if wg.get('door_pk') not in (None, ''):
                        args.extend(['--door-pk', str(wg.get('door_pk') or '').strip()])
                    if wg.get('source'):
                        args.extend(['--source', str(wg.get('source') or '').strip()])
                    cf = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    p = subprocess.Popen(args, cwd=str(base.parent), creationflags=cf)
                    _LISTENER_PROCS.append(p)
        except Exception:
            pass
    except Exception:
        pass

def _stop_listeners():
    global _LISTENER_PROCS
    # Gracefully stop processes we started
    try:
        for p in _LISTENER_PROCS:
            try:
                if p and (p.poll() is None):
                    p.terminate()
                    try:
                        p.wait(timeout=3)
                    except Exception:
                        p.kill()
            except Exception:
                pass
    except Exception:
        pass
    _LISTENER_PROCS = []
    # Also attempt to kill any python processes running our listener scripts (started by tray_launch)
    try:
        # Use tasklist to enumerate and taskkill by window title-less processes with matching command line via wmic/powershell
        # Fallback: taskkill by filter on script name strings
        for name in ['card_reader_acp.py','card_reader_elatec.py','wiegand_listener.py']:
            try:
                subprocess.run(['powershell','-ExecutionPolicy','Bypass','-Command', f"Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -match 'python|pyw') -and $_.CommandLine -like '*{name}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
    except Exception:
        pass

def _listener_running(name: str, hb_threshold: float = 15.0, startup_grace: float = 30.0) -> bool:
    target = {
        'acp': 'card_reader_acp.py',
        'elatec': 'card_reader_elatec.py',
        'wiegand': 'wiegand_listener.py',
    }.get(name, '')
    if not target:
        return False
    try:
        out = subprocess.run(['powershell','-ExecutionPolicy','Bypass','-Command', f"Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -match 'python|pyw') -and $_.CommandLine -like '*{target}*' }} | Select-Object -First 1 -ExpandProperty ProcessId"], capture_output=True, text=True)
        pid = (out.stdout or '').strip()
        if not pid:
            return False
        # Process presence is the primary liveness signal; avoid marking down solely on heartbeat age
        # Heartbeat is used for diagnostics in tooltip, not for downing the listener
        # Keep a small startup grace but otherwise return True if process exists
        if (time.time() - _START_TS) <= startup_grace:
            return True
        return True
    except Exception:
        return False

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

def _get_adms_port(explicit_port=None):
    for candidate in (explicit_port, os.environ.get('ZKACCESS_ADMS_PORT'), _CONFIG.get('tray', 'adms_port', fallback=str(DEFAULT_ADMS_PORT))):
        try:
            port = int(str(candidate).strip())
            if 1 <= port <= 65535:
                return port
        except Exception:
            continue
    return DEFAULT_ADMS_PORT

def _launch_server_process(host, port, asgi=True, retry_count=3, process_label='server', write_state=False):
    global _SERVER_PROC, _ADMS_SERVER_PROC
    current_proc = _SERVER_PROC if process_label == 'server' else _ADMS_SERVER_PROC
    if current_proc and current_proc.poll() is None:
        return True

    for attempt in range(retry_count):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt
                logging.info('%s retry attempt %d, waiting %ds', process_label.capitalize(), attempt + 1, wait_time)
                time.sleep(wait_time)
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
            env['ZKACCESS_ADMS_PORT'] = str(_get_adms_port(port if process_label == 'adms' else None))
            try:
                base_dir = Path(settings.BASE_DIR)
                parent_dir = base_dir.parent
                existing = env.get('PYTHONPATH', '')
                paths = [p for p in existing.split(os.pathsep) if p]
                if str(parent_dir) not in paths:
                    paths.insert(0, str(parent_dir))
                if str(base_dir) not in paths:
                    paths.insert(0, str(base_dir))
                env['PYTHONPATH'] = os.pathsep.join(paths)
            except Exception:
                pass

            if asgi:
                try:
                    importlib.import_module('daphne')
                    cmd = [sys.executable, '-m', 'daphne', '-b', host, '-p', str(port), 'zkeco_config.asgi:application']
                    server_type = 'ASGI (Daphne)'
                except Exception:
                    cmd = [sys.executable, str(Path(settings.BASE_DIR) / 'manage.py'), 'runserver', f'{host}:{port}', '--noreload', '--nostatic']
                    server_type = 'WSGI (runserver)'
                    asgi = False
            else:
                cmd = [sys.executable, str(Path(settings.BASE_DIR) / 'manage.py'), 'runserver', f'{host}:{port}', '--noreload', '--nostatic']
                server_type = 'WSGI (runserver)'

            log_path = _server_log_path()
            logf = open(log_path, 'ab')
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            proc = subprocess.Popen(cmd, env=env, stdout=logf, stderr=subprocess.STDOUT, cwd=str(settings.BASE_DIR), creationflags=creationflags)
            logging.info('%s started (%s) pid=%s on %s:%s (attempt %d)', process_label.capitalize(), server_type, proc.pid, host, port, attempt + 1)
            time.sleep(1.5)
            if proc.poll() is not None:
                logging.warning('%s process exited immediately, retrying...', process_label.capitalize())
                continue
            if write_state:
                try:
                    _write_server_state(proc.pid, host, int(port), bool(asgi), server_type)
                except Exception:
                    pass
            if process_label == 'server':
                _SERVER_PROC = proc
            else:
                _ADMS_SERVER_PROC = proc
            return True
        except Exception as e:
            logging.error('%s start attempt %d failed: %s', process_label.capitalize(), attempt + 1, e)
            if attempt == retry_count - 1 and process_label == 'server':
                try:
                    err = _read_first_error_from_log()
                    detail = err or f'{e.__class__.__name__}: {e}'
                    messagebox.showerror('Start Server', 'Failed after retries:\n' + detail)
                except Exception:
                    pass
    return False

def _start_adms_server(host=DEFAULT_HOST, port=None):
    adms_port = _get_adms_port(port)
    try:
        main_port = int(_CONFIG.get('tray', 'port', fallback=str(DEFAULT_PORT)))
    except Exception:
        main_port = DEFAULT_PORT
    if adms_port == main_port:
        return True
    return _launch_server_process(host=host, port=adms_port, asgi=False, retry_count=3, process_label='adms', write_state=False)

def _start_server(host=DEFAULT_HOST, port=DEFAULT_PORT, asgi=True, retry_count=3):
    global _SERVER_PROC
    if _SERVER_PROC and _SERVER_PROC.poll() is None:
        return _start_adms_server(host=host)
    # If a previous tray run crashed, the server may still be running on the last used port.
    # Stop it before we decide whether the port is already in use.
    try:
        _stop_orphan_server_from_state()
        time.sleep(0.2)
    except Exception:
        pass
    if not _launch_server_process(host=host, port=port, asgi=asgi, retry_count=retry_count, process_label='server', write_state=True):
        return False
    return _start_adms_server(host=host)

def _stop_server():
    global _SERVER_PROC, _ADMS_SERVER_PROC
    for proc_name in ('_ADMS_SERVER_PROC', '_SERVER_PROC'):
        proc = _ADMS_SERVER_PROC if proc_name == '_ADMS_SERVER_PROC' else _SERVER_PROC
        try:
            if proc and proc.poll() is None:
                try:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=5)
                except Exception:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        except Exception:
            pass
    _ADMS_SERVER_PROC = None
    _SERVER_PROC = None

def _open_dashboard():
    try:
        port = int(_CONFIG.get('tray','port', fallback=str(DEFAULT_PORT)))
    except Exception:
        port = DEFAULT_PORT
    webbrowser.open(f'http://127.0.0.1:{port}/agent/dashboard/')

def _shutdown(icon):
    """Cleanly shutdown tray agent, stop all services, and destroy the icon instance."""
    def _emit(msg: str, level: str = 'info'):
        """Log, and print to terminal only when needed.

        When the Python logger is already configured with a StreamHandler to the
        console, printing would duplicate each line.
        """
        def _console_logging_enabled() -> bool:
            try:
                import sys
                streams = (sys.stdout, sys.stderr, getattr(sys, '__stdout__', None), getattr(sys, '__stderr__', None))
                loggers = [logging.getLogger(), logging.getLogger(__name__)]
                handlers = []
                for lg in loggers:
                    try:
                        handlers.extend(list(getattr(lg, 'handlers', []) or []))
                    except Exception:
                        continue
                for h in handlers:
                    try:
                        if isinstance(h, logging.StreamHandler):
                            stream = getattr(h, 'stream', None)
                            if stream in streams:
                                return True
                            # Some environments wrap stdout; fall back to stream name.
                            try:
                                nm = getattr(stream, 'name', None)
                                if nm in ('<stdout>', '<stderr>'):
                                    return True
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception:
                return False
            return False

        def _force_print() -> bool:
            try:
                v = str(os.getenv('TRAY_FORCE_STDOUT', '') or '').strip().lower()
                return v in ('1', 'true', 'yes', 'y', 'on')
            except Exception:
                return False

        try:
            if level == 'warn':
                logging.warning(msg)
            elif level == 'err':
                logging.error(msg)
            else:
                logging.info(msg)
        except Exception:
            pass
        # Avoid duplicate console output when the logger already prints there.
        try:
            if _force_print() or (not _console_logging_enabled()):
                print(msg, flush=True)
        except Exception:
            pass

    def _taskkill_pid(pid: int, label: str = '') -> bool:
        try:
            if not pid or int(pid) <= 0:
                return False
        except Exception:
            return False
        try:
            args = ['taskkill', '/PID', str(int(pid)), '/F', '/T']
            out = subprocess.run(args, capture_output=True, text=True)
            ok = (out.returncode == 0)
            if ok:
                _emit(f"[TRAY] Killed PID {pid} {('(' + label + ')') if label else ''}".rstrip())
            else:
                msg = (out.stderr or out.stdout or '').strip()
                _emit(f"[TRAY] taskkill failed PID={pid} {('(' + label + ')') if label else ''} rc={out.returncode} msg={msg}", level='warn')
            return ok
        except Exception as e:
            _emit(f"[TRAY] taskkill exception PID={pid} {('(' + label + ')') if label else ''}: {e}", level='warn')
            return False

    def _summarize_listening(port: int) -> list[dict]:
        """Return [{pid, ours, cmd}] for LISTENING TCP port."""
        rows: list[dict] = []
        try:
            if os.name != 'nt':
                return rows
            pids = _windows_listening_pids_on_port(int(port))
            for pid in sorted(list(pids)):
                try:
                    cmd = _windows_get_process_cmdline(int(pid))
                except Exception:
                    cmd = ''
                ours = _looks_like_our_server_cmdline(cmd)
                rows.append({'pid': int(pid), 'ours': bool(ours), 'cmd': (cmd or '')[:220]})
        except Exception:
            pass
        return rows

    # ---- Capture state BEFORE stopping anything (so we can report what was used) ----
    try:
        cfg_port = int(_CONFIG.get('tray', 'port', fallback=str(DEFAULT_PORT)))
    except Exception:
        cfg_port = DEFAULT_PORT
    try:
        adms_port = int(_CONFIG.get('tray', 'adms_port', fallback=str(DEFAULT_ADMS_PORT)))
    except Exception:
        adms_port = DEFAULT_ADMS_PORT
    listener_ports_to_report: set[int] = set()
    try:
        cfg = _read_listeners_config() or {}
        acp_cfg = cfg.get('acp') or {}
        wg_cfg = cfg.get('wiegand') or {}
        if acp_cfg.get('enabled', True):
            listener_ports_to_report.add(int(acp_cfg.get('port', 9001) or 9001))
        if wg_cfg.get('enabled', False):
            listener_ports_to_report.add(int(wg_cfg.get('port', 9002) or 9002))
    except Exception:
        pass
    server_ports_to_report = sorted({int(DEFAULT_PORT), int(cfg_port), int(adms_port)})
    ports_to_report = sorted(set(server_ports_to_report).union(listener_ports_to_report))

    server_pid = None
    try:
        if _SERVER_PROC and _SERVER_PROC.poll() is None:
            server_pid = int(_SERVER_PROC.pid)
    except Exception:
        server_pid = None

    listener_pids: list[int] = []
    try:
        for p in list(_LISTENER_PROCS or []):
            try:
                if p is not None and p.poll() is None:
                    listener_pids.append(int(p.pid))
            except Exception:
                continue
    except Exception:
        pass
    listener_pids = sorted(set([p for p in listener_pids if p and int(p) > 0]))

    pre_ports: dict[int, list[dict]] = {}
    try:
        for port in ports_to_report:
            pre_ports[int(port)] = _summarize_listening(int(port))
    except Exception:
        pre_ports = {}

    try:
        _emit('===== SHUTDOWN INITIATED =====')
        _emit(f"[TRAY] Shutdown pre-scan: server_pid={server_pid or '-'} listener_pids={listener_pids or '[]'}")
        for port in ports_to_report:
            rows = pre_ports.get(int(port), [])
            if not rows:
                _emit(f"[TRAY] Port {port}: no LISTENING TCP processes")
            else:
                ours = [r for r in rows if r.get('ours') or _looks_like_our_listener_cmdline(str(r.get('cmd') or ''))]
                pids = [r.get('pid') for r in rows]
                _emit(f"[TRAY] Port {port}: LISTENING pids={pids} (ours={ [r.get('pid') for r in ours] })")
    except Exception:
        pass

    killed: list[dict] = []  # [{pid,label,ok}]

    def _enqueue_close_all_doors_before_shutdown() -> None:
        """Best-effort: queue DOOR_CLOSE for active doors before stopping CommCenter."""
        try:
            # Critical safety default: do not inject synthetic DOOR_CLOSE commands
            # during shutdown unless explicitly requested.
            should_close = str(os.getenv('ZKACCESS_CLOSE_DOORS_ON_SHUTDOWN', '0') or '0').strip().lower()
            if should_close not in ('1', 'true', 'yes', 'on'):
                _emit('[TRAY] Skip close-on-shutdown (ZKACCESS_CLOSE_DOORS_ON_SHUTDOWN!=1)')
                return
        except Exception:
            return
        try:
            from agent.models import Door, CommandLog
        except Exception as e:
            _emit(f"[TRAY] Could not import models for close-on-shutdown: {e}", level='warn')
            return
        try:
            doors = list(
                Door.objects
                .filter(enabled=True, device__enabled=True)
                .exclude(door_number__isnull=True)
                .exclude(door_number=0)
                .values('id', 'device_id', 'door_number', 'name')
            )
        except Exception as e:
            _emit(f"[TRAY] Could not query doors for close-on-shutdown: {e}", level='warn')
            return

        queued = 0
        for d in doors:
            try:
                dev_id = int(d.get('device_id') or 0)
                door_no = int(d.get('door_number') or 0)
                if dev_id <= 0 or door_no <= 0:
                    continue
                CommandLog.objects.create(device_id=dev_id, command=f'DOOR_CLOSE:{door_no}', status='PENDING')
                queued += 1
            except Exception:
                continue

        if queued:
            _emit(f"[TRAY] Queued {queued} DOOR_CLOSE command(s) before shutdown")
            # Give CommCenter a short window to flush pending close commands.
            try:
                time.sleep(1.2)
            except Exception:
                pass

    try:
        _emit('Stopping server...')
        _stop_server()
        _emit('Queueing door close commands...')
        _enqueue_close_all_doors_before_shutdown()
        _emit('Stopping commcenter...')
        _stop_comm_center()
        _emit('Stopping card listeners...')
        _stop_listeners()
        time.sleep(0.5)
    except Exception as e:
        _emit(f"Error stopping server/commcenter/listeners: {e}", level='err')

    # Extra safety: force-kill known child PIDs captured pre-stop (so we can both kill and report).
    try:
        if server_pid:
            ok = _taskkill_pid(int(server_pid), label='server')
            killed.append({'pid': int(server_pid), 'label': 'server', 'ok': bool(ok)})
    except Exception:
        pass
    try:
        for pid in listener_pids:
            try:
                ok = _taskkill_pid(int(pid), label='listener')
                killed.append({'pid': int(pid), 'label': 'listener', 'ok': bool(ok)})
            except Exception:
                continue
    except Exception:
        pass
    # Write final OFF status and set icon red
    try:
        _write_tray_status(False, False, 'OPRIT', False)
        if icon is not None:
            red_img = _build_icon(color=(231,76,60))
            if red_img is not None:
                icon.icon = red_img
            icon.title = 'ACP:OPRIT | Elatec:OPRIT | W26:OPRIT | Server:OPRIT | CommCenter:OPRIT'
    except Exception:
        pass
    
    # Cleanup ports: only stop processes that look like OUR server.
    # Also report port 8000 even if not configured.
    try:
        _emit('Cleaning up port bindings (safe: only our server cmdlines)...')
        for port in server_ports_to_report:
            try:
                _stop_our_server_on_port(int(port))
            except Exception:
                continue
        for port in sorted(listener_ports_to_report):
            try:
                _stop_our_listener_on_port(int(port))
            except Exception:
                continue
        time.sleep(0.25)
    except Exception as e:
        _emit(f'Error cleaning up ports: {e}', level='err')

    # Post-check and summary
    try:
        _emit('[TRAY] Shutdown summary:')
        if killed:
            _emit('[TRAY] Killed PIDs: ' + ', '.join([f"{k.get('pid')}({k.get('label')})" for k in killed if k.get('pid')]))
        else:
            _emit('[TRAY] Killed PIDs: (none)')

        for port in ports_to_report:
            post_rows = _summarize_listening(int(port))
            if not post_rows:
                _emit(f"[TRAY] Port {port}: FREE (no LISTENING)")
                continue
            ours = [r for r in post_rows if r.get('ours') or _looks_like_our_listener_cmdline(str(r.get('cmd') or ''))]
            if ours:
                _emit(f"[TRAY] Port {port}: still LISTENING by OUR process(es): {[r.get('pid') for r in ours]}" , level='warn')
            else:
                _emit(f"[TRAY] Port {port}: still LISTENING by non-app process(es): {[r.get('pid') for r in post_rows]}" , level='warn')
    except Exception:
        pass
    
    try:
        if _STOP_EVENT:
            _STOP_EVENT.set()
    except Exception:
        pass
    
    try:
        _emit('Removing tray icon...')
        icon.visible = False
        icon.stop()
    except Exception as e:
        _emit(f"Error removing icon: {e}", level='err')
    
    try:
        _emit('===== SHUTDOWN COMPLETE =====')
        time.sleep(0.3)
        _emit('Terminating process...')
        try:
            if _PID_FILE.exists():
                _PID_FILE.unlink()
        except Exception:
            pass
        os.kill(os.getpid(), signal.SIGTERM)
    except Exception:
        pass

def _build_menu(icon, host, port):
    # Legacy-like actions -------------------------------------------------
    def _configure_port():
        def _save():
            try:
                new_port = int(entry_port.get())
                new_adms_port = int(entry_adms_port.get())
                mode = mode_var.get()
                _CONFIG.set('tray','port', str(new_port))
                _CONFIG.set('tray','adms_port', str(new_adms_port))
                _CONFIG.set('tray','server_mode', mode)
                os.environ['ZKACCESS_ADMS_PORT'] = str(new_adms_port)
                _save_config()
                messagebox.showinfo('Port','Saved. Restarting server...')
                _stop_server(); _start_server(host=host, port=new_port, asgi=(mode=='asgi'))
            except Exception as e:
                messagebox.showerror('Error', str(e))
        root = tk.Tk(); root.title('Server Configuration'); root.geometry('340x280')
        tk.Label(root,text='Port:', anchor='w').pack(pady=6)
        entry_port = tk.Entry(root)
        entry_port.pack()
        current = _CONFIG.get('tray','port', fallback=str(port))
        entry_port.delete(0,'end'); entry_port.insert(0,current)
        tk.Label(root,text='ADMS Port:', anchor='w').pack(pady=6)
        entry_adms_port = tk.Entry(root)
        entry_adms_port.pack()
        current_adms = _CONFIG.get('tray','adms_port', fallback=str(DEFAULT_ADMS_PORT))
        entry_adms_port.delete(0,'end'); entry_adms_port.insert(0,current_adms)
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

    # Per-server submenus
    django_server_menu = pystray.Menu(
        pystray.MenuItem('Start', lambda: threading.Thread(target=lambda: (_start_server(host, port, True), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('Stop', lambda: threading.Thread(target=lambda: (_stop_server(), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('Restart', lambda: threading.Thread(target=lambda: (_stop_server(), time.sleep(1), _start_server(host=host, port=port, asgi=True), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
    )

    commcenter_menu = pystray.Menu(
        pystray.MenuItem('Start', lambda: threading.Thread(target=lambda: (_start_comm_center(), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('Stop', lambda: threading.Thread(target=lambda: (_stop_comm_center(), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('Restart', lambda: threading.Thread(target=lambda: (_stop_comm_center(), time.sleep(1), _start_comm_center(), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
    )

    wsgi_fallback_menu = pystray.Menu(
        pystray.MenuItem('Start WSGI (Fallback)', lambda: threading.Thread(target=_start_server, args=(host, port, False), daemon=True).start()),
        pystray.MenuItem('Stop WSGI', lambda: threading.Thread(target=_stop_server, daemon=True).start()),
    )

    legacy_menu = pystray.Menu(
        pystray.MenuItem('Server WSGI (Manual Fallback)', wsgi_fallback_menu),
        pystray.MenuItem('Configure Server Port', lambda: threading.Thread(target=_configure_port, daemon=True).start()),
        pystray.MenuItem('Configure Database', lambda: messagebox.showinfo('Configure DB','Using SQLite file at %s' % (Path(settings.BASE_DIR)/'db.sqlite3'))),
        pystray.MenuItem('Database Backup Location', lambda: threading.Thread(target=_select_path, args=('backup_dir','Backup Location'), daemon=True).start()),
        pystray.MenuItem('Video File Location', lambda: threading.Thread(target=_select_path, args=('video_dir','Video Files'), daemon=True).start()),
        pystray.MenuItem('Picture File Location', lambda: threading.Thread(target=_select_path, args=('picture_dir','Picture Files'), daemon=True).start()),
        pystray.MenuItem('Restore Database', lambda: threading.Thread(target=_restore_db, daemon=True).start()),
        pystray.MenuItem('Backup Database', lambda: threading.Thread(target=_backup_db, daemon=True).start()),
        pystray.MenuItem('License Activation', lambda: threading.Thread(target=_license_activation, daemon=True).start()),
        pystray.MenuItem('View Server Log', lambda: webbrowser.open(str(Path(getattr(settings, 'BASE_DIR', Path.cwd())) / 'server.log'))),
    )

    def _run_toggle(target, action, value=None):
        try:
            base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
            script = str(base.parent / 'scripts' / 'toggle_listeners.ps1')
            if not Path(script).exists():
                messagebox.showerror('Toggle', 'toggle_listeners.ps1 missing.')
                return
            args = ['powershell','-ExecutionPolicy','Bypass','-File', script, '-Target', target, '-Action', action]
            if value is not None:
                args += ['-Value', str(value)]
            subprocess.Popen(args, cwd=str(base.parent))
            messagebox.showinfo('Card Readers', 'Updated. Restart tray to apply changes.')
        except Exception as e:
            try:
                messagebox.showerror('Card Readers', f'Failed: {e}')
            except Exception:
                pass

    def _prompt_value(title, default=''):
        val = {'value': None}
        try:
            win = tk.Tk(); win.title(title); win.geometry('320x140')
            tk.Label(win, text=title).pack(pady=8)
            entry = tk.Entry(win); entry.pack(); entry.insert(0, default)
            def _save():
                val['value'] = entry.get().strip(); win.destroy()
            tk.Button(win, text='Save', command=_save).pack(pady=10)
            tk.Button(win, text='Close', command=win.destroy).pack()
            win.mainloop()
        except Exception:
            pass
        return val['value']

    def _card_readers_menu():
        return pystray.Menu(
            pystray.MenuItem('ACP: Enable', lambda: _run_toggle('acp','enable')),
            pystray.MenuItem('ACP: Disable', lambda: _run_toggle('acp','disable')),
            pystray.MenuItem('ACP: Set Port', lambda: (lambda v=_prompt_value('ACP Port','9001'): _run_toggle('acp','set', v))()),
            pystray.MenuItem('ACP: Start', lambda: threading.Thread(target=lambda: (_start_listener('acp'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('ACP: Stop', lambda: threading.Thread(target=lambda: (_set_blocked('acp', True), _stop_listener('acp'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('ACP: Restart', lambda: threading.Thread(target=lambda: (_set_blocked('acp', True), _stop_listener('acp'), time.sleep(1), _set_blocked('acp', False), _start_listener('acp'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('---', pystray.Menu()),
            pystray.MenuItem('Elatec: Enable', lambda: _run_toggle('elatec','enable')),
            pystray.MenuItem('Elatec: Disable', lambda: _run_toggle('elatec','disable')),
            pystray.MenuItem('Elatec: Set COM', lambda: (lambda v=_prompt_value('Elatec COM','COM3'): _run_toggle('elatec','set', v))()),
            pystray.MenuItem('Elatec: Start', lambda: threading.Thread(target=lambda: (_start_listener('elatec'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('Elatec: Stop', lambda: threading.Thread(target=lambda: (_set_blocked('elatec', True), _stop_listener('elatec'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('Elatec: Restart', lambda: threading.Thread(target=lambda: (_set_blocked('elatec', True), _stop_listener('elatec'), time.sleep(1), _set_blocked('elatec', False), _start_listener('elatec'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('---', pystray.Menu()),
            pystray.MenuItem('W26: Start', lambda: threading.Thread(target=lambda: (_set_blocked('wiegand', False), _start_listener('wiegand'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('W26: Stop', lambda: threading.Thread(target=lambda: (_set_blocked('wiegand', True), _stop_listener('wiegand'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('W26: Restart', lambda: threading.Thread(target=lambda: (_set_blocked('wiegand', True), _stop_listener('wiegand'), time.sleep(1), _set_blocked('wiegand', False), _start_listener('wiegand'), time.sleep(0.6), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('---', pystray.Menu()),
            pystray.MenuItem('ACP: Unblock', lambda: threading.Thread(target=lambda: (_set_blocked('acp', False), time.sleep(0.2), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('Elatec: Unblock', lambda: threading.Thread(target=lambda: (_set_blocked('elatec', False), time.sleep(0.2), _recompute_status_once()), daemon=True).start()),
            pystray.MenuItem('W26: Unblock', lambda: threading.Thread(target=lambda: (_set_blocked('wiegand', False), time.sleep(0.2), _recompute_status_once()), daemon=True).start()),
        )

    def _recompute_status_once():
        try:
            try:
                port_probe = int(_CONFIG.get('tray','port', fallback='8000'))
            except Exception:
                port_probe = 8000
            srv = _is_server_running(host='127.0.0.1', port=port_probe) or (_SERVER_PROC is not None and _SERVER_PROC.poll() is None)
            cen = _CENTER is not None
            acp_live = _listener_running('acp')
            el_live = _listener_running('elatec')
            wg_live = _listener_running('wiegand')
            # Respect enabled flags from tray_status.json
            st = _read_tray_status()
            acp_en = bool(st.get('acp_enabled', True))
            el_en = bool(st.get('elatec_enabled', True))
            wg_en = bool(st.get('wiegand_enabled', False))
            acp_blocked = bool(st.get('acp_blocked', False))
            el_blocked = bool(st.get('elatec_blocked', False))
            wg_blocked = bool(st.get('wiegand_blocked', False))
            _write_tray_status(acp_live, el_live, ('PORNIT' if srv else 'OPRIT'), cen, wg_live)
            st = _read_tray_status()
            # Nudge icon tooltip immediately; blocked takes precedence over disabled
            if icon is not None:
                tip = []
                def _reader_label(live, blocked, enabled):
                    if live:
                        return 'ON'
                    if blocked:
                        return 'OPRIT'
                    if not enabled:
                        return 'DISABLED'
                    return 'OPRIT'
                tip.append('ACP:' + _reader_label(acp_live, acp_blocked, acp_en))
                tip.append('Elatec:' + _reader_label(el_live, el_blocked, el_en))
                tip.append('W26:' + _reader_label(wg_live, wg_blocked, wg_en))
                tip.append('Server:' + ('PORNIT' if srv else 'OPRIT'))
                tip.append('CommCenter:' + ('PORNIT' if cen else 'OPRIT'))
                capture_health = st.get('capture_health') or {}
                raw_state = str(capture_health.get('raw_capture_state') or '').strip().upper()
                raw_age = capture_health.get('raw_capture_last_frame_age_s')
                if raw_state:
                    raw_bits = [raw_state]
                    if raw_age not in (None, ''):
                        raw_bits.append(f'{raw_age}s')
                    tip.append('RAW:' + ' '.join(raw_bits))
                if st.get('zkemkeeper_enabled'):
                    zkem_tip = 'ZKEM:' + str(st.get('zkemkeeper') or 'OPRIT')
                    zkem_msg = str(st.get('zkemkeeper_message') or '').strip()
                    if str(st.get('zkemkeeper') or '').strip().upper() == 'EROARE' and zkem_msg:
                        zkem_tip += ' ' + zkem_msg[:56]
                    tip.append(zkem_tip)
                tip.append(f'Licență:{_license_status()}')
                tip.append('Click dreapta: meniu')
                _set_icon_title(icon, ' | '.join(tip))
        except Exception:
            pass

    return pystray.Menu(
        pystray.MenuItem('Dashboard', lambda: _open_dashboard()),
        pystray.MenuItem('Web Server (ASGI)', django_server_menu),
        pystray.MenuItem('CommCenter', commcenter_menu),
        pystray.MenuItem('Card Readers', _card_readers_menu()),
        pystray.MenuItem('---', pystray.Menu()),  # Separator
        pystray.MenuItem('Stop All Services', lambda: threading.Thread(target=lambda: (_set_blocked('acp', True), _set_blocked('elatec', True), _set_blocked('wiegand', True), _stop_server(), _stop_comm_center(), _stop_listeners(), time.sleep(0.2), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('Start All Services', lambda: threading.Thread(target=lambda: (_update_tray_status_fields({'acp_enabled': True, 'elatec_enabled': True, 'wiegand_enabled': True, 'cmd_start_acp': True, 'cmd_start_elatec': True, 'cmd_start_wiegand': True}), _set_blocked('acp', False), _set_blocked('elatec', False), _set_blocked('wiegand', False), _start_server(host=host, port=port, asgi=True), _start_comm_center(), _start_listeners(), time.sleep(0.4), _recompute_status_once()), daemon=True).start()),
        pystray.MenuItem('---', pystray.Menu()),  # Separator
        pystray.MenuItem('Ajutor (RO)', lambda: threading.Thread(target=_show_help_ro, daemon=True).start()),
        pystray.MenuItem('Admin Menu', legacy_menu),
        pystray.MenuItem('Quit', lambda: _shutdown(icon)),
    )

class Command(BaseCommand):
    help = 'Launch system tray agent with CommCenter + server controls.'

    def add_arguments(self, parser):
        parser.add_argument('--no-server', action='store_true', help='Do not auto start server')
        parser.add_argument('--headless', action='store_true', help='Run without tray icon and keep services alive in-process')
        parser.add_argument('--asgi', action='store_true', help='Auto start Daphne ASGI server (WebSockets)')
        parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Bind host')
        parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Bind port')
        parser.add_argument('--adms-port', type=int, default=DEFAULT_ADMS_PORT, help='Dedicated ADMS/iClock bind port')
        parser.add_argument('--poll', type=float, default=0.25, help='CommCenter poll interval seconds')
        parser.add_argument(
            '--driver',
            type=str,
            default='auto',
            choices=['auto', 'stub', 'socket', 'sdk', 'zk', 'plcommpro'],
            help=(
                'CommCenter driver mode. '
                'Use plcommpro when the 32-bit bridge is configured; '
                'use zk for the pure-python ZKTech socket driver.'
            ),
        )
        parser.add_argument('--no-commcenter', action='store_true', help='Skip auto start of CommCenter')
        parser.add_argument('--status-interval', type=float, default=1.0, help='Tray tooltip update interval seconds')
        parser.add_argument('--auto-restart', action='store_true', help='Auto-restart server if process exits')
        parser.add_argument('--progress-test', action='store_true', help='Show a short demo progress window then exit')
        parser.add_argument('--self-test', action='store_true', help='Run tray diagnostics and exit')

    def handle(self, *args, **options):
        if pystray is None and not options.get('headless'):
            self.stderr.write('pystray not available; install Pillow + pystray.')
            return

        # Hard guard against running under the wrong interpreter.
        # This project MUST run under the workspace venv to avoid legacy Python26/ZKTeco paths
        # and to keep a single consistent tray/CommCenter/server stack.
        try:
            from pathlib import Path

            workspace_root = Path(__file__).resolve().parents[4]
            allowed_venv_pys: list[Path] = []
            for venv_name in ('.venv', '.venv_clean', '.venv_new'):
                p = (workspace_root / venv_name / 'Scripts' / 'python.exe')
                if p.exists():
                    allowed_venv_pys.append(p.resolve())
            if allowed_venv_pys and Path(sys.executable).resolve() not in allowed_venv_pys:
                self.stderr.write(
                    'tray_agent must be launched from the workspace virtualenv.\n'
                    f"Current: {sys.executable}\n"
                    f"Allowed: {', '.join(str(p) for p in allowed_venv_pys)}\n"
                    'Tip: run tray_launch.ps1 (it activates the venv and starts everything).'
                )
                raise SystemExit(2)
        except Exception:
            pass

        # Single-instance guard for Windows.
        # The PID-file based guard is not reliable on Windows (os.kill(pid, 0) semantics differ).
        try:
            if os.name == 'nt':
                import ctypes

                # Use a global named mutex so scheduled tasks / startup scripts can't spawn a second instance.
                mutex_name = 'Global\\ZKAccessB_Modern_TrayAgent'
                handle = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
                if handle:
                    already_exists = int(ctypes.windll.kernel32.GetLastError() or 0) == 183
                    if already_exists:
                        self.stdout.write('Tray agent already running (mutex); exiting.')
                        return
        except Exception:
            pass

        # Singleton guard: avoid multiple tray_agent instances
        try:
            if _PID_FILE.exists():
                try:
                    old = int(_PID_FILE.read_text().strip())
                except Exception:
                    old = None
                if old and old != os.getpid():
                    try:
                        os.kill(old, 0)
                        self.stdout.write(f'Tray agent already running (pid={old}); exiting.')
                        return 0
                    except Exception:
                        pass
            _PID_FILE.write_text(str(os.getpid()))
        except Exception:
            pass
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
        django.setup()
        _init_logging()
        # Apply CLI defaults to global CommCenter defaults so tray menu actions
        # (Start/Stop/Restart) reuse the same driver/poll mode.
        global _COMM_DEFAULT_DRIVER, _COMM_DEFAULT_POLL, _COMM_LAST_DRIVER, _COMM_LAST_BACKEND
        try:
            _COMM_DEFAULT_DRIVER = str(options.get('driver') or 'auto')
        except Exception:
            _COMM_DEFAULT_DRIVER = 'auto'
        try:
            _COMM_DEFAULT_POLL = max(0.1, float(options.get('poll') or 0.25))
        except Exception:
            _COMM_DEFAULT_POLL = 0.25
        _COMM_LAST_DRIVER = _COMM_DEFAULT_DRIVER
        _COMM_LAST_BACKEND = None
        host = options['host']; port = options['port']; adms_port = options['adms_port']
        # Override port/mode from persisted config
        try:
            port_cfg = int(_CONFIG.get('tray','port', fallback=str(port)))
            adms_port_cfg = int(_CONFIG.get('tray','adms_port', fallback=str(adms_port)))
            mode_cfg = _CONFIG.get('tray','server_mode', fallback=('asgi' if options.get('asgi') else 'wsgi'))
            port = port_cfg
            adms_port = adms_port_cfg
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

        # Channels channel layer: Redis is required for WebSocket group events across processes.
        # In tray mode, the web server runs in a separate subprocess, while CommCenter runs in
        # this process; without Redis, in-memory Channels will not deliver CommCenter group_send
        # messages to the WebSocket consumer.
        try:
            redis_url = (os.environ.get('REDIS_URL') or '').strip()
            if not redis_url and options.get('asgi') and (not options.get('no_server')) and (not options.get('no_commcenter')):
                import socket as _socket

                sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                try:
                    sock.settimeout(0.2)
                    sock.connect(('127.0.0.1', 6379))
                    os.environ['REDIS_URL'] = 'redis://127.0.0.1:6379/0'
                    logging.info('Redis detected on 127.0.0.1:6379; enabling REDIS_URL for cross-process WebSocket events')
                except Exception:
                    logging.warning(
                        'Redis not detected (127.0.0.1:6379). Running multi-process without REDIS_URL: '
                        'WebSocket may be connected but silent; monitor polling fallback will still work. '
                        'Start Redis and set REDIS_URL=redis://127.0.0.1:6379/0 for ideal live WS.'
                    )
                finally:
                    try:
                        sock.close()
                    except Exception:
                        pass
            elif redis_url and options.get('asgi') and (not options.get('no_server')) and (not options.get('no_commcenter')):
                # Best-effort check that Redis is actually reachable.
                try:
                    import socket as _socket

                    host = '127.0.0.1'
                    port = 6379
                    # Only parse host/port for simple redis://host:port/ forms.
                    if redis_url.startswith('redis://'):
                        rest = redis_url[len('redis://'):]
                        hp = rest.split('/', 1)[0]
                        if ':' in hp:
                            host, port_s = hp.rsplit(':', 1)
                            try:
                                port = int(port_s)
                            except Exception:
                                port = 6379
                        else:
                            host = hp

                    sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                    try:
                        sock.settimeout(0.2)
                        sock.connect((host, int(port)))
                    finally:
                        try:
                            sock.close()
                        except Exception:
                            pass
                except Exception:
                    logging.warning('REDIS_URL is set but Redis is not reachable (%s). WebSocket delivery may be unreliable.', redis_url)
        except Exception:
            pass

        # ADMS/iClock push auto-config: CommCenter needs to know the HTTP port
        # that devices should push to (/iclock/*). Default to enabled unless
        # explicitly disabled by env.
        try:
            # Always sync ADMS target port with the effective tray server port.
            # setdefault() keeps stale values from previous sessions and can break
            # push callbacks after operator changes the server port.
            os.environ['ZKACCESS_ADMS_PORT'] = str(int(adms_port))
        except Exception:
            pass
        try:
            if os.environ.get('ZKACCESS_ADMS_AUTOCONFIG') is None:
                os.environ['ZKACCESS_ADMS_AUTOCONFIG'] = '1'
        except Exception:
            pass
        if not options.get('no_server'):
            # Always stop any orphaned previous server first, so the manual port can be re-used.
            try:
                _stop_orphan_server_from_state()
                # Also stop any orphan server currently bound to the configured port.
                _stop_our_server_on_port(port)
                time.sleep(0.2)
            except Exception:
                pass

        if not options.get('no_server') and not _is_server_running(host=host, port=port):
            if _start_server(host=host, port=port, asgi=options.get('asgi')):
                mode = 'ASGI' if options.get('asgi') else 'WSGI'
                self.stdout.write(f'Started {mode} server on {host}:{port}.')
        if not options.get('no_commcenter'):
            try:
                _start_comm_center(poll_interval=options['poll'], driver=options['driver'])
                self.stdout.write('CommCenter started.')
                self.stdout.flush()
            except Exception as e:
                self.stderr.write(f'CommCenter start failed: {e}')
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
            logging.info('Status loop started')
            # Wait until the icon is actually visible, then force an immediate update
            if icon_ref is not None:
                for _ in range(50):  # up to ~5s
                    try:
                        if getattr(icon_ref, 'visible', False):
                            break
                    except Exception:
                        pass
                    time.sleep(0.1)
            try:
                # First update as soon as tray is visible
                st0 = _read_tray_status()
                srv0 = (st0.get('server') or '').upper()
                acp0 = _listener_running('acp')
                el0 = _listener_running('elatec')
                wg0 = _listener_running('wiegand')
                cen0 = _CENTER is not None
                _write_tray_status(acp0, el0, ('PORNIT' if _is_server_running('127.0.0.1', int(_CONFIG.get('tray','port', fallback='8000'))) else ('PORNESTE' if srv0=='PORNESTE' else 'OPRIT')), cen0, wg0)
            except Exception:
                pass
            while not _STOP_EVENT.is_set():
                try:
                    # Prefer state provided by tray_launch.ps1 if present
                    status_json = _read_tray_status()
                    srv_state = (status_json.get('server') or '').upper()  # PORNESTE | PORNIT | OPRIT
                    color_json = (status_json.get('color') or '').lower()
                    use_json = bool(status_json)

                    # Probe server via TCP as ground truth; fall back to process state
                    try:
                        port_probe = int(_CONFIG.get('tray','port', fallback=str(port)))
                    except Exception:
                        port_probe = port
                    server_running = _is_server_running(host='127.0.0.1', port=port_probe)
                    if not server_running:
                        server_running = _SERVER_PROC is not None and _SERVER_PROC.poll() is None
                    center_running = _CENTER is not None
                    # Ensure CommCenter is started if server is running but center stopped
                    if (not center_running) and server_running and (not options.get('no_commcenter')):
                        try:
                            _start_comm_center(poll_interval=options['poll'], driver=options['driver'])
                            center_running = _CENTER is not None
                        except Exception:
                            pass
                    # Live reader state from processes (ground truth)
                    acp_live = _listener_running('acp')
                    el_live = _listener_running('elatec')
                    wg_live = _listener_running('wiegand')
                    # Respect explicit UI blocked flags immediately
                    try:
                        st_block = status_json or {}
                        if st_block.get('acp_blocked', False):
                            acp_live = False
                        if st_block.get('elatec_blocked', False):
                            el_live = False
                        if st_block.get('wiegand_blocked', False):
                            wg_live = False
                    except Exception:
                        pass
                    # record initial source reasons
                    acp_reason = 'process' if acp_live else 'none'
                    el_reason = 'process' if el_live else 'none'
                    wg_reason = 'process' if wg_live else 'none'
                    any_running = (server_running or center_running or acp_live or el_live or wg_live)
                    tip = []
                    # Reader status summaries from JSON if present; fall back to config hints
                    try:
                        cfg = _read_listeners_config()
                        acp_cfg = (cfg or {}).get('acp') or {}
                        el_cfg = (cfg or {}).get('elatec') or {}
                        wg_cfg = (cfg or {}).get('wiegand') or {}
                        st = _read_tray_status()
                        acp_en = bool(st.get('acp_enabled', acp_cfg.get('enabled', True)))
                        el_en = bool(st.get('elatec_enabled', el_cfg.get('enabled', True)))
                        wg_en = bool(st.get('wiegand_enabled', wg_cfg.get('enabled', False)))
                        # Hardware-aware check: detect Elatec COM presence and override enabled flag
                        com_present = True
                        try:
                            import subprocess as _sp
                            com_port = str(el_cfg.get('port','COM3'))
                            cmd = ['powershell','-ExecutionPolicy','Bypass','-Command', "(Get-CimInstance Win32_SerialPort | Select-Object -ExpandProperty DeviceID) -join ','"]
                            r = _sp.run(cmd, capture_output=True, text=True)
                            ports = (r.stdout or '').strip().split(',') if r.returncode == 0 else []
                            com_present = (not com_port) or (com_port in ports)
                            if not com_present:
                                el_en = False
                        except Exception:
                            # If COM detection fails, keep previous el_en value
                            pass
                        # Handle explicit start/stop commands from UI
                        try:
                            acp_cmd_start = bool(st.get('cmd_start_acp'))
                            acp_cmd_stop = bool(st.get('cmd_stop_acp'))
                            el_cmd_start = bool(st.get('cmd_start_elatec'))
                            el_cmd_stop = bool(st.get('cmd_stop_elatec'))
                            wg_cmd_start = bool(st.get('cmd_start_wiegand'))
                            wg_cmd_stop = bool(st.get('cmd_stop_wiegand'))
                            if acp_cmd_start:
                                logging.info('UI requested: start ACP listener')
                                _start_listener('acp')
                                time.sleep(0.2)
                                acp_live = _listener_running('acp')
                            if acp_cmd_stop:
                                logging.info('UI requested: stop ACP listener')
                                _stop_listener('acp')
                                time.sleep(0.2)
                                acp_live = _listener_running('acp')
                            if el_cmd_start:
                                logging.info('UI requested: start Elatec listener')
                                if com_present:
                                    _start_listener('elatec')
                                    time.sleep(0.2)
                                else:
                                    logging.info('Elatec COM missing; ignoring start')
                                el_live = _listener_running('elatec')
                            if el_cmd_stop:
                                logging.info('UI requested: stop Elatec listener')
                                _stop_listener('elatec')
                                time.sleep(0.2)
                                el_live = _listener_running('elatec')
                            if wg_cmd_start:
                                logging.info('UI requested: start Wiegand listener')
                                _start_listener('wiegand')
                                time.sleep(0.2)
                                wg_live = _listener_running('wiegand')
                            if wg_cmd_stop:
                                logging.info('UI requested: stop Wiegand listener')
                                _stop_listener('wiegand')
                                time.sleep(0.2)
                                wg_live = _listener_running('wiegand')
                            # Clear one-shot command flags to reflect execution
                            if any([acp_cmd_start, acp_cmd_stop, el_cmd_start, el_cmd_stop, wg_cmd_start, wg_cmd_stop]):
                                try:
                                    st2 = dict(st)
                                    for k in ['cmd_start_acp','cmd_stop_acp','cmd_start_elatec','cmd_stop_elatec','cmd_start_wiegand','cmd_stop_wiegand']:
                                        if st2.get(k):
                                            st2.pop(k, None)
                                    _write_tray_status(acp_live, el_live, ('PORNIT' if server_running else 'OPRIT'), center_running, wg_live)
                                    # Also write tray_status.json with flags cleared
                                    p = _tray_status_path()
                                    import json as _json
                                    data = _read_tray_status()
                                    for k in ['cmd_start_acp','cmd_stop_acp','cmd_start_elatec','cmd_stop_elatec','cmd_start_wiegand','cmd_stop_wiegand']:
                                        if k in data:
                                            data.pop(k, None)
                                    try:
                                        (p.with_suffix('.tmp')).write_text(_json.dumps(data, ensure_ascii=False), encoding='utf-8')
                                        tmp = p.with_suffix('.tmp')
                                        if p.exists():
                                            p.unlink()
                                        tmp.replace(p)
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                            # After command handling, ensure DB reflects current live flags
                            try:
                                _set_device_online_flag('acp', bool(acp_live))
                            except Exception:
                                pass
                            try:
                                _set_device_online_flag('elatec', bool(el_live))
                            except Exception:
                                pass
                        except Exception:
                            pass

                        # For virtual-mode readers, prefer DB DeviceStatus or heartbeat as liveness signals
                        try:
                            if (not el_live):
                                try:
                                    cfg = _read_listeners_config()
                                    el_cfg = (cfg or {}).get('elatec') or {}
                                    el_mode = str(el_cfg.get('mode','')).lower()
                                    if el_mode == 'virtual':
                                        try:
                                            # Use raw SQL to check DeviceStatus.online to avoid Django app/model import
                                            from django.db import connection
                                            vendor = getattr(connection, 'vendor', '')
                                            cur = connection.cursor()
                                            if vendor == 'sqlite':
                                                sql = ("SELECT 1 FROM agent_devicestatus JOIN agent_device ON agent_devicestatus.device_id=agent_device.id "
                                                       "WHERE agent_device.scanner_type=? AND agent_device.scanner_linked=1 AND agent_device.enabled=1 AND agent_devicestatus.online=1 LIMIT 1")
                                                params = ( 'elatec', )
                                            else:
                                                sql = ("SELECT 1 FROM agent_devicestatus JOIN agent_device ON agent_devicestatus.device_id=agent_device.id "
                                                       "WHERE agent_device.scanner_type=%s AND agent_device.scanner_linked = true AND agent_device.enabled = true AND agent_devicestatus.online = 1 LIMIT 1")
                                                params = ( 'elatec', )
                                            try:
                                                cur.execute(sql, params)
                                                row = cur.fetchone()
                                                has_online = bool(row)
                                            except Exception as _e:
                                                # Avoid continuous noisy logs; log the first error and then throttle
                                                logging.debug('SQL check for DeviceStatus.online failed for elatec: %s', _e)
                                                has_online = False
                                            if has_online:
                                                el_live = True
                                                el_reason = 'db'
                                                logging.info('Elatec virtual: treated as live due to DeviceStatus.online')
                                            else:
                                                hb = Path.home() / 'zkeco_reader_heartbeat_elatec.json'
                                                if hb.exists():
                                                    try:
                                                        data = json.loads(hb.read_text(encoding='utf-8'))
                                                        ts = float(data.get('ts') or 0)
                                                        if (time.time() - ts) <= max(15.0, 5.0):
                                                            el_live = True
                                                            el_reason = 'heartbeat'
                                                            logging.info('Elatec virtual: treated as live due to recent heartbeat')
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # Log decision path for readers each loop (concise)
                        try:
                            logging.info('Reader decision: ACP live=%s reason=%s ; Elatec live=%s reason=%s ; Wiegand live=%s reason=%s', acp_live, acp_reason, el_live, el_reason, wg_live, wg_reason)
                        except Exception:
                            pass
                        try:
                            adms_port = _get_adms_port()
                            adms_running = _is_server_running(host='127.0.0.1', port=adms_port)
                            if not adms_running:
                                adms_running = _ADMS_SERVER_PROC is not None and _ADMS_SERVER_PROC.poll() is None
                            if server_running and adms_port != port_probe and not adms_running:
                                logging.info('ADMS listener down; attempting restart on port %s', adms_port)
                                _start_adms_server(host=host, port=adms_port)
                        except Exception:
                            pass
                        # Auto-restart listeners if enabled but not live (skip if user requested stop)
                        try:
                            if acp_en and not acp_live and not bool(st.get('cmd_stop_acp')) and not bool(st.get('acp_blocked', False)):
                                logging.info('ACP listener down; attempting auto-restart')
                                _start_listener('acp')
                                time.sleep(0.2)
                                acp_live = _listener_running('acp')
                            # Elatec only if enabled AND COM present (skip if user requested stop)
                            if el_en and com_present and not el_live and not bool(st.get('cmd_stop_elatec')) and not bool(st.get('elatec_blocked', False)):
                                logging.info('Elatec listener down; attempting auto-restart')
                                _start_listener('elatec')
                                time.sleep(0.2)
                                el_live = _listener_running('elatec')
                            if wg_en and not wg_live and not bool(st.get('cmd_stop_wiegand')) and not bool(st.get('wiegand_blocked', False)):
                                logging.info('Wiegand listener down; attempting auto-restart')
                                _start_listener('wiegand')
                                time.sleep(0.2)
                                wg_live = _listener_running('wiegand')
                        except Exception:
                            pass
                        # Heartbeat ages for diagnostics
                        def _hb_age(path):
                            try:
                                d = json.loads(Path(path).read_text(encoding='utf-8'))
                                ts = float(d.get('ts') or 0)
                                return max(0, int(time.time() - ts))
                            except Exception:
                                return None
                        acp_age = _hb_age(str(Path.home() / 'zkeco_reader_heartbeat_acp.json'))
                        el_age = _hb_age(str(Path.home() / 'zkeco_reader_heartbeat_elatec.json'))
                        wg_age = _hb_age(str(Path.home() / 'zkeco_reader_heartbeat_wiegand.json'))
                        acp_blocked = bool(st.get('acp_blocked', False))
                        el_blocked = bool(st.get('elatec_blocked', False))
                        wg_blocked = bool(st.get('wiegand_blocked', False))
                        def _reader_label2(live, blocked, enabled):
                            if live:
                                return 'ON'
                            if blocked:
                                return 'OPRIT'
                            if not enabled:
                                return 'DISABLED'
                            return 'OPRIT'
                        tip.append('ACP:' + _reader_label2(acp_live, acp_blocked, acp_en))
                        tip.append('Elatec:' + _reader_label2(el_live, el_blocked, el_en))
                        tip.append('W26:' + _reader_label2(wg_live, wg_blocked, wg_en))
                        if acp_age is not None:
                            tip.append(f"ACP HB:{acp_age}s")
                        if el_age is not None:
                            tip.append(f"Elatec HB:{el_age}s")
                        if wg_age is not None:
                            tip.append(f"W26 HB:{wg_age}s")
                    except Exception:
                        pass
                    # Append last card read and access evaluation status
                    try:
                        from django.core.cache import cache as _cache
                        last_card = _cache.get('agent:last_card_read') or {}
                        last_eval = _cache.get('agent:last_access_eval') or {}
                        el_err = _cache.get('agent:listener_error:elatec')
                        if el_err:
                            tip.append(f"Elatec ERR:{el_err}")
                        if last_card.get('card_number'):
                            tip.append(f"Card {last_card.get('card_number')} ({last_card.get('source','')})")
                        if last_eval.get('card_number'):
                            tip.append('Access ' + ('OK' if last_eval.get('ok') else 'DENY'))
                            rs = last_eval.get('reasons') or []
                            if rs:
                                tip.append(','.join(rs[:2]))
                    except Exception:
                        pass
                    if center_running and _CENTER:
                        total = len(_CENTER.sessions)
                        online = sum(1 for s in _CENTER.sessions.values() if s.connected)
                        tip.append(f"Dispozitive {online}/{total}")
                        tip.append(f"Cicluri {_CENTER.cycles}")
                        tip.append(f"RT {_CENTER.total_rtlog_lines}")
                    tip.append('Server:' + ( 'PORNIT' if server_running else ('PORNESTE' if srv_state=='PORNESTE' else 'OPRIT') ))
                    tip.append('CommCenter:' + ('PORNIT' if center_running else 'OPRIT'))
                    if st.get('zkemkeeper_enabled'):
                        tip.append('ZKEM:' + str(st.get('zkemkeeper') or 'OPRIT'))
                    tip.append(f'Licență:{_license_status()}')
                    tip.append('Click dreapta: meniu')
                    _set_icon_title(icon_ref, ' | '.join(tip))
                    state = (server_running, center_running, any_running, color_json if use_json else None, acp_live, el_live, wg_live)
                    if state != _LAST_ICON_STATE:
                        logging.info('State change: srv=%s, cen=%s, acp=%s, el=%s', server_running, center_running, acp_live, el_live)
                        # Derive color: green when required services running
                        cfg = _read_listeners_config()
                        st2 = _read_tray_status()
                        acp_en = bool(st2.get('acp_enabled', ((cfg or {}).get('acp') or {}).get('enabled', True)))
                        el_en = bool(st2.get('elatec_enabled', ((cfg or {}).get('elatec') or {}).get('enabled', True)))
                        all_on = server_running and center_running and ((not acp_en) or acp_live) and ((not el_en) or el_live) and ((not wg_en) or wg_live)
                        if all_on:
                            color = (46,204,113)
                        elif any_running:
                            color = (241,196,15)
                        else:
                            color = (231,76,60)
                        new_img = _build_icon(color=color)
                        if new_img is not None:
                            icon_ref.icon = new_img
                        _LAST_ICON_STATE = state
                    # Always write consolidated status for 100% sync
                    try:
                        # If JSON provided explicit server state, use it; else derive from boolean
                        srv_out = ('PORNIT' if server_running else ('PORNESTE' if srv_state=='PORNESTE' else 'OPRIT'))
                        _write_tray_status(acp_live, el_live, srv_out, center_running, wg_live)
                    except Exception:
                        pass
                except Exception:
                    pass
                _STOP_EVENT.wait(options['status_interval'])

        def _restart_loop():
            while not _STOP_EVENT.is_set():
                try:
                    if options.get('auto_restart'):
                        if (not _SERVER_PROC) or (_SERVER_PROC and _SERVER_PROC.poll() is not None):
                            _start_server(host=host, port=port, asgi=options.get('asgi'))
                        adms_port = _get_adms_port()
                        if adms_port != port and ((not _ADMS_SERVER_PROC) or (_ADMS_SERVER_PROC and _ADMS_SERVER_PROC.poll() is not None)):
                            _start_adms_server(host=host, port=adms_port)
                    _STOP_EVENT.wait(5.0)
                except Exception:
                    _STOP_EVENT.wait(5.0)

        if options.get('headless'):
            self.stdout.write('Headless tray mode active. Services will keep running without a tray icon.')
            self.stdout.write(f'Using management command at: {__file__}')
            self.stdout.flush()
            try:
                _recompute_status_once()
                time.sleep(0.3)
                _recompute_status_once()
            except Exception:
                pass
            threading.Thread(target=_status_loop, args=(None,), daemon=True).start()
            if options.get('auto_restart'):
                threading.Thread(target=_restart_loop, daemon=True).start()

            def _headless_signal_handler(signum, _frame):
                logging.info('Headless tray signal received: %s', signum)
                try:
                    _shutdown(None)
                except Exception as cleanup_err:
                    logging.error(f'Error during headless cleanup: {cleanup_err}')

            for sig_name in ('SIGINT', 'SIGTERM', 'SIGBREAK'):
                try:
                    sig = getattr(signal, sig_name)
                    signal.signal(sig, _headless_signal_handler)
                except Exception:
                    pass

            try:
                while not _STOP_EVENT.is_set():
                    time.sleep(1.0)
            except KeyboardInterrupt:
                self.stdout.write('Headless tray interrupted. Performing final cleanup...')
                try:
                    _shutdown(None)
                except Exception as cleanup_err:
                    logging.error(f'Error during headless cleanup: {cleanup_err}')
            self.stdout.write('Tray agent exited.')
            return 0

        # Clear, unique tooltip to confirm the correct agent is running
        icon = pystray.Icon('zkeco_access', _build_icon(color=_choose_icon_color(False, False)), 'Access Control — Django Tray Agent', menu=_build_menu(None, host, port))
        icon.menu = _build_menu(icon, host, port)
        # Immediate recompute before entering the GUI loop
        try:
            _recompute_status_once()
            time.sleep(0.3)
            _recompute_status_once()
        except Exception:
            pass
        threading.Thread(target=_status_loop, args=(icon,), daemon=True).start()
        if options.get('auto_restart'):
            threading.Thread(target=_restart_loop, daemon=True).start()
        self.stdout.write('Tray icon active. Right-click for menu.')
        self.stdout.write(f'Using management command at: {__file__}')
        self.stdout.flush()

        # Wrap icon.run() with exception handling and cleanup
        try:
            icon.run()
        except Exception as e:
            logging.error(f'Exception in tray icon run: {e}')
        finally:
            self.stdout.write('Tray icon loop exited. Performing final cleanup...')
            try:
                _shutdown(icon)
            except Exception as cleanup_err:
                logging.error(f'Error during final cleanup: {cleanup_err}')
            self.stdout.write('Tray agent exited.')

        return 0