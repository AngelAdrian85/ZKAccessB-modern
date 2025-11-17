from django.core.management.base import BaseCommand
from django_extensions.management.utils import get_project_root
from os.path import join as _j
import os


class Command(BaseCommand):
    help = "Removes all python bytecode compiled files from the project."
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('--optimize', '-o', '-O', action='store_true', dest='optimize',
                            help='Remove optimized python bytecode files')
        parser.add_argument('--path', '-p', action='store', dest='path',
                            help='Specify path to recurse into')
        parser.add_argument('--verbosity', '-v', action='store', dest='verbosity',
                            default='1', choices=['0', '1', '2'],
                            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output')

    def handle(self, *args, **options):
        project_root = options.get('path') or get_project_root()
        exts = ['.pyc', '.pyo'] if options.get('optimize', False) else ['.pyc']
        verbose = int(options.get('verbosity', '1')) > 1

        for root, dirs, files in os.walk(project_root):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in exts:
                    full_path = _j(root, file)
                    if verbose:
                        self.stdout.write(full_path)
                    os.remove(full_path)
