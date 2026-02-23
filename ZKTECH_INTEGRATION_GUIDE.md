# ZKTech Access Control Panel Integration Guide

## 1. Scopul & Arhitectura

Obiectiv: Conecta centrala de acces ZKTech (192.168.1.232:443) cu aplicația Django modern pentru:
- Citire în timp real a logurilor de acces
- Control ușilor (deschis/închis)
- Sincronizare timp
- Gestionare utilizatori/carduri
- Database centralizat cu loguri și stări

### Arhitectura de Comunicație

```
┌─────────────────┐
│  Django UI/API  │  (localhost:8000)
│   agent app     │
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │  ModernCommCenter    │  (agent/modern_comm_center.py)
    │  & DeviceSession     │
    │  management          │
    └────────┬─────────────┘
             │
    ┌────────▼──────────────┐
    │  CommDriver Protocol  │
    │  Socket/TCP/SDK       │
    └────────┬──────────────┘
             │ TCP 192.168.1.232:443
    ┌────────▼────────────────────┐
    │  ZKTech Access Panel        │
    │  (real hardware device)      │
    └─────────────────────────────┘
```

## 2. Configurare Hardware - Verificări Preliminare

### 2.1 Test Conectivitate Rețea

Din PowerShell, pe serverul Django:

```powershell
# Test ping la device
ping 192.168.1.232

# Test TCP connectivity pe portul 443
Test-NetConnection -ComputerName 192.168.1.232 -Port 443

# Test TCP connectivity pe portul 4370 (port SDK implicit ZKTech)
Test-NetConnection -ComputerName 192.168.1.232 -Port 4370
```

**Rezultat așteptat**:
```
TcpTestSucceeded : True
```

### 2.2 Verificare Firewall Windows

```powershell
# Adaugă excepție firewall pentru outbound TCP către device

# Port 443
New-NetFirewallRule -DisplayName "ZKTech Access Panel 443" `
    -Direction Outbound -Action Allow -Protocol TCP `
    -RemoteAddress 192.168.1.232 -RemotePort 443 `
    -Program any

# Port 4370 (SDK)
New-NetFirewallRule -DisplayName "ZKTech Access Panel 4370" `
    -Direction Outbound -Action Allow -Protocol TCP `
    -RemoteAddress 192.168.1.232 -RemotePort 4370 `
    -Program any
```

### 2.3 Documentație Hardware ZKTech

Ceea ce trebuie cunoscut:
- **IP**: 192.168.1.232
- **Port SSH/Web**: 443 (web interface) sau 22 (SSH)
- **Port SDK**: 4370 (ZKAccess SDK protocol - **IMPORTANT**)
- **Credențiale**: Obțineți din admin ZKTech (user/pass pentru admin SDK)
- **Serial Number**: Afișat pe device
- **Firmware Version**: Verificați și notați

## 3. Integrare în Database Django

### 3.1 Creare Device în ORM

Accesați Django admin (http://localhost:8000/admin/):

1. Navigați la **Agent > Devices**
2. Click **Add Device**
3. Completați:

```
Name: ZKTech Access Panel - Main
Serial Number: (din device)
Device Type: Access Control Panel
Communication Mode: TCP/IP
IP Address: 192.168.1.232
Port: 4370  (SDK port, NU 443!)
Communication Password: (dacă setată pe device)
Area Name: Main Entrance
Enabled: ✓
Auto Sync Time: ✓
Firmware Version: (notați versiunea)
Scanner Linked: ✓ (dacă folosiți ACP/Elatec readers)
```

4. **Save**

### 3.2 Verificare în Terminal

```powershell
cd zkeco_modern

# Intră în shell Django
python manage.py shell

# Verifică device-ul creat
from agent.models import Device
dev = Device.objects.filter(ip_address='192.168.1.232').first()
print(dev)
print(f"ID: {dev.id}, Name: {dev.name}, Port: {dev.port}")
```

## 4. Implementare Driver ZKTech Protocol

### 4.1 Structura - Două Opțiuni

#### **Opțiune A: Socket TCP Direct (Recomandat pentru început)**

Loc: `zkeco_modern/agent/drivers/zk_socket_driver.py` (nou fișier)

```python
import socket
import struct
import logging
import time
from typing import Dict, Any, Optional

LOG = logging.getLogger("zk_socket_driver")

class ZKTechSocketDriver:
    """Direct TCP socket communication with ZKTech Access Control Panel.
    
    Protocol: plcommpro (ZKAccess proprietary binary protocol over TCP)
    Port: 4370 (standard SDK port)
    """
    
    def __init__(self, dev):
        """
        dev: Device model instance with ip_address, port, comm_password
        """
        self.dev = dev
        self.ip = dev.ip_address
        self.port = dev.port or 4370
        self.password = (dev.comm_password or "").encode('utf-8')
        self.socket: Optional[socket.socket] = None
        self.session_id: Optional[int] = None
        self.timeout = 5.0
        
    def connect(self) -> Dict[str, Any]:
        """Establish TCP connection to ZKTech device.
        
        Returns: {"result": 1, "hcommpro": session_id} on success
                 {"result": -1, "error": "reason"} on failure
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.ip, self.port))
            
            # ZKAccess protocol: send initial handshake
            # Command: CMD_CONNECT (0x09C9)
            cmd = self._build_command(0x09C9, b"")  # Connect command
            self.socket.send(cmd)
            
            # Read response
            response = self.socket.recv(1024)
            result = self._parse_response(response)
            
            if result.get("success"):
                self.session_id = result.get("session_id", 0)
                LOG.info(f"Connected to {self.ip}:{self.port} - Session: {self.session_id}")
                return {"result": 1, "hcommpro": self.session_id, "transport": "socket"}
            else:
                self.socket.close()
                self.socket = None
                return {"result": -1, "error": "handshake_failed"}
                
        except socket.timeout:
            return {"result": -1, "error": "connection_timeout"}
        except ConnectionRefusedError:
            return {"result": -1, "error": "connection_refused"}
        except Exception as e:
            LOG.error(f"Connection failed: {e}")
            return {"result": -1, "error": str(e)}
    
    def disconnect(self) -> Dict[str, Any]:
        """Close TCP connection."""
        try:
            if self.socket:
                # Send disconnect command CMD_EXIT (0x0001)
                cmd = self._build_command(0x0001, b"")
                self.socket.send(cmd)
                self.socket.close()
            self.socket = None
            self.session_id = None
            return {"result": 1}
        except Exception as e:
            LOG.error(f"Disconnect error: {e}")
            return {"result": -1, "error": str(e)}
    
    def get_rtlog(self) -> Dict[str, Any]:
        """Retrieve real-time log entries from device.
        
        Returns: {"result": N, "data": "log_line1\r\nlog_line2\r\n..."}
        """
        if not self.socket or not self.session_id:
            return {"result": -1, "error": "not_connected"}
        
        try:
            # Command: CMD_GETRTLOG (0x09C8)
            cmd = self._build_command(0x09C8, b"")
            self.socket.send(cmd)
            
            # Read response - may be large, use loop
            data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 100000:  # Limit to prevent memory issues
                    break
            
            lines = self._parse_rtlog_response(data)
            return {"result": len(lines), "data": "\r\n".join(lines)}
            
        except Exception as e:
            LOG.error(f"get_rtlog error: {e}")
            return {"result": -1, "error": str(e)}
    
    def get_transaction(self, newlog: bool = False) -> Dict[str, Any]:
        """Retrieve transaction/event logs.
        
        Args:
            newlog: if True, retrieve only new logs since last read
        
        Returns: {"result": N, "data": {1: "line1", 2: "line2", ...}}
        """
        if not self.socket or not self.session_id:
            return {"result": -1, "error": "not_connected"}
        
        try:
            # Command: CMD_GETTRANSACTION (0x09C3) for new logs
            # or CMD_QUERYLOG (0x0950) for all transaction logs
            cmd_code = 0x09C3 if newlog else 0x0950
            cmd = self._build_command(cmd_code, b"")
            self.socket.send(cmd)
            
            data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 500000:  # Larger limit for transaction data
                    break
            
            transactions = self._parse_transaction_response(data)
            return {"result": len(transactions), "data": transactions}
            
        except Exception as e:
            LOG.error(f"get_transaction error: {e}")
            return {"result": -1, "error": str(e)}
    
    def controldevice(self, door: int, index: int, state: int) -> Dict[str, Any]:
        """Control door relay.
        
        Args:
            door: door number (1-based)
            index: relay index on that door
            state: 1 = activate (open), 0 = deactivate (close)
        """
        if not self.socket or not self.session_id:
            return {"result": -1, "error": "not_connected"}
        
        try:
            # Command: CMD_CONTROLDOOR (0x09CA)
            payload = struct.pack("<iii", door, index, state)
            cmd = self._build_command(0x09CA, payload)
            self.socket.send(cmd)
            
            response = self.socket.recv(1024)
            result = self._parse_response(response)
            
            if result.get("success"):
                LOG.info(f"Door control: door={door}, index={index}, state={state}")
                return {"result": 1, "description": f"Door {door} set to {state}"}
            else:
                return {"result": -1, "error": "control_failed"}
        except Exception as e:
            LOG.error(f"controldevice error: {e}")
            return {"result": -1, "error": str(e)}
    
    def control_normal_open(self, door: int, state: int) -> Dict[str, Any]:
        """Set normal-open mode for door."""
        # Similar to controldevice
        return self.controldevice(door, 0, state)
    
    def cancel_alarm(self, door: str) -> Dict[str, Any]:
        """Cancel door alarm."""
        if not self.socket or not self.session_id:
            return {"result": -1, "error": "not_connected"}
        
        try:
            # Command: CMD_CANCELWARNING (0x09CB)
            payload = int(door).to_bytes(4, 'little')
            cmd = self._build_command(0x09CB, payload)
            self.socket.send(cmd)
            
            response = self.socket.recv(1024)
            result = self._parse_response(response)
            return {"result": 1 if result.get("success") else -1}
        except Exception as e:
            return {"result": -1, "error": str(e)}
    
    # Placeholder methods for full CommDriver protocol
    def query_data(self, table, fields, flt, extra):
        return {"result": 0, "data": []}
    
    def update_data(self, table, data, extra):
        return {"result": 1}
    
    def delete_data(self, table, flt):
        return {"result": 1}
    
    def Get_Data_Count(self, table):
        return {"result": 0}
    
    def get_options(self, items):
        return {"result": 0, "data": ""}
    
    def set_options(self, items):
        return {"result": 1}
    
    # ============ Protocol Implementation Details ============
    
    def _build_command(self, cmd_code: int, payload: bytes) -> bytes:
        """Build ZKAccess protocol command packet.
        
        Format (little-endian):
        - Command code (2 bytes)
        - Session ID (2 bytes)
        - Reply flag (2 bytes)
        - Payload length (2 bytes)
        - Payload (N bytes)
        - Checksum (2 bytes)
        """
        session = self.session_id or 0
        reply = 1  # Expect reply
        length = len(payload)
        
        # Build header
        header = struct.pack("<hhhh", cmd_code, session, reply, length)
        
        # Compute checksum
        packet = header + payload
        checksum = self._compute_checksum(packet)
        
        return packet + struct.pack("<h", checksum)
    
    def _parse_response(self, data: bytes) -> Dict[str, Any]:
        """Parse response packet."""
        if len(data) < 8:
            return {"success": False, "error": "incomplete_response"}
        
        try:
            cmd_code, session, reply, length = struct.unpack("<hhhh", data[:8])
            return {"success": True, "session_id": session, "length": length}
        except:
            return {"success": False, "error": "parse_failed"}
    
    def _parse_rtlog_response(self, data: bytes) -> list:
        """Parse rtlog response into list of log lines."""
        # Format: sequence of log entries separated by specific markers
        # This depends on exact device firmware; adjust as needed
        try:
            lines = data.decode('utf-8', errors='ignore').split('\r\n')
            return [l.strip() for l in lines if l.strip()]
        except:
            return []
    
    def _parse_transaction_response(self, data: bytes) -> Dict[int, str]:
        """Parse transaction log response."""
        try:
            lines = data.decode('utf-8', errors='ignore').split('\r\n')
            result = {}
            for i, line in enumerate(lines, 1):
                if line.strip():
                    result[i] = line.strip()
            return result
        except:
            return {}
    
    def _compute_checksum(self, data: bytes) -> int:
        """Compute ZKAccess protocol checksum."""
        checksum = 0
        for byte in data:
            checksum ^= byte  # XOR checksum
        return checksum & 0xFFFF
```

#### **Opțiune B: SDK DLL (Dacă avem plcommpro.dll)**

Utilizați `zkeco_modern/agent/driver_ctypes.py` existent - doar trebuie extins.

## 5. Integrare în CommCenter

### 5.1 Modificare `modern_comm_center.py`

Adaug în `build_and_run_stub`:

```python
def build_and_run_stub(poll_interval=1.0,
                       use_redis: bool = False,
                       redis_url: Optional[str] = None,
                       download_hours: Optional[List[int]] = None,
                       driver: str = "auto",
                       driver_factory: Optional[Callable] = None):
    # ...existing code...
    
    if driver == "stub":
        driver_factory = lambda dev: StubDriver(dev)
    elif driver == "socket":
        driver_factory = lambda dev: LegacyDriverAdapter(dev)
    elif driver == "zk":  # NEW: ZKTech native driver
        try:
            from .drivers.zk_socket_driver import ZKTechSocketDriver
            driver_factory = lambda dev: ZKTechSocketDriver(dev)
        except ImportError:
            LOG.warning("ZKTech driver not available; falling back to stub")
            driver_factory = lambda dev: StubDriver(dev)
    elif driver == "sdk":
        # ...existing SDK code...
        pass
```

### 5.2 Pornire CommCenter cu Driver ZKTech

```powershell
cd zkeco_modern

# Testare driver ZKTech
python manage.py run_commcenter --interval 5.0 --driver zk

# Cu logging detaliat
python manage.py run_commcenter --interval 5.0 --driver zk --verbosity 3
```

## 6. Testare End-to-End

### 6.1 Database Setup

```powershell
# Migrații
python manage.py migrate

# Creare device (din secțiunea 3.1 mai sus)
python manage.py shell
```

### 6.2 Start Server + CommCenter

Terminal 1 - Server Django:
```powershell
python manage.py runserver 0.0.0.0:8000
```

Terminal 2 - CommCenter:
```powershell
python manage.py run_commcenter --interval 2.0 --driver zk
```

### 6.3 Verificare Loguri

Accesați http://localhost:8000/agent/monitor/

Veți vedea:
- ✓ Device conectat (green indicator)
- ✓ Rtlog entries în timp real
- ✓ Event log entries din device

### 6.4 Test Command Control

```powershell
python manage.py shell

from agent.models import CommandLog, Device
dev = Device.objects.get(ip_address='192.168.1.232')

# Crează command pentru deschidere ușă
cmd = CommandLog.objects.create(
    device_id=dev.id,
    command="DOOR_OPEN:1",  # Deschide ușa 1
    status="queued"
)

# CommCenter va procesa în următorul ciclu
# Verificați în /agent/monitor/ ca status devine 'completed'
```

## 7. Troubleshooting

### 7.1 "Connection refused"

```
Cauză: Device nu acceptă pe port 4370
Soluție: 
1. Verificați IP-ul: ping 192.168.1.232
2. Schimbați portul: Test ambele 443 si 4370
3. Reporniti device-ul
```

### 7.2 "Socket timeout"

```
Cauză: Device nu răspunde în timp util
Soluție:
1. Creșteți timeout în driver: self.timeout = 10.0
2. Verificați firewall
3. Verificați că SDK port-ul nu e blocat
```

### 7.3 "Authentication failed"

```
Cauза: Parola SDK incorectă
Soluție:
1. Resetați parola pe device (admin panel)
2. Actualizați în Django: Device.comm_password
3. Sincronizați cu admin ZKTech dacă protejat
```

## 8. Performance & Production

### 8.1 Poll Interval Optimization

```powershell
# Recomandări:
--interval 5.0   # 5 sec (minimal lag, resource-friendly)
--interval 1.0   # 1 sec (real-time, dar mai CPU)
--interval 30.0  # 30 sec (batch processing, low resource)
```

### 8.2 Logging

```python
# Monitorizare logs in production:
tail -f server.log | grep ZKTech
```

## 9. API Endpoints pentru Control Remote

După integrare, acestea vor fi disponibile:

```
POST /agent/api/door/open/          - Deschide ușă
POST /agent/api/door/close/         - Închide ușă
POST /agent/api/device/sync-time/   - Sincronizează ceas
GET  /agent/monitor/                - Dashboard live
GET  /agent/reports/events/         - Export event logs
```

## 10. Securi & Best Practices

1. ✓ **Parolă SDK**: Stocată encrypted în Device.comm_password
2. ✓ **Firewall**: Restrict outbound TCP către IP device
3. ✓ **Timeout**: Setați rezonabil (nu infonim la infinit)
4. ✓ **Logging**: Include source IP/port în audit logs
5. ✓ **Rate Limiting**: Implementați pe /agent/api/ endpoints

---

**Următor Pas**: Implementați `drivers/zk_socket_driver.py` și testați connectivity!
