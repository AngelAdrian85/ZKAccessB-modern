import csv
import logging

from django.db import transaction

from legacy_models.models import Device, Area

logger = logging.getLogger('zkeco.etl')


def _col_for_field(row, candidates):
    for c in candidates:
        if c in row and row[c] not in (None, ''):
            return row[c]
        for k in row:
            if k.lower() == c.lower() and row[k] not in (None, ''):
                return row[k]
    return None


def import_devices_from_csv(csv_path: str, commit: bool = True, update: bool = False, dry_run: bool = False, mapping: dict | None = None, batch_size: int = 0, offset: int = 0, progress_callback=None):
    """Import devices with update and dry-run support.

    Mapping keys: sn, device_name, device_type, area_name, fw_version, com_port, com_address, fp_count, transaction_count, acpanel_type
    Returns summary dict.
    """
    default_mapping = {
        'sn': ['sn', 'serial', 'serial_no'],
        'device_name': ['device_name', 'name'],
        'device_type': ['device_type', 'type'],
        'area_name': ['area_name', 'area'],
        'fw_version': ['fw_version', 'firmware'],
        'com_port': ['com_port'],
        'com_address': ['com_address'],
        'fp_count': ['fp_count', 'fpcnt'],
        'transaction_count': ['transaction_count', 'trans_count'],
        'acpanel_type': ['acpanel_type'],
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
        logger.info("Dry-run enabled for devices")

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
                sn = _col_for_field(row, default_mapping['sn'])
                if not sn:
                    continue
                device_name = _col_for_field(row, default_mapping['device_name'])
                device_type = _col_for_field(row, default_mapping['device_type'])
                area_name = _col_for_field(row, default_mapping['area_name'])
                fw_version = _col_for_field(row, default_mapping['fw_version'])
                com_port = _col_for_field(row, default_mapping['com_port'])
                com_address = _col_for_field(row, default_mapping['com_address'])
                fp_count = _col_for_field(row, default_mapping['fp_count'])
                trans_count = _col_for_field(row, default_mapping['transaction_count'])
                acpanel_type = _col_for_field(row, default_mapping['acpanel_type'])

                area = None
                if area_name:
                    area, _ = Area.objects.get_or_create(areaname=area_name)

                if update:
                    try:
                        obj = Device.objects.get(sn=sn)
                        changed = False
                        if device_name and obj.device_name != device_name:
                            obj.device_name = device_name
                            changed = True
                        if fw_version and obj.fw_version != fw_version:
                            obj.fw_version = fw_version
                            changed = True
                        if com_port and obj.com_port != com_port:
                            obj.com_port = com_port
                            changed = True
                        if com_address and obj.com_address != com_address:
                            obj.com_address = com_address
                            changed = True
                        if fp_count and (obj.fp_count != int(fp_count) if fp_count.isdigit() else True):
                            try:
                                obj.fp_count = int(fp_count)
                            except Exception:
                                obj.fp_count = None
                            changed = True
                        if trans_count and (obj.transaction_count != int(trans_count) if trans_count.isdigit() else True):
                            try:
                                obj.transaction_count = int(trans_count)
                            except Exception:
                                obj.transaction_count = None
                            changed = True
                        if acpanel_type and obj.acpanel_type != acpanel_type:
                            obj.acpanel_type = acpanel_type
                            changed = True
                        if area and obj.area != area:
                            obj.area = area
                            changed = True

                        if changed:
                            if not dry_run and commit:
                                obj.save()
                            actions.append({'action': 'update', 'identifier': sn, 'pk': getattr(obj, 'pk', None)})
                            updated += 1
                        else:
                            skipped += 1
                    except Device.DoesNotExist:
                        if not dry_run and commit:
                            obj = Device.objects.create(
                                sn=sn,
                                device_name=device_name or None,
                                device_type=int(device_type) if (device_type and device_type.isdigit()) else 0,
                                area=area,
                                fw_version=fw_version or None,
                                com_port=com_port or None,
                                com_address=com_address or None,
                                fp_count=int(fp_count) if (fp_count and fp_count.isdigit()) else None,
                                transaction_count=int(trans_count) if (trans_count and trans_count.isdigit()) else None,
                                acpanel_type=acpanel_type or None,
                            )
                            pk = getattr(obj, 'pk', None)
                        else:
                            pk = None
                        actions.append({'action': 'create', 'identifier': sn, 'pk': pk})
                        created += 1
                else:
                    if not dry_run and commit:
                        obj = Device.objects.create(
                            sn=sn,
                            device_name=device_name or None,
                            device_type=int(device_type) if (device_type and device_type.isdigit()) else 0,
                            area=area,
                            fw_version=fw_version or None,
                            com_port=com_port or None,
                            com_address=com_address or None,
                            fp_count=int(fp_count) if (fp_count and fp_count.isdigit()) else None,
                            transaction_count=int(trans_count) if (trans_count and trans_count.isdigit()) else None,
                            acpanel_type=acpanel_type or None,
                        )
                        pk = getattr(obj, 'pk', None)
                    else:
                        pk = None
                    actions.append({'action': 'create', 'identifier': sn, 'pk': pk})
                    created += 1

                # per-row progress callback
                try:
                    if progress_callback:
                        progress_callback(1)
                except Exception:
                    logger.exception('device progress_callback failed')

        processed += len(batch)
        logger.info('Processed %d/%d device rows (offset=%d)', processed, total_rows, offset)

    logger.info("Devices: created=%d updated=%d skipped=%d", created, updated, skipped)
    if not update and not dry_run and batch_size == 0 and offset == 0:
        return created
    return {'created': created, 'updated': updated, 'skipped': skipped, 'actions': actions}
