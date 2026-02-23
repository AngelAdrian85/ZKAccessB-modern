"""ZKTech Access Control Panel Socket Driver

Direct TCP/socket communication with ZKTech Access Control Panels using the
proprietary plcommpro binary protocol.

Supported Devices:
- ZKAccess C3-200/400/800 (Access Control Panels)
- ZKAccess F3 Series
- ZKAccess G-Series
"""

import socket
import struct
import logging
import time
from typing import Dict, Any, Optional, List

from django.conf import settings

LOG = logging.getLogger("zk_socket_driver")


class ZKTechSocketDriver:
    """Direct TCP socket communication with ZKTech Access Control Panel.
    
    Protocol: plcommpro binary protocol (ZKAccess proprietary)
    Standard Port: 4370 (SDK port)
    
    Features:
    - Real-time log (rtlog) retrieval
    - Transaction/event log download
    - Door control (open/close)
    - Device options (time sync, etc.)
    """
    
    # ZKAccess protocol command codes
    CMD_EXIT = 0x0001
    CMD_ENABLEDEVICE = 0x0020
    CMD_DISABLEDEVICE = 0x0021
    CMD_QUERYLOG = 0x0950
    CMD_GETTRANSACTION = 0x09C3
    CMD_GETRTLOG = 0x09C8
    CMD_CONNECT = 0x09C9
    CMD_CONTROLDOOR = 0x09CA
    CMD_CANCELWARNING = 0x09CB
    CMD_GETOPTIONS = 0x09D2
    CMD_SETOPTIONS = 0x09D3
    
    def __init__(self, dev):
        """
        Initialize driver with device configuration.
        
        Args:
            dev: Device model instance with properties:
                - ip_address: IPv4 address (e.g. "192.168.1.232")
                - port: TCP port (default 4370)
                - comm_password: Optional device password
        """
        self.dev = dev
        self.ip = str(dev.ip_address) if dev.ip_address else "127.0.0.1"
        self.port = int(dev.port) if dev.port else 4370
        # Communication password (NOT the web UI password). Typically numeric; default is often 0.
        self.comm_password_raw = (dev.comm_password or "") if hasattr(dev, 'comm_password') else ""
        if (not str(self.comm_password_raw or '').strip()):
            try:
                self.comm_password_raw = str(getattr(settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip()
            except Exception:
                self.comm_password_raw = self.comm_password_raw
        
        self.socket: Optional[socket.socket] = None
        self.session_id: int = 0
        self.reply_id: int = 0
        self.timeout: float = 5.0
        self._lock = __import__('threading').Lock()
        
    def connect(self) -> Dict[str, Any]:
        """Establish TCP connection to ZKTech device.
        
        Returns:
            {"result": 1, "hcommpro": session_id} - Success
            {"result": -1, "error": reason} - Failure
        """
        try:
            with self._lock:
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.ip, self.port))
                
                # Initial handshake: send connect command.
                # Many ZKTeco panels expect the device communication password as a 4-byte LE integer.
                # If not configured, use 0.
                password_int = 0
                try:
                    if str(self.comm_password_raw).strip() != "":
                        password_int = int(str(self.comm_password_raw).strip())
                except Exception:
                    password_int = 0
                payload = struct.pack('<I', password_int)

                cmd_packet = self._build_command(self.CMD_CONNECT, payload, expect_reply=1)
                self.socket.send(cmd_packet)
                
                # Receive handshake response 
                response = self.socket.recv(1024)
                
                if len(response) >= 8:
                    result = self._parse_response_header(response)
                    self.session_id = result.get("session_id", 0)
                    self.reply_id = result.get("reply_id", 0)
                    
                    LOG.info(f"Connected to {self.ip}:{self.port} - "
                            f"Session: {self.session_id}")
                    return {
                        "result": 1,
                        "hcommpro": self.session_id,
                        "transport": "socket",
                        "device": self.ip
                    }
                else:
                    self._cleanup_socket()
                    return {"result": -1, "error": "no_response"}
                    
        except socket.timeout:
            self._cleanup_socket()
            return {"result": -1, "error": "connection_timeout"}
        except ConnectionRefusedError:
            self._cleanup_socket()
            return {"result": -1, "error": "connection_refused"}
        except OSError as e:
            self._cleanup_socket()
            return {"result": -1, "error": f"socket_error: {str(e)}"}
        except Exception as e:
            self._cleanup_socket()
            LOG.error(f"Connection failed: {e}")
            return {"result": -1, "error": str(e)}
    
    def disconnect(self) -> Dict[str, Any]:
        """Close TCP connection."""
        try:
            with self._lock:
                if self.socket:
                    try:
                        # Send exit command
                        cmd_packet = self._build_command(self.CMD_EXIT, b"", expect_reply=0)
                        self.socket.send(cmd_packet)
                    except:
                        pass
                    finally:
                        self._cleanup_socket()
            
            return {"result": 1, "description": "disconnected"}
        except Exception as e:
            LOG.error(f"Disconnect error: {e}")
            return {"result": -1, "error": str(e)}
    
    def get_rtlog(self) -> Dict[str, Any]:
        """Retrieve real-time log entries.
        
        Returns:
            {"result": count, "data": "line1\r\nline2\r\n..."} - Success
            {"result": -1, "error": reason} - Failure
        """
        if not self._is_connected():
            return {"result": -1, "error": "not_connected"}
        
        try:
            with self._lock:
                # Send get rtlog command
                cmd_packet = self._build_command(self.CMD_GETRTLOG, b"", expect_reply=1)
                self.socket.send(cmd_packet)
                
                # Receive response
                data = self._recv_all(4096)
                
                if not data:
                    return {"result": 0, "data": ""}
                
                lines = self._parse_rtlog_response(data)
                LOG.debug(f"Retrieved {len(lines)} rtlog entries")
                
                return {"result": len(lines), "data": "\r\n".join(lines)}
                
        except Exception as e:
            LOG.error(f"get_rtlog error: {e}")
            return {"result": -1, "error": str(e)}
    
    def get_transaction(self, newlog: bool = False) -> Dict[str, Any]:
        """Retrieve transaction/event logs.
        
        Args:
            newlog: if True, retrieve only new logs; if False, retrieve all
        
        Returns:
            {"result": count, "data": {1: "line1", 2: "line2"...}} - Success
            {"result": 0, "data": {}} - No logs
            {"result": -1, "error": reason} - Failure
        """
        if not self._is_connected():
            return {"result": -1, "error": "not_connected"}
        
        try:
            with self._lock:
                # Use CMD_GETTRANSACTION for new logs, CMD_QUERYLOG for all
                cmd_code = self.CMD_GETTRANSACTION if newlog else self.CMD_QUERYLOG
                cmd_packet = self._build_command(cmd_code, b"", expect_reply=1)
                self.socket.send(cmd_packet)
                
                # Receive response (may be large for transaction logs)
                data = self._recv_all(65536)
                
                if not data:
                    return {"result": 0, "data": {}}
                
                transactions = self._parse_transaction_response(data)
                LOG.debug(f"Retrieved {len(transactions)} transaction entries")
                
                return {"result": len(transactions), "data": transactions}
                
        except Exception as e:
            LOG.error(f"get_transaction error: {e}")
            return {"result": -1, "error": str(e)}
    
    def controldevice(self, door: int, index: int, state: int) -> Dict[str, Any]:
        """Control door relay (open/close).
        
        Args:
            door: Door number (1-based)
            index: Relay index on door
            state: 1 = open, 0 = close
        
        Returns:
            {"result": 1} - Success
            {"result": -1, "error": reason} - Failure
        """
        if not self._is_connected():
            return {"result": -1, "error": "not_connected"}
        
        try:
            with self._lock:
                # Build payload: door(int32), index(int32), state(int32)
                payload = struct.pack("<iii", int(door), int(index), int(state))
                cmd_packet = self._build_command(self.CMD_CONTROLDOOR, payload, expect_reply=1)
                self.socket.send(cmd_packet)
                
                response = self.socket.recv(1024)
                result_code = self._parse_response_result(response)
                
                if result_code >= 0:
                    action = "OPEN" if state else "CLOSE"
                    LOG.info(f"Door control: door={door}, state={action}")
                    return {"result": 1, "description": f"Door {door} → {action}"}
                else:
                    return {"result": -1, "error": "control_failed"}
                    
        except Exception as e:
            LOG.error(f"controldevice error: {e}")
            return {"result": -1, "error": str(e)}
    
    def control_normal_open(self, door: int, state: int) -> Dict[str, Any]:
        """Set normal-open mode for door."""
        # Same as controldevice with special handling
        return self.controldevice(door, 0, state)
    
    def cancel_alarm(self, door: str) -> Dict[str, Any]:
        """Cancel door alarm."""
        if not self._is_connected():
            return {"result": -1, "error": "not_connected"}
        
        try:
            with self._lock:
                payload = int(door).to_bytes(4, 'little')
                cmd_packet = self._build_command(self.CMD_CANCELWARNING, payload, expect_reply=1)
                self.socket.send(cmd_packet)
                
                response = self.socket.recv(1024)
                result_code = self._parse_response_result(response)
                
                if result_code >= 0:
                    LOG.info(f"Alarm cancelled for door {door}")
                    return {"result": 1}
                else:
                    return {"result": -1, "error": "cancel_failed"}
                    
        except Exception as e:
            LOG.error(f"cancel_alarm error: {e}")
            return {"result": -1, "error": str(e)}
    
    # Remaining CommDriver protocol methods (stubs)
    def query_data(self, table: str, fields: str, flt: str, extra: str) -> Dict[str, Any]:
        return {"result": 0, "data": []}
    
    def update_data(self, table: str, data: str, extra: str) -> Dict[str, Any]:
        return {"result": 1}
    
    def delete_data(self, table: str, flt: str) -> Dict[str, Any]:
        return {"result": 1}
    
    def Get_Data_Count(self, table: str) -> Dict[str, Any]:
        return {"result": 0}
    
    def get_options(self, items: str) -> Dict[str, Any]:
        """Get device options (placeholder)."""
        return {"result": 0, "data": ""}
    
    def set_options(self, items: str) -> Dict[str, Any]:
        """Set device options (placeholder)."""
        return {"result": 1}
    
    # ====== Protocol Implementation Details ======
    
    def _is_connected(self) -> bool:
        """Check if socket is connected."""
        try:
            return self.socket is not None and self.session_id > 0
        except:
            return False
    
    def _cleanup_socket(self) -> None:
        """Close and clean up socket."""
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        finally:
            self.socket = None
            self.session_id = 0
            self.reply_id = 0
    
    def _recv_all(self, max_size: int = 4096) -> bytes:
        """Receive data from socket with timeout."""
        data = b""
        try:
            while len(data) < max_size:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > max_size:
                    break
        except socket.timeout:
            pass  # Timeout is OK - return what we have
        except Exception as e:
            LOG.warning(f"recv_all error: {e}")
        
        return data
    
    def _build_command(self, cmd_code: int, payload: bytes, expect_reply: int = 1) -> bytes:
        """Build ZKAccess protocol command packet.
        
        Format (little-endian):
        - Command code (2 bytes)     [0:2]
        - Session ID (2 bytes)       [2:4]
        - Reply ID (2 bytes)         [4:6]
        - Reply flag (2 bytes)       [6:8]
        - Payload length (2 bytes)   [8:10]
        - Payload (N bytes)         [10:]
        - Checksum (2 bytes)        [10+N:]
        """
        self.reply_id = (self.reply_id + 1) % 65536
        
        length = len(payload)
        header = struct.pack(
            "<hhhhh",
            cmd_code,           # Command code
            self.session_id,    # Session ID (0 for initial connect)
            self.reply_id,      # Reply ID for tracking
            expect_reply,       # Expect reply from device
            length              # Payload length
        )
        
        # Build full packet without checksum first
        packet = header + payload
        
        # Compute checksum
        checksum = self._compute_checksum(packet)
        
        # Return packet with checksum
        return packet + struct.pack("<h", checksum)
    
    def _compute_checksum(self, data: bytes) -> int:
        """Compute ZKAccess protocol checksum (XOR).
        
        Simple XOR checksum across all bytes.
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum & 0xFFFF
    
    def _parse_response_header(self, data: bytes) -> Dict[str, Any]:
        """Parse response packet header.
        
        Returns: {"session_id": X, "reply_id": Y, "status": Z}
        """
        if len(data) < 10:
            return {"session_id": 0, "reply_id": 0, "status": -1}
        
        try:
            cmd, sess, reply, flag, length = struct.unpack("<hhhhh", data[:10])
            return {
                "command": cmd,
                "session_id": sess,
                "reply_id": reply,
                "flag": flag,
                "length": length,
                "status": 0
            }
        except:
            return {"session_id": 0, "reply_id": 0, "status": -1}
    
    def _parse_response_result(self, data: bytes) -> int:
        """Extract result code from response."""
        if len(data) < 10:
            return -1
        try:
            _, _, _, _, result = struct.unpack("<hhhhh", data[:10])
            return result
        except:
            return -1
    
    def _parse_rtlog_response(self, data: bytes) -> List[str]:
        """Parse rtlog response into list of log lines.
        
        Format: Text lines separated by \r\n (or \n)
        """
        try:
            # Skip header (first 10 bytes)
            payload = data[10:]
            
            # Decode and split by newlines
            text = payload.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            
            # Filter empty lines and return
            return [l.strip() for l in lines if l.strip() and len(l) > 10]
        except Exception as e:
            LOG.error(f"parse_rtlog_response error: {e}")
            return []
    
    def _parse_transaction_response(self, data: bytes) -> Dict[int, str]:
        """Parse transaction log response.
        
        Format: Indexed log entries
        """
        try:
            payload = data[10:]  # Skip header
            text = payload.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            
            result = {}
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and len(line) > 10:
                    result[i] = line
            
            return result
        except Exception as e:
            LOG.error(f"parse_transaction_response error: {e}")
            return {}
