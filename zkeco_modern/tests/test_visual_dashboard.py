import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

BASELINE_DIR = Path(__file__).resolve().parent / "visual_baselines"
BASELINE_PATH = BASELINE_DIR / "dashboard.png"
GENERATE_BASELINE = os.environ.get("GENERATE_DASHBOARD_BASELINE") == "1"
VISUAL_DIFF_THRESHOLD = 2.0  # mean per-channel difference


class DashboardVisualTest(StaticLiveServerTestCase):
    """Comparing the dashboard UI snapshot against a stored baseline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.visual_user = User.objects.create_user(
            username="visual", email="visual@example.com", password="visualpass"
        )
        cls.visual_user.is_staff = True
        cls.visual_user.save()

    def setUp(self):
        self.client.force_login(self.visual_user)
        self.session_cookie = self.client.cookies.get("sessionid").value

    def test_dashboard_visual(self):
        screenshot_path = self._capture_dashboard()
        try:
            if GENERATE_BASELINE:
                BASELINE_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy(screenshot_path, BASELINE_PATH)
                self.skipTest("Baseline created; rerun without GENERATE_DASHBOARD_BASELINE")
            self.assertTrue(
                BASELINE_PATH.exists(),
                f"Expected baseline image at {BASELINE_PATH}"
            )
            with Image.open(BASELINE_PATH) as baseline, Image.open(screenshot_path) as current:
                baseline_rgb = baseline.convert("RGB")
                current_rgb = current.convert("RGB")
                self.assertEqual(
                    baseline_rgb.size,
                    current_rgb.size,
                    "Screenshot size mismatch; UI layout may have changed",
                )
                diff = ImageChops.difference(baseline_rgb, current_rgb)
                stat = ImageStat.Stat(diff)
                mean_diff = sum(stat.mean) / len(stat.mean)
                self.assertLess(
                    mean_diff,
                    VISUAL_DIFF_THRESHOLD,
                    f"Visual difference too large (mean={mean_diff:.2f})",
                )
        finally:
            if screenshot_path.exists():
                screenshot_path.unlink()

    def _capture_dashboard(self) -> Path:
        parsed = urlparse(self.live_server_url)
        cookie = {
            "name": "sessionid",
            "value": self.session_cookie,
            "domain": parsed.hostname,
            "path": "/",
            "httpOnly": True,
            "secure": False,
        }
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        temp_png = Path(tmp_path)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.context.add_cookies([cookie])
            page.set_viewport_size({"width": 1366, "height": 900})
            page.goto(f"{self.live_server_url}/agent/dashboard/", wait_until="networkidle")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(temp_png), full_page=True)
            browser.close()
        return temp_png
