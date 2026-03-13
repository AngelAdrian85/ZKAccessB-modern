# BACKUP / SALVARE — 13-03-2026 (copie 1:1 în Git)

Data
----
2026-03-13

Scop
----
Această salvare marchează copia de lucru actuală a proiectului în Git, astfel încât starea completă să poată fi reluată de pe alt calculator exact din punctul curent al investigației.

Context
-------
Backupul surprinde progresul legat de controllerul 22 (`192.168.1.235`), firmware `ZMM200_C3Pro / AC Ver 4.7.8.3033 Aug 14 2023`, cu accent pe recuperarea numărului real pentru carduri necunoscute atunci când controllerul trimite evenimente valide fără `CardNo`.

Descriere progres
-----------------
1. Rută și capabilități controller
- Au fost adăugate registre și utilitare pentru capabilități controller, provisioning, decodare payload-uri, rezoluție de port și probe pyzk/plcommpro.
- A fost documentată și implementată logica de preferare a portului firmware `14370` pentru familia C3-100Pro investigată.

2. Corelare unknown card prin Wiegand
- A fost introdusă infrastructura de corelare Wiegand pentru a putea atașa un număr de card sniffed unui eveniment controller fără `CardNo`.
- `DeviceRealtimeLog` a primit `correlation_payload`, cu migrația aferentă.
- CommCenter și fluxurile de push pentru reader capture au fost extinse pentru această corelare.

3. UI și monitorizare live
- Au fost adăugate componente Wiegand în UI și decodare pentru formate uzuale.
- Monitorul live și varianta embedded afișează acum explicit starea de captură brută și erorile zkemkeeper.
- Tray-ul persistă `capture_health`, `raw_capture_state` și mesajele relevante în `tray_status.json`.

4. Tooling pentru captură reală
- Au fost adăugate scripturi pentru listenerul W26, injectorul de test, bridge-urile zkemkeeper, probe controller și capturi de diagnoză.
- A fost adăugat runbook-ul [HARDWARE_W26_TAP_GUIDE.md](HARDWARE_W26_TAP_GUIDE.md) pentru tap hardware pasiv pe liniile W26 și injectarea în pipeline-ul existent.

5. Validare curentă
- Lanțul software W26 este validat: listenerul de pe `9002` primește cadre și le postează cu succes în `/agent/api/cards/read/push/`.
- După patch-ul de health derivation, `tray_status.json` raportează corect `raw_capture_state = active` după un frame nou.
- `zkemkeeper` rămâne în eroare pe controllerul 22, dar nu mai blochează testarea căii W26.

Ce NU este inclus intenționat în Git
-----------------------------------
Nu sunt incluse artefactele locale și sensibile precum:

1. cookie-uri web locale
2. capturi temporare `iclock` / `tmp_*`
3. probe și dump-uri runtime locale
4. fișiere de log generate în timpul testelor live

Următorul pas operațional
-------------------------
Din această stare, pasul următor nu mai este dezvoltare software de bază, ci un swipe real pe cititorul ale cărui linii W26 sunt efectiv tap-uite. Dacă acel swipe nu produce `frame_parsed`, blocajul rămas este exclusiv pe captură hardware.