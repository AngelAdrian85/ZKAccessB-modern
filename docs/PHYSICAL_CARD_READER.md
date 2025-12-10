# 🪪 Cititor Fizic de Carduri - Ghid Integrare

## Descriere

Sistemul detectează automat cardurile citite de un cititor fizic USB conectat la stația care rulează browser-ul web. Cititorul funcționează ca un dispozitiv de input (HID keyboard emulation) și trimite numărul cardului urmat de Enter.

## Funcționalități

### Detectare Automată
- **Buffer inteligent**: Acumulează cifrele trimise rapid de cititor (< 100ms între caractere)
- **Filtru uman vs robot**: Diferențiază între tastare umană și input de la cititor
- **Proces automat**: La detectarea Enter-ului, procesează imediat cardul

### Feedback Vizual
- **Notificare verde**: Apare în colțul dreapta-sus când se detectează un card
- **Auto-completare**: Completează automat câmpul "Card nr"
- **Event log**: Adaugă rând în tabel cu tip "CITITOR FIZIC"

### Evaluare Access Control
1. Verifică permisiunile pentru ușa selectată
2. Evaluează timpul (program de lucru, holidays)
3. Validează starea angajatului (activ/inactiv)
4. Dacă accesul este permis → **deschide automat ușa**
5. Dacă accesul este respins → afișează motivul în română

### Action Buttons
- **Card necunoscut**: Buton "Adaugă Card" pentru înregistrare rapidă
- **Card recunoscut**: Buton "Modifică" pentru editare angajat

## Instalare Hardware

### Compatibilitate
Funcționează cu majoritatea cititorilor USB care suportă:
- **HID Keyboard Emulation** (mod implicit pentru majoritatea cititorilor)
- **Output format**: Cifre + Enter
- **Standarde suportate**: EM4100, Mifare, HID Prox, etc.

### Exemplu Cititoare Compatibile
- **RFID USB Readers** (125kHz / 13.56MHz)
- **Barcode Scanners** (1D/2D, mod keyboard wedge)
- **Magnetic Card Readers** (track data sau card number only)

### Conectare
1. Conectează cititorul la portul USB al stației cu browser-ul
2. Windows va detecta automat dispozitivul (HID keyboard)
3. **NU sunt necesare drivere speciale**
4. Verifică că LED-ul cititorului se aprinde

## Utilizare

### Setup
1. Deschide pagina de monitorizare: `http://127.0.0.1:14525/agent/monitor/`
2. Selectează **ușa dorită** din dropdown-ul "Door"
3. Browser-ul trebuie să fie **activ** (nu în background)

### Testare
1. Trece un card prin cititor
2. Vei vedea:
   - Notificare verde: "🪪 Card citit: 12345678"
   - Câmpul "Card nr" completat automat
   - Rând nou în tabel cu status și motivul
3. Dacă cardul este permis:
   - Ușa selectată se deschide automat
   - Event-ul apare cu fundal verde
4. Dacă cardul este respins:
   - Event-ul apare cu fundal roșu
   - Motiv afișat în română (ex: "Card necunoscut", "Acces în afara programului")

### Debugging
```powershell
# Test simulare cititor
python scripts\test_physical_card_reader.py 12345678
```

Acest script explică cum funcționează detectarea și oferă instrucțiuni de configurare.

## Configurare Cititor

### Verificare Mod Keyboard
Majoritatea cititorilor au un buton de configurare sau necesită scanarea unui cod QR/barcode pentru a seta modul de output.

#### Setări Recomandate:
- **Output mode**: Keyboard (HID)
- **Suffix**: Enter / CR+LF
- **Prefix**: None
- **Format**: Card number only (no facility code)

### Testare Funcționalitate
Deschide Notepad și trece un card → ar trebui să vezi numărul cardului urmat de Enter (cursor pe linie nouă).

## Flux Tehnic

```
┌──────────────────┐
│  Cititor USB     │
│  (HID Keyboard)  │
└────────┬─────────┘
         │ keypress events (digits + Enter)
         ▼
┌──────────────────────────────────────┐
│  Browser JavaScript Event Listener  │
│  - Acumulează cifre în buffer       │
│  - Detectează Enter                 │
│  - Timeout 100ms între caractere    │
└────────┬─────────────────────────────┘
         │ processPhysicalCard(cardNumber)
         ▼
┌──────────────────────────────────────┐
│  Visual Feedback                     │
│  - Notificare verde                 │
│  - Auto-fill testCardInput          │
└────────┬─────────────────────────────┘
         │ fetch('/agent/api/test-read-card?card_number=...')
         ▼
┌──────────────────────────────────────┐
│  Backend Django                      │
│  - Caută card în DB                 │
│  - Evaluează acces (timeprofile)    │
│  - Returnează ok/error + reasons    │
└────────┬─────────────────────────────┘
         │ response JSON
         ▼
┌──────────────────────────────────────┐
│  Frontend Processing                 │
│  - Adaugă rând în event table       │
│  - Traduce motive în română         │
│  - Dacă ok + ușă selectată →        │
│    doorAction(device_id, door_id)   │
└──────────────────────────────────────┘
         │ fetch('/agent/api/devices/{id}/doors/{door}/open/')
         ▼
┌──────────────────────────────────────┐
│  Actuator Control                    │
│  - Comandă deschidere ușă           │
│  - Log în sistem                    │
│  - WebSocket broadcast              │
└──────────────────────────────────────┘
```

## Parametri Configurabili

În `monitor.html`, secțiunea `initCardReader()`:

```javascript
const READER_TIMEOUT = 100;  // ms între caractere de la cititor
const CARD_MIN_LENGTH = 4;   // lungime minimă card number
```

### Ajustări
- **Cititor lent**: Crește `READER_TIMEOUT` la 150-200ms
- **Carduri scurte**: Scade `CARD_MIN_LENGTH` la 2-3
- **Carduri alfanumerice**: Modifică regex `/\d/` la `/[\da-zA-Z]/`

## Troubleshooting

### Problema: Cardul nu este detectat
**Cauze posibile:**
1. Browser-ul nu este activ (tab în background)
2. Focus pe alt câmp input (ex: user tastează în altă parte)
3. Cititorul nu trimite Enter la final
4. Cititorul este în mod magnetic stripe (nu keyboard)

**Soluție:**
- Verifică în Notepad că cititorul trimite cifre + Enter
- Asigură-te că browser-ul este fereastra activă
- Reconfigurează cititorul în mod keyboard emulation

### Problema: Se detectează, dar ușa nu se deschide
**Cauze:**
1. Nici o ușă selectată în dropdown
2. Card fără permisiuni
3. Acces în afara programului de lucru

**Soluție:**
- Selectează ușa din dropdown "Door"
- Verifică permisiunile cardului în CRUD → IssueCards
- Verifică event log pentru motivul exact (tradus în română)

### Problema: Detectează tastarea normală ca și card
**Cauză:** Timeout prea mare sau user tastează foarte rapid cifre

**Soluție:**
- Scade `READER_TIMEOUT` la 50ms
- Crește `CARD_MIN_LENGTH` la 6-8 (dacă toate cardurile au min 6 cifre)

## Logs & Debugging

### Browser Console
```javascript
// Verifică dacă listener-ul s-a inițializat
// Ar trebui să vezi: "Monitor UI template loaded: v2025-12-10.3 + Physical Card Reader"

// La detectarea unui card:
console.log('🪪 Physical card detected:', cardNumber);
```

### Backend Logs
```
[TEST_READ] provided_card: 12345678
[TEST_READ] card selected: 12345678 (employee: John Doe, ok=True)
```

## Integrare cu Access Control Fizic

Sistemul este pregătit pentru conectare la controllere fizice de acces:
- **ZKTeco C3-400**: Via SDK/API
- **Relay Modules**: Via GPIO/USB
- **Electric Strikes**: Via relay control

### Exemplu flux complet:
1. User trece card prin cititor USB → Browser detectează
2. Backend evaluează acces → Returnează OK
3. Frontend trimite comandă deschidere → Backend comunică cu controller
4. Controller activează relay → Electric strike deschide ușa
5. WebSocket broadcast → Toate clientele văd evenimentul

## Securitate

### Protecții implementate:
- ✅ Input sanitization (doar cifre acceptate)
- ✅ Rate limiting via Django (previne spam)
- ✅ Session validation (doar useri autentificați)
- ✅ CSRF protection pe toate API-urile
- ✅ Card validation în backend (nu doar frontend)

### Best Practices:
- Nu folosi carduri cu numere secvențiale simple
- Activează logging pentru toate accesele
- Review periodic event logs pentru activitate suspicioasă
- Folosește time profiles pentru a restricționa accesul pe intervale

## Versioning

- **v2025-12-10.3**: Suport cititor fizic de carduri + auto-deschidere ușă
- **v2025-12-10.2**: Random card selection pentru test
- **v2025-12-10.1**: Initial monitor UI

## Support

Pentru probleme sau întrebări legate de cititorul fizic:
1. Verifică acest README
2. Rulează `python scripts\test_physical_card_reader.py`
3. Verifică browser console pentru erori JavaScript
4. Verifică backend logs pentru erori Django
