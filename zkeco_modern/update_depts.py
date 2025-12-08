import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from agent.models import Employee
from legacy_models.models import Dept

# Update employees with department IDs
emp1 = Employee.objects.get(id=2)  # Ion Popescu
emp1.dept_id = 1  # IT Department
emp1.save()
print(f'Updated {emp1.first_name} with dept_id=1')

emp2 = Employee.objects.get(id=3)  # Maria Ionescu
emp2.dept_id = 2  # HR Department
emp2.save()
print(f'Updated {emp2.first_name} with dept_id=2')

# Verify
for emp in Employee.objects.all():
    dept = Dept.objects.get(id=emp.dept_id) if emp.dept_id else None
    dept_name = dept.DeptName if dept else 'No dept'
    print(f'- {emp.first_name} {emp.last_name}: {dept_name}')
