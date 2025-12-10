from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = "Seed one Elatec and one ACP device for scanner monitoring"

    def handle(self, *args, **options):
        from agent.models import Device
        import json, pathlib
        # ACP TCP device
        acp, created_acp = Device.objects.get_or_create(
            serial_number='ACP-DEMO-001',
            defaults={
                'name': 'ACP Demo TCP',
                'device_type': 'biometric_reader',
                'comm_mode': 'tcp',
                'ip_address': '127.0.0.1',
                'port': 9001,
                'enabled': True,
                'scanner_linked': True,
                'scanner_type': 'acp',
                'area_name': 'Demo',
            }
        )
        if not created_acp:
            acp.name = acp.name or 'ACP Demo TCP'
            acp.device_type = 'biometric_reader'
            acp.comm_mode = 'tcp'
            acp.ip_address = acp.ip_address or '127.0.0.1'
            acp.port = acp.port or 9001
            acp.enabled = True
            acp.scanner_linked = True
            acp.scanner_type = 'acp'
            acp.area_name = acp.area_name or 'Demo'
            acp.save()
        
        # Elatec Serial device
        el, created_el = Device.objects.get_or_create(
            serial_number='ELATEC-DEMO-001',
            defaults={
                'name': 'Elatec Demo Serial',
                'device_type': 'biometric_reader',
                'comm_mode': 'rs485',
                'rs485_port': 'COM3',
                'rs485_baudrate': 9600,
                'enabled': True,
                'scanner_linked': True,
                'scanner_type': 'elatec',
                'area_name': 'Demo',
            }
        )
        if not created_el:
            el.name = el.name or 'Elatec Demo Serial'
            el.device_type = 'biometric_reader'
            el.comm_mode = 'rs485'
            el.rs485_port = el.rs485_port or 'COM3'
            el.rs485_baudrate = el.rs485_baudrate or 9600
            el.enabled = True
            el.scanner_linked = True
            el.scanner_type = 'elatec'
            el.area_name = el.area_name or 'Demo'
            el.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded devices: ACP id={acp.id}, Elatec id={el.id}"
        ))

        # Also configure readers and trigger tray agent start flags
        base = pathlib.Path(__file__).resolve().parents[3]  # repo root
        cfg_path = base / 'scripts' / 'card_readers.json'
        st_path = base / 'tray_status.json'
        cfg = {
            'acp': {'enabled': True, 'port': 9001, 'name': 'ACP TCP', 'mode': 'virtual'},
            'elatec': {'enabled': True, 'port': 'COM3', 'name': 'Elatec Serial', 'mode': 'virtual'}
        }
        try:
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass
        try:
            st = {}
            if st_path.exists():
                st = json.loads(st_path.read_text(encoding='utf-8'))
            st.update({'acp_enabled': True, 'elatec_enabled': True, 'cmd_start_acp': True, 'cmd_start_elatec': True})
            tmp = st_path.with_suffix('.tmp')
            tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
            if st_path.exists():
                st_path.unlink()
            tmp.replace(st_path)
        except Exception:
            pass
        self.stdout.write(self.style.WARNING("Readers configured. Ensure tray agent is running to auto-start."))
