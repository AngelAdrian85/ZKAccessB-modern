from __future__ import annotations

from dataclasses import dataclass
import os

from django.conf import settings


def _setting(name: str, default):
    if name in os.environ:
        return os.environ.get(name, default)
    return getattr(settings, name, default)


def _as_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
    except Exception:
        return int(default)
    return parsed if parsed > 0 else int(default)


def _as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PushProtocolConfig:
    protocol_version: str
    timeout_sec: int
    server_name: str
    server_version: str
    encrypt: str
    trans_tables: str
    trans_times: str
    request_delay: int
    error_delay: int
    delay: int
    trans_interval: int
    trans_flag: int
    option_trans_flag: str
    realtime: int
    rtlog: int
    timezone: int
    push_options_flag: int
    push_options: str
    attlog_stamp: int
    operlog_stamp: int
    attphoto_stamp: int
    errorlog_stamp: int
    public_scheme: str
    public_host: str
    public_port: int
    reboot_after_config: bool


def _stamp_value(value: int) -> str:
    return str(int(value)) if int(value or 0) > 0 else "None"


def get_push_protocol_config() -> PushProtocolConfig:
    return PushProtocolConfig(
        protocol_version=str(_setting("ZKACCESS_PUSH_PROTOCOL_VERSION", "2.0") or "2.0").strip() or "2.0",
        timeout_sec=_as_int(_setting("ZKACCESS_PUSH_TIMEOUT_SEC", 300), 300),
        server_name=str(_setting("ZKACCESS_PUSH_SERVER_NAME", "ZKAccessB Modern") or "ZKAccessB Modern").strip() or "ZKAccessB Modern",
        server_version=str(_setting("ZKACCESS_PUSH_SERVER_VERSION", "2026.04") or "2026.04").strip() or "2026.04",
        encrypt=str(_setting("ZKACCESS_PUSH_ENCRYPT", "0") or "0").strip() or "0",
        trans_tables=str(_setting("ZKACCESS_PUSH_TRANS_TABLES", "transaction,ATTLOG") or "transaction,ATTLOG").strip(),
        trans_times=str(_setting("ZKACCESS_PUSH_TRANS_TIMES", "00:00;24:00") or "00:00;24:00").strip() or "00:00;24:00",
        request_delay=_as_int(_setting("ZKACCESS_PUSH_REQUEST_DELAY", 3), 3),
        error_delay=_as_int(_setting("ZKACCESS_PUSH_ERROR_DELAY", 15), 15),
        delay=_as_int(_setting("ZKACCESS_PUSH_DELAY", 30), 30),
        trans_interval=_as_int(_setting("ZKACCESS_PUSH_TRANS_INTERVAL", 1), 1),
        trans_flag=_as_int(_setting("ZKACCESS_PUSH_TRANS_FLAG", 1), 1),
        option_trans_flag=str(
            _setting(
                "ZKACCESS_PUSH_OPTION_TRANS_FLAG",
                "AttLog    OpLog   AttPhoto    EnrollUser  ChgUser EnrollFP    ChgFP   Userpic",
            )
            or "AttLog    OpLog   AttPhoto    EnrollUser  ChgUser EnrollFP    ChgFP   Userpic"
        ).strip()
        or "AttLog    OpLog   AttPhoto    EnrollUser  ChgUser EnrollFP    ChgFP   Userpic",
        realtime=_as_int(_setting("ZKACCESS_PUSH_REALTIME", 1), 1),
        rtlog=_as_int(_setting("ZKACCESS_PUSH_RTLOG", 1), 1),
        timezone=_as_int(_setting("ZKACCESS_PUSH_TIMEZONE", 2), 2),
        push_options_flag=_as_int(_setting("ZKACCESS_PUSH_OPTIONS_FLAG", 1), 1),
        push_options=str(
            _setting(
                "ZKACCESS_PUSH_OPTIONS",
                "UserCount,TransactionCount,FingerFunOn,FPVersion,FPCount,FaceFunOn,FaceVersion,FaceCount,FvFunOn,FvVersion,FvCount,PvFunOn,PvVersion,PvCount,BioPhotoFun,BioDataFun,PhotoFunOn,~LockFunOn,CardProtFormat,~Platform,MultiBioPhotoSupport,MultiBioDataSupport,MultiBioVersion,MaskDetectionFunOn",
            )
            or "UserCount,TransactionCount,FingerFunOn,FPVersion,FPCount,FaceFunOn,FaceVersion,FaceCount,FvFunOn,FvVersion,FvCount,PvFunOn,PvVersion,PvCount,BioPhotoFun,BioDataFun,PhotoFunOn,~LockFunOn,CardProtFormat,~Platform,MultiBioPhotoSupport,MultiBioDataSupport,MultiBioVersion,MaskDetectionFunOn"
        ).strip(),
        attlog_stamp=_as_int(_setting("ZKACCESS_PUSH_ATTLOG_STAMP", 0), 0),
        operlog_stamp=_as_int(_setting("ZKACCESS_PUSH_OPERLOG_STAMP", 0), 0),
        attphoto_stamp=_as_int(_setting("ZKACCESS_PUSH_ATTPHOTO_STAMP", 0), 0),
        errorlog_stamp=_as_int(_setting("ZKACCESS_PUSH_ERRORLOG_STAMP", 0), 0),
        public_scheme=str(_setting("ZKACCESS_PUSH_PUBLIC_SCHEME", "http") or "http").strip().lower() or "http",
        public_host=str(_setting("ZKACCESS_PUSH_PUBLIC_HOST", "") or "").strip(),
        public_port=_as_int(_setting("ZKACCESS_PUSH_PUBLIC_PORT", 0), 0),
        reboot_after_config=_as_bool(_setting("ZKACCESS_PUSH_REBOOT_AFTER_CONFIG", False), False),
    )


def build_public_listener(server_addr: str, server_port: int) -> tuple[str, int, str]:
    config = get_push_protocol_config()
    host = config.public_host or str(server_addr or "").strip()
    port = int(config.public_port or int(server_port))
    scheme = config.public_scheme or "http"
    return host, port, scheme


def build_public_web_url(server_addr: str, server_port: int) -> str:
    host, port, scheme = build_public_listener(server_addr, server_port)
    return f"{scheme}://{host}:{int(port)}"


def build_adms_option_items(server_addr: str, server_port: int) -> str:
    config = get_push_protocol_config()
    host, port, _scheme = build_public_listener(server_addr, server_port)
    web_url = build_public_web_url(server_addr, server_port)
    items = [
        f"ServerAddr={host}",
        f"ServerPort={int(port)}",
        "CLOUDSERVICEFLAG=1",
        "PushFunOn=1",
        f"ADMSServerIP={host}",
        f"WebServerIP={host}",
        f"WebServerPort={int(port)}",
        f"WebServerURL={web_url}",
        f"TransFlag={int(config.trans_flag)}",
        f"Realtime={int(config.realtime)}",
        f"RTLog={int(config.rtlog)}",
        f"Delay={int(config.delay)}",
        f"TransTimes={config.trans_times}",
        f"TransInterval={int(config.trans_interval)}",
        f"TimeZone={int(config.timezone)}",
        f"Encrypt={config.encrypt}",
        f"PushProtVer={config.protocol_version}",
        f"PushOptionsFlag={int(config.push_options_flag)}",
        f"TimeoutSec={int(config.timeout_sec)}",
        f"RequestDelay={int(config.request_delay)}",
        f"ErrorDelay={int(config.error_delay)}",
    ]
    if config.push_options:
        items.append(f"PushOptions={config.push_options}")
    if config.trans_tables:
        items.append(f"TransTables={config.trans_tables}")
    return ",".join(items)


def build_registry_response(*, session_id: str, registry_code: str) -> str:
    config = get_push_protocol_config()
    lines = [
        "registry=ok",
        f"RegistryCode={registry_code}",
        f"ServerName={config.server_name}",
        f"ServerVer={config.server_version}",
        f"ServerVersion={config.server_version}",
        f"PushProtVer={config.protocol_version}",
        f"SessionID={session_id}",
        f"TimeoutSec={int(config.timeout_sec)}",
        f"Delay={int(config.delay)}",
        f"RequestDelay={int(config.request_delay)}",
        f"ErrorDelay={int(config.error_delay)}",
        f"TransTimes={config.trans_times}",
        f"TransInterval={int(config.trans_interval)}",
        f"Realtime={int(config.realtime)}",
        f"Encrypt={config.encrypt}",
    ]
    if config.trans_tables:
        lines.append(f"TransTables={config.trans_tables}")
    return "\n".join(lines).rstrip("\n") + "\n"


def build_option_response(*, sn: str, session_id: str, registry_code: str) -> str:
    config = get_push_protocol_config()
    serial = str(sn or "").strip()
    header = f"GET OPTION FROM:{serial}" if serial else "GET OPTION FROM"
    lines = [
        header,
        f"ATTLOGStamp={_stamp_value(config.attlog_stamp)}",
        f"OPERLOGStamp={_stamp_value(config.operlog_stamp)}",
        f"ATTPHOTOStamp={_stamp_value(config.attphoto_stamp)}",
        f"ERRORLOGStamp={_stamp_value(config.errorlog_stamp)}",
        f"ErrorDelay={int(config.error_delay)}",
        f"Delay={int(config.delay)}",
        f"TransTimes={config.trans_times}",
        f"TransInterval={int(config.trans_interval)}",
        f"TransFlag={config.option_trans_flag}",
        f"TimeZone={int(config.timezone)}",
        f"Realtime={int(config.realtime)}",
        f"Encrypt={config.encrypt}",
        f"ServerName={config.server_name}",
        f"ServerVer={config.server_version}",
        f"ServerVersion={config.server_version}",
        f"PushProtVer={config.protocol_version}",
        f"PushOptionsFlag={int(config.push_options_flag)}",
        f"SessionID={session_id}",
        f"RegistryCode={registry_code}",
        f"RTLog={int(config.rtlog)}",
        f"TimeoutSec={int(config.timeout_sec)}",
        f"RequestDelay={int(config.request_delay)}",
    ]
    if config.push_options:
        lines.append(f"PushOptions={config.push_options}")
    if config.trans_tables:
        lines.append(f"TransTables={config.trans_tables}")
    return "\n".join(lines).rstrip("\n") + "\n"


def push_https_enabled() -> bool:
    config = get_push_protocol_config()
    return _as_bool(_setting("ZKACCESS_PUSH_HTTPS_ENABLED", False), False) or config.public_scheme == "https"


def reboot_after_config_enabled() -> bool:
    return bool(get_push_protocol_config().reboot_after_config)