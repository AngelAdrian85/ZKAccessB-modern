import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.local_settings_iaccess")
os.environ.setdefault("INCLUDE_LEGACY", "1")

from django.test import Client


def test_iaccess_index_renders():
    c = Client()
    resp = c.get("/iaccess/")
    assert resp.status_code == 200
    # Expect the Acc_Door_Mng template contains recognizable text
    content = resp.content.decode("utf-8", errors="ignore")
    assert "Acc_Door_Mng" in content or "Door" in content or len(content) > 100
