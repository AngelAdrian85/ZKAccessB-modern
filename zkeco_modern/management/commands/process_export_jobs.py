import json
import os
import csv
import time
from pathlib import Path

from django.core.management.base import BaseCommand

from django.conf import settings


def _default_job_dir():
    return Path(getattr(settings, 'IACCESS_EXPORT_JOB_DIR', 'export_jobs'))


def _default_output_dir():
    return Path(getattr(settings, 'IACCESS_EXPORT_OUTPUT_DIR', 'export_outputs'))


class Command(BaseCommand):
    help = 'Process queued export job JSON files in the export_jobs directory and write CSV outputs.'

    def add_arguments(self, parser):
        parser.add_argument('--jobs-dir', dest='jobs_dir', help='Path to job directory', default=None)
        parser.add_argument('--output-dir', dest='output_dir', help='Path to output directory', default=None)

    def handle(self, *args, **options):
        jobs_dir = Path(options.get('jobs_dir') or _default_job_dir())
        out_dir = Path(options.get('output_dir') or _default_output_dir())
        jobs_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f'Scanning jobs in {jobs_dir}...')
        for p in sorted(jobs_dir.glob('*.json')):
            try:
                raw = json.loads(p.read_text(encoding='utf-8'))
            except Exception as e:
                self.stderr.write(f'Failed to read job {p}: {e}')
                continue
            status = raw.get('status')
            if status and status != 'pending':
                continue

            job_id = raw.get('id') or p.stem
            self.stdout.write(f'Processing job {job_id}...')
            # mark running
            raw['status'] = 'running'
            raw['started_at'] = time.time()
            p.write_text(json.dumps(raw), encoding='utf-8')

            # perform export of AccessLog using provided filters
            try:
                from legacy_models.models import AccessLog
            except Exception:
                AccessLog = None

            out_path = out_dir / f'{job_id}.csv'
            try:
                if AccessLog is None:
                    raise RuntimeError('AccessLog model not available')

                qs = AccessLog.objects.all()
                filters = raw.get('filters') or {}
                # support simple filters: q, door, device, event_type, start, end
                q = filters.get('q')
                if q:
                    if str(q).isdigit():
                        qs = qs.filter(userid__userid=int(q))
                    else:
                        qs = qs.filter(cardno__icontains=q)
                if filters.get('door'):
                    qs = qs.filter(door_id=int(filters.get('door')))
                if filters.get('device'):
                    qs = qs.filter(device_id=int(filters.get('device')))
                if filters.get('event_type'):
                    qs = qs.filter(event_type__iexact=filters.get('event_type'))
                # TODO: datetime parsing if provided

                with open(out_path, 'w', newline='', encoding='utf-8') as outf:
                    writer = csv.writer(outf)
                    writer.writerow(['timestamp', 'userid', 'cardno', 'door', 'device', 'event_type', 'result', 'info'])
                    for row in qs.order_by('-timestamp').iterator():
                        writer.writerow([
                            row.timestamp.isoformat() if row.timestamp else '',
                            row.userid.userid if row.userid else '',
                            row.cardno or '',
                            row.door.name if row.door else '',
                            row.device.device_name if row.device else '',
                            row.event_type or '',
                            row.result or '',
                            (row.info or '')[:1000],
                        ])

                raw['status'] = 'done'
                raw['output'] = str(out_path)
                raw['finished_at'] = time.time()
                p.write_text(json.dumps(raw), encoding='utf-8')
                self.stdout.write(f'Wrote export to {out_path}')
            except Exception as e:
                raw['status'] = 'failed'
                raw['error'] = str(e)
                raw['finished_at'] = time.time()
                p.write_text(json.dumps(raw), encoding='utf-8')
                self.stderr.write(f'Job {job_id} failed: {e}')
