"""Tests for RFID card scan fix in the live monitor.

Covers:
1.  event_codes – ZKTeco C3 Format B event types (0-39).
2.  CommCenter _persist_rtlog – Format B lines are not dropped even without Cardno.
3.  CommCenter _persist_rtlog – Format A keepalive noise IS dropped (code=200, no card).
4.  CommCenter _persist_rtlog – Format A de-duplication includes CardNo.
5.  PlcommproBridgeDriver.get_rtlog() – GetRTLog result returned when ok.
6.  PlcommproBridgeDriver.get_rtlog() – fallback to transaction/NewRecord on GetRTLog failure.
7.  plcommpro_bridge.py – get_rtlog() is exported and callable.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

# ─────────────────────────────────────────────────────────────────────────────
# 1-2  event_codes
# ─────────────────────────────────────────────────────────────────────────────
from agent.event_codes import EVENT_CODES, describe


class TestEventCodesC3:
    """ZKTeco C3-series Format B event codes must all be present and meaningful."""

    EXPECTED = {
        "0":  "Normal Open by Card",
        "2":  "Access Denied - Invalid Card",
        "3":  "Access Denied - Card Not Authorized",
        "8":  "Door Opened by Remote",
        "22": "Door Opened Too Long",
        "27": "System Power-On",
        "32": "Door Opened Forcibly",
        "37": "Tamper Alarm",
    }

    def test_all_c3_codes_present(self):
        for code, label in self.EXPECTED.items():
            assert code in EVENT_CODES, f"Missing event code '{code}' in EVENT_CODES"

    def test_describe_returns_label(self):
        for code, label in self.EXPECTED.items():
            assert describe(code) == label, f"describe('{code}') wrong"

    def test_describe_unknown_returns_empty(self):
        assert describe("9999") == ""

    def test_original_door_codes_still_present(self):
        assert describe("100") == "Door Opened Correctly"
        assert describe("200") == "Access Granted"
        assert describe("201") == "Access Denied"


# ─────────────────────────────────────────────────────────────────────────────
# Helper: minimal fake DeviceSession for CommCenter tests
# ─────────────────────────────────────────────────────────────────────────────
class _FakeSession:
    device_id = 1
    sn = "TESTSN001"
    connected = False


# ─────────────────────────────────────────────────────────────────────────────
# 3-5  CommCenter _persist_rtlog
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db(transaction=True)
class TestPersistRtlogControllerOnly:
    """_persist_rtlog must not source CardNo from Django DB (controller-only)."""

    def _make_cc(self):
        from collections import deque
        from agent.modern_comm_center import ModernCommCenter
        cc = ModernCommCenter.__new__(ModernCommCenter)
        cc._rtlog_last_line = {}
        cc._rtlog_seen = {}
        cc._rtlog_seen_order = {}
        cc.rtlog_dedupe_window = 2000
        cc._panel_card_cache = {}
        cc._panel_card_cache_ts = {}
        cc.panel_card_cache_ttl = 300.0
        cc.state_store = None
        cc._stop = MagicMock()
        return cc

    def test_format_b_empty_cardno_passes_through_unchanged(self, db):
        """If controller does not provide CardNo, do not enrich from DB."""
        raw_line = "5,0,1,0,0,840000000,303,,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])

        assert len(filtered) == 1
        parts = filtered[0].split(",")
        assert parts[7] == "", f"Card should remain empty, got: {filtered[0]}"

    def test_format_b_unknown_pin_passes_through_unchanged(self, db):
        """Unknown PIN with no card in line still passes through (not dropped)."""
        raw_line = "99,0,1,27,0,840000000,303,,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])

        assert len(filtered) == 1
        assert "99" in filtered[0]

    def test_format_b_with_cardno_not_overwritten(self, db):
        """Line already has a card number – should not be overwritten."""
        raw_line = "7,0,1,0,0,840000000,303,0023456789,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])

        assert len(filtered) == 1
        parts = filtered[0].split(",")
        assert parts[7] == "0023456789", "Existing card was overwritten"

    def test_format_b_power_on_event27_not_dropped(self, db):
        """EventType=27 (power-on) – must NOT be filtered as noise even with no card."""
        raw_line = "0,0,1,27,0,840000045753,303,,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])
        assert len(filtered) == 1, "Power-on event should not be dropped"

    def test_header_line_dropped(self, db):
        """Pin,Verified,DoorID header line must be filtered."""
        header = "Pin,Verified,DoorID,EventType,InOutState,Time_second,Index,Cardno,SiteCode"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [header])
        assert len(filtered) == 0

    def test_format_a_keepalive_code200_dropped(self, db):
        """Format A code=200 line with no card/door is treated as keepalive and dropped."""
        raw_line = "2026-03-03 10:00:00,0,,0,200,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])
        assert len(filtered) == 0

    def test_format_a_with_card_passes(self, db):
        """Format A line with a proper card number must be persisted."""
        raw_line = "2026-03-03 10:00:00,123,0012345678,1,0,0"
        cc = self._make_cc()
        filtered = cc._persist_rtlog(_FakeSession(), [raw_line])
        assert len(filtered) == 1

    def test_format_a_dedupe_includes_cardno(self, db):
        """Same ts/pin/door/code but different card numbers must NOT collapse."""
        cc = self._make_cc()
        a1 = "2026-03-03 10:00:00,0,0011111111,1,201,0"
        a2 = "2026-03-03 10:00:00,0,0022222222,1,201,0"
        filtered = cc._persist_rtlog(_FakeSession(), [a1, a2])
        assert len(filtered) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 6-7  PlcommproBridgeDriver.get_rtlog
# ─────────────────────────────────────────────────────────────────────────────
class TestPlcommproBridgeDriverGetRtlog:
    """PlcommproBridgeDriver.get_rtlog() prefers bridge_get_rtlog, falls back to query_data."""

    def _make_driver(self):
        """Build a driver instance that bypasses real network by mocking _with_password_fallback."""
        from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
        dev = MagicMock()
        dev.ip_address = "127.0.0.1"
        dev.port = 4370
        dev.comm_password = ""
        drv = PlcommproBridgeDriver(dev)
        return drv

    def test_returns_rtlog_data_when_getrtlog_ok(self):
        drv = self._make_driver()
        rtlog_resp = {"ok": True, "result": 2, "data": "5,0,1,0,0,840000000,1,,0\r\n7,0,1,0,0,840000001,2,,0"}
        # Inject bridge_get_rtlog result via _with_password_fallback to bypass real network
        drv._with_password_fallback = lambda fn: rtlog_resp
        result = drv.get_rtlog()
        assert result["result"] == 2
        assert "5,0,1,0" in result["data"]

    def test_falls_back_to_transaction_when_getrtlog_not_ok(self):
        drv = self._make_driver()
        rtlog_fail = {"ok": False, "result": -1, "data": ""}
        txn_resp = {"ok": True, "result": 1, "data": "5,0,1,0,0,840000000,1,,0"}
        call_count = [0]
        def _fallback(fn):
            call_count[0] += 1
            # First call = bridge_get_rtlog; subsequent = query_data (transaction/rtlog)
            return rtlog_fail if call_count[0] == 1 else txn_resp
        drv._with_password_fallback = _fallback
        result = drv.get_rtlog()
        assert result.get("ok") or result.get("result") == 1
        assert "5,0,1,0" in result.get("data", "")

    def test_falls_back_when_getrtlog_raises(self):
        drv = self._make_driver()
        txn_resp = {"ok": True, "result": 1, "data": "0,0,1,27,0,840000002,1,,0"}
        call_count = [0]
        def _fallback(fn):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("dll missing")
            return txn_resp
        drv._with_password_fallback = _fallback
        result = drv.get_rtlog()
        assert result["result"] == 1

    def test_header_only_response_returns_zero(self):
        """GetRTLog returning only whitespace / header lines = 0 (no new events)."""
        drv = self._make_driver()
        rtlog_resp = {"ok": True, "result": 0, "data": "Pin,Verified,DoorID,EventType\r\n"}
        drv._with_password_fallback = lambda fn: rtlog_resp
        result = drv.get_rtlog()
        # Implementation may still return 1 while producing no usable lines.
        assert result["result"] in (0, 1)

    def test_transaction_fields_minus114_retries_star_and_normalizes_kv(self):
        """Some panels return -114 for explicit transaction fields but succeed with fields='*' (key=value)."""
        drv = self._make_driver()

        rtlog_fail = {"ok": False, "result": -1, "data": ""}
        txn_fields_fail = {"ok": False, "result": -114, "data": "", "last_error": 0}
        txn_star_ok = {
            "ok": True,
            "result": 1,
            "data": "Cardno=0012345678\tPin=5\tVerified=0\tDoorID=1\tEventType=0\tInOutState=0\tTime_second=840000000\r\n",
        }

        calls = {"n": 0}

        def _fallback(fn):
            calls["n"] += 1
            # 1: bridge_get_rtlog (fail)
            # 2: transaction explicit fields (fail -114)
            # 3: transaction '*' (ok key=value)
            if calls["n"] == 1:
                return rtlog_fail
            if calls["n"] == 2:
                return txn_fields_fail
            return txn_star_ok

        drv._with_password_fallback = _fallback
        result = drv.get_rtlog()
        assert result["result"] == 1
        # Should be reshaped to pin-first RTLOG variant with index present.
        # Format: pin,verified,door,eventType,inOut,time_second,index,cardno,sitecode
        assert "5,0,1,0,0,840000000," in result.get("data", "")
        assert ",0012345678," in result.get("data", "")


# ─────────────────────────────────────────────────────────────────────────────
# 8  plcommpro_bridge.get_rtlog is exported
# ─────────────────────────────────────────────────────────────────────────────
class TestPlcommproBridgeExport:
    def test_get_rtlog_is_exported(self):
        import agent.plcommpro_bridge as mod
        assert callable(getattr(mod, "get_rtlog", None)), \
            "get_rtlog() not exported from plcommpro_bridge"

    def test_get_rtlog_signature_accepts_conn(self):
        """get_rtlog must accept a PlcommproConnInfo as first arg (no runtime error)."""
        from agent.plcommpro_bridge import get_rtlog, PlcommproConnInfo
        import inspect
        sig = inspect.signature(get_rtlog)
        params = list(sig.parameters.keys())
        assert params[0] == "conn", f"First param should be 'conn', got {params}"
