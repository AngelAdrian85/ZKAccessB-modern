# ZKTech Integration - Quick Start

## Step-by-Step Setup

### 1. Physical Device Setup (192.168.1.232)

```powershell
# Test connectivity from server
ping 192.168.1.232
Test-NetConnection -ComputerName 192.168.1.232 -Port 4370
```

**Expected**: `TcpTestSucceeded : True`

### 2. Add Firewall Rule

```powershell
New-NetFirewallRule -DisplayName "ZKTech SDK Port 4370" `
    -Direction Outbound -Action Allow -Protocol TCP `
    -RemoteAddress 192.168.1.232 -RemotePort 4370
```

### 3. Django Admin: Register Device

1. Visit http://localhost:8000/admin/agent/device/add/
2. Fill form:
   - **Name**: ZKTech Access Panel - Main
   - **IP Address**: 192.168.1.232
   - **Port**: 4370
   - **Device Type**: Access Control Panel
   - **Enabled**: ✓
   - **Auto Sync Time**: ✓

3. **Save**

### 4. Test Driver Connectivity

```powershell
cd zkeco_modern

# Test socket connectivity
python manage.py shell

from agent.models import Device
from agent.drivers import ZKTechSocketDriver

dev = Device.objects.get(ip_address='192.168.1.232')
driver = ZKTechSocketDriver(dev)

# Test connect
result = driver.connect()
print(f"Connect: {result}")

# Test rtlog
rtlog = driver.get_rtlog()
print(f"RtLog: {rtlog}")

# Disconnect
driver.disconnect()
```

**Expected Output**:
```
Connect: {'result': 1, 'hcommpro': 123, 'transport': 'socket', 'device': '192.168.1.232'}
RtLog: {'result': 5, 'data': 'line1\r\nline2\r\nline3\r\nline4\r\nline5'}
```

### 5. Start CommCenter with ZKTech Driver

**Terminal 1 - Django Server**:
```powershell
cd zkeco_modern
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - CommCenter**:
```powershell
cd zkeco_modern

# Start with ZKTech socket driver
python manage.py run_commcenter --interval 5.0 --driver zk

# Or with verbose logging
python manage.py run_commcenter --interval 2.0 --driver zk --verbosity 3
```

### 6. View Live Data

Open Dashboard: http://localhost:8000/agent/monitor/

You should see:
- ✓ Device status: **ONLINE** (green)
- ✓ Real-time entries appearing
- ✓ Event logs populated

### 7. Test Door Control

```powershell
# From Terminal 2 (while CommCenter running) open new shell

cd zkeco_modern

python manage.py shell

from agent.models import CommandLog, Device

dev = Device.objects.get(ip_address='192.168.1.232')

# Queue a door open command
cmd = CommandLog.objects.create(
    device_id=dev.id,
    command="DOOR_OPEN:1",
    status="queued"
)

print(f"Created command {cmd.id} - status will update in Monitor")
```

Visit Monitor page - status will change from `queued` → `completed`

---

## Troubleshooting

### Issue: "Connection refused" on port 4370

```
Check 1: Is device SSH port responsive?
$ ssh admin@192.168.1.232
  (if this works, device is reachable)

Check 2: Which port is SDK listening?
$ telnet 192.168.1.232 4370
$ telnet 192.168.1.232 5000  (alternate SDK port)
$ telnet 192.168.1.232 8080  (web port)

Fix Options:
a) Device may need firmware update for SDK port stability
b) Try port 5000 or 8080 instead - update Device.port in Django admin
c) Restart device: SSH → system restart
```

###Issue: Timeout on connect

```
Check firewall:
  Get-NetFirewallRule -DisplayName "*ZKTech*"

Device may have connection limits:
  Increase timeout in driver: self.timeout = 10.0
  
Also check device admin: may have max connections limit
```

### Issue: Rtlog empty / no data

```
Device may not have log entries yet. 

Trigger some activity:
1. Swipe a card at a reader
2. Press access button
3. Wait 10 sec, check again

Or test with stub driver first:
  python manage.py run_commcenter --interval 2.0 --driver stub
  (this will generate mock data for testing UI)
```

---

## Next Steps

1. ✓ Device connected and polling
2. → Set up **Access Levels** & **Doors** in Django admin
3. → Link **Employees** to cards & access levels  
4. → Configure **Time Segments** for access windows
5. → Test **Card Swipes** → Event Logs appear
6. → Deploy to production with Daphne + WebSockets

---

## Performance Notes

- **Polling Interval**: 5.0 sec is good balance (5 sec lag, low CPU)
- **Real-time**: Use 1.0 sec for live dashboard (requires server resources)
- **Batch**: Use 30.0 sec for logs review only (minimal resources)

---

## Files Modified/Created

```
zkeco_modern/
├── agent/
│   ├── drivers/                    # NEW
│   │   ├── __init__.py
│   │   └── zk_socket_driver.py     # ZKTech implementation
│   ├── modern_comm_center.py       # Updated to support --driver zk
│   └── models.py                   # Device model (no changes needed)
└── ZKTECH_QUICK_START.md           # This file
```

---

## Additional Resources

- Protocol Details: See `ZKTECH_INTEGRATION_GUIDE.md`
- API Docs: http://localhost:8000/admin/doc/
- Device Logs: `zkeco_modern/server.log`
- CommCenter Logs: `zkeco_modern/tray_agent.log`

**Questions?** Check `ZKTECH_INTEGRATION_GUIDE.md` for detailed protocol info.
