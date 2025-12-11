# 🧪 INSTRUCȚIUNI TESTARE ANIMAȚIE

## Test Direct în Monitor Page

### Setup (30 secunde)
1. **Deschide browser**
   ```
   http://127.0.0.1:14525/agent/monitor/
   ```

2. **Deschide Developer Tools**
   ```
   F12 (Windows/Linux) sau Cmd+Option+I (Mac)
   ```

3. **Mergi la Console tab**
   ```
   Ar trebui să vezi: "Monitor UI template loaded: v2025-12-10.3 + Physical Card Reader"
   ```

---

## Testare Animație

### Metoda 1: Test Button (Quick)
```
1. Selectează o ușă din dropdown "Door"
2. Click pe butonul "🪪 Test Deschidere Ușă"
3. OBSERVĂ:
   - Notificare tech-style apare în CENTRUL ecranului
   - Titlu verde: "🪪 CARD DETECTAT"
   - Card number în monospace 32px
   - Pulsing green bar
   - Durată: 1.5+ secunde
   - Apoi se estompează
4. Check console: "🪪 Physical card detected: ..."
```

### Metoda 2: Physical Reader (Dacă ai cititorul)
```
1. Conectează cititorul USB la calculator
2. Deschide /agent/monitor/
3. Selectează o ușă
4. Treci card prin cititorul USB
5. OBSERVĂ animația + event log
```

---

## Ce Ar Trebui Să Vezi

### ✅ ANIMAȚIE CORECTĂ:
```
┌──────────────────────────────────────────┐
│                                          │
│    ╔══════════════════════════════╗     │
│    ║   🪪 CARD DETECTAT           ║     │
│    ║   12345678                   ║     │
│    ║   ████████▌ (pulsing)        ║     │
│    ╚══════════════════════════════╝     │
│                                          │
│  - Centered pe screen ✓                 │
│  - Green glowing border ✓               │
│  - Blue gradient background ✓           │
│  - Pulsing bar ✓                        │
│  - 1.5 sec display ✓                    │
│  - Smooth fade-out ✓                    │
└──────────────────────────────────────────┘
```

---

## Debugging - Dacă Nu Merge

### Pas 1: Check Console
```
F12 → Console tab

Ar trebui să vezi:
✓ "Monitor UI template loaded: v2025-12-10.3 + Physical Card Reader"
✓ "🪪 Physical card detected: 12345678"
✓ "✅ CSS animations injected"

Dacă NU vezi aceste mesaje → problema în JavaScript
```

### Pas 2: Check Network
```
F12 → Network tab

Click "Test Deschidere Ușă" și observă:
✓ Request: /agent/api/test-read-card
✓ Status: 200 OK
✓ Response: JSON cu ok, card_number, status_text

Dacă Status = 500 sau 403 → problema în backend
```

### Pas 3: Check Elements
```
F12 → Elements/Inspector tab

Click "Test Deschidere Ușă"

Ar trebui să vezi în DOM:
✓ <div> with style="position: fixed; inset: 0; ..."
✓ <div> cu class "card indicator" (scaled, rotated)
✓ <style id="cardReaderAnimations"> cu @keyframes

Dacă NU apare elementul → problema în processPhysicalCard()
```

### Pas 4: Check CSS Support
```
Chrome DevTools → Console → type:

CSS.supports('animation', 'fadeInOverlay 0.3s')

Ar trebui: true

Dacă: false → browser prea vechi
```

---

## Troubleshooting

### ❌ "Nimic nu apare pe screen"

**Cauza 1**: CSS animations nu-s injected
```
Fix: Verify document.getElementById('cardReaderAnimations')
  → Ar trebui să returneze style element
```

**Cauza 2**: Overlay div zIndex conflict
```
Fix: Check alt element cu zIndex > 9998
  → Verifică în browser CSS
```

**Cauza 3**: JavaScript error în processPhysicalCard
```
Fix: F12 Console → check pentru red errors
  → Copy-paste eroare aici
```

---

### ❌ "Animația apare dar NU se mișcă"

**Cauza**: Browser nu suportă CSS animations
```
Fix: Use non-animated fallback (immediate display)
  → Deschide DevTools, check "Disable CSS"
```

**Cauza**: @keyframes nu-s loaded
```
Fix: Verify style tag în <head>
  → F12 → Elements → search "cardReaderAnimations"
```

---

### ❌ "Animația se mișcă prea repede/lent"

**Dacă prea repede** (< 1 sec):
```
Find in monitor.html:
setTimeout(() => { ... }, 1500);
         Change 1500 to 1800 (milliseconds)
```

**Dacă prea lent** (> 2 sec):
```
Change 1500 to 1200
```

---

### ❌ "Pulsing bar nu se mișcă"

**Fix**: Check pulse animation
```
@keyframes pulse {
  0%, 100% { width: 60px; opacity: 1; }
  50% { width: 120px; opacity: 0.6; }  ← Change values here
}
```

---

## Expected Console Output

Deschide F12 Console și click "Test Deschidere Ușă":

```javascript
Monitor UI template loaded: v2025-12-10.3 + Physical Card Reader
🪪 Physical card detected: 12345678
✅ CSS animations injected
📊 Starting fade-out after 1.5 seconds
✅ Animation complete, element removed from DOM
```

---

## Performance Check

Deschide F12 → Performance tab:

1. Click "Test Deschidere Ușă"
2. Press Ctrl+Shift+E (or click Record)
3. Perform test
4. Click Stop

Expected:
- ✓ No red frames (60 FPS maintained)
- ✓ Animation smooth, no stuttering
- ✓ CPU usage < 5%

---

## Final Verification Checklist

```
Test Animation:
☐ Click test button
☐ Animation appears in CENTER (not corner)
☐ Title "🪪 CARD DETECTAT" visible (green)
☐ Card number visible (32px monospace)
☐ Green pulsing bar visible
☐ Green glowing border visible
☐ Dark overlay background visible
☐ Entry animation: grows + rotates smoothly
☐ Stays visible 1.5+ seconds
☐ Exit animation: fades out smoothly
☐ Console shows no errors
☐ Network shows 200 OK on API call
☐ Event log shows new entry after animation

Physical Reader Test (if available):
☐ Connect USB reader
☐ Select door
☐ Swipe card
☐ Animation appears
☐ Event log shows entry
☐ Door opens (if access granted)
```

---

## Version Info

- **Current**: v2025-12-10.3 (Fixed)
- **Change**: Removed rotateY (not working without perspective)
- **New**: Using rotate(-15deg) instead (works in all browsers)
- **Status**: Ready for testing

---

## Report Template

Daca gasiti issue, raportati cu:

```
Browser: [Chrome/Firefox/Safari/Edge] v[version]
OS: [Windows/Mac/Linux]
Screen: [resolution, ex: 1920x1080]

Console Error (if any):
[paste here]

Expected Behavior:
- Animation centered
- Duration 1.5 sec
- Green glowing border

Actual Behavior:
[describe what happens]

Steps to Reproduce:
1. Go to /agent/monitor/
2. Click "Test Deschidere Ușă"
3. [observe]
```

---

**Status**: Ready for testing v2025-12-10.3
**Fixed**: CSS animation issue (removed rotateY, added rotate)
**Next**: User testing to confirm animation displays
