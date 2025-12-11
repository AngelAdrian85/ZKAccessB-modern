# 📊 NIVEL DE ACCES ȘI INTERVALE DE TIMP - FLUX COMPLET

## Arhitectura Sistemului

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMPLOYEE (Angajat)                          │
├─────────────────────────────────────────────────────────────────┤
│ • first_name, last_name                                         │
│ • card_number, secondary_card_number                            │
│ • active (activ/inactiv)                                        │
│ • acc_startdate, acc_enddate (valabilitate)                     │
│ • access_levels (ManyToMany) ────────────────┐                  │
│                                              ▼                  │
├──────────────────────────────────────────────┐─────────────────┤
│                                              │                 │
└──────────────────────────────────────────────┼─────────────────┘
                                               │
                                               │
                ┌──────────────────────────────┴──────────────────┐
                ▼                                                  ▼
        ┌──────────────────┐                            ┌────────────────┐
        │  ACCESS LEVEL    │                            │  TIME SEGMENT  │
        ├──────────────────┤                            ├────────────────┤
        │ • name           │                            │ • name         │
        │ • doors (M2M)    │────────┐                   │ • start_time   │
        │ • time_segments  │        │                   │ • end_time     │
        │   (M2M) ───────┐ │        │                   │ • days_mask    │
        │                └─┼────┐   │                   └────────────────┘
        └──────────────────┘    │   │
                                │   │
                                ▼   ▼
                        ┌────────────────────┐
                        │      DOOR          │
                        ├────────────────────┤
                        │ • name             │
                        │ • device (FK)      │
                        │ • is_open          │
                        └────────────────────┘
```

## Fluxul de Evaluare Acces

### 1. **Citire Card (Physical or Test)**
```
User swipes card / Test button click
         ↓
Browser detectează cardNumber
         ↓
AJAX: /agent/api/test-read-card?card_number=12345678&door_pk=5
         ↓
Backend: access_evaluate_and_open()
```

### 2. **Rezolvare Angajat (Employee Lookup)**
```
SELECT * FROM Employee 
WHERE card_number = '12345678' 
   OR secondary_card_number = '12345678'

IF NOT FOUND:
  SELECT employee FROM EmployeeCard 
  WHERE card_number = '12345678'
```

### 3. **Validări Succesive**

#### Pas A: Employee Status
```python
✓ IF emp is None:
  reason = 'no_employee_for_card' ❌

✓ IF emp.active == False:
  reason = 'employee_inactive' ❌
```

#### Pas B: Validitate Perioadă Angajat
```python
✓ IF today < emp.acc_startdate:
  reason = 'outside_employee_validity' (card nu e încă valabil) ❌

✓ IF today > emp.acc_enddate:
  reason = 'outside_employee_validity' (card a expirat) ❌
```

#### Pas C: Verificare Zile de Sărbătoare
```python
✓ IF Holiday.objects.filter(date=today).exists():
  reason = 'holiday_block' (azi e sărbătoare) ❌
```

#### Pas D: Access Levels pe Door
```python
access_levels = emp.access_levels.all()  # ManyToMany

✓ IF access_levels is EMPTY:
  reason = 'no_access_levels' (angajat fără nivel acces) ❌

✓ IF door NOT IN any access_level.doors:
  reason = 'door_not_in_access_levels' (acest angajat nu are acces la ușa) ❌
```

#### Pas E: Time Segments (Intervale Orar)
```python
# Pentru fiecare AccessLevel care conține door-ul:
for level in access_levels:
  segments = level.time_segments.all()
  
  for segment in segments:
    # Check if today's weekday is in the segment's days_mask
    IF (segment.days_mask & (1 << weekday_index)):
      
      # Check if current time is within segment's time window
      IF (segment.start_time <= current_time <= segment.end_time):
        ✓ TIME OK ✅
        allowed = True
        break
    ELSE:
      reason = 'outside_time_segments' (ora nu-i în interval) ❌
```

### 4. **Rezultat Final**
```python
IF allowed == True:
  ✅ ACCEPTAT - Deschide ușa automat
  
ELSE:
  ❌ RESPINS
  Return reasons list (motivele respingerii)
```

## Componentele Principale

### 📋 EMPLOYEE MODEL
**Locație**: `zkeco_modern/agent/models.py` (lines 224-302)

```python
class Employee(models.Model):
    # Identificare
    first_name = CharField()
    last_name = CharField()
    card_number = CharField(unique=True)
    secondary_card_number = CharField(unique=True, nullable)
    
    # Status
    active = BooleanField(default=True)  # Angajat activ?
    
    # Valabilitate
    acc_startdate = DateField(nullable)  # De când e valabil cardul?
    acc_enddate = DateField(nullable)    # Până când e valabil?
    
    # Access
    access_levels = ManyToManyField(AccessLevel)  # Ce niveluri de acces?
```

### 🔐 ACCESS LEVEL MODEL
**Locație**: `zkeco_modern/agent/models.py` (lines 210-222)

```python
class AccessLevel(models.Model):
    name = CharField(max_length=64, unique=True)
    doors = ManyToManyField(Door)          # La ce uși are acces?
    time_segments = ManyToManyField(TimeSegment)  # In ce intervale orare?
    description = CharField()
```

### ⏰ TIME SEGMENT MODEL
**Locație**: `zkeco_modern/agent/models.py` (lines 156-200)

```python
class TimeSegment(models.Model):
    name = CharField()
    start_time = TimeField()  # Ex: 08:00:00
    end_time = TimeField()    # Ex: 18:00:00
    
    # Bitmask days: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    days_mask = IntegerField(default=127)  # 127 = toti 7 zile
    
    def days_display(self):  # Returnează zile active: "Mon,Tue,Wed..."
        ...
```

### 🚪 DOOR MODEL
**Locație**: `zkeco_modern/agent/models.py` (lines 139-154)

```python
class Door(models.Model):
    name = CharField(max_length=128)
    device = ForeignKey(Device)
    location = CharField()
    enabled = BooleanField()
    is_open = BooleanField()
```

### 🎯 HOLIDAY MODEL
**Locație**: `zkeco_modern/agent/models.py` (lines 201-209)

```python
class Holiday(models.Model):
    name = CharField()  # Ex: "Crăciun 2025"
    date = DateField(unique=True)  # Ex: 2025-12-25
    description = CharField()
```

---

## Fluxul UI - CRUD pentru Managementul Accesului

### 1. **Pagina Employees (CRUD)**
**URL**: `/agent/crud/employees/`

#### Creează/Editează Employee:
```
Form Fields:
├─ first_name, last_name
├─ card_number
├─ secondary_card_number
├─ active (checkbox)
├─ acc_startdate (date picker)
├─ acc_enddate (date picker)
└─ access_levels (multi-select dropdown)
```

**Model Form**: `EmployeeExtendedForm` (zkeco_modern/agent/forms.py)

---

### 2. **Pagina Access Levels**
**URL**: `/agent/crud/access-levels/` (trebuie verificat dacă există)

#### Creează/Editează Access Level:
```
Form Fields:
├─ name (text field)
├─ doors (multi-select dropdown)  ← Selectează care uși
└─ time_segments (multi-select dropdown)  ← Selectează care intervale
```

**Model Form**: `AccessLevelForm` (zkeco_modern/agent/forms.py, line 47)

---

### 3. **Pagina Time Segments**
**URL**: `/agent/crud/time-segments/` (trebuie verificat)

#### Creează/Editează Time Segment:
```
Form Fields:
├─ name (text field)  # Ex: "8-18 working hours"
├─ start_time (time picker)  # Ex: 08:00
├─ end_time (time picker)    # Ex: 18:00
└─ days_mask (day checkboxes)  # Selectează care zile
    ├─ ☑ Monday (1 << 0 = 0b0000001)
    ├─ ☑ Tuesday (1 << 1 = 0b0000010)
    ├─ ☑ Wednesday (1 << 2 = 0b0000100)
    ├─ ☑ Thursday (1 << 3 = 0b0001000)
    ├─ ☑ Friday (1 << 4 = 0b0010000)
    ├─ ☐ Saturday (1 << 5 = 0b0100000)
    └─ ☐ Sunday (1 << 6 = 0b1000000)
```

**Model Form**: `TimeSegmentFormWithDays` (zkeco_modern/agent/forms.py, line 352)

---

### 4. **Pagina Holidays**
**URL**: `/agent/crud/holidays/` (trebuie verificat)

#### Creează/Editează Holiday:
```
Form Fields:
├─ name (text field)  # Ex: "Crăciun"
├─ date (date picker)  # Ex: 2025-12-25
└─ description (text area)
```

---

## Exemplu Complet de Configurare

### Scenario: "Angajat Developer cu acces la 2 birouri, 8-18 de luni la vineri"

#### 1. Creează Time Segment (Interval orar)
```
URL: /agent/crud/time-segments/add/

Name: "Working Hours 8-18"
Start Time: 08:00:00
End Time: 18:00:00
Days: Mon, Tue, Wed, Thu, Fri (days_mask = 0b0011111 = 31)
```

#### 2. Creează Access Level (Nivel acces)
```
URL: /agent/crud/access-levels/add/

Name: "Developer Office Access"
Doors: [birou_1, birou_2]  (selectează din list)
Time Segments: [Working Hours 8-18]
```

#### 3. Creează Employee (Angajat)
```
URL: /agent/crud/employees/add/

First Name: John
Last Name: Doe
Card Number: 12345678
Secondary Card: 87654321
Active: ✓
acc_startdate: 2025-01-01
acc_enddate: 2025-12-31
access_levels: [Developer Office Access]
```

#### 4. Testare
```
User swipes card 12345678 on Monday at 10:00
├─ Employee found: John Doe ✓
├─ Active: Yes ✓
├─ In validity period (2025-01-01 to 2025-12-31): Yes ✓
├─ No holiday: Yes ✓
├─ Has access_levels: Yes ✓
│  └─ "Developer Office Access" contains door "birou_1": Yes ✓
├─ Time segment "Working Hours 8-18":
│  ├─ Monday in days_mask: Yes ✓
│  └─ 10:00 between 08:00-18:00: Yes ✓
└─ RESULT: ✅ ACCEPTAT - Deschide birou_1
```

---

## Backend Views (Access Evaluation)

### Endpoint Principal
**`POST /agent/api/access-evaluate-and-open/`**

**Locație**: `zkeco_modern/agent/views.py` (line 1529)

```python
def access_evaluate_and_open(request):
    """
    Payload JSON:
    {
        "card_number": "12345678",
        "door_pk": 5,
        "source": "test" | "physical_reader" | "tray_agent"
    }
    
    Returns:
    {
        "ok": true/false,
        "employee": employee_id,
        "employee_name": "John Doe",
        "door": door_id,
        "reasons": ["reason1", "reason2"],  # Motivele dacă respins
        "status_text": "ACCEPTAT" | "RESPINS",
        "card_number": "12345678"
    }
    """
```

### Endpoint Test
**`GET /agent/api/test-read-card/?card_number=12345678&door_pk=5`**

**Locație**: `zkeco_modern/agent/views.py` (line 1655)

```python
def test_read_card(request):
    """
    Wrapper care apelează access_evaluate_and_open
    Query params:
    - card_number: optional
    - door_pk: optional
    - use_existing: "1" pentru a folosi un card existent din DB
    """
```

---

## Motivele de Respingere (Reasons)

```python
'no_employee_for_card'           # Cardul nu e înregistrat în sistem
'employee_inactive'               # Angajatul e marcat ca inactiv
'door_not_resolved'               # Ușa nu a putut fi găsită
'outside_employee_validity'       # Cardul e în afara perioadei valide (acc_startdate/acc_enddate)
'holiday_block'                   # Azi e zi de sărbătoare
'no_access_levels'                # Angajatul nu are nici un nivel de acces asignat
'door_not_in_access_levels'       # Ușa NU e inclusă în nivelurile de acces ale angajatului
'outside_time_segments'           # Ora actuală nu-i în nici un time segment valid
'door_open_failed'                # Ușa nu a putut fi deschisă (eroare hardware/API)
```

---

## File-uri Implicate

| Componenta | File | Linii |
|-----------|------|-------|
| Models | `zkeco_modern/agent/models.py` | 139-376 |
| Forms | `zkeco_modern/agent/forms.py` | 15-118 |
| Views | `zkeco_modern/agent/views.py` | 1529-1750 |
| URLs | `zkeco_modern/agent/urls.py` | ? |
| Templates | `zkeco_modern/agent/templates/agent/*.html` | ? |

---

## Update Flow - Pași pentru Upgrade

### Pentru a adăuga o nouă funcționalitate:

1. **Actualizează Model** (models.py)
   - Adaugă câmpuri noi
   - Creează migrations: `python manage.py makemigrations`
   - Aplică: `python manage.py migrate`

2. **Actualizează Form** (forms.py)
   - Adaugă câmpuri în ModelForm.Meta.fields

3. **Actualizează View** (views.py)
   - Logica de evaluare acces se schimbă aici

4. **Actualizează Template**
   - UI pentru edit/create/list

5. **Actualizează API Endpoint**
   - JSON responses, validări

---

## Următorii Pași

1. Verifică dacă pagina de Access Levels CRUD există
2. Verifică dacă pagina de Time Segments CRUD există
3. Verifică dacă pagina de Holidays CRUD există
4. Update sau creeaza UI-uri lipsă
5. Test end-to-end: Employee → AccessLevel → TimeSegment → Test Card → Result
