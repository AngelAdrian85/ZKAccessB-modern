import pytest

from agent.models import AuditLog, Device, Door
from agent.views import _broadcast_door_event


@pytest.mark.django_db
def test_broadcast_door_event_persists_audit_deduped():
    dev = Device.objects.create(name='Dev', serial_number='SN_TEST_DOOR', ip_address='1.2.3.4')
    door = Door.objects.create(name='Door 1', device=dev, door_number=1)

    AuditLog.objects.filter(module='door').delete()

    _broadcast_door_event(dev.id, door, 'door.open', verify_mode='AUTO(5s)')
    _broadcast_door_event(dev.id, door, 'door.open', verify_mode='AUTO(5s)')

    assert AuditLog.objects.filter(module='door', action='open', entity_id=door.id).count() == 1
