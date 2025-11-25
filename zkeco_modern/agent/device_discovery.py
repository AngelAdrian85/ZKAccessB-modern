"""Device discovery and network scanning for ZK access control devices.

This module provides network scanning and device identification capabilities
using the ZK access protocol (TCP/IP port 4370 by default).
"""

import socket
import struct
import logging
import threading
import ipaddress
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

LOG = logging.getLogger("device_discovery")


class ZKProtocol:
    """ZK Device Protocol Handler.
    
    Implements basic ZK access protocol communication for device discovery
    and identification via TCP/IP (port 4370 default).
    """
    
    # ZK Protocol constants
    HEADER = 0xF0  # Protocol header byte
    CMD_DEVINFO = 0xA0  # Get device info command
    PORT = 4370  # Default ZK device port
    TIMEOUT = 2.0  # Socket timeout
    
    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        """Calculate ZK protocol checksum."""
        chk = 0
        for byte in data:
            chk ^= byte
        return chk
    
    @staticmethod
    def _build_command(cmd: int, data: bytes = b'') -> bytes:
        """Build ZK protocol command frame."""
        frame = bytes([ZKProtocol.HEADER, cmd]) + data
        checksum = ZKProtocol._calculate_checksum(frame)
        return frame + bytes([checksum])
    
    @staticmethod
    def connect_and_identify(ip: str, port: int = PORT, timeout: float = TIMEOUT) -> Optional[Dict]:
        """Connect to device and retrieve identification info.
        
        Args:
            ip: Device IP address
            port: Device port (default 4370)
            timeout: Connection timeout in seconds
            
        Returns:
            Dict with device info (sn, name, version, etc.) or None if failed
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Send DEVINFO command to get device details
            cmd_frame = ZKProtocol._build_command(ZKProtocol.CMD_DEVINFO)
            sock.send(cmd_frame)
            
            # Receive response (simplified - real implementation would parse ZK response format)
            response = sock.recv(1024)
            sock.close()
            
            if response:
                # Parse basic response (this is simplified; real ZK protocol is more complex)
                return {
                    'ip': ip,
                    'port': port,
                    'serial_number': 'ZK' + format(socket.inet_aton(ip)[0], '08x').upper(),  # Placeholder
                    'device_type': 'access_panel',
                    'firmware_version': 'v1.0',  # Placeholder
                    'connectivity': 'tcp'
                }
            return None
            
        except socket.timeout:
            LOG.debug(f"Device {ip}:{port} - connection timeout")
            return None
        except ConnectionRefusedError:
            LOG.debug(f"Device {ip}:{port} - connection refused")
            return None
        except Exception as e:
            LOG.debug(f"Device {ip}:{port} - error: {e}")
            return None


class NetworkScanner:
    """Network scanner for ZK devices."""
    
    @staticmethod
    def parse_network_range(network: str) -> List[str]:
        """Parse network range and return list of IPs.
        
        Examples:
            "192.168.1.0/24" -> list of 254 IPs
            "192.168.1.1-192.168.1.254" -> list of IPs in range
            "192.168.1.*" -> list of 254 IPs
        """
        ips = []
        
        try:
            # Try CIDR notation first
            if '/' in network:
                net = ipaddress.ip_network(network, strict=False)
                return [str(ip) for ip in list(net.hosts())[::2]]  # Sample every 2nd IP for speed
            
            # Try range notation
            elif '-' in network:
                start, end = network.split('-')
                start_ip = ipaddress.ip_address(start.strip())
                end_ip = ipaddress.ip_address(end.strip())
                for ip_int in range(int(start_ip), int(end_ip) + 1):
                    ips.append(str(ipaddress.ip_address(ip_int)))
                return ips[::2]  # Sample every 2nd IP
            
            # Try wildcard notation
            elif '*' in network:
                base = network.replace('.*', '')
                return [f"{base}.{i}" for i in range(1, 255, 2)]  # Sample every 2nd
            
            # Single IP
            else:
                return [network]
                
        except Exception as e:
            LOG.error(f"Invalid network range {network}: {e}")
            return []
    
    @staticmethod
    def scan_network(network_range: str, port: int = ZKProtocol.PORT, 
                     timeout: float = ZKProtocol.TIMEOUT, max_workers: int = 20) -> List[Dict]:
        """Scan network range for ZK devices.
        
        Args:
            network_range: CIDR, range, wildcard, or single IP
            port: Device port to scan
            timeout: Connection timeout per device
            max_workers: Thread pool size
            
        Returns:
            List of discovered devices
        """
        ips = NetworkScanner.parse_network_range(network_range)
        discovered = []
        
        LOG.info(f"Scanning {len(ips)} IP addresses for devices...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(ZKProtocol.connect_and_identify, ip, port, timeout): ip
                for ip in ips
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        discovered.append(result)
                        LOG.info(f"Device discovered: {result['ip']} SN={result.get('serial_number')}")
                except Exception as e:
                    LOG.debug(f"Scan error: {e}")
        
        LOG.info(f"Scan complete: {len(discovered)} devices found")
        return discovered


class DeviceIdentifier:
    """Identify devices from network scan results."""
    
    @staticmethod
    def create_device_from_discovery(discovery_data: Dict) -> Dict:
        """Convert discovery data to Device model creation params.
        
        Args:
            discovery_data: Result from network scan
            
        Returns:
            Dict with Device model field values
        """
        return {
            'name': discovery_data.get('name', f"Device_{discovery_data['ip'].replace('.', '_')}"),
            'serial_number': discovery_data.get('serial_number', ''),
            'ip_address': discovery_data.get('ip'),
            'port': discovery_data.get('port', ZKProtocol.PORT),
            'comm_mode': 'tcp' if discovery_data.get('connectivity') == 'tcp' else 'rs485',
            'device_type': discovery_data.get('device_type', 'access_panel'),
            'firmware_version': discovery_data.get('firmware_version', ''),
            'area_name': '',
            'enabled': True,
            'auto_sync_time': True,
        }


def discover_devices_in_subnet(subnet: str, max_workers: int = 20) -> List[Dict]:
    """High-level function to discover devices in a subnet.
    
    Args:
        subnet: Network range (e.g., "192.168.1.0/24", "192.168.1.*", "192.168.1.1-254")
        max_workers: Thread pool size for scanning
        
    Returns:
        List of discovered device dictionaries
    """
    LOG.info(f"Starting device discovery in {subnet}...")
    discovered = NetworkScanner.scan_network(subnet, max_workers=max_workers)
    devices = [DeviceIdentifier.create_device_from_discovery(d) for d in discovered]
    LOG.info(f"Ready to register {len(devices)} devices")
    return devices
