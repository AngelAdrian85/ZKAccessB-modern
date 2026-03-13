import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.join(REPO_ROOT, "zkeco_modern")
for path in (PROJECT_ROOT, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

from agent.pyzk_probe import build_parser, render_human, run_probe


def main() -> int:
    args = build_parser().parse_args()
    report = run_probe(args)
    if args.json:
        import json

        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(render_human(report), end="")
    return 0 if report.get("first_success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

