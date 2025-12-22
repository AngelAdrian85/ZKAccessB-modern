"""
Script pentru crearea datelor de test complete (access levels, doors, etc.)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from agent.models import AccessLevel, Door, Device

print("Creez date de test pentru Access Levels...")

# Creează device de test dacă nu există
device, created = Device.objects.get_or_create(
    name='Device Test',
    defaults={
        'serial_number': 'TEST001',
        'device_type': 'access_panel',
        'comm_mode': 'tcp',
        'ip_address': '192.168.1.100',
        'port': 4370,
        'enabled': True
    }
)
if created:
    print(f"✓ Device creat: {device.name}")

# Creează uși de test
doors_data = [
    {'name': 'FINANCIAR', 'location': 'Etaj 1'},
    {'name': 'MEDICAL', 'location': 'Etaj 2'},
    {'name': 'B.T.I.C', 'location': 'Etaj 3'},
    {'name': 'DISPENSAR', 'location': 'Parter'},
    {'name': 'EVIDENTA', 'location': 'Etaj 1'},
    {'name': 'RU', 'location': 'Etaj 2'},
    {'name': 'SECRETARIAT', 'location': 'Parter'},
]

doors = []
for door_data in doors_data:
    door, created = Door.objects.get_or_create(
        name=door_data['name'],
        defaults={
            'location': door_data['location'],
            'device': device,
            'enabled': True
        }
    )
    doors.append(door)
    if created:
        print(f"✓ Ușă creată: {door.name} ({door.location})")

# Creează nivele de acces
access_levels_data = [
    {'name': 'ASMANENT', 'doors': ['FINANCIAR', 'MEDICAL']},
    {'name': 'B.T.I.C', 'doors': ['B.T.I.C']},
    {'name': 'Dispensar', 'doors': ['DISPENSAR']},
    {'name': 'EVIDENTA', 'doors': ['EVIDENTA']},
    {'name': 'Medical acces', 'doors': ['MEDICAL']},
    {'name': 'Personal Medical', 'doors': ['MEDICAL', 'DISPENSAR']},
    {'name': 'RU', 'doors': ['RU']},
    {'name': 'SECRETARIAT', 'doors': ['SECRETARIAT']},
]

for al_data in access_levels_data:
    al, created = AccessLevel.objects.get_or_create(
        name=al_data['name'],
        defaults={'description': f"Access level pentru {al_data['name']}"}
    )
    if created or al.doors.count() == 0:
        # Adaugă ușile
        for door_name in al_data['doors']:
            door = Door.objects.filter(name=door_name).first()
            if door:
                al.doors.add(door)
        print(f"✓ Access Level creat: {al.name} ({al.doors.count()} uși)")

print("\n" + "="*60)
print("✓ Date de test create cu succes!")
print("="*60)
print(f"Device: {Device.objects.count()}")
print(f"Doors: {Door.objects.count()}")
print(f"Access Levels: {AccessLevel.objects.count()}")
print("="*60)
