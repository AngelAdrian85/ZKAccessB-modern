from django.test import TestCase, RequestFactory
from django.urls import reverse
from zkeco_modern.iaccess_port import views

from legacy_models.models import AccessLog, Employee, Door, Device
from django.utils import timezone
from django.contrib.auth import get_user_model

class AccessLogViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # create sample data
        self.emp = Employee.objects.create(userid=1001, firstname='Test', lastname='User')
        self.door = Door.objects.create(name='Main Door')
        self.device = Device.objects.create(device_name='Panel 1')
        for i in range(30):
            AccessLog.objects.create(
                timestamp=timezone.now(),
                userid=self.emp,
                cardno=f'CARD{i}',
                door=self.door,
                device=self.device,
                event_type='open',
                result='ok',
                info='ok',
            )
        # create a staff user for CSV export tests
        User = get_user_model()
        self.staff = User.objects.create(username='staff', is_staff=True)

    def test_logs_page_renders(self):
        req = self.factory.get('/iaccess/logs/')
        resp = views.access_log(req)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Access Logs', resp.content)

    def test_csv_export(self):
        req = self.factory.get('/iaccess/logs/?export=csv')
        # attach a staff user to pass permission check
        req.user = self.staff
        resp = views.access_log(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        # StreamingHttpResponse doesn't expose .content; collect streaming_content
        if hasattr(resp, 'streaming_content'):
            parts = []
            for chunk in resp.streaming_content:
                if isinstance(chunk, bytes):
                    parts.append(chunk.decode('utf-8'))
                else:
                    parts.append(str(chunk))
            content = ''.join(parts)
        else:
            content = resp.content.decode('utf-8')

        # header + 30 lines
        lines = content.strip().splitlines()
        self.assertTrue(lines[0].startswith('timestamp,userid,cardno'))
        self.assertTrue(len(lines) >= 31)
