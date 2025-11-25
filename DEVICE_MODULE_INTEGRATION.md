# Device Module Integration - ZKAccessB Modern

## Overview
The Device module is the **core component** of the ZKAccessB system. It manages the integration of all access control hardware devices (ZK Teco access panels, door controllers, biometric readers, etc.) with the centralized system.

---

## CommCenter Service

### What It Does
**CommCenter** is the background communication service that maintains real-time synchronization with all connected access control devices.

#### Key Responsibilities:
1. **Device Session Lifecycle Management**
   - Maintains persistent connections to each registered device
   - Automatically reconnects on failures with retry logic
   - Tracks device health status (online/offline)

2. **Real-Time Log Polling (RTLog)**
   - Continuously polls devices for transaction logs (access events, door opens, etc.)
   - Stores events in `DeviceEventLog` table
   - Maintains timestamp synchronization

3. **Command Queue Processing**
   - Executes system commands on devices:
     - Door open/close control
     - Time synchronization
     - Personnel data push (employee records)
     - Firmware updates
     - Remote configuration changes
   - Processes commands asynchronously via pluggable driver backend

4. **Data Synchronization**
   - Syncs employee records to devices
   - Syncs access levels and time segments
   - Syncs holiday exceptions
   - Bidirectional: Device→System (events) and System→Device (config)

5. **Health & Heartbeat Tracking**
   - Monitors device availability
   - Tracks connection failures and recovery
   - Provides status for UI dashboards

6. **Event Code Translation**
   - Decodes device event codes into human-readable descriptions
   - Maps device-specific codes to standard event types (access granted, denied, alarm, etc.)

#### Architecture:
- **Process Type**: Daemon thread started by tray agent on system boot
- **Driver Backend**: Pluggable (`CommDriver` protocol supports stub, socket, SDK, or real DLL calls)
- **Database**: Uses Django ORM with `legacy_models` for Device, Employee, etc.
- **Channels**: Uses Django Channels for WebSocket push to UI (real-time updates)
- **Logging**: Comprehensive logging to `server.log` for debugging

#### Current Status:
✅ **OPERATIONAL** - CommCenter thread auto-starts with tray agent and maintains device connections.

---

## Device Module Components

### Database Models

#### 1. **Device** (Primary Model)
```python
Fields:
  - name: Display name (e.g., "FINANCIAR", "RU", "Medical Access")
  - device_type: Type (e.g., "Access Control Panel")
  - ip_address: Network IP for management
  - area_name: Physical area/location
  - enabled: Active/disabled flag
  - serial_number: Device SN for identification
  - firmware_version: Current FW version
  - created_at: Registration timestamp
```
**Purpose**: Central registry of all hardware devices in the system.

#### 2. **DeviceRealtimeLog** (RTLog)
```python
Fields:
  - device_id: FK to Device
  - sn: Device serial number (denormalized for query speed)
  - raw: Raw transaction data from device
  - created_at: Timestamp of event
```
**Purpose**: Fast queryable log of real-time transactions.

#### 3. **DeviceEventLog** (Event Log)
```python
Fields:
  - device_id: FK to Device
  - sn: Device serial number
  - timestamp_str: Event timestamp from device
  - code: Event code (e.g., "0", "1", "3" for various events)
  - raw_line: Complete raw event string
  - created_at: When received by system
```
**Purpose**: Detailed event tracking for audit trails and alarms.

#### 4. **DeviceStatus** (Live Status)
```python
Fields:
  - device: FK to Device
  - online: Is device reachable (boolean)
  - door_state: Current door state (OPEN, CLOSED, ALARM)
  - updated_at: Last heartbeat timestamp
```
**Purpose**: Real-time device state cache for rapid UI updates.

#### 5. **Door** (Access Point)
```python
Fields:
  - name: Door name (e.g., "Entry A", "Lab Door 1")
  - device: FK to Device that controls this door
  - location: Physical location description
  - normally_open: Safety mode flag
  - enabled: Active/disabled
  - is_open: Simulated current state
  - last_state_change: When state changed
```
**Purpose**: Logical representation of access-controlled doors/gates.

### Views & CRUD Operations

#### Device List (`/agent/devices/`)
- Read-only view of all registered devices
- Shows device name, serial, type, firmware

#### Device Menu (`/agent/menu/device/`)
- Quick access hub for device operations
- Links to:
  - Add/discover devices
  - Monitor real-time events
  - Backup device data
  - Sync time across devices
  - Push personnel changes

#### Device CRUD (`/agent/crud/devices/`)
- Full CRUD operations:
  - **Create**: Register new device with IP, SN, name
  - **Read**: View device details and status
  - **Update**: Edit device name, area, firmware info
  - **Delete**: Unregister device from system

#### Device Discovery (`/agent/devices/discover/`)
- Scans network subnet for responsive ZK devices
- Returns list of reachable IPs for registration

#### Device Health Check (`/agent/devices/ping/`)
- Quick network test to verify device reachability
- Useful for troubleshooting connectivity

### Integration Points

#### 1. **CommCenter → Device Module**
CommCenter continuously:
- Polls each Device for new transactions
- Updates DeviceStatus with health data
- Stores DeviceEventLog entries
- Broadcasts changes via WebSocket consumers

#### 2. **Personnel Module → Device Module**
- Employee records sync'd to devices via CommCenter
- Access levels filtered per device
- Time segments enforced at device level

#### 3. **Access Control Module → Device Module**
- Door configurations stored in Door model
- Linked to Device for hardware mapping
- Access level policies applied per door

#### 4. **Reports & Monitoring → Device Module**
- Real-time events displayed from DeviceEventLog
- Device status shown in dashboards
- Access logs traced to source device

---

## Current Implementation Status

### ✅ Completed
- Device model and migrations (9 migrations applied)
- CRUD operations (create, read, update, delete)
- Device discovery/ping utilities
- CommCenter daemon service
- DeviceStatus real-time tracking
- Event log storage and retrieval
- WebSocket consumers for live updates
- Navigation sidebar with Device section

### 📋 New in This Session
1. **Device Module Added to Navigation**
   - Sidebar now includes "Device" section
   - Links to Device menu, device list, discovery, real-time monitor
   
2. **CommCenter Documentation**
   - Explained role in system architecture
   - Clarified communication with devices
   - Defined protocol for events, commands, sync

### ⚠️ Known Limitations
- Device discovery limited to small subnet (first 10 IPs)
- No persistent connection pooling (reconnects per poll cycle)
- Driver backend currently stub (can be replaced with real DLL calls)
- No historical device configuration tracking

---

## Next Steps for Production

1. **Real Hardware Driver Integration**
   - Replace stub driver with actual ZK SDK calls
   - Implement proper socket protocol for device communication

2. **Persistent Connections**
   - Pool device connections to reduce overhead
   - Implement keep-alive heartbeats

3. **Device Grouping**
   - Add device groups for batch operations
   - Support multi-device commands (e.g., "sync time all")

4. **Advanced Monitoring**
   - Device performance metrics (response times, error rates)
   - Automatic firmware update management
   - Device capacity monitoring (transaction log size)

5. **Backup & Recovery**
   - Automatic device data backup
   - Firmware rollback capability
   - Transaction log archiving

---

## Testing Device Module

### Verify Device Display
1. Open dashboard: `http://localhost:14525/agent/dashboard/`
2. Click "Dashboard" in sidebar → Device section now visible
3. Click "Devices" → Shows device menu
4. Click "Device List" → Lists all registered devices

### Add Sample Device
1. Navigate to `http://localhost:14525/agent/crud/devices/new/`
2. Fill in:
   - Name: "TEST_DEVICE_001"
   - IP Address: 192.168.1.100
   - Serial Number: ZK123456
   - Area: "Lab"
3. Save → Device appears in list

### Monitor Events
1. Click "Real-time Monitor" in Device menu
2. CommCenter polls this device
3. Events appear in event stream as they occur

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Tray Agent                         │
│          (Windows System Tray Integration)           │
└────────────┬──────────────────────────┬──────────────┘
             │                          │
             ▼                          ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  ASGI Server     │      │  CommCenter      │◄──────┐
    │  (Daphne)        │      │  (Background)    │       │
    │  Port: 14525     │      │                  │       │
    └──────────┬───────┘      └────────┬─────────┘       │
               │                       │                  │
               │ HTTP/WebSocket        │ Polling          │
               │                       │ Commands         │
               ▼                       ▼                  │
    ┌──────────────────────────────────────────┐        │
    │        Django Application                 │        │
    │  ┌────────────────────────────────────┐  │        │
    │  │   Device Module                    │  │        │
    │  │  ├─ CRUD Views                     │  │        │
    │  │  ├─ CommCenter Consumers           │  │        │
    │  │  └─ Real-time Monitor              │  │        │
    │  └────────────────────────────────────┘  │        │
    └──────────────────┬───────────────────────┘        │
                       │                                 │
               ┌───────▼──────────┐                      │
               │   Database       │                      │
               │  ┌────────────┐  │                      │
               │  │ Device     │  │                      │
               │  │ DeviceLog  │  │◄─────────────────────┘
               │  │ Status     │  │
               │  │ Door       │  │
               │  └────────────┘  │
               └──────────────────┘
                      ▲
                      │ Network
                      │
            ┌─────────▼──────────┐
            │  ZK Devices        │
            │  (Access Panels)   │
            │  192.168.1.xxx     │
            └────────────────────┘
```

---

## File Locations

| Component | Path |
|-----------|------|
| Device Models | `zkeco_modern/agent/models.py` (lines 37-68) |
| Device Views | `zkeco_modern/agent/views.py` (device_* functions) |
| Device Templates | `zkeco_modern/agent/templates/agent/device_*.html` |
| CommCenter | `zkeco_modern/agent/modern_comm_center.py` |
| Routes | `zkeco_modern/agent/urls.py` (device routes) |
| Navigation | `zkeco_modern/agent/templates/agent/base_legacy.html` (sidebar) |
| Migrations | `zkeco_modern/agent/migrations/0002_device.py` |

---

## References

- **Legacy Device Model**: `legacy_models/models.py` (Device class)
- **New Device Model**: `zkeco_modern/agent/models.py` (Device class)
- **CommCenter Implementation**: `zkeco_modern/agent/modern_comm_center.py`
- **Tray Integration**: `zkeco_modern/agent/management/commands/tray_agent.py`

