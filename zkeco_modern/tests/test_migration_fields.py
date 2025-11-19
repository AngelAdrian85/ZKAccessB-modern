from django.test import TestCase


class MigrationFieldsSmoke(TestCase):
    def test_employee_additional_fields(self):
        from legacy_models.models import Employee

        e = Employee.objects.create(
            userid=2002,
            firstname='Jane',
            lastname='Roe',
            email='jane.roe@example.local',
            identitycard='ID2002',
            Password='x',
            FPHONE='12345',
        )

        self.assertEqual(e.email, 'jane.roe@example.local')
        self.assertEqual(e.identitycard, 'ID2002')
