#!/usr/bin/env python3
"""
Quick local explorer that uses Django's test Client to request discovered URL patterns.
Does NOT need the runserver; it imports Django settings and runs views internally.

Run with the project's venv and with DJANGO_SETTINGS_MODULE and PYTHONPATH set to the
`zkeco_modern` package path (the calling command will do that).
"""
import os
import sys
import django
from django.test import Client
import argparse
import re

# Ensure settings and path (caller sets DJANGO_SETTINGS_MODULE and PYTHONPATH,
# but be permissive if they're not set)
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'

# Add zkeco_modern to sys.path if present in repo root
repo_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'zkeco_modern'))
if os.path.isdir(repo_mod) and repo_mod not in sys.path:
    sys.path.insert(0, repo_mod)

try:
    django.setup()
except Exception as e:
    print("Django setup() failed:", e)
    raise

# Ensure test Client host won't be rejected by ALLOWED_HOSTS when using the test client
try:
    # import here after django.setup()
    from django.conf import settings as _dj_settings
    # Normalize to a mutable list and include common local test hosts
    try:
        current = list(getattr(_dj_settings, 'ALLOWED_HOSTS', []) or [])
    except Exception:
        current = []
    for _h in ('testserver', 'localhost', '127.0.0.1'):
        if _h not in current:
            current.append(_h)
    try:
        _dj_settings.ALLOWED_HOSTS = current
    except Exception:
        # Some setups may not allow writing; ignore if so (requests will still attempt)
        pass
except Exception as _e:
    print('Warning adjusting ALLOWED_HOSTS for test client:', _e)

from django.urls import get_resolver
from django.core.exceptions import ImproperlyConfigured

client = Client()

def collect_simple_paths(limit=20, include_admin=False, try_params=False):
    resolver = get_resolver()
    patterns = resolver.url_patterns
    paths = []

    def route_to_path(route: str):
        # Convert simple path() expressions like '<int:pk>' into sample values if try_params
        if not try_params:
            if '<' in route or '(' in route or '\\' in route or '^' in route:
                return None
            return '/' + route.lstrip('/')

        # replace common converters
        def repl(m):
            inside = m.group(1)
            # inside may be like 'int:pk' or 'slug:slug'
            if ':' in inside:
                typ, name = inside.split(':', 1)
            else:
                typ = 'str'
            typ = typ.strip()
            if typ in ('int', 'pk'):
                return '1'
            if typ in ('slug', 'str', 'path'):
                return 'test'
            if typ == 'uuid':
                return '00000000-0000-0000-0000-000000000000'
            return 'test'

        # Django path converters are inside <>; replace them
        try:
            s = re.sub(r'<([^>]+)>', repl, route)
        except Exception:
            return None
        if '(' in s or '^' in s or '\\' in s:
            return None
        return '/' + s.lstrip('/')

    def walk(patterns, prefix=''):
        for p in patterns:
            # Try to get a human-readable pattern string
            try:
                route = str(p.pattern)
            except Exception:
                route = getattr(p, 'pattern', str(p))
            full = prefix + route
            # Filter noises
            if not include_admin and any(x in full for x in ('static', 'media', 'favicon')):
                continue

            candidate = route_to_path(full)
            if candidate:
                if candidate not in paths:
                    paths.append(candidate)
                if len(paths) >= limit:
                    return

            # Recurse into included resolvers if present
            if hasattr(p, 'url_patterns'):
                walk(p.url_patterns, prefix=prefix)
            if len(paths) >= limit:
                return

    walk(patterns)
    return paths


def test_paths(paths):
    results = []
    for p in paths:
        try:
            resp = client.get(p)
            snippet = resp.content.decode('utf-8', errors='replace')[:300].replace('\n', ' ')
            results.append((p, resp.status_code, snippet))
        except Exception as e:
            results.append((p, 'EXCEPTION', str(e)))
    return results


def main():
    parser = argparse.ArgumentParser(description='Explore Django URL patterns using the test Client.')
    parser.add_argument('--limit', '-n', type=int, default=30, help='max number of paths')
    parser.add_argument('--include-admin', action='store_true', help='do not filter admin-related paths')
    parser.add_argument('--try-params', action='store_true', help='attempt to fill common path parameters (int,slug,uuid)')
    parser.add_argument('--create-user', action='store_true', help='create a test user and login before requests')
    parser.add_argument('--username', default='explorer', help='username for test user')
    parser.add_argument('--password', default='password', help='password for test user')
    args = parser.parse_args()

    print('Collecting candidate paths...')
    try:
        paths = collect_simple_paths(limit=args.limit, include_admin=args.include_admin, try_params=args.try_params)
    except ImproperlyConfigured as e:
        print('Resolver import/config error:', e)
        return 2

    if not paths:
        print('No simple (non-parameterized) paths discovered to test.')
        return 0

    # Optionally create and login a local test user
    if args.create_user:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            u, created = User.objects.get_or_create(username=args.username)
            if created:
                u.set_password(args.password)
                u.is_staff = True
                u.is_superuser = True
                u.save()
                print(f'Created test user {args.username}')
            else:
                # ensure password matches
                u.set_password(args.password)
                u.save()
                print(f'Updated password for existing user {args.username}')
            logged = client.login(username=args.username, password=args.password)
            print('Client login success:' , logged)
        except Exception as e:
            print('Failed to create/login test user:', e)

    print('Discovered paths to test:', paths)
    results = test_paths(paths)

    print('\nResults:')
    for p, status, snippet in results:
        print(f"{p} -> {status}\n  {snippet}\n")

    # Summary
    ok = sum(1 for _, s, _ in results if s == 200)
    print(f"Summary: {ok}/{len(results)} returned 200 OK")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
