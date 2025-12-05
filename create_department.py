"""
Script pentru crearea unui departament de test în legacy_models
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

try:
    from legacy_models.models import Dept as LegacyDept
    
    # Creează câteva departamente de test
    departments = [
        {'DeptName': 'IT Department', 'code': 'IT001'},
        {'DeptName': 'HR Department', 'code': 'HR001'},
        {'DeptName': 'Finance', 'code': 'FIN001'},
        {'DeptName': 'Medical', 'code': 'MED001'},
        {'DeptName': 'Administration', 'code': 'ADM001'},
    ]
    
    for dept_data in departments:
        dept, created = LegacyDept.objects.get_or_create(
            DeptName=dept_data['DeptName'],
            defaults={'code': dept_data['code']}
        )
        if created:
            print(f"✓ Departament creat: {dept.DeptName} ({dept.code})")
        else:
            print(f"  Departament existent: {dept.DeptName}")
    
    print(f"\n✓ Total departamente în baza de date: {LegacyDept.objects.count()}")
    
except Exception as e:
    print(f"Eroare: {e}")
    print("Probabil legacy_models nu este disponibil. Câmpul Departament nu va fi functional.")
