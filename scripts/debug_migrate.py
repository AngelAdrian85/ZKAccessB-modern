#!/usr/bin/env python
"""Trace which module is trying to import 'mysite'."""

import sys
import importlib.abc
import importlib.machinery


class DebugFinder(importlib.abc.Finder):
    def find_module(self, fullname, path=None):
        if "mysite" in fullname:
            import traceback

            print(f"\n{'=' * 60}")
            print(f"ATTEMPTING TO IMPORT: {fullname}")
            print("Stack trace:")
            for line in traceback.format_stack()[:-1]:
                print(line.strip())
            print("=" * 60 + "\n")
        return None


sys.meta_path.insert(0, DebugFinder())

import os  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

from django.core.management import execute_from_command_line  # noqa: E402

if __name__ == "__main__":
    execute_from_command_line(["manage.py", "migrate", "--no-input"])
