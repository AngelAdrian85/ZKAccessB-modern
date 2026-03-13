import json
from argparse import Namespace

from django.core.management.base import BaseCommand

from agent.pyzk_probe import build_parser, render_human, run_probe


class Command(BaseCommand):
    help = "Probe a controller with pyzk via Django management, using Device defaults when available."

    def add_arguments(self, parser):
        probe_parser = build_parser()
        for action in probe_parser._actions:
            if not action.option_strings or action.dest == "help":
                continue
            kwargs = {
                "default": action.default,
                "help": action.help,
            }
            if getattr(action, "choices", None):
                kwargs["choices"] = action.choices
            if getattr(action, "type", None):
                kwargs["type"] = action.type
            if getattr(action, "nargs", None) is not None:
                kwargs["nargs"] = action.nargs
            if getattr(action, "const", None) is not None:
                kwargs["const"] = action.const
            if action.required:
                kwargs["required"] = action.required
            if getattr(action, "metavar", None) is not None:
                kwargs["metavar"] = action.metavar

            if action.__class__.__name__ == "_AppendAction":
                kwargs["action"] = "append"
            elif action.__class__.__name__ == "_StoreTrueAction":
                kwargs["action"] = "store_true"
            else:
                kwargs["action"] = "store"

            parser.add_argument(*action.option_strings, **kwargs)

    def handle(self, *args, **options):
        report = run_probe(Namespace(**options))
        if bool(options.get("json")):
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
            return
        self.stdout.write(render_human(report))