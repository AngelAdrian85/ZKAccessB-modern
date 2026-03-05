import datetime

import pytest
from django.contrib.auth.models import User

from agent.models import AccessLevel, CommandLog, Device, Door, Employee, TimeSegment


class DummyCenter:
    def __init__(self):
        self.enqueued = []

    def enqueue_command(self, device_id: int, cmd: str) -> None:
        self.enqueued.append((int(device_id), str(cmd)))


@pytest.mark.django_db
def test_device_sync_personnel_requires_staff(client):
    dev = Device.objects.create(
        name="CTRL1",
        serial_number="SN_SYNC_1",
        ip_address="192.168.50.10",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-personnel/", data="{}", content_type="application/json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_device_sync_personnel_rejects_non_physical(client):
    u = User.objects.create_user("staff_sync1", "s@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync1", password="pass")

    dev = Device.objects.create(
        name="TEST_CTRL",
        serial_number="SN_SYNC_TEST",
        ip_address="192.168.50.11",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-personnel/", data="{}", content_type="application/json")
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False
    assert body.get("error") in ("device-not-physical", "device-not-physical")


@pytest.mark.django_db
def test_device_sync_personnel_requires_syncable_employees(client):
    u = User.objects.create_user("staff_sync2", "s2@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync2", password="pass")

    dev = Device.objects.create(
        name="CTRL_NO_EMP",
        serial_number="SN_SYNC_2",
        ip_address="192.168.50.12",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-personnel/", data="{}", content_type="application/json")
    assert r.status_code == 400
    assert r.json().get("error") == "no_syncable_employees"


@pytest.mark.django_db
def test_device_sync_personnel_enqueues_commandlog_without_starting_real_center(client):
    u = User.objects.create_user("staff_sync3", "s3@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync3", password="pass")

    dev = Device.objects.create(
        name="CTRL_OK",
        serial_number="SN_SYNC_3",
        ip_address="192.168.50.13",
        port=4370,
        enabled=True,
        device_type="access_panel",
        comm_mode="tcp",
    )

    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(
        name="ALWAYS",
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 59, 59),
        days_mask=127,
    )
    level = AccessLevel.objects.create(name="AL_SYNC")
    level.doors.add(door)
    level.time_segments.add(seg)

    emp = Employee.objects.create(first_name="A", last_name="B", card_number="123", legacy_userid=10, active=True)
    emp.access_levels.add(level)

    import agent.modern_comm_center as mcc

    prev = getattr(mcc, "ACTIVE_CENTER", None)
    prev_build = getattr(mcc, "build_and_run_stub", None)
    dummy = DummyCenter()
    mcc.ACTIVE_CENTER = dummy
    # Ensure that even if views tries to start a center, it will get our dummy.
    mcc.build_and_run_stub = lambda *args, **kwargs: dummy
    try:
        r = client.post(f"/agent/api/devices/{dev.id}/sync-personnel/", data="{}", content_type="application/json")
        assert r.status_code == 200
        body = r.json()
        assert body.get("ok") is True
        cmd_id = int(body.get("command_id") or 0)
        assert cmd_id > 0
        assert int(body.get("syncable_employees") or 0) >= 1

        cmd = CommandLog.objects.get(pk=cmd_id)
        assert cmd.device_id == dev.id
        assert cmd.command.startswith("SYNC_ALL") or cmd.command.startswith("SYNC_PERSONNEL")
        # Enqueue may be in-process (ACTIVE_CENTER) or DB-only fallback.
        # The contract here is that we persist a CommandLog row and return its id.
    finally:
        mcc.ACTIVE_CENTER = prev
        if prev_build is not None:
            mcc.build_and_run_stub = prev_build


@pytest.mark.django_db
def test_device_sync_access_levels_requires_staff(client):
    dev = Device.objects.create(
        name="CTRL1",
        serial_number="SN_SYNC_AL_1",
        ip_address="192.168.50.20",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-access-levels/", data="{}", content_type="application/json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_device_sync_access_levels_rejects_non_physical(client):
    u = User.objects.create_user("staff_sync_al1", "s@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync_al1", password="pass")

    dev = Device.objects.create(
        name="TEST_CTRL",
        serial_number="SN_SYNC_AL_TEST",
        ip_address="192.168.50.21",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-access-levels/", data="{}", content_type="application/json")
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False
    assert body.get("error") in ("device-not-physical", "device-not-physical")


@pytest.mark.django_db
def test_device_sync_access_levels_requires_syncable_employees(client):
    u = User.objects.create_user("staff_sync_al2", "s2@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync_al2", password="pass")

    dev = Device.objects.create(
        name="CTRL_NO_EMP",
        serial_number="SN_SYNC_AL_2",
        ip_address="192.168.50.22",
        port=4370,
        enabled=True,
    )

    r = client.post(f"/agent/api/devices/{dev.id}/sync-access-levels/", data="{}", content_type="application/json")
    assert r.status_code == 400
    assert r.json().get("error") == "no_syncable_employees"


@pytest.mark.django_db
def test_device_sync_access_levels_enqueues_commandlog(client):
    u = User.objects.create_user("staff_sync_al3", "s3@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync_al3", password="pass")

    dev = Device.objects.create(
        name="CTRL_OK",
        serial_number="SN_SYNC_AL_3",
        ip_address="192.168.50.23",
        port=4370,
        enabled=True,
        device_type="access_panel",
        comm_mode="tcp",
    )

    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(
        name="ALWAYS",
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 59, 59),
        days_mask=127,
    )
    level = AccessLevel.objects.create(name="AL_SYNC2")
    level.doors.add(door)
    level.time_segments.add(seg)

    emp = Employee.objects.create(first_name="A", last_name="B", card_number="124", legacy_userid=11, active=True)
    emp.access_levels.add(level)

    import agent.modern_comm_center as mcc

    prev = getattr(mcc, "ACTIVE_CENTER", None)
    prev_build = getattr(mcc, "build_and_run_stub", None)
    dummy = DummyCenter()
    mcc.ACTIVE_CENTER = dummy
    mcc.build_and_run_stub = lambda *args, **kwargs: dummy
    try:
        r = client.post(f"/agent/api/devices/{dev.id}/sync-access-levels/", data="{}", content_type="application/json")
        assert r.status_code == 200
        body = r.json()
        assert body.get("ok") is True
        cmd_id = int(body.get("command_id") or 0)
        assert cmd_id > 0

        cmd = CommandLog.objects.get(pk=cmd_id)
        assert cmd.device_id == dev.id
        assert cmd.command.startswith("SYNC_ACCESS_LEVELS") or cmd.command.startswith("SYNC_PERSONNEL")
    finally:
        mcc.ACTIVE_CENTER = prev
        if prev_build is not None:
            mcc.build_and_run_stub = prev_build


@pytest.mark.django_db
def test_device_sync_all_enqueues_commandlog(client):
    u = User.objects.create_user("staff_sync_all1", "s_all@b.c", "pass")
    u.is_staff = True
    u.save()
    assert client.login(username="staff_sync_all1", password="pass")

    dev = Device.objects.create(
        name="CTRL_OK",
        serial_number="SN_SYNC_ALL_1",
        ip_address="192.168.50.30",
        port=4370,
        enabled=True,
        device_type="access_panel",
        comm_mode="tcp",
    )

    door = Door.objects.create(name="D1", device=dev, door_number=1)
    seg = TimeSegment.objects.create(
        name="ALWAYS",
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 59, 59),
        days_mask=127,
    )
    level = AccessLevel.objects.create(name="AL_SYNC_ALL")
    level.doors.add(door)
    level.time_segments.add(seg)

    emp = Employee.objects.create(first_name="A", last_name="B", card_number="125", legacy_userid=12, active=True)
    emp.access_levels.add(level)

    import agent.modern_comm_center as mcc

    prev = getattr(mcc, "ACTIVE_CENTER", None)
    prev_build = getattr(mcc, "build_and_run_stub", None)
    dummy = DummyCenter()
    mcc.ACTIVE_CENTER = dummy
    mcc.build_and_run_stub = lambda *args, **kwargs: dummy
    try:
        r = client.post(f"/agent/api/devices/{dev.id}/sync/", data="{}", content_type="application/json")
        assert r.status_code == 200
        body = r.json()
        assert body.get("ok") is True
        cmd_id = int(body.get("command_id") or 0)
        assert cmd_id > 0

        cmd = CommandLog.objects.get(pk=cmd_id)
        assert cmd.device_id == dev.id
        assert cmd.command.startswith("SYNC_ALL") or cmd.command.startswith("SYNC_PERSONNEL") or cmd.command.startswith("SYNC_ACCESS_LEVELS")
    finally:
        mcc.ACTIVE_CENTER = prev
        if prev_build is not None:
            mcc.build_and_run_stub = prev_build
