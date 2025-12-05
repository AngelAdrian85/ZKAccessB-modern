"""
Script pentru crearea automată a unui angajat de test cu toate câmpurile completate.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from datetime import date
from zkeco_modern.agent.models import Employee, AccessLevel, EmployeeCard

# Creează sau obține departament
try:
    from legacy_models.models import Dept as LegacyDept
    dept, _ = LegacyDept.objects.get_or_create(
        DeptName='IT Department',
        defaults={'code': 'IT001'}
    )
except Exception:
    dept = None
    print("Warning: Legacy department not available")

# Șterge angajatul de test dacă există
Employee.objects.filter(card_number='TEST001').delete()

print("Creez angajat de test cu toate câmpurile completate...")

# Creează angajatul de test
employee = Employee.objects.create(
    # Core fields
    first_name='Ion',
    last_name='Popescu',
    card_number='TEST001',
    active=True,
    
    # Legacy bridge
    legacy_userid=1,
    
    # Personal information
    gender='M',
    ssn='1234567890123',
    birthday=date(1990, 5, 15),
    city='București',
    
    # Contact information
    mobile_phone='0723456789',
    home_phone='0213334444',
    phone='0213335555',
    email='ion.popescu@test.ro',
    
    # Address information
    homeaddress='Str. Exemplu Nr. 10, Sector 1',
    street='Str. Exemplu',
    identitycard='Bd. Unirii Nr. 20',
    
    # Card and access information
    card_type='SITE',
    site_code='001',
    password_on_record='123456',
    reservation_password='654321',
    selfpassword='',
    
    # Employment information
    hire_date=date(2020, 1, 15),
    hiretype='Full-time',
    emptype='Staff',
    privilege='User',
    role_on_device='Normal',
    
    # Access control settings
    acc_startdate=date(2020, 1, 15),
    acc_enddate=date(2025, 12, 31),
    extend_time=30,
    delayed_door_open=False,
    access_superuser=False,
    
    # Elevator control settings
    elevator_superuser=False,
    elevator_level='L1',
    
    # Multi-card support
    multi_card_group='',
    set_validity=True
)

print(f"✓ Angajat creat: {employee.first_name} {employee.last_name} (ID: {employee.id})")

# Adaugă card secundar
secondary_card = EmployeeCard.objects.create(
    employee=employee,
    card_number='TEST002'
)
print(f"✓ Card secundar adăugat: {secondary_card.card_number}")

# Adaugă nivele de acces dacă există
access_levels = AccessLevel.objects.all()[:2]
if access_levels:
    employee.access_levels.set(access_levels)
    print(f"✓ Nivele de acces adăugate: {', '.join([al.name for al in access_levels])}")
else:
    print("Warning: Nu există nivele de acces în baza de date")

print("\n" + "="*60)
print("DETALII ANGAJAT DE TEST:")
print("="*60)
print(f"Nr. Personal: {employee.legacy_userid}")
print(f"Nume complet: {employee.first_name} {employee.last_name}")
print(f"CNP: {employee.ssn}")
print(f"Gen: {employee.gender}")
print(f"Data nașterii: {employee.birthday}")
print(f"Oraș: {employee.city}")
print(f"Email: {employee.email}")
print(f"Telefon Birou: {employee.phone}")
print(f"Telefon Mobil: {employee.mobile_phone}")
print(f"Telefon Acasă: {employee.home_phone}")
print(f"Card Principal: {employee.card_number}")
print(f"Card Secundar: {secondary_card.card_number}")
print(f"Tip Card: {employee.card_type}")
print(f"Site Code: {employee.site_code}")
print(f"Parolă: {employee.password_on_record}")
print(f"Data angajării: {employee.hire_date}")
print(f"Tip angajare: {employee.hiretype}")
print(f"Tip personal: {employee.emptype}")
print(f"Adresă domiciliu: {employee.homeaddress}")
print(f"Adresă serviciu: {employee.identitycard}")
print(f"Access superuser: {employee.access_superuser}")
print(f"Elevator superuser: {employee.elevator_superuser}")
print(f"Activ: {employee.active}")
print("="*60)
print("✓ Angajat de test creat cu succes!")
print("Poți verifica în baza de date sau în interfața web.")
