"""
Script de testare completă a formularului de angajat prin simulare POST
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json

# Creează user admin dacă nu există
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@test.ro',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin_user.set_password('adminpass')
    admin_user.save()
    print(f"✓ Admin user creat: admin / adminpass")

# Obține departament
try:
    from legacy_models.models import Dept as LegacyDept
    dept = LegacyDept.objects.first()
    dept_id = dept.id if dept else None
except:
    dept_id = None

# Creează client de test
client = Client()
client.force_login(admin_user)

print("\n" + "="*60)
print("TESTARE FORMULAR ANGAJAT PRIN MODAL")
print("="*60)

# Date complete pentru formular (toate câmpurile din modal)
form_data = {
    # Core fields (required)
    'first_name': 'Maria',
    'last_name': 'Ionescu',
    'card_number': 'CARD123',
    'active': 'on',  # checkbox
    
    # Legacy bridge
    'legacy_userid': '2',
    'dept': dept_id if dept_id else '',
    
    # Personal information
    'gender': 'F',
    'ssn': '2850101123456',
    'birthday': '1985-01-01',
    'city': 'Cluj-Napoca',
    
    # Contact information
    'mobile_phone': '0745123456',
    'home_phone': '0264123456',
    'phone': '0264123457',
    'email': 'maria.ionescu@test.ro',
    
    # Address information
    'homeaddress': 'Str. Libertății Nr. 25',
    'street': 'Str. Libertății',
    'identitycard': 'Bd. Muncii Nr. 10',
    
    # Card and access
    'card_type': 'SITE',
    'site_code': 'CLJ',
    'password_on_record': '654321',
    'reservation_password': '123456',
    'secondary_card_number': 'CARD124',
    
    # Employment
    'hire_date': '2023-03-15',
    'hiretype': 'Full-time',
    'emptype': 'Manager',
    'privilege': 'Admin',
    'role_on_device': 'Supervisor',
    
    # Access control
    'acc_startdate': '2023-03-15',
    'acc_enddate': '2026-12-31',
    'extend_time': '60',
    'delayed_door_open': 'on',
    'access_superuser': 'on',
    
    # Elevator
    'elevator_superuser': '',
    'elevator_level': 'L2',
    
    # Multi-card
    'multi_card_group': '',
    'set_validity': 'on',
}

print("\nTrimitem POST request cu date complete...")
print(f"Departament ID: {dept_id}")
print(f"Număr câmpuri: {len(form_data)}")

# Trimite POST request
response = client.post(
    '/agent/crud/employees/new/',
    data=form_data,
    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
)

print(f"\nStatus code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'N/A')}")

if response.status_code == 200:
    try:
        data = json.loads(response.content)
        print(f"\nRăspuns JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('ok'):
            print("\n✓ SUCCESS! Angajat creat cu succes!")
            print(f"  ID: {data.get('id')}")
            print(f"  Nume: {data.get('name')}")
            
            # Verifică în baza de date
            from zkeco_modern.agent.models import Employee
            emp = Employee.objects.get(id=data['id'])
            print(f"\n✓ Verificare baza de date:")
            print(f"  Nume complet: {emp.first_name} {emp.last_name}")
            print(f"  Card principal: {emp.card_number}")
            print(f"  CNP: {emp.ssn}")
            print(f"  Email: {emp.email}")
            print(f"  Oraș: {emp.city}")
            print(f"  Card secundar: {emp.cards.first().card_number if emp.cards.exists() else 'N/A'}")
        else:
            print("\n✗ ERORI în formular:")
            for field, errors in data.get('errors', {}).items():
                print(f"  {field}: {errors}")
    except json.JSONDecodeError:
        print(f"\nRăspuns non-JSON:")
        print(response.content.decode('utf-8')[:500])
else:
    print(f"\n✗ Eroare HTTP {response.status_code}")
    print(response.content.decode('utf-8')[:500])

print("="*60)
