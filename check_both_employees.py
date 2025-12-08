"""Check both Employee tables"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Check zkeco_modern legacy_models
from legacy_models.models import Employee as ModernEmployee
print("=== zkeco_modern/legacy_models ===")
emp_count = ModernEmployee.objects.count()
print(f'Total employees: {emp_count}')
for emp in ModernEmployee.objects.all().order_by('userid'):
    print(f'  UserID={emp.userid}, Name={emp.firstname} {emp.lastname}')

# Try to check root legacy_models if it exists
try:
    import sys
    # Remove zkeco_modern from path temporarily
    sys.path.pop(0)
    sys.path.insert(0, os.path.dirname(__file__))
    
    # This will try to import from root
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("legacy_models_root", "legacy_models/models.py")
        if spec:
            print("\n=== Root legacy_models (if different) ===")
            # Get the actual database config
            from django.db import connections
            print(f"Current DB: {connections.databases['default']['NAME']}")
    except:
        pass
except Exception as e:
    print(f"Error: {e}")
