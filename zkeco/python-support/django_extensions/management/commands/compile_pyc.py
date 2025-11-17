from django.core.management.base import BaseCommand
from django_extensions.management.utils import get_project_root
from os.path import join as _j
import py_compile
import os


class Command(BaseCommand):
    help = "Compile python bytecode files for the project."

    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('--path', '-p', action='store', dest='path', help='Specify path to recurse into')

    def handle(self, *args, **options):
        project_root = options.get("path", None)
        if not project_root:
            project_root = get_project_root()
        verbose = int(options.get("verbosity", 1)) > 1

        for root, dirs, files in os.walk(project_root):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".py":
                    full_path = _j(root, file)
                    if verbose:
                        print("%sc" % full_path)
                    py_compile.compile(full_path)
