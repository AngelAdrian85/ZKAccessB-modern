import time
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from agent.modern_comm_center import build_and_run_stub

layer = get_channel_layer()
if not layer:
    print('NO_CHANNEL_LAYER')
    raise SystemExit(1)

chan = async_to_sync(layer.new_channel)()
print('channel:', chan)
async_to_sync(layer.group_add)('monitor', chan)

# Start stub center which will broadcast device.status
center = build_and_run_stub(poll_interval=0.5, driver='stub')
print('Started stub center')

received = []
start = time.time()
# Wait up to 5 seconds for messages
while time.time() - start < 5:
    try:
        msg = async_to_sync(layer.receive)(chan)
        if msg:
            print('RECV MSG:', msg)
            received.append(msg)
    except Exception as e:
        # no message available or backend not supporting receive
        time.sleep(0.05)

# cleanup
try:
    async_to_sync(layer.group_discard)('monitor', chan)
except Exception:
    pass
center._stop.set()

print('TOTAL RECV:', len(received))
# Extract payloads
payloads = [m.get('payload') for m in received if isinstance(m, dict) and m.get('payload')]
print('PAYLOADS:', json.dumps(payloads, default=str))
