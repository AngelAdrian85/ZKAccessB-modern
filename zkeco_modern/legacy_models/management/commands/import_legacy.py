import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
import time
import datetime

from django.core.management.base import BaseCommand, CommandError

from zkeco_modern.etl.employee import import_employees_from_csv
from zkeco_modern.etl.issuecard import import_issuecards_from_csv
from zkeco_modern.etl.device import import_devices_from_csv

try:
    import yaml
    YAML_AVAILABLE = True
except Exception:
    YAML_AVAILABLE = False

logger = logging.getLogger('zkeco.etl')


def _setup_file_logging(log_path: str = None):
    if not log_path:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / 'etl.log'
    else:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(str(log_path), maxBytes=5 * 1024 * 1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _auto_detect_mapping_from_header(header_cols, model_keys):
    # header_cols: list of CSV header column names
    # model_keys: dict canonical_field -> [candidate names]
    detected = {}
    lower_header = {c.lower(): c for c in header_cols}
    for field, candidates in model_keys.items():
        found = None
        for cand in candidates:
            if cand.lower() in lower_header:
                found = lower_header[cand.lower()]
                break
        detected[field] = found
    return detected


class Command(BaseCommand):
    help = 'Import legacy CSV exports into Django models. Supports dry-run, update, batching, preview and reporting.'

    def add_arguments(self, parser):
        parser.add_argument('--employees', dest='employees', help='Path to employees CSV')
        parser.add_argument('--issuecards', dest='issuecards', help='Path to issuecards CSV')
        parser.add_argument('--devices', dest='devices', help='Path to devices CSV')
        parser.add_argument('--mapping', dest='mapping', help='Path to mapping JSON/YAML', default=None)
        parser.add_argument('--mapping-auto', action='store_true', dest='mapping_auto', help='Auto-detect mapping from CSV headers')
        parser.add_argument('--preview', action='store_true', dest='preview', help='Preview mapping/rows without importing')
        parser.add_argument('--preview-html', dest='preview_html', help='Write a small HTML preview file', default=None)
        parser.add_argument('--limit', dest='limit', type=int, help='Limit rows for preview', default=10)
        parser.add_argument('--update', action='store_true', dest='update', help='Use update-or-create semantics')
        parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='Do not write to DB; show actions')
        parser.add_argument('--commit', action='store_true', dest='commit', help='Commit DB writes (default false when dry-run)')
        parser.add_argument('--report', dest='report', help='CSV path to write action report', default=None)
        parser.add_argument('--log-file', dest='log_file', help='Path to write ETL log file', default=None)
        parser.add_argument('--batch-size', dest='batch_size', type=int, help='Batch size for commits (0 = all)', default=0)
        parser.add_argument('--offset', dest='offset', type=int, help='Row offset to resume import', default=0)
        parser.add_argument('--state-file', dest='state_file', help='Path to JSON state file to store offsets', default=None)
        parser.add_argument('--state-flush-interval', dest='state_flush_interval', type=int, help='Write state-file every N processed rows (default 1)', default=1)
        parser.add_argument('--state-dry-run', action='store_true', dest='state_dry_run', help='Allow state-file updates during dry-run')

    def _load_mapping(self, path):
        if not path:
            return None
        if not os.path.exists(path):
            raise CommandError(f"mapping file not found: {path}")
        if path.lower().endswith(('.yml', '.yaml')):
            if not YAML_AVAILABLE:
                raise CommandError('PyYAML not available; install pyyaml or provide JSON mapping')
            with open(path, 'r', encoding='utf-8') as fh:
                return yaml.safe_load(fh)
        else:
            with open(path, 'r', encoding='utf-8') as fh:
                return json.load(fh)

    def handle(self, *args, **options):
        mapping = None
        if options.get('mapping'):
            mapping = self._load_mapping(options.get('mapping'))

        update = options.get('update', False)
        dry_run = options.get('dry_run', False)
        commit = options.get('commit', False) and not dry_run
        batch_size = options.get('batch_size', 0) or 0
        offset = options.get('offset', 0) or 0
        limit = options.get('limit', 10) or 10
        preview = options.get('preview', False)
        preview_html = options.get('preview_html')
        mapping_auto = options.get('mapping_auto', False)
        report_path = options.get('report')
        log_file = options.get('log_file')
        from django.conf import settings as _dj_settings

        # Determine flush interval: respect CLI, but allow a project setting to override the default.
        cli_val = int(options.get('state_flush_interval') or 0)
        settings_default = getattr(_dj_settings, 'IACCESS_STATE_FLUSH_INTERVAL', None)
        if settings_default is not None and cli_val == 1:
            # CLI default of 1 means the user didn't explicitly lower/raise; prefer settings override
            state_flush_interval = int(settings_default)
        else:
            state_flush_interval = int(options.get('state_flush_interval') or 1)

        state_dry_run = bool(options.get('state_dry_run') or False)

        # basic logging to console
        logging.basicConfig(level=logging.INFO)
        # add rotating file logging
        _setup_file_logging(log_file)

        report_rows = []
        state_file = options.get('state_file')
        state = {}
        if state_file and os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as sfh:
                    state = json.load(sfh)
            except Exception:
                logger.warning('Could not read state file %s, starting fresh', state_file)

        # helper to compute effective offset for a model: prefer explicit CLI --offset (>0),
        # otherwise resume from state file if available
        def _effective_offset(model_name: str):
            try:
                cli_offset = int(options.get('offset', 0) or 0)
            except Exception:
                cli_offset = 0
            if cli_offset and cli_offset > 0:
                return cli_offset
            return int(state.get(model_name, 0) or 0)

        def _save_state():
            if not state_file:
                return
            try:
                state_path = Path(state_file)
                state_path.parent.mkdir(parents=True, exist_ok=True)
                with open(state_path, 'w', encoding='utf-8') as sfh:
                    json.dump(state, sfh, indent=2, ensure_ascii=False)
            except Exception:
                logger.exception('Failed to write state file %s', state_file)

        def _write_report():
            if not report_path:
                return
            import csv as _csv
            report_p = Path(report_path)
            report_p.parent.mkdir(parents=True, exist_ok=True)
            with open(report_p, 'w', newline='', encoding='utf-8') as outf:
                writer = _csv.writer(outf)
                writer.writerow(['timestamp', 'duration_s', 'model', 'action', 'identifier', 'pk'])
                for r in report_rows:
                    writer.writerow([r.get('timestamp'), r.get('duration_s'), r.get('model'), r.get('action'), r.get('identifier'), r.get('pk')])

        # helper to preview header/mapping
        def _preview_csv(path, model_key_template=None):
            if not os.path.exists(path):
                raise CommandError(f'file not found: {path}')
            import csv as _csv
            with open(path, newline='', encoding='utf-8') as fh:
                reader = _csv.reader(fh)
                header = next(reader, [])
                rows = [row for _, row in zip(range(limit), reader)]
            self.stdout.write(f'Header: {header}')
            if mapping_auto and model_key_template:
                detected = _auto_detect_mapping_from_header(header, model_key_template)
                self.stdout.write('Auto-detected mapping:')
                for k, v in detected.items():
                    self.stdout.write(f'  {k} -> {v}')
                if preview_html:
                    # write a richer HTML preview (mapping + sample rows)
                    html = ['<html><head><meta charset="utf-8"><title>ETL Preview</title></head><body>']
                    html.append('<h2>Mapping preview</h2>')
                    html.append('<table border="1" style="border-collapse:collapse"><tr><th>field</th><th>column</th></tr>')
                    for k, v in detected.items():
                        html.append(f'<tr><td>{k}</td><td>{v or ""}</td></tr>')
                    html.append('</table>')
                    html.append('<h2>Sample rows</h2>')
                    html.append('<table border="1" style="border-collapse:collapse"><tr>')
                    for h in header:
                        html.append(f'<th>{h}</th>')
                    html.append('</tr>')
                    for r in rows:
                        html.append('<tr>' + ''.join(f'<td>{(c or "")}</td>' for c in r) + '</tr>')
                    html.append('</table>')
                    html.append('</body></html>')
                    with open(preview_html, 'w', encoding='utf-8') as fh:
                        fh.write('\n'.join(html))
                    self.stdout.write(f'Wrote preview HTML to {preview_html}')
            return header, rows

        # known key templates for auto-detection (should mirror ETL defaults)
        employee_template = {
            'userid': ['userid', 'user_id', 'id'],
            'badgenumber': ['badgenumber', 'badge', 'cardno'],
            'firstname': ['firstname', 'first_name', 'name'],
            'lastname': ['lastname', 'last_name'],
            'dept': ['dept', 'department', 'DeptName', 'deptname'],
        }
        device_template = {
            'sn': ['sn', 'serial', 'serial_no'],
            'device_name': ['device_name', 'name'],
            'device_type': ['device_type', 'type'],
            'area_name': ['area_name', 'area'],
        }
        issuecard_template = {
            'cardno': ['cardno', 'card_no', 'cardnumber', 'card'],
            'cardstatus': ['cardstatus', 'status'],
            'userid': ['userid', 'user_id'],
        }

        # Preview mode short-circuits import and shows mapping/rows
        if preview:
            if options.get('employees'):
                _preview_csv(options['employees'], employee_template)
            if options.get('devices'):
                _preview_csv(options['devices'], device_template)
            if options.get('issuecards'):
                _preview_csv(options['issuecards'], issuecard_template)
            return

        # Perform imports and collect report rows
        if options.get('employees'):
            emp_path = options['employees']
            self.stdout.write(f"Importing employees from {emp_path} (update={update} dry_run={dry_run} batch_size={batch_size} offset={offset})")
            mp = mapping.get('employee') if mapping else None
            # if mapping_auto, build mapping from header
            if mapping_auto:
                header, _ = _preview_csv(emp_path, employee_template)
                mp = _auto_detect_mapping_from_header(header, employee_template)
            eff_offset = _effective_offset('employee')
            if eff_offset:
                self.stdout.write(f'Resuming employees import at offset {eff_offset} (from --offset or state-file)')
            # ensure state starts at effective offset so per-row progress increments resume correctly
            state['employee'] = int(state.get('employee', 0) or 0)
            if eff_offset and eff_offset > state['employee']:
                state['employee'] = eff_offset

            def _emp_progress(delta=1):
                # respect dry-run: only persist if not dry-run or user explicitly requested state-dry-run
                if dry_run and not state_dry_run:
                    return
                # accumulate and flush only on the configured interval
                state['employee'] = int(state.get('employee', 0) or 0) + int(delta or 1)
                if state_flush_interval <= 1 or (state['employee'] % state_flush_interval) == 0:
                    _save_state()
            start = time.time()
            res = import_employees_from_csv(emp_path, commit=commit, update=update, dry_run=dry_run, mapping=mp, batch_size=batch_size, offset=eff_offset, progress_callback=_emp_progress)
            duration = time.time() - start
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            self.stdout.write(str(res))
            processed = 0
            if isinstance(res, dict):
                for a in res.get('actions', []):
                    report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'employee', 'action': a.get('action'), 'identifier': a.get('identifier'), 'pk': a.get('pk')})
                processed = len(res.get('actions', []))
            else:
                # legacy numeric return
                report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'employee', 'action': 'create_many', 'identifier': None, 'pk': res})
                try:
                    processed = int(res or 0)
                except Exception:
                    processed = 0
            if processed:
                # ensure final state is persisted at import end only when the
                # configured flush interval would trigger a write. This avoids
                # persisting small partial imports when the user requested a
                # larger flush interval (useful for dry-run / resume semantics).
                should_flush_final = (state_flush_interval <= 1) or ((int(state.get('employee', 0) or 0) % state_flush_interval) == 0)
                if (not dry_run or state_dry_run) and should_flush_final:
                    _save_state()
                    try:
                        self.stdout.write(f"Saved state for employee: {int(state.get('employee',0) or 0)}")
                    except Exception:
                        pass

        if options.get('devices'):
            dev_path = options['devices']
            self.stdout.write(f"Importing devices from {dev_path} (update={update} dry_run={dry_run} batch_size={batch_size} offset={offset})")
            mp = mapping.get('device') if mapping else None
            if mapping_auto:
                header, _ = _preview_csv(dev_path, device_template)
                mp = _auto_detect_mapping_from_header(header, device_template)
            eff_offset = _effective_offset('device')
            if eff_offset:
                self.stdout.write(f'Resuming devices import at offset {eff_offset} (from --offset or state-file)')
            state['device'] = int(state.get('device', 0) or 0)
            if eff_offset and eff_offset > state['device']:
                state['device'] = eff_offset

            def _dev_progress(delta=1):
                if dry_run and not state_dry_run:
                    return
                state['device'] = int(state.get('device', 0) or 0) + int(delta or 1)
                if state_flush_interval <= 1 or (state['device'] % state_flush_interval) == 0:
                    _save_state()
            start = time.time()
            res = import_devices_from_csv(dev_path, commit=commit, update=update, dry_run=dry_run, mapping=mp, batch_size=batch_size, offset=eff_offset, progress_callback=_dev_progress)
            duration = time.time() - start
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            self.stdout.write(str(res))
            processed = 0
            if isinstance(res, dict):
                for a in res.get('actions', []):
                    report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'device', 'action': a.get('action'), 'identifier': a.get('identifier'), 'pk': a.get('pk')})
                processed = len(res.get('actions', []))
            else:
                report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'device', 'action': 'create_many', 'identifier': None, 'pk': res})
                try:
                    processed = int(res or 0)
                except Exception:
                    processed = 0
            if processed:
                should_flush_final = (state_flush_interval <= 1) or ((int(state.get('device', 0) or 0) % state_flush_interval) == 0)
                if (not dry_run or state_dry_run) and should_flush_final:
                    _save_state()
                    try:
                        self.stdout.write(f"Saved state for device: {int(state.get('device',0) or 0)}")
                    except Exception:
                        pass

        if options.get('issuecards'):
            ic_path = options['issuecards']
            self.stdout.write(f"Importing issuecards from {ic_path} (update={update} dry_run={dry_run} batch_size={batch_size} offset={offset})")
            mp = mapping.get('issuecard') if mapping else None
            if mapping_auto:
                header, _ = _preview_csv(ic_path, issuecard_template)
                mp = _auto_detect_mapping_from_header(header, issuecard_template)
            eff_offset = _effective_offset('issuecard')
            if eff_offset:
                self.stdout.write(f'Resuming issuecards import at offset {eff_offset} (from --offset or state-file)')
            state['issuecard'] = int(state.get('issuecard', 0) or 0)
            if eff_offset and eff_offset > state['issuecard']:
                state['issuecard'] = eff_offset

            def _ic_progress(delta=1):
                if dry_run and not state_dry_run:
                    return
                state['issuecard'] = int(state.get('issuecard', 0) or 0) + int(delta or 1)
                if state_flush_interval <= 1 or (state['issuecard'] % state_flush_interval) == 0:
                    _save_state()
            start = time.time()
            res = import_issuecards_from_csv(ic_path, commit=commit, update=update, dry_run=dry_run, mapping=mp, batch_size=batch_size, offset=eff_offset, progress_callback=_ic_progress)
            duration = time.time() - start
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            self.stdout.write(str(res))
            processed = 0
            if isinstance(res, dict):
                for a in res.get('actions', []):
                    report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'issuecard', 'action': a.get('action'), 'identifier': a.get('identifier'), 'pk': a.get('pk')})
                processed = len(res.get('actions', []))
            else:
                report_rows.append({'timestamp': ts, 'duration_s': round(duration, 3), 'model': 'issuecard', 'action': 'create_many', 'identifier': None, 'pk': res})
                try:
                    processed = int(res or 0)
                except Exception:
                    processed = 0
            if processed:
                should_flush_final = (state_flush_interval <= 1) or ((int(state.get('issuecard', 0) or 0) % state_flush_interval) == 0)
                if (not dry_run or state_dry_run) and should_flush_final:
                    _save_state()
                    try:
                        self.stdout.write(f"Saved state for issuecard: {int(state.get('issuecard',0) or 0)}")
                    except Exception:
                        pass

        # write report CSV if requested
        if report_path:
            _write_report()
            self.stdout.write(f'Wrote report CSV to {report_path}')
