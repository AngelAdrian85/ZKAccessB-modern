# 🏗️ DIAGRAMA FLUXULUI COMPLET - Access Control System

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCESS CONTROL SYSTEM v2025                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      INPUT LAYER (Card Detection)                    │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                      │  │
│  │  ┌─────────────────────────┐    ┌──────────────────────────────┐  │  │
│  │  │  Physical Card Reader   │    │  Browser Test Button         │  │  │
│  │  │  (USB HID Keyboard)     │    │  /agent/monitor/             │  │  │
│  │  └────────────┬────────────┘    └──────────────┬───────────────┘  │  │
│  │               │ keypress events                │ click event       │  │
│  │               └────────────────┬───────────────┘                   │  │
│  │                                │                                   │  │
│  │                    ┌───────────▼───────────┐                      │  │
│  │                    │  Card Number Buffer   │                      │  │
│  │                    │  (Smart Detection)    │                      │  │
│  │                    │  - READER_TIMEOUT:100 │                      │  │
│  │                    │  - MIN_LENGTH: 4      │                      │  │
│  │                    └───────────┬───────────┘                      │  │
│  │                                │                                   │  │
│  │                    ┌───────────▼───────────┐                      │  │
│  │                    │  Tech Animation       │                      │  │
│  │                    │  (Centered, 1.5sec)  │                      │  │
│  │                    │  🪪 CARD DETECTAT    │                      │  │
│  │                    └───────────┬───────────┘                      │  │
│  │                                │                                   │  │
│  └────────────────────────────────┼───────────────────────────────────┘  │
│                                   │                                       │
│  ┌────────────────────────────────▼───────────────────────────────────┐  │
│  │                    BACKEND PROCESSING LAYER                        │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ Endpoint: /agent/api/test-read-card                        │  │  │
│  │  │ Query: card_number, door_pk                               │  │  │
│  │  └────────────────┬─────────────────────────────────────────┘  │  │
│  │                   │                                              │  │
│  │   ┌───────────────▼──────────────────────┐                     │  │
│  │   │ Employee Lookup                       │                    │  │
│  │   ├──────────────────────────────────────┤                     │  │
│  │   │ SELECT * FROM Employee WHERE        │                    │  │
│  │   │   card_number = '12345678' OR       │                    │  │
│  │   │   secondary_card_number = '12345678'│                    │  │
│  │   │ IF NOT FOUND: EmployeeCard lookup   │                    │  │
│  │   │                                      │                    │  │
│  │   └───────────────┬──────────────────────┘                    │  │
│  │                   │                                             │  │
│  │   ┌───────────────▼──────────────────────────────┐            │  │
│  │   │ VALIDATION PIPELINE (7 Checks)               │            │  │
│  │   ├──────────────────────────────────────────────┤            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 1: Employee exists?                │            │  │
│  │   │   └─ FAIL → reason: 'no_employee_for_card' │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 2: Employee active?                │            │  │
│  │   │   └─ FAIL → reason: 'employee_inactive'    │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 3: In validity period?             │            │  │
│  │   │   ├─ acc_startdate <= today ✓              │            │  │
│  │   │   └─ today <= acc_enddate ✓                │            │  │
│  │   │   └─ FAIL → 'outside_employee_validity'    │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 4: Not a holiday?                  │            │  │
│  │   │   └─ SELECT * FROM Holiday WHERE date=today│            │  │
│  │   │   └─ FAIL → reason: 'holiday_block'        │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 5: Has access levels?              │            │  │
│  │   │   └─ emp.access_levels.count() > 0?        │            │  │
│  │   │   └─ FAIL → reason: 'no_access_levels'     │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 6: Door in access levels?          │            │  │
│  │   │   └─ FOR each AccessLevel:                 │            │  │
│  │   │      SELECT * FROM doors WHERE             │            │  │
│  │   │      access_level=X AND door=selected_door │            │  │
│  │   │   └─ FAIL → 'door_not_in_access_levels'    │            │  │
│  │   │                                              │            │  │
│  │   │ ✓ Check 7: Valid time?                     │            │  │
│  │   │   └─ FOR each TimeSegment in AccessLevel:  │            │  │
│  │   │      ├─ Today in days_mask?                │            │  │
│  │   │      ├─ Current time in [start-end]?       │            │  │
│  │   │   └─ FAIL → 'outside_time_segments'        │            │  │
│  │   │                                              │            │  │
│  │   └───────────────┬──────────────────────────────┘            │  │
│  │                   │                                             │  │
│  │   ┌───────────────▼──────────────────────┐                    │  │
│  │   │ DECISION LOGIC                        │                   │  │
│  │   ├──────────────────────────────────────┤                   │  │
│  │   │                                      │                   │  │
│  │   │ IF all_checks_pass:                 │                   │  │
│  │   │   allowed = True                     │                   │  │
│  │   │   CALL: door_open()                 │                   │  │
│  │   │ ELSE:                                │                   │  │
│  │   │   allowed = False                    │                   │  │
│  │   │   reasons = [failed_checks]         │                   │  │
│  │   │                                      │                   │  │
│  │   └───────────────┬──────────────────────┘                   │  │
│  │                   │                                            │  │
│  │   ┌───────────────▼──────────────────────────────┐           │  │
│  │   │ Response (JSON)                              │           │  │
│  │   ├──────────────────────────────────────────────┤           │  │
│  │   │ {                                            │           │  │
│  │   │   "ok": true/false,                         │           │  │
│  │   │   "employee_name": "John Doe",              │           │  │
│  │   │   "card_number": "12345678",                │           │  │
│  │   │   "status_text": "ACCEPTAT"/"RESPINS",      │           │  │
│  │   │   "reasons": ["reason1", "reason2"],        │           │  │
│  │   │   "door": door_id                           │           │  │
│  │   │ }                                            │           │  │
│  │   └───────────────┬──────────────────────────────┘           │  │
│  │                   │                                            │  │
│  └───────────────────┼──────────────────────────────────────────┘  │
│                      │                                               │
│  ┌───────────────────▼──────────────────────────────────────────┐  │
│  │                   FRONTEND RESPONSE LAYER                    │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │ Event Log Table Entry                              │    │  │
│  │  ├────────────────────────────────────────────────────┤    │  │
│  │  │ Time: 10:30:45                                    │    │  │
│  │  │ Event: 🪪 CARD FIZIC ACCEPTAT (or RESPINS)      │    │  │
│  │  │ Card: 12345678                                    │    │  │
│  │  │ Employee: John Doe                                │    │  │
│  │  │ Door: Birou Financial                             │    │  │
│  │  │ Status: ✅ ACCEPTAT (green) / ❌ RESPINS (red)   │    │  │
│  │  │ Reason: outside_time_segments → "Acces in afara" │    │  │
│  │  │         programului"                              │    │  │
│  │  │ Verify Mode: CITITOR FIZIC                        │    │  │
│  │  │                                                    │    │  │
│  │  │ [Buttons if applicable]:                          │    │  │
│  │  │ - If RESPINS + unknown card: [Adaugă Card]       │    │  │
│  │  │ - If ACCEPTAT + known employee: [Modifică]       │    │  │
│  │  │                                                    │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │ IF ok = true:                                      │    │  │
│  │  │   ├─ Auto-open selected door                      │    │  │
│  │  │   ├─ Log entry background: GREEN (#1a3d2a)       │    │  │
│  │  │   └─ WebSocket broadcast door state change       │    │  │
│  │  │                                                    │    │  │
│  │  │ IF ok = false:                                    │    │  │
│  │  │   ├─ Log entry background: RED (#3b1e1e)         │    │  │
│  │  │   ├─ Show reason in Romanian                      │    │  │
│  │  │   └─ Show action button if applicable            │    │  │
│  │  │                                                    │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               DOOR CONTROL (Auto-Open Handler)               │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  IF access_granted:                                         │  │
│  │    doorAction(device_id, door_id, 'open')                 │  │
│  │     └─► POST /agent/api/devices/{id}/doors/{id}/open/    │  │
│  │         └─► Backend sends command to device               │  │
│  │         └─► Device activates relay/solenoid               │  │
│  │         └─► Electric strike releases lock                 │  │
│  │         └─► WebSocket broadcasts: door.open event         │  │
│  │         └─► All clients see door state change             │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model Relationship Diagram

```
                    ┌─────────────────┐
                    │    EMPLOYEE     │
                    ├─────────────────┤
                    │ id              │
                    │ first_name      │
                    │ last_name       │
                    │ card_number     │◄──────────┐ (Primary key lookup)
                    │ secondary_card  │◄──────────┤ (Secondary key lookup)
                    │ active          │           │
                    │ acc_startdate   │           │
                    │ acc_enddate     │           │
                    └────────┬────────┘           │
                             │                    │
                             │ M2M                │
                             ▼                    │
                    ┌─────────────────┐          │
                    │  ACCESS LEVEL   │          │
                    ├─────────────────┤          │
                    │ id              │          │
                    │ name            │          │
                    │ description     │          │
                    └────────┬────────┘          │
                             │                   │
                    ┌────────┴───────────┐       │
                    │ M2M (1)      M2M (2)       │
                    ▼                    ▼       │
        ┌─────────────────┐    ┌──────────────┐ │
        │   TIME SEGMENT  │    │     DOOR     │ │
        ├─────────────────┤    ├──────────────┤ │
        │ id              │    │ id           │ │
        │ name            │    │ name         │ │
        │ start_time      │    │ location     │ │
        │ end_time        │    │ device (FK)  │ │
        │ days_mask       │    │ is_open      │ │
        │ (0b1111111)     │    └──────────────┘ │
        └─────────────────┘                      │
                                                 │
    ┌────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────┐
│  EMPLOYEE CARD      │
├─────────────────────┤ (Additional cards not in Employee model)
│ id                  │
│ employee (FK)       │
│ card_number         │
│ description         │
└─────────────────────┘

┌─────────────────────┐
│     HOLIDAY         │
├─────────────────────┤ (Blocks all access on specified dates)
│ id                  │
│ name                │
│ date                │ (unique per day)
│ description         │
└─────────────────────┘
```

---

## Time Segment Days Mask Explanation

```
Binary Representation: 0b0SSFMTWM (7 bits for 7 days)
Position:                0123456

Bit 0 (LSB): Monday      = 0b0000001 = 1
Bit 1:       Tuesday     = 0b0000010 = 2
Bit 2:       Wednesday   = 0b0000100 = 4
Bit 3:       Thursday    = 0b0001000 = 8
Bit 4:       Friday      = 0b0010000 = 16
Bit 5:       Saturday    = 0b0100000 = 32
Bit 6 (MSB): Sunday      = 0b1000000 = 64

Examples:
─────────────────────────────────────────────────────────────

All Days (Default):
  0b1111111 = 127
  Mon, Tue, Wed, Thu, Fri, Sat, Sun ✓

Weekdays Only (Mon-Fri):
  0b0011111 = 31
  Mon, Tue, Wed, Thu, Fri ✓
  Sat, Sun ✗

Weekend Only (Sat-Sun):
  0b1100000 = 96
  Sat, Sun ✓
  Mon-Fri ✗

Business Days (Tue-Thu):
  0b0001110 = 14
  Tue, Wed, Thu ✓
  Mon, Fri, Sat, Sun ✗

Monday Only:
  0b0000001 = 1
  Mon ✓
  Others ✗

Check in Code:
  IF (segment.days_mask & (1 << weekday_index)):
    # Today is in the segment's active days
```

---

## Access Evaluation Decision Tree

```
                          🪪 Card Swiped
                               │
                               ▼
                    Find Employee by Card
                               │
                    ┌──────────┴──────────┐
                    │                     │
                   NO                    YES
                    │                     │
              ❌ RESPINS           Active=True?
              no_employee          │
                    │         ┌────┴────┐
                    │        NO         YES
                    │        │          │
                    │   ❌ RESPINS  In Date Range?
                    │   employee_    │
                    │   inactive  ┌──┴──┐
                    │            NO    YES
                    │            │     │
                    │       ❌ RESPINS Holiday?
                    │       outside_  │
                    │       employee_ ┌┴┐
                    │       validity NO YES
                    │              │  │
                    │          ❌ RESPINS
                    │          holiday_block
                    │              │
                    │         Has AccessLevels?
                    │              │
                    │          ┌───┴───┐
                    │         NO      YES
                    │         │        │
                    │    ❌ RESPINS   Door in
                    │    no_access   Levels?
                    │    _levels      │
                    │         │   ┌───┴───┐
                    │         │  NO      YES
                    │         │  │        │
                    │         │ ❌ RESPINS Valid Time
                    │         │ door_not_ in Segment?
                    │         │ in_access │
                    │         │ _levels  ┌┴┐
                    │         │        NO YES
                    │         │        │  │
                    │         │    ❌ RESPINS
                    │         │    outside_
                    │         │    time_
                    │         │    segments
                    │         │    │
                    └─────────┴────┴──► ❌ RESPINS
                                        
                                 ✅ ACCEPTAT
                                 Allow=True
                                 Open Door
```

---

## Integration Points

### 1. Physical Hardware
```
Card Reader (USB)
   └─► HID Keyboard Events
       └─► Browser JavaScript
           └─► /agent/api/test-read-card
               └─► Backend evaluation
                   └─► Device Control
                       └─► Relay/Electric Strike
```

### 2. Database Schema
```
Employee ─M2M─ AccessLevel ─M2M─ TimeSegment
                 │
              M2M │
                  └─► Door ─FK─► Device
                  
Holiday ────────► (blocks all access on that date)
EmployeeCard ───► Employee (additional cards)
```

### 3. Time-Based Evaluation
```
Current Time
     │
     ├─► Extract: weekday_index (0-6), time (HH:MM)
     │
     ├─► Check Holiday table
     │
     └─► For each TimeSegment:
         ├─ Check days_mask & (1 << weekday_index)
         └─ Check start_time ≤ current_time ≤ end_time
```

---

## Performance Characteristics

```
Single Card Evaluation (typical):
├─ Employee DB lookup: ~5ms (indexed by card_number)
├─ AccessLevel lookup: ~10ms (M2M query)
├─ TimeSegment evaluation: ~5ms (in-memory iteration)
├─ Holiday check: ~5ms (indexed by date)
├─ Door lookup: ~2ms (indexed by pk)
└─ Total: ~30ms per request

Expected Load:
├─ 1-10 cards/sec: No issues
├─ 10-100 cards/sec: Still fine (Django handles this)
└─ 100+ cards/sec: May need Redis caching layer

Caching Strategy (optional):
├─ Holiday list: 24hr TTL in Redis
├─ AccessLevel assignments: 5min TTL per employee
└─ TimeSegment rules: 1hr TTL (reload on config change)
```

---

## Monitoring & Debugging

```
Live Debugging:
├─ Browser Console: console.log('🪪 Physical card detected: ...')
├─ Backend Logs: print(..., file=sys.stderr)
├─ Event Table: Real-time display of access attempts
├─ Admin: /admin/ for manual DB inspection
└─ Django Shell: Inspect records programmatically

Common Issues:
├─ "outside_time_segments" ← Check current system time
├─ "no_access_levels" ← Verify employee assignment in admin
├─ "door_not_in_access_levels" ← Verify AccessLevel doors list
├─ "holiday_block" ← Check Holiday table for today
└─ "outside_employee_validity" ← Check acc_startdate/acc_enddate
```

---

**This diagram represents the complete flow for v2025-12-10 with Physical Card Reader support.**
