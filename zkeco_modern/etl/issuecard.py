import csv
import logging

from django.db import transaction

from legacy_models.models import IssueCard, Employee

logger = logging.getLogger('zkeco.etl')


def _col_for_field(row, candidates):
    for c in candidates:
        if c in row and row[c] not in (None, ''):
            return row[c]
        for k in row:
            if k.lower() == c.lower() and row[k] not in (None, ''):
                return row[k]
    return None


def import_issuecards_from_csv(csv_path: str, commit: bool = True, update: bool = False, dry_run: bool = False, mapping: dict | None = None, batch_size: int = 0, offset: int = 0, progress_callback=None):
    """Import issue cards with optional update and dry-run.

    Mapping keys: cardno, cardstatus, userid
    Returns summary dict: {'created': int, 'updated': int, 'skipped': int}
    """
    default_mapping = {
        'cardno': ['cardno', 'card_no', 'cardnumber', 'card'],
        'cardstatus': ['cardstatus', 'status'],
        'userid': ['userid', 'user_id'],
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
        logger.info("Dry-run enabled for issuecards")

    total_rows = len(rows)
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
                try:
                    cardno = _col_for_field(row, default_mapping['cardno'])
                    if not cardno:
                        continue
                    cardstatus = _col_for_field(row, default_mapping['cardstatus'])
                    userid_raw = _col_for_field(row, default_mapping['userid'])
                    user = None
                    if userid_raw not in (None, ''):
                        try:
                            userid_val = int(userid_raw)
                        except Exception:
                            userid_val = userid_raw
                        try:
                            user = Employee.objects.get(userid=userid_val)
                        except Employee.DoesNotExist:
                            user = None

                    if update:
                        try:
                            obj = IssueCard.objects.get(cardno=cardno)
                            changed = False
                            if cardstatus and obj.cardstatus != cardstatus:
                                obj.cardstatus = cardstatus
                                changed = True
                            if user and obj.userid != user:
                                obj.userid = user
                                changed = True
                            if changed:
                                if not dry_run and commit:
                                    obj.save()
                                actions.append({'action': 'update', 'identifier': cardno, 'pk': getattr(obj, 'pk', None)})
                                updated += 1
                            else:
                                skipped += 1
                        except IssueCard.DoesNotExist:
                            if not dry_run and commit:
                                obj = IssueCard.objects.create(cardno=cardno, cardstatus=cardstatus or None, userid=user)
                                pk = getattr(obj, 'pk', None)
                            else:
                                pk = None
                            actions.append({'action': 'create', 'identifier': cardno, 'pk': pk})
                            created += 1
                    else:
                        if not dry_run and commit:
                            obj = IssueCard.objects.create(cardno=cardno, cardstatus=cardstatus or None, userid=user)
                            pk = getattr(obj, 'pk', None)
                        else:
                            pk = None
                        actions.append({'action': 'create', 'identifier': cardno, 'pk': pk})
                        created += 1
                except Exception:
                    logger.exception('Error processing issuecard row: %r', row)
                    continue

                # per-row progress callback
                try:
                    if progress_callback:
                        progress_callback(1)
                except Exception:
                    logger.exception('issuecard progress_callback failed')

        processed += len(batch)
        logger.info('Processed %d/%d issuecard rows (offset=%d)', processed, total_rows, offset)

    logger.info("IssueCards: created=%d updated=%d skipped=%d", created, updated, skipped)
    if not update and not dry_run and batch_size == 0 and offset == 0:
        return created
    return {'created': created, 'updated': updated, 'skipped': skipped, 'actions': actions}
