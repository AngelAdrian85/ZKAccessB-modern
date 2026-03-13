# W26 Hardware Tap Runbook

## Scop

Controllerul 22 la `192.168.1.235` continua sa produca evenimente valide de tip `27` cu `CardNo` gol. Calea software a fost deja epuizata. Singura pista ramasa pentru numarul real al cardului este capturarea pasiva a liniilor Wiegand dintre cititor si controller si injectarea cadrului brut in pipeline-ul existent din repo.

Acest runbook este pentru montajul curent:

1. `device_id = 22`
2. `door_id = 1`
3. `door_pk = 27`
4. formatul asteptat este `Wiegand 26`
5. listenerul software este pe `0.0.0.0:9002`
6. source-ul salvat in monitor este `w26-hardware-tap`

## Criteriul de succes

Runbook-ul este considerat reusit numai daca apar toate trei:

1. in [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl) apare `frame_parsed` la swipe real
2. monitorul trece din `RAW capture absent` in stare activa
3. evenimentul controllerului fara `CardNo` este corelat cu numarul real al cardului prin pipeline-ul existent

## Hardware minim acceptat

Aveti nevoie de unul dintre aceste montaje:

1. convertor `Wiegand -> USB/UART` care poate citi pasiv `D0`, `D1`, `GND`
2. convertor `Wiegand -> TCP` care poate deschide o conexiune TCP si trimite un frame pe linie
3. microcontroller simplu, de exemplu `ESP32`, `ESP8266`, `Arduino`, `Raspberry Pi Pico`, configurat ca sniffer pasiv

Important:

1. tap-ul trebuie facut in paralel, nu in serie
2. nu intrerupeti legatura reader -> controller
3. nu injectati tensiune in `D0` sau `D1`
4. masa trebuie sa fie comuna: `Reader GND` catre `Sniffer GND`

## Puncte de conectare

Legatura minima este:

1. `Reader GND` -> `Sniffer GND`
2. `Reader D0` -> `Sniffer D0 input`
3. `Reader D1` -> `Sniffer D1 input`

Ordinea practica recomandata la instalare:

1. identificati pe reader sau pe borna controllerului cele trei fire: `D0`, `D1`, `GND`
2. confirmati cu multimetrul doar continuitatea si masa comuna, fara a alimenta snifferul din liniile de date
3. prindeti tap-ul cat mai aproape de controller, nu la distanta mare pe cablu, ca sa reduceti reflexiile si zgomotul

## Contractul de intrare catre pipeline

Listenerul software deja existent primeste cadre TCP text, cate un cadru pe linie. Sunt acceptate urmatoarele forme:

1. `BITS:10101010101010101010101010`
2. `HEX:123456`
3. `INT:1193046`
4. JSON, de exemplu `{"wiegand_bits":"1010...","wiegand_format":"Wiegand 26"}`

La nivel software, aceste cadre sunt inghitite de [scripts/wiegand_listener.py](scripts/wiegand_listener.py), apoi sunt postate catre `/agent/api/cards/read/push/` si intra in decoderul si bufferul de corelare deja implementate.

## Configuratia curenta din repo

Repo-ul este deja pregatit pentru controllerul 22 prin [scripts/card_readers.json](scripts/card_readers.json):

1. `wiegand.enabled = true`
2. `wiegand.listen_host = 0.0.0.0`
3. `wiegand.port = 9002`
4. `wiegand.format_name = Wiegand 26`
5. `wiegand.device_id = 22`
6. `wiegand.door_id = 1`
7. `wiegand.door_pk = 27`
8. `wiegand.source = w26-hardware-tap`

Nu schimbati aceste valori pana cand nu exista dovada ca readerul real foloseste alta usa sau alt format.

## Pasul 1: porniti serverul local

Listenerul W26 posteaza in aplicatia Django locala. Inainte de orice test hardware, serverul trebuie sa fie sus.

Din radacina repo-ului:

```powershell
$env:DJANGO_SETTINGS_MODULE = 'zkeco_config.settings'
.\tray_launch.ps1
```

Daca lucrati deja cu tray-ul pornit, nu il reporniti inutil. Verificati doar ca UI-ul sa fie accesibil pe portul tray-ului curent.

## Pasul 2: armati listenerul W26

Din radacina repo-ului:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_w26_tap_capture.ps1 -ServerUrl http://127.0.0.1:15437 -ListenHost 0.0.0.0 -ListenPort 9002 -FormatName 'Wiegand 26' -DeviceId 22 -DoorId 1 -DoorPk 27 -Source w26-hardware-tap
```

Ce trebuie sa vedeti imediat:

1. mesajul `W26 tap capture armed`
2. un PID pentru listener
3. `TCP target: 0.0.0.0:9002`

Fișierele care trebuie sa existe dupa armare:

1. [tmp_w26_tap_capture.log](tmp_w26_tap_capture.log)
2. [tmp_w26_tap_capture.err.log](tmp_w26_tap_capture.err.log)
3. [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl)
4. `%USERPROFILE%\zkeco_reader_heartbeat_wiegand.json`

## Pasul 3: validati software-ul fara hardware

Inainte de primul swipe real, trebuie sa demonstrati ca pipeline-ul software functioneaza singur.

Executati:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\send_w26_test_frame.ps1 -Host 127.0.0.1 -Port 9002 -Payload 'BITS:10101010101010101010101010'
```

Rezultatul asteptat:

1. in [tmp_w26_tap_capture.log](tmp_w26_tap_capture.log) apare `[WIEGAND] RX`
2. in [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl) apare `frame_parsed`
3. monitorul nu mai raporteaza listener down

Daca acest pas esueaza, nu treceti la hardware. Problema este software sau port local, nu cablarea W26.

## Pasul 4: armati observabilitatea pentru testul real

Deschideti in paralel urmatoarele surse de adevar:

1. monitorul live din aplicatie
2. [tmp_w26_tap_capture.log](tmp_w26_tap_capture.log)
3. [tmp_w26_tap_capture.err.log](tmp_w26_tap_capture.err.log)
4. [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl)

Comenzi utile:

```powershell
Get-Content .\tmp_w26_tap_capture.log -Wait
```

```powershell
Get-Content .\tmp_w26_tap_capture.err.log -Wait
```

```powershell
Get-Content .\tmp_wiegand_listener_trace.jsonl -Wait
```

## Pasul 5: faceti swipe-ul real pe cardul necunoscut

Executati swipe-ul real de 3 pana la 5 ori, la intervale de 2-3 secunde.

La fiecare swipe cautati exact asta:

1. in trace: `client_connected`, apoi `frame_parsed`, apoi `frame_processed`
2. in log: `[WIEGAND] RX ...`
3. in monitor: evenimentul controllerului este imbogatit sau apare corelarea Wiegand

## Pasul 6: interpretarea rezultatului

### Cazul A: apare `frame_parsed`

Asta inseamna ca tap-ul hardware vede readerul real. Din acest punct, numarul real al cardului trebuie sa existe in payloadul Wiegand si problema ramasa este doar de format sau de corelare.

Pasii imediati:

1. extrageti frame-ul exact din [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl)
2. rulati-l si prin [tools/decode_wiegand.py](tools/decode_wiegand.py) daca numarul nu pare corect
3. daca rezultatul decodat nu este bun, incercati alt format Wiegand pe acelasi raw frame, nu schimbati cablarea

Exemplu:

```powershell
.venv\Scripts\python.exe .\tools\decode_wiegand.py --bits 10101010101010101010101010 --format 'Wiegand 26'
```

### Cazul B: listenerul este sus, dar nu apare niciun `frame_parsed`

Asta inseamna ca tap-ul nu vede traficul real al readerului. In ordinea probabilitatii:

1. tap-ul este pus pe fire gresite
2. lipseste masa comuna
3. cititorul nu este pe traseul fizic pe care il testati
4. readerul nu este W26 sau foloseste o alta topologie electrica fata de cea presupusa
5. dispozitivul de sniffing nu detecteaza corect impulsurile Wiegand

In acest caz, problema nu mai este in Django sau in pipeline. Este strict hardware sau de nivel electric.

### Cazul C: apare `frame_parsed`, dar cardul decodat este gresit

Asta inseamna format gresit, nu captura gresita. Pasii sunt:

1. pastrati raw bits exact cum au fost capturate
2. testati decodarea cu mai multe formate compatibile
3. confirmati lungimea reala a frame-ului inainte sa schimbati `format_name`

## Semnele ca totul merge corect

Semnalul bun arata asa, cap-coada:

1. listenerul este pe `9002`
2. swipe-ul real produce `frame_parsed`
3. `raw capture absent` dispare din monitor
4. evenimentul controllerului fara `CardNo` primeste numarul real al cardului din bufferul Wiegand

## Ce nu trebuie facut

1. nu folositi acelasi montaj ca injector activ pe `D0/D1`
2. nu reporniti controllerul intre teste daca problema este lipsa `frame_parsed`
3. nu schimbati simultan portul listenerului, usa, formatul si source-ul
4. nu tratati lipsa de `frame_parsed` ca bug software; este indicator de lipsa captura hardware

## Fisierele de adevar pentru acest runbook

1. [scripts/start_w26_tap_capture.ps1](scripts/start_w26_tap_capture.ps1)
2. [scripts/send_w26_test_frame.ps1](scripts/send_w26_test_frame.ps1)
3. [scripts/wiegand_listener.py](scripts/wiegand_listener.py)
4. [scripts/card_readers.json](scripts/card_readers.json)
5. [tmp_w26_tap_capture.log](tmp_w26_tap_capture.log)
6. [tmp_w26_tap_capture.err.log](tmp_w26_tap_capture.err.log)
7. [tmp_wiegand_listener_trace.jsonl](tmp_wiegand_listener_trace.jsonl)

## Verdict operational

Daca Pasul 3 trece si Pasul 5 nu produce `frame_parsed`, blocajul ramas este 100% pe tap-ul fizic W26. Daca Pasul 5 produce `frame_parsed`, numarul real al cardului este in sfarsit pe traseul corect si se poate regla doar formatul de decodare.
