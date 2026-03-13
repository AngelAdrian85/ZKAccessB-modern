import json
import time

from agent.modern_comm_center import ModernCommCenter


def test_exclusive_capture_ignores_future_heartbeat(tmp_path, monkeypatch):
    monkeypatch.setenv('USERPROFILE', str(tmp_path))
    monkeypatch.setenv('ZKACCESS_ZKEMKEEPER_EXCLUSIVE', '1')

    hb_path = tmp_path / 'zkeco_reader_heartbeat_zkemkeeper.json'
    hb_path.write_text(
        json.dumps(
            {
                'ts': time.time() + 3600,
                'status': 'connected',
                'device_id': 22,
            }
        ),
        encoding='utf-8',
    )

    center = ModernCommCenter(poll_interval=0.1)

    assert center._exclusive_device_ids() == set()