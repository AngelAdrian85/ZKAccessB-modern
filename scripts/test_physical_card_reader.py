"""
Script pentru testarea cititorului fizic de carduri.
Simuleaza input-ul de la un cititor de carduri fizic.
"""

import sys
import time

def simulate_card_read(card_number: str):
    """
    Simulate a physical card reader by sending keystrokes followed by Enter.
    In a real scenario, the card reader sends these automatically.
    """
    print(f"🪪 Simulare citire card: {card_number}")
    print(f"   Cifrele transmise: {' '.join(card_number)}")
    print(f"   Enter la final: ✓")
    print()
    print("În aplicația reală, cititorul fizic trimite:")
    for digit in card_number:
        print(f"  → keypress: '{digit}'")
        time.sleep(0.01)  # Card readers send very fast
    print(f"  → keypress: 'Enter'")
    print()
    print("Aplicația JavaScript va detecta automat secvența și va procesa cardul.")

def main():
    if len(sys.argv) > 1:
        card = sys.argv[1]
    else:
        print("Utilizare: python test_physical_card_reader.py <numar_card>")
        print("Exemplu: python test_physical_card_reader.py 12345678")
        print()
        card = "12345678"
        print(f"Folosesc card implicit: {card}")
        print()
    
    simulate_card_read(card)
    print()
    print("INSTRUCȚIUNI CITITOR FIZIC:")
    print("=" * 60)
    print("1. Conectează cititorul de carduri USB la stația cu browser-ul")
    print("2. Deschide pagina de monitorizare în browser")
    print("3. Selectează ușa dorită din dropdown-ul 'Door'")
    print("4. Trece un card prin cititor")
    print("5. Aplicația va:")
    print("   - Detecta automat numărul cardului")
    print("   - Afișa notificare vizuală verde în dreapta-sus")
    print("   - Completa automat câmpul 'Card nr'")
    print("   - Evalua accesul pentru ușa selectată")
    print("   - Adăuga eveniment în tabel cu tip 'CITITOR FIZIC'")
    print("   - Deschide automat ușa dacă accesul este permis")
    print()
    print("CONFIGURARE CITITOR:")
    print("-" * 60)
    print("• Majoritatea cititorilor USB funcționează ca HID keyboard")
    print("• Nu necesită drivere speciale (plug-and-play)")
    print("• Verifică că cititorul trimite Enter la final")
    print("• Dacă nu funcționează, verifică că:")
    print("  - Cititorul este în mod 'keyboard emulation'")
    print("  - Browser-ul nu blochează input-ul (nu este în alt tab)")
    print("  - Nu există focus pe alt câmp input (exceptând testCardInput)")

if __name__ == "__main__":
    main()
