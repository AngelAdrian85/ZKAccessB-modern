import socket
import threading
import requests
import asyncio
import websockets
import json
from utils import decode_rtlog_packet
from config import CONTROLLER_IP, CONTROLLER_PORT, DJANGO_ENDPOINT

connected_clients = set()

def handle_controller(conn, addr):
    print(f"Controller connected: {addr}")
    buffer = b''
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            # fiecare pachet are 64 bytes
            while len(buffer) >= 64:
                packet_bytes = buffer[:64]
                buffer = buffer[64:]
                event = decode_rtlog_packet(packet_bytes)
                if event:
                    print(event)
                    # trimite JSON la Django
                    try:
                        requests.post(DJANGO_ENDPOINT, json=event, timeout=1)
                    except Exception as e:
                        print("Eroare POST Django:", e)
                    # trimite și la WebSocket
                    asyncio.run(broadcast(event))
        except Exception as e:
            print("Eroare conexiune:", e)
            break
    conn.close()
    print(f"Controller disconnected: {addr}")

async def ws_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            await websocket.send("Server alive")
    except:
        pass
    finally:
        connected_clients.remove(websocket)

async def broadcast(event):
    if connected_clients:
        msg = json.dumps(event, default=str)
        await asyncio.wait([client.send(msg) for client in connected_clients])

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((CONTROLLER_IP, CONTROLLER_PORT))
    s.listen(5)
    print(f"Microservice TCP listening on {CONTROLLER_IP}:{CONTROLLER_PORT}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_controller, args=(conn, addr), daemon=True).start()

async def start_ws_server():
    ws_server = await websockets.serve(ws_handler, "0.0.0.0", 8765)
    print("WebSocket server listening on port 8765")
    await ws_server.wait_closed()

import os
def _log_startup_exception(e):
    log_path = os.path.join(os.path.dirname(__file__), 'startup_error.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            import traceback
            f.write(f"[STARTUP ERROR] {e}\n")
            traceback.print_exc(file=f)
    except Exception as logerr:
        pass

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(start_ws_server())
        loop.run_in_executor(None, start_server)
        loop.run_forever()
    except Exception as e:
        _log_startup_exception(e)
        raise
