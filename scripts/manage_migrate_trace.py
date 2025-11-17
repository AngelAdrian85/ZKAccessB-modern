import sys
import traceback


class TraceFinder:
    def find_spec(self, fullname, path, target=None):
        if "mysite" in fullname:
            print("TRACE: import requested for", fullname)
            traceback.print_stack()
        return None


sys.meta_path.insert(0, TraceFinder())

# Ensure project package dir is on sys.path
import os  # noqa: E402

proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "zkeco_modern"))
if proj not in sys.path:
    sys.path.insert(0, proj)

print("Running migrate with traced imports, sys.path[0]", sys.path[0])

import os  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

from django.core.management import execute_from_command_line  # noqa: E402

if __name__ == "__main__":
    execute_from_command_line(["manage.py", "migrate"])
