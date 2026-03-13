import json
from pathlib import Path

from django.core.management.base import BaseCommand

from agent.controller_capabilities import build_capability_report, render_markdown_report


def _read_probe_artifact_text(probe_path: Path) -> str:
    if not probe_path.exists() or not probe_path.is_file():
        return ""
    raw = probe_path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _default_probe_artifact() -> Path:
    return Path(__file__).resolve().parents[4] / "probe_controller_direct_4370.latest.txt"


class Command(BaseCommand):
    help = "Describe controller capabilities, application mappings, and current gaps."

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["json", "markdown"],
            default="markdown",
            help="Output format.",
        )
        parser.add_argument(
            "--probe-artifact",
            default="",
            help="Optional path to a saved direct 4370 probe artifact. Defaults to probe_controller_direct_4370.latest.txt when present.",
        )

    def handle(self, *args, **options):
        out_format = str(options.get("format") or "markdown").strip().lower()
        probe_arg = str(options.get("probe_artifact") or "").strip()
        probe_path = Path(probe_arg) if probe_arg else _default_probe_artifact()
        probe_text = _read_probe_artifact_text(probe_path)
        if out_format == "json":
            self.stdout.write(
                json.dumps(
                    build_capability_report(direct_4370_probe_text=probe_text),
                    indent=2,
                    ensure_ascii=True,
                )
            )
            return
        self.stdout.write(render_markdown_report(direct_4370_probe_text=probe_text))
