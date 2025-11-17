#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand
import time
import datetime
from base.backup import backupdb
import sched
from django.db import connection
import traceback

schedule = sched.scheduler(time.time, time.sleep)


def execute_command(cmd, inc):
    cmd()
    schedule.enter(inc, 0, execute_command, (backupdb, inc))


class Command(BaseCommand):
    def handle(self, *args, **options):
        from mysite.utils import write_log

        write_log("Starting  service...", True)
        # 每次启动服务先检查mysql数据库是否损坏，如果已经损坏（特别是myisam）则修复。-darcy20120327
        try:
            if "mysql" in connection.__module__:  #
                # 仅门禁mysql使用，新zkeco可不合并该代码-darcy20120327
                start_time = datetime.datetime.now()
                write_log("Start to check the mysql(myisam) tables...", True)
                cursor = connection.cursor()
                tables = [
                    "acc_monitor_log",
                    "action_log",
                    "iclock",
                    "devcmds",
                    "checkinout",
                ]
                for table in tables:
                    cursor.execute("check table %s quick;" % table)
                    check_ret = cursor.fetchall()
                    if check_ret[0][3] != "OK":
                        write_log(
                            "Start to repair the mysql(myisam) table %s..." % table,
                            True,
                        )
                        cursor.execute(
                            "repair table %s quick" % table
                        )  # 需要修复时会产生两条记录
                        repair_ret = cursor.fetchall()
                        if (
                            repair_ret[1][3] == "OK"
                        ):  # (('zkeco_video.acc_monitor_log', 'repair', 'status', 'OK'),)
                            # (('zkeco_video.acc_monitor_log', 'repair', 'warning', 'Number of rows changed from 64332 to 64312'), ('zkeco_video.acc_monitor_log', 'repair', 'status', 'OK'))
                            write_log(
                                "Repair the table %s OK. %s: %s..."
                                % (table, repair_ret[0][2], repair_ret[0][3]),
                                True,
                            )
                        else:
                            write_log(
                                "Failed to repair the mysql(myisam) table %s..."
                                % table,
                                True,
                            )
                    else:
                        write_log(
                            "Check the mysql(myisam) table %s OK..." % table, True
                        )

                connection.close()
                end_time = datetime.datetime.now()
                time_delta = end_time - start_time
                write_log(
                    "Check and Repair mysql tables for %s s or %s microseconds..."
                    % (time_delta.seconds, time_delta.microseconds),
                    True,
                )
        except Exception as e:
            write_log("--Check and Repair mysql tables error=%s" % e, True)
            # Print full traceback for debugging
            traceback.print_exc()
        write_log("Start to execute backupdb...", True)
        while True:
            backupdb()
            time.sleep(10)


#        schedule.enter(0,0,execute_command,(backupdb,60))
#        schedule.run()
