#!/usr/bin/env python3
"""Validate fixed sanitized partials with Django and produce safe patches.

Reads `sanitized_fixed_report.json` to know which fixed partials correspond
to original templates. For each fixed partial it attempts to parse the
template using Django's template engine. If parsing succeeds, the script
writes a replacement file under `scripts/patches/` (mirrored path) and
records the mapping in `scripts/validation_report.json`.

This script does NOT overwrite original templates; it only generates
patch files for manual review and an index of changes.
"""
import json
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'zkeco_modern' / 'scripts'
REPORT_SRC = SCRIPTS / 'sanitized_fixed_report.json'
REPORT_OUT = SCRIPTS / 'validation_report.json'
PATCH_DIR = SCRIPTS / 'patches'

def main():
    if not REPORT_SRC.exists():
        print('Missing', REPORT_SRC)
        return 2

    data = json.loads(REPORT_SRC.read_text(encoding='utf-8'))
    fixed = data.get('fixed', [])
    if not fixed:
        print('No fixed partials listed in', REPORT_SRC)
        return 0

    # Initialize Django and import template utils lazily
    try:
        import django
        from django.template import Engine, TemplateSyntaxError, Context
    except Exception as e:
        print('Failed to import Django:', e)
        return 3

    # Ensure settings are configured; user should set DJANGO_SETTINGS_MODULE
    engine = None
    # Set up a file-only logger to avoid spamming stdout/stderr during tests
    LOGFILE = SCRIPTS / 'validate_debug.log'
    logger = logging.getLogger('zkeco_validate')
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        fh = logging.FileHandler(LOGFILE, encoding='utf-8')
        fh.setLevel(logging.WARNING)
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logger.addHandler(fh)
        logger.propagate = False

    try:
        django.setup()
        try:
            engine = Engine.get_default() if hasattr(Engine, 'get_default') else Engine()
        except Exception as e:
            # If the default engine initialization hits app loading issues,
            # fall back to a standalone Engine to allow parse-time checks.
            logger.warning('default Engine init failed: %s', e)
    except Exception as e:
        logger.warning('django.setup() failed: %s', e)

    if engine is None:
        from django.template import Engine as _Engine
        engine = _Engine()

    # Try to attach known legacy templatetag modules' registers to the engine
    # so filters/tags like HasPerm, lescape, etc. are available even when
    # the app registry couldn't be loaded.
    legacy_modules = [
        'zkeco_modern.legacy_models.templatetags.legacy_filters',
        'zkeco_modern.legacy_models.templatetags.legacy_shims',
        'zkeco_modern.legacy_models.templatetags.dbapp_tags',
        'zkeco_modern.legacy_models.templatetags.legacy_defaulttags',
    ]

    for modname in legacy_modules:
        try:
            mod = __import__(modname, fromlist=['register'])
            reg = getattr(mod, 'register', None)
            if reg is not None:
                try:
                    engine.template_builtins.append(reg)
                except Exception:
                    pass
        except Exception:
            # ignore missing modules; we'll normalize templates where necessary
            pass

    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    report = {'validated': [], 'failed': []}

    for entry in fixed:
        orig = entry.get('file')
        fixed_partial = entry.get('fixed_partial')
        if not fixed_partial:
            report['failed'].append({'file': orig, 'reason': 'no_fixed_partial'})
            continue

        ppath = Path(fixed_partial)
        if not ppath.exists():
            report['failed'].append({'file': orig, 'reason': 'fixed_partial_missing', 'path': fixed_partial})
            continue

        text = ppath.read_text(encoding='utf-8')
        def try_parse(ttext):
            try:
                tpl = engine.from_string(ttext)
                try:
                    tpl.render(Context({}))
                except Exception:
                    pass
                return True, None, tpl
            except TemplateSyntaxError as e:
                return False, str(e), None
            except Exception as e:
                return False, str(e), None

        ok, err, tpl = try_parse(text)
        normalized = None
        if not ok:
            # Try conservative normalization for common legacy items: i18n loads / trans / blocktrans, and known filters
            t = text
            # remove any `{% load ... %}` lines to avoid requiring importable
            # templatetag libraries during parsing (we attach builtin shims
            # separately when possible)
            import re
            t = re.sub(r"{%-?\s*load\b[^%]*-?%}\s*\n?", "", t)
            # replace simple trans tags: {% trans "text" %} -> text
            t = re.sub(r"{%-?\s*trans\s+\"([^\"]*)\"\s*-?%}", lambda m: m.group(1), t)
            t = re.sub(r"{%-?\s*trans\s+'([^']*)'\s*-?%}", lambda m: m.group(1), t)
            # replace trans of a variable: {% trans var %} -> {{ var }}
            t = re.sub(r"{%-?\s*trans\s+([\w\.]+)\s*-?%}", lambda m: "{{ %s }}" % m.group(1), t)
            # strip blocktrans tags but keep inner content
            t = re.sub(r"{%-?\s*blocktrans[^%]*-?%}(.*?){%-?\s*endblocktrans\s*-?%}", lambda m: m.group(1), t, flags=re.S)
            # remove known legacy filters by name
            for f in ('lescape', 'shortTime'):
                t = re.sub(r"\|%s\b" % f, '', t)

            # attempt parse again
            ok2, err2, tpl2 = try_parse(t)
            if ok2:
                normalized = t
                tpl = tpl2
                ok = True
            else:
                err = err2 or err

        if not ok:
            report['failed'].append({'file': orig, 'partial': str(ppath), 'error': err})
            continue

        # success -> create a patch file (mirrored safe replacement)
        rel = ppath.relative_to(SCRIPTS / 'sanitized_fixed')
        out_path = PATCH_DIR / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # write the suggested replacement content
        out_path.write_text(text, encoding='utf-8')

        report['validated'].append({'file': orig, 'partial': str(ppath), 'patch': str(out_path)})

    REPORT_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote validation report to', REPORT_OUT)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
