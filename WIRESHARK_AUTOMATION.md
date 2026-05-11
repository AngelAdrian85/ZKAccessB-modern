# Wireshark Automation

Scopul acestui flux este sa elimine pasii manuali sensibili la eroare cand vrei sa capturezi traficul controllerului si sa vezi rapid care `tcp.stream` merita analizat.

## Comanda principala

Din radacina repo-ului:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_controller_pcap.ps1 -ControllerIp 192.168.1.235 -Seconds 20
```

Ce face automat:

1. detecteaza `tshark.exe`
2. alege automat prima interfata `Ethernet` non-loopback daca nu specifici una
3. captureaza doar hostul controllerului si porturile uzuale `4370`, `14370`, `8091`
4. salveaza captura in `captures/wireshark/`
5. ruleaza analizorul local si genereaza rezumate langa fisierul `.pcapng`
6. exporta primele streamuri TCP cu payload in fisiere text separate

## Exemple utile

Lista interfetelor detectate de `tshark`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_controller_pcap.ps1 -ListInterfaces
```

Captura pe o interfata anume:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_controller_pcap.ps1 -ControllerIp 192.168.1.235 -Interface 1 -Seconds 15
```

Captura fara analiza automata:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_controller_pcap.ps1 -ControllerIp 192.168.1.235 -SkipAnalysis
```

Analiza manuala ulterioara pentru un `.pcapng` deja salvat:

```powershell
.venv\Scripts\python.exe .\scripts\analyze_controller_pcap.py --pcap .\captures\wireshark\controller_192_168_1_235_YYYYMMDD_HHMMSS.pcapng --controller-ip 192.168.1.235 --port 4370 --port 14370 --port 8091
```

## Fisiere generate

Pentru o captura `controller_...pcapng`, scripturile vor produce:

1. `controller_...pcapng`
2. `controller_...pcapng.summary.json`
3. `controller_...pcapng.summary.txt`
4. `controller_...pcapng.candidates.json`
5. `controller_...pcapng.candidates.csv`
6. folderul `controller_..._streams\` cu dump-uri `tcp.stream`

## Cum folosesti rezultatul

1. deschizi `.summary.txt`
2. alegi un filtru sugerat de forma `tcp.stream eq N`
3. daca streamul pare bun, deschizi captura in Wireshark si aplici acel filtru
4. verifici `*.candidates.csv` pentru comparatia rapida a offset-urilor candidate `CardNo/Event/Door`
5. verifici dump-ul asociat din folderul `_streams`

## Recomandare practica pentru controller 22

Pentru investigatia curenta, secventa recomandata este:

1. pornesti captura pentru `15-20s`
2. faci exact un singur swipe necunoscut
3. opresti automat la expirarea duratei
4. citesti `.summary.txt`
5. verifici streamul cu cele mai multe `payload_packets`

Acest flux nu inlocuieste decodarea protocolului ZKTeco, dar reduce drastic riscul de a alege interfata gresita, filtrul gresit sau streamul gresit.