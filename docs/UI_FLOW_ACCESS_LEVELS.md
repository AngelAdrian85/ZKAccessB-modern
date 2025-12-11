# 🎯 UI FLOW - Niveluri de Acces și Intervale Orare

## URLs Disponibile (CRUD)

### 1. TIME SEGMENTS (Intervale Orare)
```
📍 /agent/crud/time-segments/              [Lista]
📍 /agent/crud/time-segments/new/           [Creeaza]
📍 /agent/crud/time-segments/<id>/edit/     [Editeaza]
📍 /agent/crud/time-segments/<id>/delete/   [Sterge]
```

### 2. HOLIDAYS (Zile de Sarbatoare)
```
📍 /agent/crud/holidays/                    [Lista]
📍 /agent/crud/holidays/new/                [Creeaza]
📍 /agent/crud/holidays/<id>/edit/          [Editeaza]
📍 /agent/crud/holidays/<id>/delete/        [Sterge]
```

### 3. ACCESS LEVELS (Niveluri de Acces)
```
📍 /agent/crud/access-levels/               [Lista]
📍 /agent/crud/access-levels/new/           [Creeaza]
📍 /agent/crud/access-levels/<id>/edit/     [Editeaza]
📍 /agent/crud/access-levels/<id>/delete/   [Sterge]
```

### 4. EMPLOYEES (Angajati)
```
📍 /agent/crud/employees/                   [Lista]
📍 /agent/crud/employees/new/               [Creeaza]
📍 /agent/crud/employees/<id>/edit/         [Editeaza]
📍 /agent/crud/employees/<id>/delete/       [Sterge]
```

---

## STEP-BY-STEP: Cum se Configureaza Accesul

### STEP 1️⃣: Creaza Intervale Orare (Time Segments)

**URL**: `http://localhost:14525/agent/crud/time-segments/new/`

```
┌─────────────────────────────────────────────────────────┐
│          Create Time Segment (Interval Orar)            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Name: [________________ "8-18 Workday" ________________]│
│                                                          │
│  Start Time: [__:__]  ← 08:00                          │
│  End Time:   [__:__]  ← 18:00                          │
│                                                          │
│  Days of Week:                                          │
│  ☑ Monday    ☑ Tuesday    ☑ Wednesday    ☑ Thursday   │
│  ☑ Friday    ☐ Saturday   ☐ Sunday                     │
│                                                          │
│  [Create]  [Cancel]                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘

REZULTAT SALVAT:
- Time Segment "8-18 Workday"
- Valid: Mon-Fri 08:00-18:00
- days_mask = 0b0011111 (31 in decimal)
```

### STEP 2️⃣: Creaza Niveluri de Acces (Access Levels)

**URL**: `http://localhost:14525/agent/crud/access-levels/new/`

```
┌──────────────────────────────────────────────────────────┐
│          Create Access Level (Nivel Acces)               │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Name: [________________ "Office Staff" ________________]│
│                                                           │
│  Description: [________________________________...]     │
│                                                           │
│  Doors (select multiple):                               │
│  ☑ Birou John Doe (id=1)                               │
│  ☑ Birou Finance Team (id=2)                           │
│  ☐ Director Room (id=3)                                │
│  ☐ Server Room (id=4)                                  │
│  ☐ ... [show more]                                     │
│                                                           │
│  Time Segments (select multiple):                       │
│  ☑ 8-18 Workday                                        │
│  ☐ 24/7 Emergency                                      │
│  ☐ Evening Shift (18-02)                               │
│  ☐ ... [show more]                                     │
│                                                           │
│  [Create]  [Cancel]                                     │
│                                                           │
└──────────────────────────────────────────────────────────┘

REZULTAT SALVAT:
- Access Level "Office Staff"
- Doors: Birou John Doe + Finance Team
- Time Segments: 8-18 Workday (Mon-Fri 08:00-18:00)
```

### STEP 3️⃣: Asigneaza Access Level la Employee

**URL**: `http://localhost:14525/agent/crud/employees/<id>/edit/`

```
┌───────────────────────────────────────────────────────────┐
│          Edit Employee (Editeaza Angajat)                 │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  First Name: [____________ "John" ____________]           │
│  Last Name:  [____________ "Doe" ____________]            │
│  Card Number: [_________ "12345678" _________]            │
│  Secondary Card: [______ "87654321" ______]               │
│                                                            │
│  Active: ☑ (checkbox)                                    │
│                                                            │
│  Validity Period:                                         │
│  acc_startdate: [2025-01-01]  ← De când?                │
│  acc_enddate:   [2025-12-31]  ← Până când?              │
│                                                            │
│  Access Levels (select multiple):                        │
│  ☑ Office Staff                    ← PE ASTA SELECTEAZA│
│  ☐ Management Access                                     │
│  ☐ IT Admin Access                                       │
│  ☐ ... [show more]                                       │
│                                                            │
│  [Save]  [Cancel]  [Delete]                              │
│                                                            │
└───────────────────────────────────────────────────────────┘

REZULTAT SALVAT:
- Employee "John Doe"
- Card: 12345678
- Access Level: "Office Staff"
  └─ Doors: Birou John Doe, Finance Team
  └─ Time Segments: 8-18 Workday (Mon-Fri 08:00-18:00)
```

### STEP 4️⃣: Testeaza Accesul

**URL**: `http://localhost:14525/agent/monitor/`

```
┌───────────────────────────────────────────────────────────┐
│          Real-Time Monitoring (Monitor)                   │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  Area: [All ▼]                                           │
│  Door: [Birou John Doe ▼]  ← selecteaza usa             │
│                                                            │
│  [🪪 Test Citire Card]  [Card nr input: ________]       │
│                                                            │
│  ┌─ Click Test button SAU treaca card fizic             │
│  │                                                        │
│  └─► Apare NOTIFICARE ANIMATA:                          │
│      ╔═══════════════════════════════╗                  │
│      ║   🪪 CARD DETECTAT            ║                  │
│      ║   12345678                    ║                  │
│      ║   [pulse bar animation]       ║                  │
│      ╚═══════════════════════════════╝                  │
│                                                            │
│  └─► Backend checks:                                     │
│      ✓ Employee found: John Doe                         │
│      ✓ Active: Yes                                       │
│      ✓ In validity (2025-01-01 to 2025-12-31): Yes    │
│      ✓ Has Access Level: "Office Staff"                │
│      ✓ Door "Birou John Doe" in access level: Yes      │
│      ✓ Time Segment valid:                              │
│         - Today is Monday (in days_mask): Yes           │
│         - Current time 10:30 between 08:00-18:00: Yes   │
│                                                            │
│  └─► RESULTADO:                                          │
│      ┌────────────────────────────────────────────┐     │
│      │ Status: ✅ ACCEPTAT                       │     │
│      │ Door opened automatically                 │     │
│      ├────────────────────────────────────────────┤     │
│      │ Time    │ Event         │ Card    │ Status│     │
│      ├─────────┼───────────────┼─────────┼───────┤     │
│      │ 10:30   │ 🪪 CARD FIZIC │ 1234... │ ✅     │     │
│      │ ACCEPTAT│ DESCHIS       │         │       │     │
│      └────────────────────────────────────────────┘     │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

---

## SCENARII DE RESPINGERE

### ❌ Scenario 1: Card Nerecunoscut
```
Cardul: 99999999 (nu exista in DB)

Verificare:
✗ Employee NOT found for card 99999999
└─ reason: 'no_employee_for_card'

Rezultat: ❌ RESPINS
Button: [Adaugă Card]  ← rapid add new employee
```

### ❌ Scenario 2: Angajat Inactiv
```
Cardul: 12345678
Employee: John Doe, active=False

Verificare:
✓ Employee found: John Doe
✗ Active: No
└─ reason: 'employee_inactive'

Rezultat: ❌ RESPINS
```

### ❌ Scenario 3: Cardul Expirat
```
Cardul: 12345678
Employee: John Doe
acc_enddate: 2024-12-31
Today: 2025-01-15

Verificare:
✓ Employee found: John Doe
✓ Active: Yes
✗ Today (2025-01-15) > acc_enddate (2024-12-31)
└─ reason: 'outside_employee_validity'

Rezultat: ❌ RESPINS
```

### ❌ Scenario 4: Fara Nivel de Acces
```
Cardul: 12345678
Employee: John Doe
access_levels: [] (gol)

Verificare:
✓ Employee found: John Doe
✓ Active: Yes
✓ In validity period: Yes
✗ access_levels is EMPTY
└─ reason: 'no_access_levels'

Rezultat: ❌ RESPINS
```

### ❌ Scenario 5: Usa Nu-i in Nivel de Acces
```
Cardul: 12345678
Employee: John Doe
access_levels: ["Office Staff"]
  └─ doors: [birou_1, birou_2]
Selected door: Server Room (birou_4)

Verificare:
✓ Employee found: John Doe
✓ Active: Yes
✓ In validity period: Yes
✓ Has access_levels: Yes
✗ Door "Server Room" NOT in access_levels
└─ reason: 'door_not_in_access_levels'

Rezultat: ❌ RESPINS (acces neautorizat la aceasta usa)
```

### ❌ Scenario 6: Ora Nu-i in Interval
```
Cardul: 12345678
Employee: John Doe
Time segment: 8-18 Workday (Mon-Fri)
Current time: 2025-01-15 (Saturday) 14:00

Verificare:
✓ Employee found: John Doe
✓ Active: Yes
✓ In validity period: Yes
✓ Has access_levels: Yes
✓ Door in access_levels: Yes
✗ Current time check:
  - Today: Saturday (bit 5 in days_mask)
  - Time Segment "8-18 Workday" has days_mask = 0b0011111 (Mon-Fri only)
  - Saturday NOT in days_mask
  └─ reason: 'outside_time_segments'

Rezultat: ❌ RESPINS (acces in afara programului)
```

### ❌ Scenario 7: Zi de Sarbatoare
```
Cardul: 12345678
Employee: John Doe
Today: 2025-12-25 (Crăciun)

Verificare:
✓ Employee found: John Doe
✓ Active: Yes
✓ In validity period: Yes
✓ Has access_levels: Yes
✓ Door in access_levels: Yes
✗ Holiday check:
  - Holiday.objects.filter(date='2025-12-25') exists
  └─ reason: 'holiday_block'

Rezultat: ❌ RESPINS (azi e zi de sarbatoare - acces blocat)
```

---

## Logica de Evaluare - Flow Chart

```
                        ┌─────────────────────┐
                        │  Card Swiped (USB)  │
                        │  or Test Clicked    │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ Resolve Employee by Card    │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ Employee Found?     │
                        ├─────┬──────────────┤
                       NO    YES              │
                        │     │               │
                        │     ▼               │
                        │   Active?           │
                        │   ├─┬──────────┤   │
                        │  NO YES       │   │
                        │   │  │        │   │
                        │   │  ▼        │   │
                        │   │ In Date   │   │
                        │   │ Range?    │   │
                        │   │ ├─┬───┤  │   │
                        │   │NO YES  │  │   │
                        │   │  │  │  │  │   │
                        │   │  │  ▼  │  │   │
                        │   │  │ Holiday?  │
                        │   │  │ ├─┬──┤   │
                        │   │  │NO YES    │
                        │   │  │  │  │    │
                        │   │  │  │  ▼    │
                        │   │  │  │ Has Access
                        │   │  │  │ Levels?
                        │   │  │  │ ├─┬────┤
                        │   │  │  │NO YES  │
                        │   │  │  │  │  │  │
                        │   │  │  │  │  ▼  │
                        │   │  │  │  │ Door in
                        │   │  │  │  │ Levels?
                        │   │  │  │  │ ├─┬──┤
                        │   │  │  │  │NO YES
                        │   │  │  │  │  │  │
                        │   │  │  │  │  │  ▼
                        │   │  │  │  │  │ Valid
                        │   │  │  │  │  │ Time?
                        │   │  │  │  │  │ ├─┬──┤
                        │   │  │  │  │  │NO YES
                        │   │  │  │  │  │  │
                        ▼   ▼  ▼  ▼  ▼  ▼  ▼
                    ┌──────────────────────────┐
                    │ ❌ RESPINS               │
                    │ reason: [...]           │
                    └──────────┬───────────────┘
                               │
                               │         ┌──────────────┐
                               │         │ ✅ ACCEPTAT  │
                               │         │ Open Door    │
                               │         └──────────────┘
                               │                │
                               └────────┬───────┘
                                        │
                                        ▼
                    ┌──────────────────────────────┐
                    │ Log Event in Event Table     │
                    │ Add row with:                │
                    │ - Time                       │
                    │ - Event Description          │
                    │ - Card Number                │
                    │ - Employee Name              │
                    │ - Status (ACCEPTAT/RESPINS) │
                    │ - Reason (if respins)        │
                    └──────────────────────────────┘
```

---

## Update Timeline

Ordinea implementarii noilor feature-uri:

1. ✅ Physical Card Reader Detection (DONE)
2. 🔄 **Access Levels + Time Segments Display**
3. 🔄 **Enhanced Employee form with Time-based warnings**
4. 🔄 **Holiday Management UI**
5. 🔄 **Access Reports (audit log)**
6. 🔄 **Device-level access (multi-door coordination)**

---

## Test Cases

### Test 1: Full Access Path
```
1. Create TimeSegment "Test Hours" (08:00-17:00, Mon-Fri)
2. Create AccessLevel "Test Access" with Test Hours
3. Create Employee "Test User" with card "99999999"
4. Assign AccessLevel to Employee
5. Select door, click Test
6. Verify: ✅ ACCEPTAT, door opens
7. Check event log for correct entry
```

### Test 2: Time Restriction
```
1. Set AccessLevel with 09:00-12:00 time segment
2. Set current system time to 14:00
3. Swipe card
4. Verify: ❌ RESPINS, reason 'outside_time_segments'
5. Change system time to 10:00
6. Swipe card again
7. Verify: ✅ ACCEPTAT
```

### Test 3: Holiday Block
```
1. Create Holiday "Test Day" on today's date
2. Swipe valid card
3. Verify: ❌ RESPINS, reason 'holiday_block'
4. Delete holiday
5. Swipe card again
6. Verify: ✅ ACCEPTAT
```

---

## Admin Notes

- **days_mask**: Binary representation of days
  - 0b0000001 = Monday only
  - 0b0000010 = Tuesday only
  - 0b0011111 = Monday-Friday
  - 0b1111111 = All days (default)

- **Overlap Detection**: System warns if creating overlapping time segments

- **Cascade Delete**: Removing AccessLevel doesn't delete TimeSegments (reusable)

- **Performance**: Time evaluation is done at request-time (no caching to avoid stale data)
