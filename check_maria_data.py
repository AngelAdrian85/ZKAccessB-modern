import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from agent.models import Employee

print("="*60)
print("VERIFICARE MARIA IONESCU - Date din DB")
print("="*60)

# Caută Maria Ionescu
employees = Employee.objects.filter(first_name__icontains='Maria', last_name__icontains='Ionescu')
print(f"\nGăsite {employees.count()} înregistrări:")

for e in employees:
    print(f"\n  ID: {e.id}")
    print(f"  Nume: {e.first_name} {e.last_name}")
    print(f"  legacy_userid (Employee model): {e.legacy_userid}")
    print(f"  card_number: {e.card_number}")
    print(f"  email: {e.email}")
    print(f"  mobile_phone: {e.mobile_phone}")
    
    # Verifică și în legacy dacă există
    try:
        from legacy_models.models import Employee as LegacyEmployee
        legacy = LegacyEmployee.objects.filter(card_number=e.card_number).first()
        if legacy:
            print(f"  >>> LEGACY userid: {legacy.userid}")
            print(f"  >>> LEGACY firstname: {legacy.firstname}")
            print(f"  >>> LEGACY lastname: {legacy.lastname}")
        else:
            print(f"  >>> Nu există în legacy cu acest card")
    except Exception as ex:
        print(f"  >>> Legacy check error: {ex}")

print("\n" + "="*60)
