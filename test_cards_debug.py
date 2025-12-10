#!/usr/bin/env python
import os
import sys
import django

# Set up Django
sys.path.insert(0, r'c:\Users\AngelAdrian\Desktop\Acces\ZKAccessB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_modern.settings')
django.setup()

from zkeco_modern.agent.models import Employee, EmployeeCard

# Check all cards in DB
all_cards = []

# Primary cards from Employee
primary = list(Employee.objects.exclude(card_number__isnull=True).exclude(card_number='').values_list('card_number', flat=True))
print(f"Employee PRIMARY cards ({len(primary)}): {primary}")

# Secondary cards from Employee
secondary = list(Employee.objects.exclude(secondary_card_number__isnull=True).exclude(secondary_card_number='').values_list('secondary_card_number', flat=True))
print(f"Employee SECONDARY cards ({len(secondary)}): {secondary}")

# Additional cards from EmployeeCard
additional = list(EmployeeCard.objects.exclude(card_number__isnull=True).exclude(card_number='').values_list('card_number', flat=True))
print(f"EmployeeCard ADDITIONAL cards ({len(additional)}): {additional}")

# Combine
all_cards = primary + secondary + additional
unique = list(dict.fromkeys(all_cards))
print(f"\n===== SUMMARY =====")
print(f"TOTAL UNIQUE CARDS: {len(unique)}")
print(f"Card numbers: {unique}")

# Test round-robin selection logic
print(f"\n===== SIMULATING ROUND-ROBIN =====")
if unique:
    for idx in range(min(10, len(unique) * 2)):
        selected_idx = idx % len(unique)
        card = unique[selected_idx]
        print(f"Click {idx+1}: card_index={selected_idx}, card_number={card}")
