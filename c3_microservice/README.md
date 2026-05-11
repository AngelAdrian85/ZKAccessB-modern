# C3-100Pro Microservice

Acest microserviciu ascultă evenimentele push TCP de la controllerul C3-100Pro, decodează pachetele brute de 64 bytes (inclusiv UID/card_no pentru swipe-uri necunoscute), transmite evenimentele către Django și oferă monitorizare live prin WebSocket.

## Structură
- `main.py` — server TCP + WebSocket + integrare Django
- `utils.py` — funcții de decodare pachet
- `config.py` — setări controller, endpoint Django
- `requirements.txt` — dependențe Python

## Pornire
1. Instalează dependențele:
   ```
pip install -r requirements.txt
   ```
2. Rulează microserviciul:
   ```
python main.py
   ```
3. Deschide monitorul live în browser:
   ```
file:///.../c3_microservice/live_monitor.html
   ```

## Exemplu frontend live (HTML+JS)
```html
<!DOCTYPE html>
<html>
<head><title>C3 Live Monitor</title></head>
<body>
<h1>Live Swipe Monitor</h1>
<ul id="events"></ul>
<script>
let ws = new WebSocket("ws://localhost:8765/");
ws.onmessage = function(e) {
    let data = JSON.parse(e.data);
    let li = document.createElement("li");
    li.textContent = `Card: ${data.card_no || "UNKNOWN"}, Event: ${data.event_code}, Door: ${data.door_number}, Time: ${data.timestamp}`;
    document.getElementById("events").prepend(li);
}
</script>
</body>
</html>
```

## Notă
- Pentru carduri necunoscute, controllerul poate trimite `card_no=None` ("NoCard").
- Pentru a prinde UID brut, asigură-te că firmware-ul nu filtrează complet datele sau folosește sniffing Wiegand.
