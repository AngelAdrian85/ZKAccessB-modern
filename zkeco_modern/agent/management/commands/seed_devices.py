from django.core.management.base import BaseCommand
from agent.models import Device

SAMPLE = [
    dict(name='FINANCIAR', area_name='Financiar', ip_address='192.168.1.201', serial_number='SNFIN001', firmware_version='AC Ver 4.1.6'),
    dict(name='RU', area_name='Administrativ 1', ip_address='192.168.1.202', serial_number='SNRU002', firmware_version='AC Ver 4.1.9'),
    dict(name='Armament 1', area_name='Armament', ip_address='192.168.1.213', serial_number='SNARM003', firmware_version='AC Ver 4.1.9'),
    dict(name='Medical Acces Club', area_name='Medical', ip_address='192.168.1.203', serial_number='SNMED004', firmware_version='AC Ver 4.1.9'),
    dict(name='Medical acces Cabine', area_name='Medical', ip_address='192.168.1.204', serial_number='SNCAB005', firmware_version='AC Ver 4.3.4'),
    dict(name='Medical acces capela', area_name='Medical', ip_address='192.168.1.205', serial_number='SNCAP006', firmware_version='AC Ver 5.4.3'),
    dict(name='Dispercat', area_name='Dispercat', ip_address='192.168.1.209', serial_number='SNDISP007', firmware_version='AC Ver 18.1.3'),
    dict(name='B.T.I.C', area_name='Corp K', ip_address='192.168.1.207', serial_number='SNBTIC008', firmware_version='AC Ver 18.1.3'),
]

class Command(BaseCommand):
    help = 'Seed sample devices into Device model for UI prototype.'

    def handle(self, *args, **options):
        created = 0
        for data in SAMPLE:
            if not Device.objects.filter(name=data['name']).exists():
                Device.objects.create(**data)
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Seed complete. Created {created} devices. Total now {Device.objects.count()}'))
