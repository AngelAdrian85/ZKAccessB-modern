from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time, date

from .models import TimeSegment, Device, Door, Employee, AccessLevel, Holiday, CommandLog, EmployeeAccessCache, EmployeeCard

class CoreAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pass')

    def build_mask(self, days):
        m = 0
        for d in days:
            m |= (1 << d)
        return m

    def test_time_segment_overlap_days(self):
        TimeSegment.objects.create(name='WK Morning', start_time=time(9,0), end_time=time(10,0), days_mask=self.build_mask([0,1,2,3,4]))
        ts2 = TimeSegment(name='Sat Morning', start_time=time(9,0), end_time=time(10,0), days_mask=self.build_mask([5]))
        ts2.full_clean(); ts2.save()
        ts3 = TimeSegment(name='Tue Mid', start_time=time(9,30), end_time=time(9,45), days_mask=self.build_mask([1]))
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ts3.full_clean()

    def test_employee_crud(self):
        level = AccessLevel.objects.create(name='Office')
        resp = self.client.post('/agent/crud/employees/new/', {
            'first_name': 'Ana', 'last_name': 'Pop', 'card_number': 'CARD123', 'access_levels': [level.id], 'active': 'on'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Employee.objects.count(), 1)
        emp = Employee.objects.first()
        self.assertIn(level, emp.access_levels.all())

    def test_secondary_card_persistence(self):
        resp = self.client.post('/agent/crud/employees/new/', {
            'first_name': 'Bogdan', 'last_name': 'Ionescu', 'card_number': 'CARD200',
            'secondary_card_number': 'CARD200B', 'active': 'on'
        })
        self.assertEqual(resp.status_code, 200)
        emp = Employee.objects.first()
        self.assertTrue(EmployeeCard.objects.filter(employee=emp, card_number='CARD200B').exists())

    def test_door_pk_open_close(self):
        dev = Device.objects.create(name='Dev1')
        door = Door.objects.create(name='Door1', device=dev)
        r1 = self.client.get(f'/agent/api/doors/{door.id}/open/')
        self.assertJSONEqual(r1.content.decode(), {'ok': True})
        door.refresh_from_db(); self.assertTrue(door.is_open)
        r2 = self.client.get(f'/agent/api/doors/{door.id}/close/')
        self.assertJSONEqual(r2.content.decode(), {'ok': True})
        door.refresh_from_db(); self.assertFalse(door.is_open)
        self.assertTrue(CommandLog.objects.filter(command__contains='DOOR_OPEN').exists())

    def test_access_evaluation_api(self):
        dev = Device.objects.create(name='DevA')
        door = Door.objects.create(name='Front', device=dev)
        lvl = AccessLevel.objects.create(name='FrontAccess')
        lvl.doors.add(door)
        seg = TimeSegment.objects.create(name='Morning', start_time=time(9,0), end_time=time(11,0), days_mask=self.build_mask([0]))
        lvl.time_segments.add(seg)
        emp = Employee.objects.create(first_name='Ion', last_name='Ionescu', card_number='CARD999')
        emp.access_levels.add(lvl)
        resp = self.client.get(f'/agent/api/access/check/?employee={emp.id}&door={door.id}')
        data = resp.json(); self.assertTrue('allowed' in data)
        Holiday.objects.create(name='TestHol', date=date.today())
        resp2 = self.client.get(f'/agent/api/access/check/?employee={emp.id}&door={door.id}')
        data2 = resp2.json(); self.assertFalse(data2['allowed'])

    def test_bulk_import(self):
        AccessLevel.objects.create(name='Server')
        import io
        csv_content = 'Ana,Pop,C123,Server\nBogdan,Ion,C124,'
        f = io.BytesIO(csv_content.encode('utf-8'))
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile('emps.csv', f.getvalue(), content_type='text/csv')
        resp = self.client.post('/agent/crud/employees/import/', {'file': upload})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Employee.objects.count(), 2)
        self.assertTrue(Employee.objects.filter(card_number='C123').exists())
        exp = self.client.get('/agent/crud/employees/export/?format=csv')
        self.assertEqual(exp.status_code, 200)
        self.assertIn('employees.csv', exp.get('Content-Disposition',''))

    def test_access_cache(self):
        dev = Device.objects.create(name='DevB')
        door = Door.objects.create(name='Lab', device=dev)
        lvl = AccessLevel.objects.create(name='LabAccess')
        lvl.doors.add(door)
        seg = TimeSegment.objects.create(name='AllDay', start_time=time(0,0), end_time=time(23,59), days_mask=self.build_mask([0,1,2,3,4,5,6]))
        lvl.time_segments.add(seg)
        emp = Employee.objects.create(first_name='Eva', last_name='Test', card_number='EC1')
        emp.access_levels.add(lvl)
        r1 = self.client.get(f'/agent/api/access/check/?employee={emp.id}&door={door.id}')
        data1 = r1.json(); self.assertTrue(data1['allowed']); self.assertFalse(data1['cached'])
        self.assertTrue(EmployeeAccessCache.objects.filter(employee=emp, door=door).exists())
        r2 = self.client.get(f'/agent/api/access/check/?employee={emp.id}&door={door.id}')
        data2 = r2.json(); self.assertTrue(data2['allowed']); self.assertTrue(data2['cached'])

    def test_async_command_ack(self):
        dev = Device.objects.create(name='DevCmd')
        door = Door.objects.create(name='CmdDoor', device=dev)
        self.client.get(f'/agent/api/doors/{door.id}/open/')
        self.assertTrue(CommandLog.objects.filter(command__contains='DOOR_OPEN').exists())
        log = CommandLog.objects.filter(command__contains='DOOR_OPEN').latest('created_at')
        self.assertIn(log.status, ['PENDING','OK','ERR'])
        import time as _t
        for _ in range(10):
            _t.sleep(0.1)
            log.refresh_from_db()
            if log.status in ['OK','ERR']:
                break
        self.assertIn(log.status, ['OK','ERR'])
