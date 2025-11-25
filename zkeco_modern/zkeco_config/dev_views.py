from django.http import HttpResponse, Http404
from django.template import loader, TemplateDoesNotExist

def serve_legacy_template(request, tmpl_path):
    """Development-only view to render a legacy template by filename.

    `tmpl_path` is the template filename or path under the legacy template dir,
    for example: `index.html` or `registration/login.html`.
    """
    try:
        tpl = loader.get_template(tmpl_path)
    except TemplateDoesNotExist:
        raise Http404(f"Legacy template not found: {tmpl_path}")
    content = tpl.render({ 'request': request })
    return HttpResponse(content)

def serve_index(request):
    return serve_legacy_template(request, 'index.html')

def oauth_debug(request):
    """Development-only debug endpoint to inspect OAuth callbacks.

    Returns a simple HTML page showing the received query parameters so
    you can register `http://127.0.0.1:8000/oauth-debug/` as a redirect
    URI and confirm Django receives the `code`/`state` payload.
    """
    params = request.GET.dict()
    lines = [f"<p><b>{k}</b>: {v}</p>" for k, v in params.items()]
    body = "".join(lines) or "<p><i>No query parameters received.</i></p>"
    body += f"<hr><p>Method: {request.method}</p>"
    return HttpResponse(f"<html><body><h2>OAuth debug</h2>{body}</body></html>")
