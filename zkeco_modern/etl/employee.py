import csv
import logging
from datetime import datetime
from typing import Optional

from django.db import transaction

from legacy_models.models import Employee, Dept

logger = logging.getLogger('zkeco.etl')


def _parse_date(s: str) -> Optional[datetime.date]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def _col_for_field(row, candidates):
    """Find first present column value from candidates in the CSV row dict."""
    for c in candidates:
        # case-insensitive handling: look for exact key and lower-case key
        if c in row and row[c] not in (None, ''):
            return row[c]
        low = c.lower()
        for k in row:
            if k.lower() == low and row[k] not in (None, ''):
                return row[k]
    return None


def import_employees_from_csv(csv_path: str, commit: bool = True, update: bool = False, dry_run: bool = False, mapping: dict | None = None, batch_size: int = 0, offset: int = 0, progress_callback=None):
    """Import employees from a CSV.

    Supports idempotent update (update=True), dry-run mode (dry_run=True), batching and offset for resumable imports.
    Mapping is a dict model_field -> list_of_candidate_csv_columns.
    Returns int for simple create-only calls (legacy) or a dict summary when update/dry_run/batching used.
    """
    default_mapping = {
        'userid': ['userid', 'user_id', 'id'],
        'badgenumber': ['badgenumber', 'badge', 'cardno'],
        'firstname': ['firstname', 'first_name', 'name'],
        'lastname': ['lastname', 'last_name'],
        'dept': ['dept', 'department', 'DeptName', 'deptname'],
        'email': ['email'],
        'identitycard': ['identitycard', 'idcard'],
        'acc_startdate': ['acc_startdate', 'accstartdate'],
        'acc_enddate': ['acc_enddate', 'accenddate'],
    }
    if mapping:
        for k, v in mapping.items():
            default_mapping[k] = v

    created = 0
    updated = 0
    skipped = 0
    actions = []

    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if dry_run:
        logger.info("Dry-run enabled: no DB writes will be performed")

    total_rows = len(rows)
    # apply offset
    if offset and offset > 0:
        rows = rows[offset:]

    def _iter_batches(items, size):
        if size and size > 0:
            for i in range(0, len(items), size):
                yield items[i:i+size]
        else:
            yield items

    processed = 0
    for batch in _iter_batches(rows, batch_size):
        with transaction.atomic():
            for row in batch:
                userid_raw = _col_for_field(row, default_mapping['userid'])
                badgenumber = _col_for_field(row, default_mapping['badgenumber'])
                # normalize userid to int when possible; if missing, set to None
                userid = None
                if userid_raw not in (None, ''):
                    try:
                        userid = int(userid_raw)
                    except Exception:
                        userid = None
                firstname = _col_for_field(row, default_mapping['firstname']) or ''
                lastname = _col_for_field(row, default_mapping['lastname']) or ''
                dept_name = _col_for_field(row, default_mapping['dept']) or 'Default'
                email = _col_for_field(row, default_mapping.get('email', []))
                identitycard = _col_for_field(row, default_mapping.get('identitycard', []))
                acc_start = _parse_date(_col_for_field(row, default_mapping.get('acc_startdate', [])) or '')
                acc_end = _parse_date(_col_for_field(row, default_mapping.get('acc_enddate', [])) or '')

                dept, _ = Dept.objects.get_or_create(DeptName=dept_name, defaults={'code': dept_name[:10]})

                if update:
                    # try to find existing by userid then badgenumber
                    obj = None
                    if userid:
                        try:
                            obj = Employee.objects.get(userid=userid)
                        except Employee.DoesNotExist:
                            obj = None
                    if obj is None and badgenumber:
                        try:
                            obj = Employee.objects.get(badgenumber=badgenumber)
                        except Employee.DoesNotExist:
                            obj = None

                    if obj:
                        changed = False
                        if firstname and obj.firstname != firstname:
                            obj.firstname = firstname
                            changed = True
                        if lastname and obj.lastname != lastname:
                            obj.lastname = lastname
                            changed = True
                        if email and getattr(obj, 'email', None) != email:
                            obj.email = email
                            changed = True
                        if identitycard and getattr(obj, 'identitycard', None) != identitycard:
                            obj.identitycard = identitycard
                            changed = True
                        if acc_start and getattr(obj, 'acc_startdate', None) != acc_start:
                            obj.acc_startdate = acc_start
                            changed = True
                        if acc_end and getattr(obj, 'acc_enddate', None) != acc_end:
                            obj.acc_enddate = acc_end
                            changed = True
                        if obj.defaultdept != dept:
                            obj.defaultdept = dept
                            changed = True

                        if changed:
                            if not dry_run and commit:
                                obj.save()
                            actions.append({'action': 'update', 'identifier': (userid or badgenumber), 'pk': getattr(obj, 'pk', None)})
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        if not dry_run and commit:
                            # creation requires a valid userid (database constraint)
                            if userid is None:
                                logger.warning('Skipping create for row without valid userid (badgenumber=%s)', badgenumber)
                                skipped += 1
                                continue
                            obj, created_flag = Employee.objects.get_or_create(
                                userid=userid,
                                defaults={
                                    'badgenumber': badgenumber or None,
                                    'firstname': firstname,
                                    'lastname': lastname,
                                    'defaultdept': dept,
                                    'email': email or None,
                                    'identitycard': identitycard or None,
                                    'acc_startdate': acc_start,
                                    'acc_enddate': acc_end,
                                }
                            )
                            pk = getattr(obj, 'pk', None)
                            if not created_flag:
                                # already exists - treat as skipped for create-only import
                                skipped += 1
                        else:
                            pk = None
                        actions.append({'action': 'create', 'identifier': (userid or badgenumber), 'pk': pk})
                        created += 1
                else:
                    # Creation requires a valid userid due to DB constraint; skip otherwise
                    if userid is None:
                        logger.warning('Skipping create for row without valid userid (badgenumber=%s)', badgenumber)
                        skipped += 1
                        actions.append({'action': 'skip', 'identifier': badgenumber, 'pk': None})
                        continue
                    if not dry_run and commit:
                        obj, created_flag = Employee.objects.get_or_create(
                            userid=userid,
                            defaults={
                                'badgenumber': badgenumber or None,
                                'firstname': firstname,
                                'lastname': lastname,
                                'defaultdept': dept,
                                'email': email or None,
                                'identitycard': identitycard or None,
                                'acc_startdate': acc_start,
                                'acc_enddate': acc_end,
                            }
                        )
                        pk = getattr(obj, 'pk', None)
                        if not created_flag:
                            skipped += 1
                    else:
                        pk = None
                    actions.append({'action': 'create', 'identifier': (userid or badgenumber), 'pk': pk})
                    created += 1

                # notify progress per row
                processed += 1
                try:
                    if progress_callback:
                        progress_callback(1)
                except Exception:
                    # don't let callback failures stop import
                    logger.exception('progress_callback failed')

        logger.info('Processed %d/%d rows (offset=%d)', processed, total_rows, offset)

    logger.info("Employees: created=%d updated=%d skipped=%d", created, updated, skipped)
    # Backwards-compatible return: if caller used simple create-only import (update/dry_run false),
    # return integer number of created rows for older callers. Otherwise return summary dict.
    if not update and not dry_run and batch_size == 0 and offset == 0:
        return created
    return {'created': created, 'updated': updated, 'skipped': skipped, 'actions': actions}
