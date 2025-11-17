import os
import sys
from django.core.management.base import CommandError, AppCommand, _make_writeable
from django_extensions.management.color import color_style



class Command(AppCommand):
    def add_arguments(self, parser):
        parser.add_argument("--name", "-n", action="store", dest="command_name", default="sample", help="The name to use for the management command")
        parser.add_argument("--base", "-b", action="store", dest="base_command", default="Base", help="The base class used for implementation of this command. Should be one of Base, App, Label, or NoArgs")

    help = (
        "Creates a Django management command directory structure for the given app name"
        " in the current directory."
    )
    args = "[appname]"
    label = "application name"

    requires_model_validation = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = True

    def handle_app(self, app, **options):
        directory = os.getcwd()
        app_name = app.__name__.split(".")[-2]
        project_dir = os.path.join(directory, app_name)
        if not os.path.exists(project_dir):
            try:
                os.mkdir(project_dir)
            except OSError as e:
                raise CommandError(e)

        copy_template(
            "command_template",
            project_dir,
            options.get("command_name"),
            "%sCommand" % options.get("base_command"),
        )


def copy_template(template_name, copy_to, command_name, base_command):
    """copies the specified template directory to the copy_to location"""
    import django_extensions
    import shutil
    template_dir = os.path.join(django_extensions.__path__[0], "conf", template_name)

    # color/style helper for messages
    style = color_style()

    handle_method = "handle(self, *args, **options)"
    if base_command == "AppCommand":
        handle_method = "handle_app(self, app, **options)"
    elif base_command == "LabelCommand":
        handle_method = "handle_label(self, label, **options)"
    elif base_command == "NoArgsCommand":
        handle_method = "handle_noargs(self, **options)"

    # walks the template structure and copies it
    for d, subdirs, files in os.walk(template_dir):
        relative_dir = d[len(template_dir) + 1 :]
        if relative_dir and not os.path.exists(os.path.join(copy_to, relative_dir)):
            os.mkdir(os.path.join(copy_to, relative_dir))
        for i, subdir in enumerate(subdirs):
            if subdir.startswith("."):
                del subdirs[i]
        for f in files:
            if f.endswith(".pyc") or f.startswith(".DS_Store"):
                continue
            path_old = os.path.join(d, f)
            path_new = os.path.join(
                copy_to, relative_dir, f.replace("sample", command_name)
            )
            if os.path.exists(path_new):
                path_new = os.path.join(copy_to, relative_dir, f)
                if os.path.exists(path_new):
                    continue
            path_new = path_new.rstrip(".tmpl")
            # Use context managers for file IO
            with open(path_old, "r", encoding="utf-8", errors="surrogateescape") as fp_old:
                content = fp_old.read()
            content = (
                content
                .replace("{{ command_name }}", command_name)
                .replace("{{ base_command }}", base_command)
                .replace("{{ handle_method }}", handle_method)
            )
            with open(path_new, "w", encoding="utf-8", errors="surrogateescape") as fp_new:
                fp_new.write(content)
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                try:
                    sys.stderr.write(
                        style.NOTICE(
                            "Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n"
                            % path_new
                        )
                    )
                except Exception:
                    # best-effort logging; swallow if style fails
                    pass
