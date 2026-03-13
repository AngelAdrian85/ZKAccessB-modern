import pytest
from django.core.cache import cache
from django.utils import timezone

from agent.models import AccessLevel, CommandLog, Device, DeviceRealtimeLog, Door, Employee, TimeSegment
from agent.modern_comm_center import ModernCommCenter
from agent.rtlog_entries import build_rtlog_entry
from agent.uid_correlation import remember_sniffed_uid


class _ProbeRtlogDriver:
    """Driver that returns RTLOG data once (to simulate connect probe drain)."""

    def __init__(self, payload: str):
        self._payloads = [payload]

    def connect(self):
        return {"result": 1, "hcommpro": 1}

    def disconnect(self):
        return {"result": 1}

    def get_rtlog(self):
        if self._payloads:
            return {"result": 1, "data": self._payloads.pop(0)}
        return {"result": 0, "data": ""}

    def get_transaction(self, newlog: bool = False):
        return {"result": 0, "data": {}}

    # Unused in this test; present for protocol completeness
    def query_data(self, table: str, fields: str, flt: str, extra: str):
        return {"result": 0, "data": {}}

    def update_data(self, table: str, data: str, extra: str):
        return {"result": 0, "data": {}}

    def delete_data(self, table: str, flt: str, extra: str):
        return {"result": 0, "data": {}}

    def Get_Data_Count(self, table: str):
        return {"result": 0}

    def controldevice(self, door: int, index: int, state: int):
        return {"result": 0}

    def control_normal_open(self, door: int, state: int):
        return {"result": 0}

    def cancel_alarm(self, door: str):
        return {"result": 0}

    def get_options(self, items: str):
        return {"result": 0, "data": ""}

    def set_options(self, items: str):
        return {"result": 0, "data": ""}


class _TxnCardFallbackDriver:
    def __init__(self, tx_line: str):
        self._tx_line = tx_line

    def connect(self):
        return {"result": 1, "hcommpro": 1}

    def disconnect(self):
        return {"result": 1}

    def get_rtlog(self):
        return {"result": 0, "data": ""}

    def get_transaction(self, newlog: bool = False):
        if self._tx_line:
            line = self._tx_line
            self._tx_line = ""
            return {"result": 1, "data": {1: line}}
        return {"result": 0, "data": {}}

    def query_data(self, table: str, fields: str, flt: str, extra: str):
        return {"result": 0, "data": {}}

    def update_data(self, table: str, data: str, extra: str):
        return {"result": 0, "data": {}}

    def delete_data(self, table: str, flt: str, extra: str):
        return {"result": 0, "data": {}}

    def Get_Data_Count(self, table: str):
        return {"result": 0}

    def controldevice(self, door: int, index: int, state: int):
        return {"result": 0}

    def control_normal_open(self, door: int, state: int):
        return {"result": 0}

    def cancel_alarm(self, door: str):
        return {"result": 0}

    def get_options(self, items: str):
        return {"result": 0, "data": ""}

    def set_options(self, items: str):
        return {"result": 0, "data": ""}


class _SyncNoopGuardDriver:
    def __init__(self):
        self.users: list[dict[str, str]] = []
        self.update_calls: list[str] = []

    def connect(self):
        return {"result": 1, "hcommpro": 1}

    def disconnect(self):
        return {"result": 1}

    def get_rtlog(self):
        return {"result": 0, "data": ""}

    def get_transaction(self, newlog: bool = False):
        return {"result": 0, "data": {}}

    def query_data(self, table: str, fields: str = '', filter: str = '', option: str = '', **kwargs):
        if table.lower() != 'user':
            return {"result": 1, "data": ""}

        flt = str(filter or kwargs.get('flt') or '').strip()
        rows = list(self.users)
        if flt:
            key, val = (flt.split('=', 1) + [''])[:2]
            key = key.strip().lower()
            val = val.strip().strip("'").strip('"')
            if key in ('pin', 'cardno'):
                rows = [r for r in rows if str(r.get(key, '')) == val]

        data = "Pin,CardNo,ViceCard,Group\r\n" + "\r\n".join(
            f"{r.get('pin', '')},{r.get('cardno', '')},{r.get('vicecard', '')},{r.get('group', '')}" for r in rows
        )
        return {"result": 1, "data": data}

    def update_data(self, table: str, data: str, extra: str):
        self.update_calls.append(table)
        if table.lower() == 'user':
            for line in (data or '').split("\r\n"):
                if not str(line or '').strip():
                    continue
                kv: dict[str, str] = {}
                for part in str(line).split("\t"):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        kv[k.strip().lower()] = v.strip()
                pin = str(kv.get('pin', '')).strip()
                card = str(kv.get('cardno', '')).strip()
                vice = str(kv.get('vicecard', '')).strip()
                group = str(kv.get('group', '')).strip()
                if pin:
                    self.users.append({'pin': pin, 'cardno': card, 'vicecard': vice, 'group': group})
        return {"result": 0, "data": {}}

    def delete_data(self, table: str, flt: str, extra: str = ''):
        return {"result": 0, "data": {}}

    def Get_Data_Count(self, table: str):
        if table.lower() == 'user':
            return {"result": len(self.users)}
        return {"result": 0}

    def controldevice(self, door: int, index: int, state: int):
        return {"result": 0}

    def control_normal_open(self, door: int, state: int):
        return {"result": 0}

    def cancel_alarm(self, door: str):
        return {"result": 0}

    def get_options(self, items: str):
        return {"result": 0, "data": ""}

    def set_options(self, items: str):
        return {"result": 0, "data": ""}


class _SyncWriteNoEffectDriver:
    def __init__(self):
        self.update_calls: list[str] = []

    def connect(self):
        return {"result": 1, "hcommpro": 1}

    def disconnect(self):
        return {"result": 1}

    def get_rtlog(self):
        return {"result": 0, "data": ""}

    def get_transaction(self, newlog: bool = False):
        return {"result": 0, "data": {}}

    def query_data(self, table: str, fields: str = '', filter: str = '', option: str = '', **kwargs):
        if str(table or '').lower() == 'user':
            return {"result": 1, "data": "Pin,CardNo\r\n"}
        return {"result": 1, "data": ""}

    def update_data(self, table: str, data: str, extra: str):
        self.update_calls.append(str(table or '').lower())
        return {"result": 0, "data": {}}

    def delete_data(self, table: str, flt: str, extra: str = ''):
        return {"result": 0, "data": {}}

    def Get_Data_Count(self, table: str):
        if str(table or '').lower() == 'user':
            return {"result": 0}
        return {"result": 0}

    def controldevice(self, door: int, index: int, state: int):
        return {"result": 0}

    def control_normal_open(self, door: int, state: int):
        return {"result": 0}

    def cancel_alarm(self, door: str):
        return {"result": 0}

    def get_options(self, items: str):
        return {"result": 0, "data": ""}

    def set_options(self, items: str):
        return {"result": 0, "data": ""}


@pytest.mark.django_db
def test_commcenter_connect_probe_persists_and_normalizes_rtlog():
    dev = Device.objects.create(
        name="CTRL_PROBE",
        serial_number="SN_PROBE_1",
        ip_address="192.168.1.99",
        port=4370,
        enabled=True,
    )

    # Tab-separated line (common on some firmware). CommCenter should normalize to commas.
    payload = "2026-02-20 10:00:00\t0\t123456\t1\t0\t0\r\n"

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _ProbeRtlogDriver(payload))

    # connect_all() performs an RTLOG probe; that probe must not drop real scans.
    center.connect_all()

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == dev.id
    assert row.sn == dev.serial_number
    assert row.raw.strip() == "2026-02-20 10:00:00,0,123456,1,0,0"

    # Also publish last card to cache for instant enrollment UI.
    cached = cache.get('agent:last_card_read')
    assert cached and cached.get('card_number') == '123456'
    assert cached.get('source') == 'controller_rtlog'


@pytest.mark.django_db
def test_commcenter_event_batch_falls_back_to_index_for_card_code():
    Device.objects.create(
        name="CTRL_TXN",
        serial_number="SN_TXN_1",
        ip_address="192.168.1.100",
        port=4370,
        enabled=True,
    )

    # Format B with empty cardno (field 8) but index present (field 7).
    tx_line = "0,4,1,27,0,840045753,04EEFF11,,0"

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _TxnCardFallbackDriver(tx_line))

    published = []
    center._publish_event = lambda payload: published.append(payload)
    center.run_once()

    evt = next((p for p in published if p.get("type") == "event.batch"), None)
    assert evt is not None
    cards = evt.get("card_nos") or []
    assert cards and cards[0] == "04EEFF11"
    entries = evt.get("entries") or []
    assert entries and entries[0].get("card_no") == "04EEFF11"
    assert entries[0].get("enrichment_source") == "rtlog.index"
    assert entries[0].get("enrichment_status") == "derived"


@pytest.mark.django_db
def test_commcenter_event_batch_does_not_use_small_numeric_index_as_card():
    Device.objects.create(
        name="CTRL_TXN_IDX",
        serial_number="SN_TXN_IDX_1",
        ip_address="192.168.1.101",
        port=4370,
        enabled=True,
    )

    # Format B with index at field 7 and empty cardno at field 8.
    # Index is a small sequence number and must not be interpreted as card.
    tx_line = "0,4,1,27,0,840045753,255,,0"

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _TxnCardFallbackDriver(tx_line))

    published = []
    center._publish_event = lambda payload: published.append(payload)
    center.run_once()

    evt = next((p for p in published if p.get("type") == "event.batch"), None)
    assert evt is not None
    cards = evt.get("card_nos") or []
    assert cards and cards[0] == ""
    entries = evt.get("entries") or []
    assert entries and entries[0].get("card_no") == ""
    assert entries[0].get("enrichment_status") == "unresolved"


@pytest.mark.django_db
def test_real_log_command_persists_and_broadcasts_rtlog():
    dev = Device.objects.create(
        name="CTRL_REALLOG_CMD",
        serial_number="SN_REALLOG_CMD_1",
        ip_address="192.168.1.102",
        port=4370,
        enabled=True,
    )

    payload = "2026-03-06 08:05:00\t0\t987654\t1\t27\t4\r\n"

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _ProbeRtlogDriver(payload))
    session = center.sessions[dev.id]
    assert session.connect() is True

    published = []
    center._publish_event = lambda payload: published.append(payload)

    cmd = CommandLog.objects.create(device=dev, command="REAL_LOG", status="PENDING")
    center._process_one_command()

    cmd.refresh_from_db()
    assert cmd.status == "OK"
    assert "count=1" in str(cmd.result)
    assert "2026-03-06 08:05:00,0,987654,1,27,4" in str(cmd.result)

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == dev.id
    assert row.raw.strip() == "2026-03-06 08:05:00,0,987654,1,27,4"

    evt = next((p for p in published if p.get("type") == "rtlog.batch"), None)
    assert evt is not None
    assert evt.get("device_id") == dev.id
    assert evt.get("lines") == ["2026-03-06 08:05:00,0,987654,1,27,4"]
    entries = evt.get("entries") or []
    assert entries and entries[0].get("card_no") == "987654"
    assert entries[0].get("source_format") == "timestamp-led"


@pytest.mark.django_db
def test_real_log_command_broadcast_includes_wiegand_correlation_payload():
    dev = Device.objects.create(
        name="CTRL_REALLOG_WG",
        serial_number="SN_REALLOG_WG_1",
        ip_address="192.168.1.106",
        port=4370,
        enabled=True,
    )

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _ProbeRtlogDriver("0,4,1,27,0,840045753,255,,0\r\n"))
    session = center.sessions[dev.id]
    assert session.connect() is True

    remember_sniffed_uid(
        device_id=dev.id,
        door_number='1',
        card_number='77665544',
        source='w26',
        payload={'reader': 'wiegand'},
    )

    published = []
    center._publish_event = lambda payload: published.append(payload)

    cmd = CommandLog.objects.create(device=dev, command="REAL_LOG", status="PENDING")
    center._process_one_command()

    cmd.refresh_from_db()
    assert cmd.status == "OK"

    evt = next((p for p in published if p.get("type") == "rtlog.batch"), None)
    assert evt is not None
    entries = evt.get("entries") or []
    assert entries
    assert (entries[0].get("correlation_payload") or {}).get("resolved_from_wiegand") is True
    assert (entries[0].get("correlation_payload") or {}).get("sniffed_card_number") == "77665544"


@pytest.mark.django_db
def test_commcenter_rtlog_entries_enrich_card_from_panel_user_map():
    dev = Device.objects.create(
        name="CTRL_PANEL_MAP",
        serial_number="SN_PANEL_MAP_1",
        ip_address="192.168.1.103",
        port=4370,
        enabled=True,
    )

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _ProbeRtlogDriver("0,4,1,27,0,840045753,255,,0\r\n"))
    session = center.sessions[dev.id]
    center._panel_card_cache[dev.id] = {"123": "99887766"}
    center._panel_card_cache_ts[dev.id] = 10**9

    entry = center._decoded_rtlog_entry(session, "123,4,1,0,0,840045753,255,,0")
    assert entry is not None
    assert entry.get("card_no") == "99887766"
    assert entry.get("enrichment_source") == "panel_user_map"
    assert entry.get("enrichment_status") == "enriched"
    assert entry.get("controller_event_status") == ""
    assert entry.get("controller_event_without_cardno") is False


@pytest.mark.django_db
def test_commcenter_rtlog_entries_mark_controller_events_without_cardno():
    dev = Device.objects.create(
        name="CTRL_NO_CARD",
        serial_number="SN_NO_CARD_1",
        ip_address="192.168.1.104",
        port=4370,
        enabled=True,
    )

    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: _ProbeRtlogDriver("0,4,1,27,0,840045753,255,,0\r\n"))
    session = center.sessions[dev.id]

    entry = center._decoded_rtlog_entry(session, "0,4,1,27,0,840045753,255,,0")
    assert entry is not None
    assert entry.get("card_no") == ""
    assert entry.get("enrichment_status") == "unresolved"
    assert entry.get("controller_event_status") == "controller-event-without-cardno"
    assert entry.get("controller_event_without_cardno") is True
    assert entry.get("card_display_status") == "valid_without_cardno"
    assert entry.get("card_display_label") == "Valid fara CardNo"
    assert "Eveniment valid" in str(entry.get("card_display_note") or "")


@pytest.mark.django_db
def test_rtlog_entry_correlates_recent_external_reader_card_for_missing_controller_cardno():
    dev = Device.objects.create(
        name="CTRL_CORRELATE",
        serial_number="SN_CORRELATE_1",
        ip_address="192.168.1.105",
        port=4370,
        enabled=True,
    )

    target_dt = timezone.localtime().replace(microsecond=0)
    target_ts = target_dt.strftime("%Y-%m-%d %H:%M:%S")
    secs = int((target_dt.replace(tzinfo=None) - timezone.datetime(2000, 1, 1, 0, 0, 0)).total_seconds())

    DeviceRealtimeLog.objects.create(
        device_id=dev.id,
        sn=dev.serial_number,
        raw=f"{target_ts},0,555444,1,0,CITITOR EXTERN,acp",
    )

    entry = build_rtlog_entry(
        f"0,4,1,27,0,{secs},255,,0",
        device_id=dev.id,
        serial_number=dev.serial_number,
    )

    assert entry is not None
    assert entry.get("card_no") == "555444"
    assert entry.get("card_no_raw") == "555444"
    assert entry.get("enrichment_status") == "enriched"
    assert entry.get("enrichment_source") == "external_reader_recent"
    assert "recent_external_reader_card_match" in str(entry.get("enrichment_note") or "")
    assert entry.get("controller_event_status") == ""
    assert entry.get("controller_event_without_cardno") is False


@pytest.mark.django_db
def test_sync_does_not_noop_when_device_user_table_empty():
    dev = Device.objects.create(
        name="CTRL_SYNC_GUARD",
        serial_number="SN_SYNC_GUARD_1",
        ip_address="192.168.1.210",
        port=4370,
        enabled=True,
    )
    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(name="ALWAYS", start_time="00:00:00", end_time="23:59:59", days_mask=127)
    level = AccessLevel.objects.create(name="AL_SYNC_GUARD")
    level.doors.add(door)
    level.time_segments.add(seg)
    emp = Employee.objects.create(first_name="Sync", last_name="Guard", card_number="123456", legacy_userid=91, active=True)
    emp.access_levels.add(level)

    driver = _SyncNoopGuardDriver()
    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: driver)
    session = center.sessions[dev.id]

    ok_first, info_first = center._sync_personnel_to_device(session)
    assert ok_first is True
    assert "synced" in str(info_first)
    assert driver.users

    CommandLog.objects.create(
        device=dev,
        command="SYNC_ALL",
        status="OK",
        result=str(info_first),
        executed_at=timezone.now(),
    )

    driver.users = []
    driver.update_calls = []

    ok_second, info_second = center._sync_personnel_to_device(session)
    assert ok_second is True
    assert "noop hash=" not in str(info_second)
    assert "synced" in str(info_second)
    assert 'user' in driver.update_calls


@pytest.mark.django_db
def test_sync_fails_when_write_has_no_effect_on_user_table(monkeypatch):
    monkeypatch.setenv('SYNC_ENFORCE_NO_EFFECT_GUARD', '1')
    dev = Device.objects.create(
        name="CTRL_SYNC_NO_EFFECT",
        serial_number="SN_SYNC_NO_EFFECT_1",
        ip_address="192.168.1.211",
        port=4370,
        enabled=True,
    )
    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(name="ALWAYS_NE", start_time="00:00:00", end_time="23:59:59", days_mask=127)
    level = AccessLevel.objects.create(name="AL_SYNC_NO_EFFECT")
    level.doors.add(door)
    level.time_segments.add(seg)
    emp = Employee.objects.create(first_name="No", last_name="Effect", card_number="123456", legacy_userid=92, active=True)
    emp.access_levels.add(level)

    driver = _SyncWriteNoEffectDriver()
    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: driver)
    session = center.sessions[dev.id]

    ok, info = center._sync_personnel_to_device(session)
    assert ok is False
    assert 'sync_no_effect:user_table_empty_after_write' in str(info)
    assert 'user' in driver.update_calls


@pytest.mark.django_db
def test_sync_personnel_writes_secondary_card_and_department_group():
    dev = Device.objects.create(
        name="CTRL_SYNC_MULTI",
        serial_number="SN_SYNC_MULTI_1",
        ip_address="192.168.1.212",
        port=4370,
        enabled=True,
        hardware_version="C3-200",
    )
    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(name="ALWAYS_MULTI", start_time="00:00:00", end_time="23:59:59", days_mask=127)
    level = AccessLevel.objects.create(name="AL_SYNC_MULTI")
    level.doors.add(door)
    level.time_segments.add(seg)
    emp = Employee.objects.create(
        first_name="Multi",
        last_name="Card",
        card_number="123456",
        secondary_card_number="654321",
        dept_id=7,
        legacy_userid=93,
        active=True,
    )
    emp.access_levels.add(level)

    driver = _SyncNoopGuardDriver()
    center = ModernCommCenter(poll_interval=0.1)
    center.build_sessions(lambda _dev: driver)
    session = center.sessions[dev.id]

    ok, info = center._sync_personnel_to_device(session)
    assert ok is True
    assert "synced" in str(info)
    assert driver.users
    row = driver.users[0]
    assert row["vicecard"] == "654321"
    assert row["group"] == "7"
