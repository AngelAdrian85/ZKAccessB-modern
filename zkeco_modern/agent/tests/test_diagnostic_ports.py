from agent.diagnostic_ports import password_candidates, resolve_diagnostic_route


class _DeviceStub:
    def __init__(self):
        self.port = 4370
        self.name = "CTRL C3-100Pro"
        self.hardware_version = "ZMM200_C3Pro"
        self.firmware_version = "AC Ver 4.7.8.3033 Aug 14 2023"
        self.comm_password = "2468"


def test_resolve_diagnostic_route_prefers_effective_port_for_c3pro():
    route_ctx = resolve_diagnostic_route(device=_DeviceStub(), configured_port=4370, strict_port=False)

    assert route_ctx["effective_port"] == 14370
    assert route_ctx["candidate_ports"][:2] == [14370, 4370]


def test_resolve_diagnostic_route_can_lock_to_strict_requested_port():
    route_ctx = resolve_diagnostic_route(device=_DeviceStub(), configured_port=4370, strict_port=True)

    assert route_ctx["candidate_ports"] == [4370]


def test_password_candidates_keep_supplied_then_device_then_common_fallbacks(settings):
    settings.ZKACCESS_DEFAULT_COMM_PASSWORD = "1357"

    values = password_candidates(supplied_password="9999", device=_DeviceStub())

    assert values[:5] == ["9999", "2468", "1357", "", "0"]
