import datetime

def decode_rtlog_packet(packet_bytes):
    """Decodează pachet 64 bytes de la C3-100Pro"""
    import os
    log_path = os.path.join(os.path.dirname(__file__), 'rtlog_debug.log')
    def log_line(msg):
        print(msg)
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg+'\n')
        except Exception as e:
            print(f"[DECODE][LOG ERROR] {e}")

    if len(packet_bytes) < 12:
        log_line(f"[DECODE] Packet too short: {len(packet_bytes)} bytes")
        return None
    # Log hex dump of packet
    hex_str = ' '.join(f'{b:02X}' for b in packet_bytes[:64])
    log_line(f"[DECODE] RTLOG packet HEX: {hex_str}")
    card = int.from_bytes(packet_bytes[0:4], 'little')
    log_line(f"[DECODE] CardNo raw bytes: {packet_bytes[0:4].hex()} (little-endian) => {card}")
    event = packet_bytes[4]
    verify_code = packet_bytes[5]
    verify_mode = packet_bytes[6]
    door = packet_bytes[7]
    direction = packet_bytes[8]
    timestamp = datetime.datetime.fromtimestamp(int.from_bytes(packet_bytes[8:12], 'little'))
    # Log all extracted fields
    log_line(f"[DECODE] Fields: card_no={card if card != 0 else None}, event_code={event}, verify_code={verify_code}, verify_mode={verify_mode}, door_number={door}, direction={direction}, timestamp={timestamp}")
    result = {
        "card_no": card if card != 0 else None,
        "event_code": event,
        "verify_code": verify_code,
        "verify_mode": verify_mode,
        "door_number": door,
        "direction": direction,
        "timestamp": timestamp,
        "unknown_card": card==0
    }
    # Fallback: dacă card_no nu e valid, caută candidat în payload
    if card == 0:
        # Caut orice secvență de 4 bytes non-zero în payload (little-endian)
        for i in range(0, min(len(packet_bytes)-3, 16)):
            candidate = int.from_bytes(packet_bytes[i:i+4], 'little')
            if candidate != 0:
                log_line(f"[DECODE][FALLBACK] CardNo candidate at offset {i}: {packet_bytes[i:i+4].hex()} => {candidate}")
                result["card_no_candidate"] = candidate
                result["card_no_candidate_offset"] = i
                break
    return result
