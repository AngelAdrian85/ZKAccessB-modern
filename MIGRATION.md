## Modern CommCenter Migration Path

### 1. Objectives
Replace legacy monolithic DataCommCenter (Python2, multi-process, Redis dict queue) with a maintainable Django-managed agent providing:
 - Per-device session management
 - Real-time log (rtlog) collection
 - Periodic transaction/new log downloads
 - Command queue processing (connect/disconnect/control operations)
 - Structured logging & metrics
 - Optional Redis backends (queue + heartbeat)
 - Persisted logs/events in relational DB tables

### 2. Components Added
`agent/modern_comm_center.py` – Coordinator + sessions + persistence.
`agent/models.py` – `DeviceRealtimeLog`, `DeviceEventLog` models.
`agent/management/commands/run_commcenter.py` – Launch command.
Redis integration: queue (`RedisQueue`) and heartbeat (`RedisHeartbeat`).
Socket-capable driver adapter: `LegacyDriverAdapter` probing `com_address`/`com_port`.

### 3. Runtime Invocation
```bash
python zkeco_modern/manage.py run_commcenter --interval 1.0 --hours 0,6,12,18 --metrics
python zkeco_modern/manage.py run_commcenter --redis --redis-url redis://localhost:6379/0 --json-logs
```

### 4. Data Flow
1. Load devices via ORM.
2. Build sessions with driver adapter.
3. Poll cycle: process 1 command, poll rtlog, optionally download new logs on configured hours.
4. Persist rtlog lines -> `DeviceRealtimeLog` rows; new logs -> `DeviceEventLog` rows.
5. Update heartbeat (in-memory or Redis).
6. Emit metrics counters periodically when `--metrics` provided.

### 5. Parity Mapping (Legacy → Modern)
| Legacy Concept | Modern Equivalent |
| -------------- | ---------------- |
| `TDevComm.connect` | `DeviceSession.connect()` calling adapter |
| Realtime log thread | Inline polling in `_poll_cycle` |
| Redis dict/queue server | `RedisQueue` / `RedisHeartbeat` (optional) |
| New log hour triggers | `--hours` CLI argument / `_should_download()` |
| Event log text lines | Parsed, persisted `DeviceEventLog` |

### 6. Extensibility Points
Driver integration: replace socket attempts with SDK/DLL via `ctypes` inside `LegacyDriverAdapter` methods.
Command set: expand parser in `_process_one_command()` for control operations.
Metrics: integrate `prometheus_client` to expose `/metrics` via a lightweight HTTP server if needed.
Error handling: wrap persistence in bulk inserts for performance.

### 7. Migration Phases
Phase 1 – Observation: Run both legacy and modern (interval high) to compare outputs.
Phase 2 – Shadow Mode: Disable legacy processing of new logs; rely on modern agent; verify counts.
Phase 3 – Cutover: Stop legacy service; enable Redis for resilience; lower interval.
Phase 4 – Optimization: Add bulk insert, Prometheus exporter, real driver calls.

### 8. Operational Checks
Health: `last_cycle` timestamp in Redis hash or in-memory.
Throughput: metrics counters `rtlog_lines`, `event_logs`.
Error surfaces: JSON logs with `level=ERROR` for driver failures.

### 9. Rollback Strategy
Keep legacy service binary & config intact; stop modern agent and re-enable legacy Windows service if critical error spikes or data gaps observed.

### 10. Next Enhancements
 - Bulk persistence & batching
 - Retry/backoff strategy for socket failures
 - Command deduplication & prioritization
 - Structured validation & parsing of event log lines
 - Prometheus metrics endpoint

### 11. Security Considerations
Restrict Redis usage to authenticated instances (use `rediss://` or ACL).
Validate device input lines before persistence to avoid injecting malformed data.
Limit socket timeouts to prevent resource exhaustion.

### 12. Maintenance
Encapsulate driver specifics in adapter; keep `ModernCommCenter` free of protocol details.
Add unit tests targeting parsing & persistence helpers.

---
Document generated as part of modernization tasks; adjust as implementation evolves.
