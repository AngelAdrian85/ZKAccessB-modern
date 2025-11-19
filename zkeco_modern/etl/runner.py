"""Small runner to call the ETL importers for multiple CSVs."""
from typing import Optional, Callable


def run_all(employee_csv: Optional[str] = None, issuecard_csv: Optional[str] = None, device_csv: Optional[str] = None, progress_callback: Callable | None = None):
    """Run available importers and optionally forward a per-row progress callback.

    The `progress_callback` will be called by each importer for every processed
    row if provided. Return a dict of results keyed by model name.
    """
    results = {}
    if employee_csv:
        from .employee import import_employees_from_csv

        results['employees'] = import_employees_from_csv(employee_csv, progress_callback=progress_callback)
    if issuecard_csv:
        from .issuecard import import_issuecards_from_csv

        results['issuecards'] = import_issuecards_from_csv(issuecard_csv, progress_callback=progress_callback)
    if device_csv:
        from .device import import_devices_from_csv

        results['devices'] = import_devices_from_csv(device_csv, progress_callback=progress_callback)
    return results
