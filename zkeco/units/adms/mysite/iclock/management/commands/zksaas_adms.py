# -*- coding: utf-8 -*-
from django.conf import settings

try:
    db_engine = getattr(settings, "DATABASE_ENGINE", None)
    if db_engine == "pool":
        settings.DATABASE_ENGINE = getattr(settings, "POOL_DATABASE_ENGINE", db_engine)
except Exception:
    pass

from django.core.management.base import BaseCommand
import time
import os
import shutil
from traceback import print_exc

try:
    from django.utils.simplejson import dumps  # noqa: F401
except ImportError:
    import json  # noqa: F401


def sort_files(fns: list) -> None:
    ln = len(fns)
    for i in range(ln - 1):
        j = i + 1
        while j < ln:
            if t_e(fns[i]) > t_e(fns[j]):
                tmp = fns[i]
                fns[i] = fns[j]
                fns[j] = tmp
            j += 1


def t_e(d: str) -> int:
    x = d.split(".")[0]
    if len(x) > 17:
        return int((str(d).split("_")[0] + "000000")[:17])
    else:
        return int((x + "000000")[:17])


def process_data():
    from mysite.iclock.models.model_device import Device
    from mysite.iclock.devview import write_data

    data = ""
    devs = Device.objects.filter(device_type=1)
    path = settings.C_ADMS_PATH + "new/"
    for d in devs:
        try:
            objpath = path % d.sn
            #            if not os.path.exists(objpath):
            #                os.makedirs(objpath)

            if os.path.exists(objpath):
                files = []
                for f in os.listdir(objpath):
                    if os.path.isfile(objpath + f):
                        try:
                            files.append(f)
                        except Exception:
                            pass
                if len(files) > 1:
                    sort_files(files)
                # print files
                for f in files:
                    if os.path.exists(objpath + f):
                        process_flag = True
                        try:
                            with open(objpath + f, "r+") as fs:
                                data = fs.read()
                            write_data(data, d)
                        except Exception:
                            process_flag = False
                            print_exc()
                        finally:
                            try:
                                f_dir = f[:8]
                                cf_path = settings.C_ADMS_PATH + f_dir + "/"
                                cf_path = cf_path % d.sn
                                if not os.path.exists(cf_path):
                                    os.makedirs(cf_path)
                                if not process_flag:
                                    f = "error_" + f
                                shutil.copy(objpath + f, cf_path + f)
                                os.remove(objpath + f)
                            except Exception:
                                print_exc()
            else:
                pass
                # print "path not exists '%s' "%objpath
        except Exception:
            import traceback

            traceback.print_exc()
        time.sleep(0.1)


class Command(BaseCommand):
    help = "Starts zksaas adms ."

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        while True:
            try:
                process_data()
            except Exception:
                import traceback

                traceback.print_exc()
            time.sleep(5)
