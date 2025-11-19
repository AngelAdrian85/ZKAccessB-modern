from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
import os

# Simple view that attempts to render a legacy template from the old project
def legacy_render(request, subpath=""):
    # Map a few known routes to likely template names when possible
    mapping = {
        "": "registration/login.html",
        "WorktableMap/": "Acc_Worktable_Map.html",
        "WorktableMapMonitor/": "Acc_Worktable_Map_Monitor.html",
        "RTMonitorPage/": "Acc_RTMonitor.html",
        "DoorSetPage/": "Acc_Door_Mng.html",
        "AccLevelSet/": "AccLevelSet_list.html",
        "AccTimeSeg/": "AccTimeSeg_edit.html",
    }
    tpl = None
    # normalize
    sub = subpath or ""
    if sub in mapping:
        tpl = mapping[sub]
    else:
        # try to use subpath as template name under iaccess/
        candidate = sub.lstrip('/')
        if candidate.endswith('/'):
            candidate = candidate[:-1]
        if candidate:
            tpl = os.path.join('iaccess', f"{candidate}.html")

    if not tpl:
        return HttpResponse(f"No legacy template mapping for {subpath}", status=404)

    # Try several candidate template locations (legacy templates are not always namespaced)
    candidates = [tpl, os.path.basename(tpl), os.path.join('iaccess', os.path.basename(tpl))]
    found = None
    for c in candidates:
        try:
            loader.get_template(c)
            found = c
            break
        except Exception:
            continue

    if not found:
        return HttpResponse(f"Could not find legacy template for {subpath}, tried: {candidates}", status=404)

    # Provide a few request attributes and context variables the legacy templates expect
    try:
        # some templates use request.surl and request.dbapp_url
        if not hasattr(request, 'surl'):
            request.surl = ''
        if not hasattr(request, 'dbapp_url'):
            request.dbapp_url = '/'
        # also provide MEDIA_URL, LANGUAGE_CODE commonly referenced in templates
        from django.conf import settings as _s
        context = {
            'request': request,
            'MEDIA_URL': getattr(_s, 'MEDIA_URL', '/media'),
            'LANGUAGE_CODE': getattr(_s, 'LANGUAGE_CODE', 'en'),
        }
        return render(request, found, context=context)
    except Exception as e:
        # If template rendering fails, surface a helpful message
        return HttpResponse(f"Could not render legacy template {found}: {e}", status=500)
