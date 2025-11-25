# uncompyle6 version 3.9.3
# Python bytecode version base 2.6 (62161)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: F:\2.bb\zkaccess_usa\units\adms\mysite\iaccess\dev_comm_center.py
# Compiled at: 2017-06-12 11:08:05
from multiprocessing import Pool, Process
import threading, time, datetime
from time import sleep, ctime
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
from django.db import models, connection
import os, re, redis, dict4ini
from redis.server import queqe_server, start_dict_server
from mysite.iaccess.devcomm import TDevComm
from mysite.iaccess.devcomm import *
from traceback import print_exc
from mysite.utils import printf, delete_log, write_log
from ctypes import *
from dbapp.utils import encode_time
from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP, ACCDEVICE_DISABLED, DEVICE_AS_CONTROLLER, DEVICE_ZKVISION_CAMERA, DEVICE_HIKVISION_VIDEO, DEVICE_HIKVISION_CAMERA, DEVICE_DAHUA_VIDEO, DEVICE_DAHUA_CAMERA
from mysite.personnel.models.model_emp import format_pin
from base.middleware import threadlocals
from process_comm_data import strtodatetime, strtoint, is_comm_io_error, delete_tempcmd, FmtTTime
from process_comm_data import get_linkageio_to_dict, get_linkageio_to_dict_for_id, get_videoip_channelno_to_dict
from models.accmonitorlog import EVENT_LINKCONTROL, OPEN_AUXOUT, CLOSE_AUXOUT, INOUT_SEVER, INOUT_SHORT, DOOR_STATE_ID, ALARM_ID_START, CANCEL_ALARM, CANCEL_ALARM_TYPE, TAMPER_ALARM, TIME_OUT_ALARM, DURESS_FP_ALARM, DURESS_PWD_ALARM, OPENED_FORCEFULLY_ALARM, ALARM_ID_END, EVENT_POINT_TYPE_NONE, EVENT_POINT_TYPE_DOOR, EVENT_POINT_TYPE_AUX, DEVICE_STARTED, EVENT_CHOICES, EVENT_LOG_AS_ATT, START_FIRE_DOOR, OPEN_ELEVTOR_FUN, CLOSE_ELEVTOR_FUN
from django.conf import settings
from process_comm_data import get_reader, get_aux, get_emp, get_area, get_aux_name, get_dev_door, get_dept
try:
    import cPickle as pickle
except:
    import pickle

import thread
from mysite.iaccess.view import check_acpanel_args
cfg = dict4ini.DictIni(os.getcwd() + '/appconfig.ini', values={'iaccess': {'reconnect_time': 60}})
MAX_TRY_COMM_TIME = 20
MAX_CONNECT_COUNT = 60 * 24 * 30
MAX_INTERVAL_CONNTECT_TIME = cfg.iaccess.reconnect_time and int(cfg.iaccess.reconnect_time) or 60
PAUSE_TIMEOUT = 60
g_devcenter = None
g_cursor = connection.cursor()
g_reader_dict = {}
g_aux_dict = {}
g_emp_dict = {}
g_area_dict = {}
g_dev_door_dict = {}
g_dept_dict = {}
g_att_doors_list = []
g_get_new_log_thread_cur_count = 0
g_get_new_log_thread_lock = thread.allocate_lock()
GET_NEW_LOG_THREAD_MAX_COUNT = 40
G_DEVICE_CONNECT = 'CONNECT'
G_DEVICE_DISCONNECT = 'DISCONNECT'
G_DEVICE_UPDATE_DATA = 'DATA UPDATE'
G_DEVICE_QUERY_DATA = 'DATA QUERY'
G_DEVICE_DELETE_DATA = 'DATA DELETE'
G_DEVICE_GET_DATA = 'DEVICE GET'
G_DEVICE_SET_DATA = 'DEVICE SET'
G_DEVICE_CANCEL_ALARM = 'CANCEL ALARM'
G_DEVICE_CONTROL_NO = 'CONTROL NO'
G_DEVICE_UPGRADE_FIRMWARE = 'UPGRADE FIRMWARE'
G_DEVICE_GET_OPTION = 'OPTION GET'
G_DEVICE_SET_OPTION = 'SET OPTION'
G_REAL_LOG = 'REAL_LOG'
G_DOWN_NEWLOG = 'DOWN_NEWLOG'
G_QUEUE_ERROR = 'QUEUE_ERROR'
G_CHECK_SERVICE = 'CHECK_SERVICE'
G_DATA_COUNT = 'DATA COUNT'
G_HARD_DISK_LESS_THAN_1G = 'CHECK_DISK'
GR_RETURN_OK = 200
MAX_RTLOG = 500
TRY_USE_DISK_FILE_CMD_COUNT = 512
DEVOPT = 'DEV_OPERATE'
CENTER_PROCE_HEART = 'CENTER_HEART_%s'
CENTER_PROCE_LIST = 'CENTER_PROCE_LIST'
CENTER_MAIN_PID = 'CENTER_MAIN_PID'
OPERAT_ADD = 1
OPERAT_EDIT = 2
OPERAT_DEL = 3
PROCESS_NORMAL = 0
PROCESS_WAIT_PAUSE = 1
PROCESS_PAUSE = 2
THREAD_NORMAL = 0
THREAD_WAIT_PAUSE = 1
THREAD_PAUSE = 2
DEVICE_COMMAND_TABLE = [
 _(u'\u0x4fe10x606f'),
 _(u'\u0x67430x96500x4fe10x606f'),
 _(u'\u0x65e50x8bbe0x7f6e'),
 _(u'\u0x6bb50x8bbe0x7f6e'),
 _(u'\u0x5e380x5f000x8bbe0x7f6e'),
 _(u'\u0x5f000x95e80x8bbe0x7f6e'),
 _(u'\u0x8bb00x5f55'),
 _(u'\u0x8bbe0x7f6e'),
 _(u'\u0x65700x636e')]
DEVICE_MONITOR_CONTENT = [
 _(u'\u0x65700x636e:'),
 _(u'\u0x65700x636e:'),
 _(u'\u0x65700x636e:'),
 _(u'\u0x8bbe0x59070x72b60x6001'),
 _(u'\u0x8bbe0x59070x72b60x6001'),
 _(u'\u0x8bbe0x59070x53c20x6570:'),
 _(u'\u0x8bbe0x59070x53c20x6570:'),
 _(u'\u0x8bbe0x5907'),
 _(u'\u0x5b9e0x65f60x4e8b0x4ef6'),
 _(u'\u0x65b00x8bb00x5f55'),
 _(u'\u0x65ad0x5f00'),
 _(u'\u0x62a50x8b66'),
 _(u'\u0x961f0x52170x68c00x6d4b'),
 _(u'\u0x4e2d0x5fc30x670d0x52a10x68c00x6d4b'),
 _(u'\u0x8bb00x5f550x6570'),
 _(u'\u0x786c0x76d80x7a7a0x95f4')]
DEVICE_COMMAND_RETURN = {'0': (_(u'\u')), 
   '-1': (_(u'\u0x53d10x90010x59310x8d25')), 
   '-2': (_(u'\u0x8d850x65f6')), 
   '-3': (_(u'\u0x76840x7f130x5b580x4e0d0x8db3')), 
   '-4': (_(u'\u0x59310x8d25')), 
   '-5': (_(u'\u0x65700x636e0x957f0x5ea60x95190x8bef')), 
   '-6': (_(u'\u0x95190x8bef')), 
   '-7': (_(u'\u0x91cd0x590d')), 
   '-8': (_(u'\u0x5c1a0x672a0x63880x6743')), 
   '-9': (_(u'\u0x95190x8bef0xff0cCRC0x68210x9a8c0x59310x8d25')), 
   '-10': (_(u'\u0x95190x8bef0xff0cSDK0x65e00x6cd50x89e30x6790')), 
   '-11': (_(u'\u0x53c20x65700x95190x8bef')), 
   '-12': (_(u'\u0x62670x884c0x95190x8bef')), 
   '-13': (_(u'\u0x95190x8bef0xff0c0x6ca10x67090x6b640x547d0x4ee4')), 
   '-14': (_(u'\u0x5bc60x78010x95190x8bef')), 
   '-15': (_(u'\u0x4ef60x59310x8d25')), 
   '-16': (_(u'\u0x4ef60x59310x8d25')), 
   '-17': (_(u'\u0x4e0d0x5b580x5728')), 
   '-18': (_(u'\u0x7a7a0x95f40x5df20x6ee1')), 
   '-19': (_(u'\u0x548c0x51fa0x9519')), 
   '-20': (_(u'\u0x957f0x5ea60x95190x8bef')), 
   '-21': (_(u'\u0x8bbe0x7f6e0x5e730x53f00x53c20x6570')), 
   '-22': (_(u'\u0x5e730x53f00x4e0d0x4e000x81f4')), 
   '-23': (_(u'\u0x76840x56fa0x4ef60x72480x672c0x8fc70x65e7')), 
   '-24': (_(u'\u0x65870x4ef60x68070x8bc60x51fa0x9519')), 
   '-25': (_(u'\u0x540d0x95190x8bef')), 
   '-26': (_(u'\u0x6a210x677f0x957f0x5ea60x4e0d0x80fd0x4e3a0')), 
   '-27': (_(u'\u0x52300x63070x7eb90x6a210x677f0x5bf90x5e940x75280x6237')), 
   '-28': (_(u'\u0x65f60x95f40x6bb50x65e00x6cd50x51730x95e8')), 
   '-99': (_(u'\u0x95190x8bef')), 
   '-100': (_(u'\u0x67840x4e0d0x5b580x5728')), 
   '-101': (_(u'\u0x67840x4e2d0xff0c0x67610x4ef60x5b570x6bb50x4e0d0x5b580x5728')), 
   '-102': (_(u'\u0x603b0x65700x4e0d0x4e000x81f4')), 
   '-103': (_(u'\u0x63920x5e8f0x4e0d0x4e000x81f4')), 
   '-104': (_(u'\u0x4e8b0x4ef60x65700x636e0x95190x8bef')), 
   '-105': (_(u'\u0x65700x636e0x65f60xff0c0x65700x636e0x95190x8bef')), 
   '-106': (_(u'\u0x6ea20x51fa0xff0c0x4e0b0x53d10x65700x636e0x8d850x51fa4M')), 
   '-107': (_(u'\u0x88680x7ed30x67840x59310x8d25')), 
   '-108': (_(u'\uOPTIONS0x90090x9879')), 
   '-126': (_(u'\u0x4ef60x4e0d0x5b580x57280x62160x80050x52a00x8f7d0x59310x8d25')), 
   '-201': (_(u'\u0x4ef60x4e0d0x5b580x5728')), 
   '-202': (_(u'\u0x63a50x53e30x59310x8d25')), 
   '-203': (_(u'\u0x521d0x59cb0x53160x59310x8d25')), 
   '-206': (_(u'\u0x88ab0x53600x75280x62160x4e320x53e30x4e0d0x5b580x5728')), 
   '-301': (_(u'\uTCP/IP0x72480x672c0x59310x8d25')), 
   '-302': (_(u'\u0x7684TCP/IP0x72480x672c0x53f7')), 
   '-303': (_(u'\u0x534f0x8bae0x7c7b0x578b0x59310x8d25')), 
   '-304': (_(u'\uSOCKET')), 
   '-305': (_(u'\uCKET0x95190x8bef')), 
   '-306': (_(u'\uST0x95190x8bef')), 
   '-307': (_(u'\u0x8d850x65f6')), 
   '-1001': (_(u'\u0x65ad0x5f00')), 
   '-1002': (_(u'\u')), 
   '-1003': (_(u'\u0x672a0x542f0x52a8')), 
   '-1004': (_(u'\u0x7ebf0x7a0b0x66820x505c')), 
   '-1005': (_(u'\u0x59040x74060x547d0x4ee40x59310x8d25')), 
   '-1006': (_(u'\u0x547d0x4ee4')), 
   '-1007': (_(u'\u0x4e8b0x4ef60x8bb00x5f550x59310x8d25')), 
   '-1008': (_(u'\u0x7a7a0x95f40x5c0f0x4e8e1G')), 
   '-1100': (_(u'\u0x5f020x5e38! 0x8bf70x53d60x6d880x961f0x52170x540e0x91cd0x65b00x540c0x6b650x65700x636e')), 
   '1000': (_(u'\u0x65b00x8bb00x5f55')), 
   '1001': (_(u'\u0x8fde0x63a5'))}

def get_cmd_table(cmd_str):
    retstr = ''
    if cmd_str.startswith('userauthorize'):
        retstr = unicode(DEVICE_COMMAND_TABLE[1])
    elif cmd_str.startswith('user'):
        retstr = unicode(DEVICE_COMMAND_TABLE[0])
    elif cmd_str.startswith('holiday'):
        retstr = unicode(DEVICE_COMMAND_TABLE[2])
    elif cmd_str.startswith('timezone'):
        retstr = unicode(DEVICE_COMMAND_TABLE[3])
    elif cmd_str.startswith('firstcard'):
        retstr = unicode(DEVICE_COMMAND_TABLE[4])
    elif cmd_str.startswith('multimcard'):
        retstr = unicode(DEVICE_COMMAND_TABLE[5])
    elif cmd_str.startswith('transaction'):
        retstr = unicode(DEVICE_COMMAND_TABLE[6])
    elif cmd_str.startswith('inoutfun'):
        retstr = unicode(DEVICE_COMMAND_TABLE[7])
    elif cmd_str.startswith('templatev10'):
        retstr = unicode(DEVICE_COMMAND_TABLE[8])
    return retstr


def get_cmd_content(cmd_str):
    comm_param = cmd_str.strip()
    retstr = ''
    if comm_param.startswith(G_QUEUE_ERROR):
        retstr = unicode(DEVICE_MONITOR_CONTENT[12])
    if comm_param.startswith(G_DEVICE_CONNECT):
        retstr = unicode(DEVICE_MONITOR_CONTENT[7])
    elif comm_param.startswith(G_REAL_LOG):
        retstr = unicode(DEVICE_MONITOR_CONTENT[8])
    elif comm_param.startswith(G_DOWN_NEWLOG):
        retstr = unicode(DEVICE_MONITOR_CONTENT[9])
    elif comm_param.startswith(G_DEVICE_DISCONNECT):
        retstr = unicode(DEVICE_MONITOR_CONTENT[10])
    elif comm_param.startswith(G_DEVICE_UPDATE_DATA):
        strs = comm_param.split(' ', 3)
        table = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[0]) + get_cmd_table(table)
    elif comm_param.startswith(G_DEVICE_QUERY_DATA):
        strs = comm_param.split(' ', 4)
        table = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[1]) + get_cmd_table(table)
    elif comm_param.startswith(G_DEVICE_DELETE_DATA):
        strs = comm_param.split(' ', 3)
        table = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[2]) + get_cmd_table(table)
    elif comm_param.startswith(G_DATA_COUNT):
        strs = comm_param.split(' ', 3)
        table = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[14]) + get_cmd_table(table)
    elif comm_param.startswith(G_DEVICE_GET_DATA):
        retstr = unicode(DEVICE_MONITOR_CONTENT[3])
    elif comm_param.startswith(G_DEVICE_SET_DATA):
        strs = comm_param.split(' ', 5)
        retstr = unicode(DEVICE_MONITOR_CONTENT[4])
    elif comm_param.startswith(G_DEVICE_GET_OPTION):
        strs = comm_param.split(' ', 2)
        opt = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[5]) + opt
    elif comm_param.startswith(G_DEVICE_SET_OPTION):
        strs = comm_param.split(' ', 3)
        opt = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[6]) + opt
    elif comm_param.startswith(G_DEVICE_CANCEL_ALARM):
        strs = comm_param.split(' ')
        opt = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[7]) + opt
    elif comm_param.startswith(G_CHECK_SERVICE):
        retstr = unicode(DEVICE_MONITOR_CONTENT[13])
    elif comm_param.startswith(G_HARD_DISK_LESS_THAN_1G):
        retstr = unicode(DEVICE_MONITOR_CONTENT[15])
    return retstr


def check_service_commcenter(d_server):
    ret = d_server.get_from_dict('CENTER_RUNING')
    if ret:
        return True
    else:
        return False
    return


def set_door_connect(device, vcom, d_server):
    try:
        doorstate = d_server.get_from_dict(device.get_doorstate_cache_key())
    except Exception, e:
        printf('set_door_connect 1 error=%s' % e)

    if doorstate is None:
        doorstate = '0,0,0,0,0,0'
    doorstr = doorstate.split(',', 6)
    if vcom > 0:
        try:
            d_server.set_to_dict(device.get_doorstate_cache_key(), '%s,%s,%d,%s,%s,%s' % (doorstr[0], doorstr[1], vcom, doorstr[3], doorstr[4], doorstr[5]))
        except Exception, e:
            printf('set_door_connect 2 error=%s' % e)

    else:
        try:
            d_server.set_to_dict(device.get_doorstate_cache_key(), '0,0,0,0,0,0')
        except Exception, e:
            printf('set_door_connect 3 error=%s' % e)

    return


def checkdevice_and_savecache(d_server, devobj, cursor):
    global g_cursor
    from mysite.iclock.models import Device
    last_activity_time = d_server.get_from_dict(devobj.get_last_activity())
    now_t = time.mktime(datetime.datetime.now().timetuple())
    if last_activity_time:
        if float(last_activity_time) > now_t:
            d_server.set_to_dict(devobj.get_last_activity(), '1')
        elif now_t - float(last_activity_time) > 120:
            from django.db import IntegrityError
            try:
                d_server.set_to_dict(devobj.get_last_activity(), str(now_t))
            except IntegrityError:
                connection._commit()
            except Exception, e:
                connection.close()
                g_cursor = connection.cursor()
                connection._commit()
                print_exc()

    else:
        d_server.set_to_dict(devobj.get_last_activity(), '1')
    return


def appendrtlog(d_server, cursor, dev, rtlog):
    global g_dev_door_dict
    global g_emp_dict
    global g_reader_dict
    devobj = dev.devobj
    try:
        rtlogs = rtlog.split('\r\n')
        operator = threadlocals.get_current_user()
        if not cursor:
            cursor = connection.cursor()
        try:
            for rtlog in rtlogs:
                if not rtlog:
                    continue
                str = rtlog.split(',', 7)
                if len(str) < 7:
                    return 0
                if strtoint(str[4]) == DOOR_STATE_ID:
                    door_state = d_server.get_from_dict(devobj.get_doorstate_cache_key())
                    if door_state:
                        val = door_state.split(',', 6)
                        if str[1] != val[0] or str[2] != val[1] or str[6] != val[3] or str[3] != val[4] or str[5] != val[5]:
                            now_t = time.mktime(datetime.datetime.now().timetuple())
                            d_server.set_to_dict('GET_DOORSTATE_AGAIN', now_t)
                    d_server.set_to_dict(devobj.get_doorstate_cache_key(), '%s,%s,1,%s,%s,%s' % (str[1], str[2], str[6], str[3], str[5]))
                    return
                door_dict = None
                try:
                    update_device = d_server.get_from_dict('UPDATE_DEVICE_DOOR')
                    if not g_dev_door_dict or update_device:
                        g_dev_door_dict = get_dev_door()
                        d_server.set_to_dict('UPDATE_DEVICE_DOOR', 0)
                    if not (strtoint(str[4]) in [INOUT_SEVER, INOUT_SHORT, OPEN_AUXOUT, CLOSE_AUXOUT, START_FIRE_DOOR, 
                     CLOSE_ELEVTOR_FUN, OPEN_ELEVTOR_FUN] or strtoint(str[4]) == EVENT_LINKCONTROL and strtoint(str[6]) in [INOUT_SEVER, INOUT_SHORT]):
                        if strtoint(str[4]) == EVENT_LINKCONTROL and int(str[1]) > 0:
                            key = '%s_6_%s' % (devobj.id, str[1])
                        else:
                            key = '%s_%s' % (devobj.id, str[3])
                        door_dict = g_dev_door_dict.has_key(key) and g_dev_door_dict[key] or None
                        str[3] = door_dict and door_dict['door_id'] or 0
                except:
                    print_exc()

                try:
                    update_linkage_acc = d_server.get_from_dict('UPDATE_LINKAGE_COMM')
                    if update_linkage_acc != 2:
                        d_server.set_to_dict('LINKAGEIO_DICT_ACC', get_linkageio_to_dict_for_id())
                        d_server.set_to_dict('UPDATE_LINKAGE_COMM', 2)
                    update_linkage_vid = d_server.get_from_dict('UPDATE_LINKAGE_VID_RECORD')
                    if update_linkage_vid != 2:
                        d_server.set_to_dict('LINKAGEIO_DICT', get_linkageio_to_dict())
                        d_server.set_to_dict('UPDATE_LINKAGE_VID_RECORD', 2)
                    if 'mysite.video' in settings.INSTALLED_APPS:
                        get_videoip_channelno_to_dict(d_server)
                    log = '%s,%s,%s,%s,%s,%s,%s,%d' % (str[0], str[1], str[3], str[4], str[5], str[6], str[2], devobj and devobj.id or 0)
                    d_server.rpush_to_dict('MONITOR_RT', log)
                except:
                    print_exc()

                if strtoint(str[4]) >= ALARM_ID_START and strtoint(str[4]) < ALARM_ID_END:
                    d_server.rpush_to_dict('ALARM_RT', log)
                event_sql = parse_event_to_sql(str, operator, door_dict, devobj, d_server, cursor)
                if 'mysite.video' in settings.INSTALLED_APPS and event_sql:
                    from mysite.video.process_vid_comm import video_linkageio_record_or_capture, check_video_linkageio_event
                    video_linkage = check_video_linkageio_event(d_server, str, door_dict, dev, g_reader_dict)
                    if video_linkage:
                        need_return_log_info = True
                    else:
                        need_return_log_info = False
                    event_info = save_event_log(event_sql[0], [event_sql[1]], cursor, need_return_event_info=need_return_log_info)
                    if event_info:
                        video_linkageio_record_or_capture(d_server, cursor, cfg, str, door_dict, dev, event_info, video_linkage)
                elif event_sql:
                    save_event_log(event_sql[0], [event_sql[1]], cursor)
                if door_dict and door_dict['is_att'] and strtoint(str[4]) in EVENT_LOG_AS_ATT:
                    try:
                        emp_monitor = d_server.get_from_dict('EMP_MONITOR')
                        if not g_emp_dict or emp_monitor:
                            g_emp_dict = get_emp(cursor)
                            d_server.set_to_dict('EMP_MONITOR', 0)
                        emp_pin = int(str[1]) and format_pin(str[1]) or '--'
                        if g_emp_dict and emp_pin in g_emp_dict:
                            sync_to_att(None, [(devobj.sn, g_emp_dict[emp_pin][4], str[0])], cursor)
                    except:
                        pass

        finally:
            pass

    except:
        print_exc()

    return


def save_event_logParse error at or near `LOAD_CONST' instruction at offset 0


def parse_event_to_sql(split_log, operator, door_dict, devobj=None, d_server=None, cursor=None):
    global g_area_dict
    global g_aux_dict
    global g_dept_dict
    global g_emp_dict
    global g_reader_dict
    from mysite.iaccess.models.acclinkageio import ACTIONTYPE_CHOICES
    from django.utils.translation import ugettext as _u
    dev_id = 0
    dev_name = ''
    dev_sn = ''
    door_id = 0
    door_name = ''
    reader_name = ''
    firstname = ''
    lastname = ''
    dept = ''
    area = ''
    if devobj:
        try:
            dev_id = devobj.id
            dev_name_change = d_server.get_from_dict('DEVICE_ALIAS_CHANGE_%s' % dev_id)
            if dev_name_change:
                devobj.alias = dev_name_change
                d_server.delete_dict('DEVICE_ALIAS_CHANGE_%s' % dev_id)
            dev_name = unicode(devobj.alias)
            dev_sn = devobj.sn
        except:
            print_exc()

    if door_dict:
        try:
            door_id = door_dict['door_id']
            door_name = unicode(door_dict['door_name'])
        except:
            print_exc()

    reader_monitor = d_server.get_from_dict('READER_MONITOR_SAVE')
    if not g_reader_dict or reader_monitor:
        g_reader_dict = get_reader()
        d_server.set_to_dict('READER_MONITOR_SAVE', 0)
    aux_monitor = d_server.get_from_dict('AUX_MONITOR_SAVE')
    if not g_aux_dict or aux_monitor:
        g_aux_dict = get_aux()
        d_server.set_to_dict('AUX_MONITOR_SAVE', 0)
    update_linkage = d_server.get_from_dict('UPDATE_LINKAGE_COMM')
    if update_linkage != 2:
        d_server.set_to_dict('LINKAGEIO_DICT_ACC', get_linkageio_to_dict_for_id())
        d_server.set_to_dict('UPDATE_LINKAGE_COMM', 2)
    emp_monitor = d_server.get_from_dict('EMP_MONITOR')
    if not g_emp_dict or emp_monitor:
        g_emp_dict = get_emp(cursor)
        d_server.set_to_dict('EMP_MONITOR', 0)
    area_monitor = d_server.get_from_dict('AREA_MONITOR')
    if not g_area_dict or area_monitor:
        g_area_dict = get_area(cursor)
        d_server.set_to_dict('AREA_MONITOR', 0)
    dept_monitor = d_server.get_from_dict('DEPT_MONITOR')
    if not g_dept_dict or dept_monitor:
        g_dept_dict = get_dept(cursor)
        d_server.set_to_dict('DEPT_MONITOR', 0)
    state = len(split_log[5]) > 0 and split_log[5] or 0
    reader_key = '%s_%s' % (door_id, state)
    if g_reader_dict.has_key(reader_key):
        reader_name = g_reader_dict[reader_key][0]
    if not reader_name:
        if state in (0, '0'):
            reader_name = unicode(_(u'\u'))
        elif state in (1, '1'):
            reader_name = unicode(_(u'\u'))
    if g_area_dict.has_key(dev_id):
        area = g_area_dict[dev_id]
    event_type = strtoint(split_log[4])
    if event_type == EVENT_LINKCONTROL:
        pin = '--'
    else:
        pin = int(split_log[1]) and format_pin(split_log[1]) or '--'
    card = ''
    if g_emp_dict.has_key(pin):
        try:
            emp_info = g_emp_dict[pin]
            firstname = emp_info[0]
            lastname = emp_info[1]
            dept_id = emp_info[2]
            card = str(emp_info[7]) + ' ' + str(emp_info[6])
            if g_dept_dict.has_key(dept_id):
                dept = g_dept_dict[dept_id]
        except:
            print_exc()

    transaction_struct = {}
    transaction_struct['change_operator'] = None
    transaction_struct['change_time'] = None
    transaction_struct['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    transaction_struct['delete_operator'] = None
    transaction_struct['delete_time'] = None
    transaction_struct['time'] = strtodatetime(split_log[0])
    transaction_struct['card_no'] = split_log[2] and int(split_log[2]) or '--'
    transaction_struct['pin'] = pin
    transaction_struct['state_name'] = reader_name
    transaction_struct['event_type'] = len(split_log[4]) > 0 and split_log[4] or 0
    transaction_struct['status'] = 0
    transaction_struct['verified'] = 200
    transaction_struct['event_point_type'] = EVENT_POINT_TYPE_NONE
    transaction_struct['event_point_id'] = -1
    transaction_struct['event_point_name'] = ''
    transaction_struct['trigger_opt'] = -1
    transaction_struct['description'] = ''
    transaction_struct['device_id'] = dev_id
    transaction_struct['device_name'] = dev_name
    transaction_struct['device_sn'] = dev_sn
    transaction_struct['state'] = state
    transaction_struct['video_ip'] = None
    transaction_struct['channel_no'] = None
    transaction_struct['firstname'] = firstname
    transaction_struct['lastname'] = lastname
    transaction_struct['dept'] = dept
    transaction_struct['area'] = area
    if card != ' ' and card != '':
        transaction_struct['card_no'] = card
    if event_type in [INOUT_SEVER, INOUT_SHORT]:
        transaction_struct['event_point_type'] = EVENT_POINT_TYPE_AUX
        aux_in_ret = get_aux_name(dev_id, int(split_log[3]) or 0, 0, g_aux_dict)
        transaction_struct['event_point_id'] = aux_in_ret and aux_in_ret[0] or -1
        transaction_struct['event_point_name'] = aux_in_ret and aux_in_ret[1] or ''
    elif event_type in [OPEN_AUXOUT, CLOSE_AUXOUT]:
        transaction_struct['event_point_type'] = EVENT_POINT_TYPE_AUX
        aux_out_ret = get_aux_name(dev_id, int(split_log[3]) or 0, 1, g_aux_dict)
        transaction_struct['event_point_id'] = aux_out_ret and aux_out_ret[0] or -1
        transaction_struct['event_point_name'] = aux_out_ret and aux_out_ret[1] or ''
    elif event_type == CANCEL_ALARM:
        cancel_alarm_type = int(split_log[6])
        transaction_struct['event_point_type'] = EVENT_POINT_TYPE_DOOR
        transaction_struct['event_point_id'] = door_id
        transaction_struct['event_point_name'] = door_name
        if cancel_alarm_type in [TAMPER_ALARM, TIME_OUT_ALARM, DURESS_FP_ALARM, DURESS_PWD_ALARM, OPENED_FORCEFULLY_ALARM]:
            transaction_struct['description'] = unicode(dict(CANCEL_ALARM_TYPE)[cancel_alarm_type])
    elif event_type == EVENT_LINKCONTROL:
        if strtoint(split_log[6]) in [INOUT_SEVER, INOUT_SHORT]:
            transaction_struct['event_point_type'] = EVENT_POINT_TYPE_AUX
            aux_in_ret = get_aux_name(dev_id, int(split_log[3]) or 0, 0, g_aux_dict)
            if aux_in_ret:
                transaction_struct['event_point_id'] = aux_in_ret and aux_in_ret[0] or -1
                transaction_struct['event_point_name'] = aux_in_ret and aux_in_ret[1] or ''
            else:
                return
        else:
            transaction_struct['event_point_type'] = EVENT_POINT_TYPE_DOOR
            transaction_struct['event_point_id'] = door_id
            transaction_struct['event_point_name'] = door_name
        try:
            linkage_id = len(split_log[2]) > 0 and split_log[2] or 0
            linkageio_obj_dict = d_server.get_from_dict('LINKAGEIO_DICT_ACC')
            if linkageio_obj_dict:
                acc_linkage = linkageio_obj_dict[int(linkage_id)]
            else:
                acc_linkage = None
        except:
            acc_linkage = None
        else:
            transaction_struct['card_no'] = '--'
            trigger_opt = len(split_log[6]) > 0 and split_log[6] or 0
            transaction_struct['trigger_opt'] = trigger_opt
            transaction_struct['description'] = acc_linkage and '%s:%s\r\n%s:%s\r\n%s:%s' % (unicode(_(u'\u0x67610x4ef6')), unicode(dict(EVENT_CHOICES)[int(trigger_opt)]), unicode(_(u'\u0x70b90x57300x5740')), _u(acc_linkage.get_out_address()), unicode(_(u'\u0x7c7b0x578b')), unicode(dict(ACTIONTYPE_CHOICES)[acc_linkage.action_type])) or ''
    elif event_type in [DEVICE_STARTED, CANCEL_ALARM]:
        pass
    else:
        transaction_struct['verified'] = len(split_log[6]) > 0 and split_log[6] or 0
        transaction_struct['event_point_type'] = EVENT_POINT_TYPE_DOOR
        transaction_struct['event_point_id'] = door_id
        transaction_struct['event_point_name'] = door_name
    if 'mysite.video' in settings.INSTALLED_APPS:
        from mysite.video.process_vid_comm import get_videoip_channelno
        get_videoip_channelno_to_dict(d_server)
        video_channel_list = get_videoip_channelno(door_id, split_log[5], d_server)
        if video_channel_list and video_channel_list[0]:
            if video_channel_list[0][6] not in [DEVICE_ZKVISION_CAMERA, DEVICE_DAHUA_VIDEO]:
                transaction_struct['video_ip'] = video_channel_list[0][0]
                transaction_struct['channel_no'] = video_channel_list[0][1]
    sql = 'INSERT INTO acc_monitor_log(change_operator,change_time,create_operator,create_time,delete_operator,delete_time,status,time,pin,card_no,            device_id,device_sn,device_name,event_point_type,event_point_id,event_point_name,verified,state_name,event_type,trigger_opt,description,            state,video_ip,channel_no,firstname,lastname,dept,area) values(NULL,NULL,NULL,%s,NULL,NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
    params = (
     transaction_struct['create_time'],
     transaction_struct['status'],
     transaction_struct['time'],
     transaction_struct['pin'],
     transaction_struct['card_no'],
     transaction_struct['device_id'],
     transaction_struct['device_sn'],
     transaction_struct['device_name'],
     transaction_struct['event_point_type'],
     transaction_struct['event_point_id'],
     transaction_struct['event_point_name'],
     transaction_struct['verified'],
     transaction_struct['state_name'],
     transaction_struct['event_type'],
     transaction_struct['trigger_opt'],
     transaction_struct['description'],
     transaction_struct['state'],
     transaction_struct['video_ip'],
     transaction_struct['channel_no'],
     transaction_struct['firstname'],
     transaction_struct['lastname'],
     transaction_struct['dept'],
     transaction_struct['area'])
    return [
     sql, params]


def process_event_log(dev, qret, cursor=None, d_server=None):
    global g_dev_door_dict
    global g_emp_dict
    if qret['result'] >= 0:
        if not cursor:
            cursor = connection.cursor()
        try:
            printf('--------begin-time=%s' % dev, True)
            operator = threadlocals.get_current_user()
            acc_params_list = []
            acc_insert_sql = ''
            dev_db_event_list = []
            dev_event_min_time = ''
            tmp_events_dict = {}
            dev_sn = dev.sn
            dev_id = dev.id
            att_events_dict = {}
            att_min_time = ''
            insert_count = 0
            has_key_count = 0
            for i in range(1, qret['result'] + 1, 1):
                log = qret['data'][i]
                str = log.split(',', 7)
                door_dict = None
                try:
                    update_device = d_server.get_from_dict('UPDATE_DEVICE_DOOR')
                    if not g_dev_door_dict or update_device:
                        g_dev_door_dict = get_dev_door()
                        d_server.set_to_dict('UPDATE_DEVICE_DOOR', 0)
                    if not (strtoint(str[4]) in [INOUT_SEVER, INOUT_SHORT, OPEN_AUXOUT, CLOSE_AUXOUT] or strtoint(str[4]) == EVENT_LINKCONTROL and strtoint(str[2]) in [INOUT_SEVER, INOUT_SHORT]):
                        if strtoint(str[4]) == EVENT_LINKCONTROL and int(str[1]) > 0:
                            key = '%s_6_%s' % (dev_id, str[1])
                        else:
                            key = '%s_%s' % (dev_id, str[3])
                        door_dict = g_dev_door_dict.has_key(key) and g_dev_door_dict[key] or None
                        str[3] = door_dict and door_dict['door_id'] or 0
                except:
                    print_exc()

                try:
                    restr = '%s,%s,%s,%s,%s,%s,%s' % (FmtTTime(str[6]), str[1], str[0], str[3], str[4], str[5], str[2])
                    restr = restr.split(',', 7)
                except:
                    print_exc()
                    continue

                cur_event_time = restr[0]
                if not dev_event_min_time or dev_event_min_time > cur_event_time:
                    dev_event_min_time = cur_event_time
                sql_and_param = parse_event_to_sql(restr, operator, door_dict, dev, d_server, cursor)
                if sql_and_param:
                    sql = sql_and_param[0]
                    param = sql_and_param[1]
                    key = '%s_%s_%s_%s_%s_%s_%s_%s_%s_%s' % (param[2], param[3], param[4], param[5], param[11], param[16], param[13], param[8], param[9], param[14])
                    if not tmp_events_dict.has_key(key):
                        tmp_events_dict[key] = param
                        insert_count = insert_count + 1
                    else:
                        has_key_count = has_key_count + 1
                    if not acc_insert_sql:
                        acc_insert_sql = sql
                if door_dict and door_dict['is_att'] and strtoint(restr[4]) in EVENT_LOG_AS_ATT:
                    emp_monitor = d_server.get_from_dict('EMP_MONITOR')
                    if not g_emp_dict or emp_monitor:
                        g_emp_dict = get_emp(cursor)
                        d_server.set_to_dict('EMP_MONITOR', 0)
                    if g_emp_dict and sql_and_param:
                        emp_pin = param[3]
                        att_time = param[2]
                        key = '%s_%s' % (emp_pin, att_time)
                        if emp_pin in g_emp_dict and key not in att_events_dict:
                            try:
                                if not att_min_time or att_min_time > cur_event_time:
                                    att_min_time = cur_event_time
                                att_events_dict[key] = (
                                 dev_sn, g_emp_dict[emp_pin][4], att_time)
                            except:
                                pass

            printf('====devSn=%s , insert_count=%s' % (dev_sn, insert_count), True)
            printf('====devSn=%s , has_key_count=%s' % (dev_sn, has_key_count), True)
            time.sleep(3)
            if dev_event_min_time:
                printf('-----parse-finish-time=%s' % dev, True)
                try:
                    sql = "select time,pin,card_no,device_id,verified,state,event_type,event_point_type,event_point_id,trigger_opt from acc_monitor_log where device_id=%s and time>='%s'" % (dev_id, dev_event_min_time)
                    cursor.execute(sql)
                    rets = cursor.fetchall()
                    for ret in rets:
                        key = '%s_%s_%s_%s_%s_%s_%s_%s_%s_%s' % (ret[0], ret[1], ret[2], ret[3], ret[4], ret[5], ret[6], ret[7], ret[8], ret[9])
                        dev_db_event_list.append(key)

                except:
                    pass
                else:
                    for key in tmp_events_dict.iterkeys():
                        try:
                            if key not in dev_db_event_list:
                                acc_params_list.append(tmp_events_dict[key])
                            if len(acc_params_list) == 3000:
                                save_event_log(acc_insert_sql, acc_params_list, cursor)
                                acc_params_list = []
                                time.sleep(3)
                        except:
                            pass

                    try:
                        if acc_params_list:
                            save_event_log(acc_insert_sql, acc_params_list, cursor)
                        if att_events_dict:
                            sync_to_att(att_min_time, att_events_dict, cursor)
                    except:
                        pass

        except Exception, e:
            printf('---2-----process_event_log e=%s' % e, True)

        dev_db_event_list = None
        acc_params_list = None
        acc_insert_sql = None
        att_events_dict = None
        tmp_events_dict = None
        printf('--------finish-time=%s' % dev, True)
        return {'ret': (qret['result']), 'retdata': ''}
    else:
        return {'ret': (-1), 'retdata': ''}
        return


def sync_to_att(att_event_min_time, att_events, cursor=None):
    if not cursor:
        cursor = connection.cursor()
    try:
        try:
            att_insert_sql = "insert into checkinout(sn_name, userid, checktime, checktype, verifycode) values(%s, %s, %s, 'I', 2)"
            if att_event_min_time:
                db_att_events = {}
                att_event_list = []
                att_sql = "select badgenumber, checktime from checkinout c, userinfo u where c.userid=u.userid and checktime>'%s'" % att_event_min_time
                cursor.execute(att_sql)
                att_rets = cursor.fetchall()
                for ret in att_rets:
                    key = '%s_%s' % (ret[0], ret[1])
                    db_att_events[key] = 1

                for key in att_events.iterkeys():
                    if key not in db_att_events:
                        att_event_list.append(att_events[key])
                    if len(att_event_list) == 3000:
                        save_event_log(att_insert_sql, att_event_list, cursor)
                        att_event_list = []
                        time.sleep(3)

                if att_event_list:
                    save_event_log(att_insert_sql, att_event_list, cursor)
            elif str(type(att_events)) == "<type 'dict'>":
                for value in att_events.itervalues():
                    save_event_log(att_insert_sql, [value], cursor)

            elif str(type(att_events)) == "<type 'list'>":
                for value in att_events:
                    save_event_log(att_insert_sql, [value], cursor)

        except Exception, e:
            pass

    finally:
        db_att_events = None
        att_event_list = None

    return


def get_new_log(dev_comm, dev_obj, d_server):
    try:
        ret = dev_comm.get_transaction(newlog=True)
    except Exception, e:
        print_exc()
        printf('%s *****reconnect****get_transaction error: %s' % (dev_obj.alias.encode('gb18030'), e), True)

    try:
        process_event_log(dev_obj, ret, cursor=None, d_server=d_server)
    except Exception, e:
        print_exc()
        printf('reconnect %s after check_and_down_log e: %s' % (dev_obj.alias.encode('gb18030'), e), True)

    return


class GetNewLogThread(threading.Thread):

    def __init__(self, dev, d_server):
        threading.Thread.__init__(self)
        self.dev_obj = dev.devobj
        self.d_server = d_server
        self.dev_comm = dev.comm
        self.ret = None
        try:
            self.d_server.set_to_dict(dev.comm_tmp, {'SN': (self.dev_obj), 'CmdContent': G_DOWN_NEWLOG, 'CmdReturn': 0})
            self.ret = self.dev_comm.get_transaction(newlog=True)
            self.d_server.set_to_dict(dev.comm_tmp, {'SN': (self.dev_obj), 'CmdContent': G_DOWN_NEWLOG, 'CmdReturn': (self.ret['result'])})
        except Exception, e:
            print_exc()
            printf('%s *****reconnect****get_transaction error: %s' % (dev_obj.alias.encode('gb18030'), e), True)

        return

    def run(self):
        global g_get_new_log_thread_cur_count
        global g_get_new_log_thread_lock
        while True:
            g_get_new_log_thread_lock.acquire()
            if g_get_new_log_thread_cur_count < GET_NEW_LOG_THREAD_MAX_COUNT:
                g_get_new_log_thread_cur_count += 1
                g_get_new_log_thread_lock.release()
                break
            g_get_new_log_thread_lock.release()
            time.sleep(10)

        try:
            if self.ret:
                process_event_log(self.dev_obj, self.ret, cursor=None, d_server=self.d_server)
        except Exception, e:
            print_exc()
            printf('reconnect %s after check_and_down_log e: %s' % (dev_obj.alias.encode('gb18030'), e), True)

        g_get_new_log_thread_lock.acquire()
        g_get_new_log_thread_cur_count -= 1
        g_get_new_log_thread_lock.release()
        return


def process_comm_task(devs, comm_param, cursor, d_server):
    from mysite.iclock.models import Transaction
    try:
        ret = 0
        devcomm = devs.comm
        if comm_param.startswith(G_DEVICE_CONNECT):
            qret = devcomm.connect()
            if devcomm.hcommpro > 0:
                check_acpanel_args(devs, devs.comm)
            return {'ret': (qret['result']), 'retdata': (qret['data'])}
        if comm_param.startswith(G_DEVICE_DISCONNECT):
            return devcomm.disconnect()
        if comm_param.startswith(G_DEVICE_UPDATE_DATA):
            strs = comm_param.split(' ', 3)
            table = strs[2]
            if len(table) > 0:
                data = comm_param[comm_param.find(table) + len(table) + 1:]
                data = re.sub(u'\\', '\r', data)
                qret = devcomm.update_data(table.strip(), data.strip(), '')
            return {'ret': (qret['result']), 'retdata': (qret['data'])}
        if comm_param.startswith(G_DEVICE_QUERY_DATA):
            if comm_param.find('transaction') > 0:
                from mysite.iaccess.models import AccRTMonitor
                if comm_param.find('NewRecord') > 0:
                    qret = devcomm.get_transaction(True)
                else:
                    qret = devcomm.get_transaction(False)
                return process_event_log(devs.devobj, qret, cursor, d_server)
            else:
                str = ''
                strs = comm_param.split(' ', 4)
                table = strs[2]
                field_names = strs[3]
                if len(table) > 0:
                    filter = comm_param[comm_param.find(field_names) + len(field_names) + 1:]
                    qret = devcomm.query_data(table.strip(), field_names.strip(), filter.strip(), '')
                if comm_param.find('user') > 0:
                    from process_comm_data import process_user_info
                    return process_user_info(qret, cursor)
                if comm_param.find('templatev10') > 0:
                    from process_comm_data import process_template_info
                    return process_template_info(qret, cursor)
                return {'ret': (qret['result']), 'retdata': (qret['data'])}
        elif comm_param.startswith(G_DEVICE_DELETE_DATA):
            strs = comm_param.split(' ', 3)
            table = strs[2]
            if len(table) > 0:
                qret = devcomm.delete_data(table, comm_param[comm_param.find(table) + len(table) + 1:])
            return {'ret': (qret['result']), 'retdata': (qret['data'])}
        if comm_param.startswith(G_DEVICE_GET_DATA):
            return
        if comm_param.startswith(G_DATA_COUNT):
            strs = comm_param.split(' ', 3)
            table = strs[2]
            qret = devcomm.Get_Data_Count(table)
            return {'ret': (qret['result']), 'retdata': (qret['data'])}
        if comm_param.startswith(G_DEVICE_SET_DATA):
            try:
                comm_param = comm_param.strip()
                strs = comm_param.split(' ', 5)
                door = int(strs[2])
                index = int(strs[3])
                state = int(strs[4])
                qret = devcomm.controldevice(door, index, state)
                return {'ret': (qret['result']), 'retdata': (qret['data'])}
            except:
                print_exc()
                printf('-------process_comm_task G_DEVICE_SET_DATA error return devs.devobj=%s' % devs.devobj, True)
                return

        elif comm_param.startswith(G_DEVICE_CONTROL_NO):
            try:
                comm_param = comm_param.strip()
                strs = comm_param.split(' ', 5)
                door = int(strs[2])
                state = int(strs[3])
                qret = devcomm.control_normal_open(door, state)
                return {'ret': (qret['result']), 'retdata': (qret['data'])}
            except:
                print_exc()
                printf('-------process_comm_task G_DEVICE_CONTROL_NO error return devs.devobj=%s' % devs.devobj, True)
                return

        elif comm_param.startswith(G_DEVICE_CANCEL_ALARM):
            try:
                door = comm_param.strip().split(' ')[2]
                qret = devcomm.cancel_alarm(door)
                return {'ret': (qret['result']), 'retdata': (qret['data'])}
            except:
                print_exc()
                printf('-------process_comm_task G_DEVICE_CANCEL_ALARM error return devs.devobj=%s' % devs.devobj, True)
                return

        else:
            if comm_param.startswith(G_DEVICE_GET_OPTION):
                strs = comm_param.split(' ', 2)
                opt = strs[2]
                if len(opt) > 0:
                    optitem = re.sub(u'\t', ',', opt)
                    qret = devcomm.get_options(optitem.strip())
                return {'ret': (qret['result']), 'retdata': (qret['data'])}
            else:
                if comm_param.startswith(G_DEVICE_SET_OPTION):
                    strs = comm_param.split(' ', 3)
                    opt = strs[2]
                    if len(opt) > 0:
                        optitem = re.sub(u'\t', ',', opt).strip()
                        qret = devcomm.set_options(optitem.strip())
                    return {'ret': (qret['result']), 'retdata': (qret['data'])}
                return {'ret': 0, 'retdata': 'unknown command'}
    except:
        print_exc()

    return


class DeviceMonitor(object):

    def __init__(self):
        self.id = 0
        self.comm_tmp = ''
        self.new_cln = ''
        self.devobj = None
        self.comm = None
        self.try_failed_time = 0
        self.try_connect_count = 0
        self.try_connect_delay = 0
        self.no_command_count = 0
        return


def process_general_cmd(dev, d_server, q_server, acmd=None, cursor=None, push_on=None):
    if not cursor:
        cursor = connection.cursor()
    cmd_ret = False
    cnt = int(d_server.get_from_dict(dev.cnk) or 0)
    if not acmd and cnt == 0:
        dev.no_command_count += 1
        if dev.no_command_count < TRY_USE_DISK_FILE_CMD_COUNT:
            return
        dev.no_command_count = 0
    try:
        if not acmd:
            acmd = q_server.getrpop_from_file(dev.new_cln)
        if type(acmd) == type('str') and acmd.startswith(G_QUEUE_ERROR):
            cmd_ret = True
            try:
                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': G_QUEUE_ERROR, 'CmdReturn': (-1100)})
            except:
                print_exc()

    except Exception, e:
        printf('process_general_cmd error=%s' % e, True)
        print_exc()

    try:
        if acmd and type(acmd) == type('str'):
            acmd = pickle.loads(acmd)
    except:
        printf('---pickle loads acmd error dev=%s' % dev, True)
        acmd = None

    if acmd is not None:
        try:
            from mysite.iclock.models.model_device import MAX_COMMAND_TIMEOUT_SECOND
            try:
                cmdline = str(acmd.CmdContent)
            except:
                cmdline = str(acmd.CmdContent.encode('gb18030'))

            is_immed = False
            if acmd.CmdImmediately:
                is_immed = True
                now_t = datetime.datetime.now()
                if (now_t - acmd.CmdCommitTime).seconds > MAX_COMMAND_TIMEOUT_SECOND:
                    acmd.CmdReturn = -1005
                    acmd.CmdReturnContent = u'%s' % _(u'\u0x8d850x65f6')
                    acmd.CmdTransTime = datetime.datetime.now()
                    acmd.save()
                    return False
        except Exception, e:
            printf('check cmd error = %s' % e, True)
            print_exc()
        else:
            if cmdline != None:
                try:
                    cmd_ret = True
                    ret = {'ret': (-1005)}
                    try:
                        d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': (acmd.CmdContent), 'CmdReturn': 0})
                        ret = process_comm_task(dev, cmdline, cursor, d_server)
                    except Exception, e:
                        printf('%s *********process_comm_task error =%s' % (dev.devobj.alias.encode('gb18030'), e), True)
                        print_exc()

                    if ret['ret'] >= 0:
                        if not is_immed:
                            q_server.rpop_from_file(dev.new_cln)
                            cmdCount = int(q_server.llen_file(dev.new_cln))
                            if cmdCount < 0:
                                cmdCount = int(q_server.llen_file(dev.new_cln))
                            d_server.set_to_dict(dev.cnk, '%d' % cmdCount)
                        acmd.CmdReturn = ret['ret']
                        acmd.CmdReturnContent = ret['retdata']
                        acmd.CmdTransTime = datetime.datetime.now()
                        acmd.save()
                        checkdevice_and_savecache(d_server, dev.devobj, cursor)
                        dev.try_failed_time = 0
                    elif acmd.CmdImmediately == 1:
                        printf('--- delcmd3--in process_general_cmd function', True)
                        acmd.CmdReturn = ret['ret']
                        acmd.CmdReturnContent = ret['retdata']
                        acmd.CmdTransTime = datetime.datetime.now()
                        acmd.save()
                    if ret['ret'] == -18:
                        printf('----ret=-18,delete all new commands--dev=%s' % dev.devobj.alias.encode('gb18030'), True)
                        d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': (acmd.CmdContent), 'CmdReturn': (-18)})
                        return -18
                    cmd_ret = False
                    d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': (acmd.CmdContent), 'CmdReturn': (ret['ret'])})
                    time.sleep(3)
                    if ret['ret'] == -1 or ret['ret'] == -2:
                        dev.try_failed_time += 1
                        if dev.try_failed_time > MAX_TRY_COMM_TIME:
                            try:
                                dev.comm.disconnect()
                                dev.try_connect_delay = time.mktime(datetime.datetime.now().timetuple())
                                set_door_connect(dev.devobj, 0, d_server)
                                dev.try_failed_time = 0
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                            except:
                                print_exc()

                    if ret['ret'] < -10000 and ret['ret'] > -20000:
                        dev.comm.disconnect()
                        d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                        dev.comm.connect()
                except Exception, e:
                    printf('process_comm_task failed.....dev=%s,e=%s' % (dev.devobj.alias.encode('gb18030'), e), True)
                    print_exc()
                    cmd_ret = False

    return cmd_ret


def add_devs_dict(devs_dict, devobj, d_server):
    try:
        devs_dict[devobj.id] = DeviceMonitor()
        devs_dict[devobj.id].id = devobj.id
        devs_dict[devobj.id].sn = devobj.sn
        devs_dict[devobj.id].new_cln = devobj.new_command_list_name()
        devs_dict[devobj.id].comm_tmp = devobj.command_temp_list_name()
        devs_dict[devobj.id].cnk = devobj.command_count_key()
        devs_dict[devobj.id].devobj = devobj
        devs_dict[devobj.id].comm = TDevComm(devobj.getcomminfo())
        devs_dict[devobj.id].try_connect_count = 0
        devs_dict[devobj.id].enabled = devobj.enabled
        devs_dict[devobj.id].comminfo = devobj.getdevinfo()
        if devs_dict[devobj.id].enabled:
            devs_dict[devobj.id].comm.connect()
            if devs_dict[devobj.id].comm.hcommpro > 0:
                d_server.set_to_dict(devs_dict[devobj.id].comm_tmp, {'SN': (devs_dict[devobj.id].devobj), 'CmdContent': 'CONNECT', 'CmdReturn': (devs_dict[devobj.id].comm.hcommpro)})
                devs_dict[devobj.id].try_connect_delay = time.mktime(datetime.datetime.now().timetuple())
                set_door_connect(devs_dict[devobj.id].devobj, 1, d_server)
                check_acpanel_args(devs_dict[devobj.id], devs_dict[devobj.id].comm)
                if devs_dict[devobj.id].devobj.sync_time:
                    devs_dict[devobj.id].devobj.set_time(False)
                try:
                    GetNewLogThread(devs_dict[devobj.id], d_server).start()
                except:
                    pass

            else:
                set_door_connect(devs_dict[devobj.id].devobj, 0, d_server)
                devs_dict[devobj.id].try_connect_delay = 0
        else:
            set_door_connect(devs_dict[devobj.id].devobj, 0, d_server)
            devs_dict[devobj.id].try_connect_delay = 0
            devs_dict[devobj.id].comm.hcommpro = -1002
    except Exception, e:
        printf('15. add_devs_dict id=%d error =%s' % (devobj.id, e))

    return


def check_and_down_log(dev, d_server, cursor, down_log_time):
    from mysite.iaccess.models import AccRTMonitor
    try:
        now_hour = datetime.datetime.now().hour
        num = smart_str(down_log_time).split(',')
        if str(now_hour) not in num:
            return
        last_time = d_server.get_from_dict('DOWN_LOG_TIME_%s' % dev.id)
        if last_time == None:
            d_server.set_to_dict('DOWN_LOG_TIME_%s' % dev.id, str(now_hour))
        elif str(last_time) == str(now_hour):
            return
        d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DOWN_NEWLOG', 'CmdReturn': 1000})
    except Exception, e:
        printf('22-1. %s check_and_down_log e: %s' % (dev.devobj.alias.encode('gb18030'), e), True)
        print_exc()

    try:
        delete_log()
    except Exception, e:
        write_log('22-1-add. check_and_down_log delete_log e: %s' % e)

    try:
        ret = dev.comm.get_transaction(newlog=True)
        d_server.set_to_dict('DOWN_LOG_TIME_%s' % dev.id, str(now_hour))
    except Exception, e:
        printf('%s *********get_transaction error: %s' % (dev.devobj.alias.encode('gb18030'), e), True)

    try:
        process_event_log(dev.devobj, ret, cursor, d_server)
    except Exception, e:
        printf('23-2. %s after check_and_down_log e: %s' % (dev.devobj.alias.encode('gb18030'), e), True)

    return ret['result']


def check_server_stop(procename, pid, devs, d_server):
    try:
        ret = False
        proce_server_key = '%s_SERVER' % procename
        proce_stop = d_server.get_from_dict(proce_server_key)
        if proce_stop == 'STOP':
            d_server.lpop_from_dict(proce_server_key)
            printf('%s servers return ' % procename, True)
            for devsn in devs:
                dev = devs[devsn]
                try:
                    d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                except:
                    print_exc()

            ret = True
    except Exception, e:
        print_exc()
        printf('stop server error=%s' % e)

    return ret


def wait_com_pause(d_server, com_port, timeout):
    channel_key = 'COM_%d_CHANNELS' % com_port
    com_key = 'COM_%d_PID' % com_port
    com_pid = d_server.get_from_dict(com_key)
    if com_pid is None:
        return True
    else:
        d_server.set_to_dict(channel_key, '%d' % PROCESS_WAIT_PAUSE)
        for i in range(0, timeout, 1):
            com_status = d_server.get_from_dict(channel_key)
            if com_status is None:
                time.sleep(1)
                continue
            try:
                ret = int(com_status)
            except:
                ret = 0

            if int(ret) > PROCESS_WAIT_PAUSE:
                channel_timeout_key = 'COM_%d_CHANNELS_TIMEOUT' % com_port
                d_server.delete_dict(channel_timeout_key)
                return True
            time.sleep(1)

        return False


def wait_thread_pause(d_server, thread, timeout):
    channel_key = 'DEVICE_%d_CHANNELS' % thread
    d_server.set_to_dict(channel_key, '%d' % THREAD_WAIT_PAUSE)
    for i in range(0, timeout):
        thread_status = d_server.get_from_dict(channel_key)
        if thread_status is None:
            time.sleep(1)
            continue
        try:
            ret = int(thread_status)
        except:
            ret = 0

        if int(ret) > THREAD_WAIT_PAUSE:
            channel_timeout_key = 'DEVICE_%d_CHANNELS_TIMEOUT' % thread
            d_server.delete_dict(channel_timeout_key)
            return True
        time.sleep(1)

    return False


def set_comm_run(d_server, com_port):
    channel_key = 'COM_%d_CHANNELS' % com_port
    channel_timeout_key = 'COM_%d_CHANNELS_TIMEOUT' % com_port
    d_server.delete_dict(channel_key)
    d_server.delete_dict(channel_timeout_key)
    return


def set_thread_run(d_server, thread):
    thread_key = 'DEVICE_%d_CHANNELS' % thread
    thread_timeout_key = 'DEVICE_%d_CHANNELS_TIMEOUT' % thread
    d_server.delete_dict(thread_key)
    d_server.delete_dict(thread_timeout_key)
    return


def net_task_process(devobjs, devcount, procename=''):
    from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485
    d_server = start_dict_server()
    q_server = queqe_server()
    try:
        tt = d_server.get_from_dict('CENTER_RUNING')
        pid = os.getpid()
        q_server.set_to_file('PROCESS_%s_PID' % procename, str(pid))
        d_server.rpush_to_dict(CENTER_PROCE_LIST, '%s' % procename)
        devs_dict = {}
        path = '%s/_fqueue/' % settings.APP_HOME
        for devobj in devobjs:
            try:
                add_devs_dict(devs_dict, devobj, d_server)
                d_server.delete_dict(devs_dict[devobj.id].comm_tmp)
                d_server.set_to_dict(devs_dict[devobj.id].comm_tmp, {'SN': devobj, 'CmdContent': 'CONNECT', 'CmdReturn': (devs_dict[devobj.id].comm.hcommpro)})
                d_server.set_to_dict(ACCDEVICE_DISABLED % devobj.id, not devobj.enabled)
            except Exception, e:
                printf('add_devs_dict %d error=%s' % (devobj.id, e), True)

            if check_server_stop(procename, pid, devs_dict, d_server):
                return 0

        printf('%s :current process: %d' % (procename, os.getpid()))
        cfg_delay = dict4ini.DictIni(os.getcwd() + '/appconfig.ini', values={'iaccess': {'realtime_delay': 1000.0}})
        realtime_delay = cfg_delay.iaccess.realtime_delay / 1000.0
        cfg = dict4ini.DictIni(os.getcwd() + '/appconfig.ini', values={'iaccess': {'down_newlog': 0, 'realtime_forever': 1}})
        realtime_forever = int(cfg.iaccess.realtime_forever)
        down_log_time = cfg.iaccess.down_newlog
        while 1:
            cursor = g_cursor
            try:
                proce_server_key = '%s_SERVER' % procename
                proce_stop = d_server.get_from_dict(proce_server_key)
                if proce_stop == 'STOP':
                    try:
                        d_server.delete_dict(proce_server_key)
                        printf('%s servers return ' % procename, True)
                        for devsn in devs_dict:
                            dev = devs_dict[devsn]
                            try:
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                            except:
                                print_exc()

                        d_server.close()
                        q_server.connection.disconnect()
                    except Exception, e:
                        print_exc()
                        printf('stop server error=%s' % e, True)

                    return 0
                pid_t = time.mktime(datetime.datetime.now().timetuple())
                d_server.set_to_dict(CENTER_PROCE_HEART % procename, str(pid_t))
                if tt != d_server.get_from_dict('CENTER_RUNING'):
                    try:
                        printf('%s servers id error return ' % procename, True)
                        for devsn in devs_dict:
                            dev = devs_dict[devsn]
                            try:
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                            except:
                                print_exc()

                        d_server.close()
                        q_server.connection.disconnect()
                    except Exception, e:
                        print_exc()
                        printf('stop server error=%s' % e, True)

                    return 0
                process_realtime_devinfo = d_server.get_from_dict(procename) or []
                process_current_devinfo = []
                del_dev = {}
                thread_dev = {}
                for devsn in devs_dict:
                    try:
                        thread_dev = devs_dict[devsn].comminfo
                        process_current_devinfo.append(thread_dev)
                    except Exception, e:
                        printf('process_current_devinfo append device error=%s' % e, True)

                    if not thread_dev:
                        continue
                    if thread_dev not in process_realtime_devinfo:
                        try:
                            devs_dict[devsn].comm.disconnect()
                            del_dev[devsn] = devs_dict[devsn]
                        except Exception, e:
                            print_exc()
                            printf('16. %s delete device error id=%d error=%s' % (procename, thread_dev['id'], e), True)

                try:
                    for del_d in del_dev:
                        del devs_dict[del_d]

                except:
                    printf('procecache delete device error', True)

                for process_dev in process_realtime_devinfo:
                    if process_dev not in process_current_devinfo:
                        try:
                            cdev = Device.objects.filter(id=process_dev['id'])
                            if cdev:
                                add_devs_dict(devs_dict, cdev[0], d_server)
                                d_server.delete_dict(devs_dict[cdev[0].id].comm_tmp)
                                d_server.set_to_dict(devs_dict[cdev[0].id].comm_tmp, {'SN': (cdev[0]), 'CmdContent': 'CONNECT', 'CmdReturn': (devs_dict[cdev[0].id].comm.hcommpro)})
                                d_server.set_to_dict(ACCDEVICE_DISABLED % cdev[0].id, not cdev[0].enabled)
                        except Exception, e:
                            print_exc()
                            printf('add device error e=' % e, True)
                            continue

                if procename.find('COM') >= 0:
                    try:
                        if devs_dict.__len__() == 0:
                            channel_key = '%s_CHANNELS' % procename
                            channel_timeout_key = '%s_CHANNELS_TIMEOUT' % procename
                            channel_now = time.mktime(datetime.datetime.now().timetuple())
                            channel_timeout = d_server.get_from_dict(channel_timeout_key)
                            if channel_timeout:
                                try:
                                    channel_timeout = int(channel_timeout)
                                except:
                                    channel_timeout = 0
                                else:
                                    if channel_now - int(channel_timeout) > PAUSE_TIMEOUT:
                                        d_server.delete_dict(channel_key)
                                        d_server.delete_dict(channel_timeout_key)
                            channel_status = d_server.get_from_dict(channel_key)
                            if channel_status is None:
                                channel_status = 0
                            try:
                                channel_status = int(channel_status)
                            except:
                                channel_status = 0
                            else:
                                if channel_status == PROCESS_WAIT_PAUSE:
                                    d_server.set_to_dict(channel_key, '%d' % PROCESS_PAUSE)
                                    d_server.set_to_dict(channel_timeout_key, '%d' % int(channel_now))
                                if channel_status > PROCESS_NORMAL:
                                    d_server.set_to_dict(CENTER_PROCE_HEART % procename, time.mktime(datetime.datetime.now().timetuple()))
                                    continue
                    except Exception, e:
                        printf('proccache device empty return error=%s' % e, True)

                for devsn in devs_dict:
                    proce_server_key = '%s_SERVER' % procename
                    proce_stop = d_server.get_from_dict(proce_server_key)
                    if proce_stop == 'STOP':
                        try:
                            d_server.lpop_from_dict(proce_server_key)
                            printf('%s servers return ' % procename, True)
                            for devsn in devs_dict:
                                dev = devs_dict[devsn]
                                try:
                                    d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                                except:
                                    print_exc()

                            d_server.close()
                            q_server.connection.disconnect()
                        except Exception, e:
                            print_exc()
                            printf('stop server error=%s' % e, True)

                        return 0
                    if tt != d_server.get_from_dict('CENTER_RUNING'):
                        try:
                            printf('%s servers id error return ' % procename, True)
                            for devsn in devs_dict:
                                dev = devs_dict[devsn]
                                try:
                                    d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                                except:
                                    print_exc()

                            d_server.close()
                            q_server.connection.disconnect()
                        except Exception, e:
                            print_exc()
                            printf('stop server error=%s' % e, True)

                        return 0
                    dev = devs_dict[devsn]
                    cnt = d_server.get_from_dict(dev.cnk)
                    if cnt is None:
                        cmdcount = q_server.llen_file(dev.devobj.new_command_list_name())
                        d_server.set_to_dict(dev.cnk, '%d' % int(cmdcount))
                    try:
                        if procename.find('COM') >= 0:
                            channel_key = '%s_CHANNELS' % procename
                            channel_timeout_key = '%s_CHANNELS_TIMEOUT' % procename
                        else:
                            channel_key = 'DEVICE_%s_CHANNELS' % dev.id
                            channel_timeout_key = 'DEVICE_%d_CHANNELS_TIMEOUT' % dev.id
                        channel_now = time.mktime(datetime.datetime.now().timetuple())
                        channel_timeout = d_server.get_from_dict(channel_timeout_key)
                        if channel_timeout:
                            try:
                                channel_timeout = int(channel_timeout)
                            except:
                                channel_timeout = 0
                            else:
                                if channel_now - int(channel_timeout) > PAUSE_TIMEOUT:
                                    d_server.delete_dict(channel_key)
                                    d_server.delete_dict(channel_timeout_key)
                        channel_status = d_server.get_from_dict(channel_key)
                        if channel_status is None:
                            channel_status = 0
                        try:
                            channel_status = int(channel_status)
                        except:
                            channel_status = 0

                        if procename.find('COM') >= 0:
                            com_upgrade_dis_devid = d_server.get_from_dict('COM_UPGRADE_DIS_DEVID_%d' % dev.devobj.id)
                            if com_upgrade_dis_devid:
                                if dev.comm.hcommpro > 0:
                                    dev.comm.disconnect()
                                    d_server.delete_dict('COM_UPGRADE_DIS_DEVID_%d' % dev.devobj.id)
                        if channel_status == PROCESS_WAIT_PAUSE:
                            if procename.find('COM') < 0:
                                if dev.comm.hcommpro > 0:
                                    dev.comm.disconnect()
                            d_server.set_to_dict(channel_key, '%d' % PROCESS_PAUSE)
                            d_server.set_to_dict(channel_timeout_key, '%d' % int(channel_now))
                        if int(channel_status) > PROCESS_NORMAL:
                            d_server.set_to_dict(CENTER_PROCE_HEART % procename, time.mktime(datetime.datetime.now().timetuple()))
                            d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'CONNECT', 'CmdReturn': (-1004)})
                            set_door_connect(dev.devobj, 0, d_server)
                            continue
                    except Exception, e:
                        print_exc()
                        printf('thread pause error=%s' % e, True)

                    try:
                        try:
                            check_disabled = d_server.get_from_dict(ACCDEVICE_DISABLED % dev.devobj.id)
                        except Exception, e:
                            printf('check_disabled error=%s' % e, True)

                        if check_disabled:
                            try:
                                dev.enabled = 0
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISABLED', 'CmdReturn': (-1002)})
                            except Exception, e:
                                printf('check_disabled 2 error=%s' % e, True)
                            else:
                                if dev.comm.hcommpro > 0:
                                    dev.comm.disconnect()
                                try:
                                    set_door_connect(dev.devobj, 0, d_server)
                                except Exception, e:
                                    printf('check_disabled 3 error=%s' % e, True)
                                else:
                                    now_t = time.mktime(datetime.datetime.now().timetuple())
                                    if now_t - dev.try_connect_delay < MAX_INTERVAL_CONNTECT_TIME:
                                        dev.try_connect_delay = now_t - MAX_INTERVAL_CONNTECT_TIME
                                    try:
                                        d_server.set_to_dict(CENTER_PROCE_HEART % procename, time.mktime(datetime.datetime.now().timetuple()))
                                    except Exception, e:
                                        printf('check_disabled 4 error=%s' % e, True)
                                    else:
                                        continue
                        else:
                            dev.enabled = 1
                    except Exception, e:
                        print_exc()
                        printf('4. check_dev_enabled error=%s' % e, True)

                    try:
                        immed_cmd_dict = d_server.get_from_dict('TEMP_CMD')
                        ret = False
                        if immed_cmd_dict:
                            for dev_id in devs_dict.keys():
                                if dev_id in immed_cmd_dict.keys():
                                    dev_obj = devs_dict[dev_id]
                                    devcmd_list = immed_cmd_dict.get(dev_obj.id)
                                    timeout = 0
                                    while True:
                                        temp_cmd_lock = d_server.get_from_dict('TEMP_CMD_LOCK')
                                        if temp_cmd_lock:
                                            timeout += 1
                                            if timeout > 300:
                                                break
                                            time.sleep(1)
                                            continue
                                        else:
                                            d_server.set_to_dict('TEMP_CMD_LOCK', 1)
                                            delete_tempcmd(dev_obj, devcmd_list, d_server)
                                            d_server.set_to_dict('TEMP_CMD_LOCK', 0)
                                            break

                                    if dev_obj.comm.hcommpro <= 0 or not dev_obj.enabled:
                                        temp_hcommpro = dev_obj.comm.hcommpro
                                        if not dev_obj.enabled:
                                            temp_hcommpro = -1002
                                        elif temp_hcommpro == 0:
                                            temp_hcommpro = -1001
                                        if devcmd_list:
                                            for acmd in devcmd_list:
                                                acmd.CmdReturn = temp_hcommpro
                                                acmd.CmdTransTime = datetime.datetime.now()
                                                acmd.save()

                                    elif devcmd_list:
                                        for acmd in devcmd_list:
                                            ret = process_general_cmd(dev_obj, d_server, q_server, acmd, cursor=cursor, push_on=False)

                                    continue

                    except Exception, e:
                        printf('-!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!-process temp_cmd e=%s' % e, True)

                    if dev.comm.hcommpro <= 0:
                        now_t = time.mktime(datetime.datetime.now().timetuple())
                        if now_t - dev.try_connect_delay > MAX_INTERVAL_CONNTECT_TIME:
                            try:
                                dev.try_connect_count += 1
                                dev.try_connect_delay = time.mktime(datetime.datetime.now().timetuple())
                                dev.comm.disconnect()
                                dev.comm.connect()
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'CONNECT', 'CmdReturn': (dev.comm.hcommpro)})
                            except Exception, e:
                                printf('5.0 %s -- try connect device error=%s' % (dev.devobj.alias.encode('gb18030'), e))
                                print_exc()
                            else:
                                if dev.comm.hcommpro > 0:
                                    d_server.set_to_dict(devs_dict[dev.devobj.id].comm_tmp, {'SN': (devs_dict[dev.devobj.id].devobj), 'CmdContent': 'CONNECT', 'CmdReturn': (devs_dict[dev.devobj.id].comm.hcommpro)})
                                    try:
                                        dev.try_connect_count = 0
                                        set_door_connect(dev.devobj, 1, d_server)
                                        if dev.devobj.sync_time:
                                            dev.devobj.set_time(False)
                                        check_acpanel_args(dev, dev.comm)
                                        GetNewLogThread(dev, d_server).start()
                                    except:
                                        print_exc()

                                else:
                                    try:
                                        set_door_connect(dev.devobj, 0, d_server)
                                        if dev.try_connect_count > MAX_CONNECT_COUNT:
                                            printf('6. %s -- set dev disabled' % dev.devobj.alias.encode('gb18030'), True)
                                            dev.try_connect_count = 0
                                            dev.devobj.set_dev_disabled(d_server)
                                    except:
                                        print_exc()

                        continue
                    try:
                        ret = process_general_cmd(dev, d_server, q_server, acmd=None, cursor=cursor, push_on=False)
                        d_server.set_to_dict(CENTER_PROCE_HEART % procename, time.mktime(datetime.datetime.now().timetuple()))
                        if ret == True:
                            pass
                        elif dev.comm.hcommpro <= 0:
                            continue
                        elif ret == -18:
                            continue
                    except Exception, e:
                        print_exc()
                        printf('process_general_cmd error=%s' % e, True)

                    currunt_time = datetime.datetime.now()
                    rtmonitor_stamp = d_server.get_from_dict('RTMONITOR_STAMP')
                    try:
                        if realtime_forever or rtmonitor_stamp and (currunt_time - rtmonitor_stamp).seconds <= 60:
                            rtlog = dev.comm.get_rtlog()
                            if is_comm_io_error(rtlog['result']):
                                printf('7. %s -- get rtlog return failed result=%d' % (dev.devobj.alias.encode('gb18030'), rtlog['result']), True)
                                printf('commstatus 4 REAL_LOG--CmdReturn=%d' % rtlog['result'], True)
                                d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'REAL_LOG', 'CmdReturn': (rtlog['result'])})
                                dev.try_failed_time += 1
                                if dev.try_failed_time > MAX_TRY_COMM_TIME:
                                    try:
                                        dev.comm.disconnect()
                                        dev.try_connect_delay = time.mktime(datetime.datetime.now().timetuple())
                                        set_door_connect(dev.devobj, 0, d_server)
                                        dev.try_failed_time = 0
                                        set_door_connect(dev.devobj, 0, d_server)
                                        d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'DISCONNECT', 'CmdReturn': (-1001)})
                                    except:
                                        print_exc()

                                continue
                            else:
                                try:
                                    d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': 'REAL_LOG', 'CmdReturn': 1})
                                    checkdevice_and_savecache(d_server, dev.devobj, cursor)
                                except:
                                    print_exc()
                                else:
                                    if rtlog['result'] > 0:
                                        appendrtlog(d_server, cursor, dev, rtlog['data'])
                                    dev.try_failed_time = 0
                        else:
                            d_server.set_to_dict(dev.comm_tmp, {'SN': (dev.devobj), 'CmdContent': '', 'CmdReturn': 0})
                    except Exception, e:
                        print_exc()
                        printf('control realtime monitoring error=%s' % e, True)

                    try:
                        ret_log = check_and_down_log(dev, d_server, cursor, down_log_time)
                        if ret_log > 0:
                            printf('check_and_down_log end .... ret_log=%d' % ret_log, True)
                            pid_t = time.mktime(datetime.datetime.now().timetuple())
                            d_server.set_to_dict(CENTER_PROCE_HEART % procename, str(pid_t))
                    except Exception, e:
                        print_exc()
                        printf('check_and_down_log error=%s' % e, True)

                time.sleep(realtime_delay)
            except Exception, e:
                print_exc()

        return 0
    finally:
        if d_server:
            d_server.close()
        if q_server:
            q_server.connection.disconnect()

    return


class TThreadMonitor(object):

    def __init__(self, func, args):
        self.func = func
        self.args = args
        return

    def __call__(self):
        apply(self.func, self.args)
        return


class TDevDataCommCenter(object):

    def __init__(self, d_server, q_server):
        cfg = dict4ini.DictIni(os.getcwd() + '/appconfig.ini', values={'iaccess': {'max_thread': 5}})
        self.max_thread = cfg.iaccess.max_thread
        self.d_server = d_server
        self.q_server = q_server
        self.pool = Pool(processes=self.max_thread)
        self.comport_set = {}
        self.NetDev = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER).filter(comm_type=COMMU_MODE_PULL_TCPIP)
        self.ComDev = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER).filter(comm_type=COMMU_MODE_PULL_RS485)
        self.net_dev_set = self.set_thread_dev(self.NetDev)
        printf('self.net_dev_set=%s' % self.net_dev_set, True)
        self.killRsagent()
        self.pid = os.getpid()
        printf('CommCenter main pid=%d' % self.pid, True)
        self.q_server.set_to_file(CENTER_MAIN_PID, '%d' % self.pid)
        for i in range(0, self.max_thread):
            devs = self.net_dev_set[i]
            tName = 'Net%d' % i
            self.d_server.set_to_dict(CENTER_PROCE_HEART % tName, time.mktime(datetime.datetime.now().timetuple()))
            self.d_server.delete_dict(tName)
            for dev in devs:
                dev_info = dev.getdevinfo()
                try:
                    self.d_server.rpush_to_dict(tName, dev_info)
                except:
                    print_exc()

            self.pool.apply_async(net_task_process, [devs, len(devs), tName])

        self.comports = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
        for comport in self.comports:
            comdevs = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485, com_port=comport['com_port'])
            tName = 'COM_%d' % comport['com_port']
            devs = []
            self.d_server.delete_dict(tName)
            for comdev in comdevs:
                devs.append(comdev)
                comdev_info = comdev.getdevinfo()
                self.d_server.rpush_to_dict(tName, comdev_info)

            p = Process(target=net_task_process, args=(devs, len(devs), tName))
            self.d_server.set_to_dict('%s_PID' % tName, '%d' % p._parent_pid)
            p.start()

        return

    def killRsagent(self):
        return os.system('taskkill /im plrscagent.* /f')

    def set_thread_dev(self, devset):
        devs = []
        for i in range(0, self.max_thread):
            devs.append([])

        for i in range(0, len(devset)):
            devs[i % self.max_thread].append(devset[i])

        return devs

    def refushcomport(self):
        from mysite.iclock.models.model_device import Device, DEVICE_AS_CONTROLLER, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        self.comports = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
        self.NetDev = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER).filter(comm_type=COMMU_MODE_PULL_TCPIP)
        return

    def delete_device(self, devinfo):
        from mysite.iclock.models.model_device import Device, DEVICE_AS_CONTROLLER, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        if devinfo['comm_type'] == COMMU_MODE_PULL_TCPIP:
            for i in range(0, len(self.net_dev_set)):
                for net_dev in self.net_dev_set[i]:
                    if net_dev.id == devinfo['id']:
                        self.net_dev_set[i].remove(net_dev)
                        tName = 'Net%d' % i
                        self.d_server.delete_dict(tName)
                        for dev in self.net_dev_set[i]:
                            self.d_server.rpush_to_dict(tName, dev.getdevinfo())

        elif devinfo['comm_type'] == COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485, com_port=devinfo['com_port'].split('COM')[1])
            tName = devinfo['com_port'][0:3] + '_' + devinfo['com_port'][3:]
            self.d_server.delete_dict(tName)
            for dev in comdevs:
                self.d_server.rpush_to_dict(tName, dev.getdevinfo())

        self.d_server.save()
        return

    def edit_device(self, dev):
        from mysite.iclock.models.model_device import Device, DEVICE_AS_CONTROLLER, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        if dev.comm_type == COMMU_MODE_PULL_TCPIP:
            for i in range(0, len(self.net_dev_set)):
                for net_dev in net_dev_set[i]:
                    if net_dev.id == dev.id:
                        ii = net_dev_set[i].index(net_dev)
                        net_dev_set[i][ii] = dev
                        tName = 'Net%d' % i
                        self.d_server.delete_dict(tName)
                        dev = []
                        for dev0 in self.net_dev_set[i]:
                            try:
                                dev = Device.objects.filter(id=dev0.id)
                                self.d_server.rpush_to_dict(tName, dev[0].getdevinfo())
                            except:
                                printf('edit_device error')

        elif dev.comm_type == COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485, com_port=dev.com_port)
            tName = 'COM_%d' % dev.com_port
            devs = []
            self.d_server.delete_dict(tName)
            for comdev in comdevs:
                devs.append(comdev)
                self.d_server.rpush_to_dict(tName, comdev.getdevinfo())

        self.d_server.save()
        return

    def adddevice(self, dev):
        from mysite.iclock.models.model_device import Device, DEVICE_AS_CONTROLLER, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        self.NetDev = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER).filter(comm_type=COMMU_MODE_PULL_TCPIP)
        if dev.comm_type == COMMU_MODE_PULL_TCPIP:
            new_dev = True
            for dev_set in self.net_dev_set:
                if dev in dev_set:
                    new_dev = False

            if new_dev:
                for i in range(0, self.max_thread):
                    if len(self.net_dev_set[i]) <= len(self.NetDev) / self.max_thread:
                        self.net_dev_set[i].append(dev)
                        tName = 'Net%d' % i
                        self.d_server.rpush_to_dict(tName, dev.getdevinfo())
                        break

        elif dev.comm_type == COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485, com_port=dev.com_port)
            tName = 'COM_%d' % dev.com_port
            devs = []
            self.d_server.delete_dict(tName)
            for comdev in comdevs:
                devs.append(comdev)
                self.d_server.rpush_to_dict(tName, comdev.getdevinfo())

            com_list = []
            for v in self.comports:
                com_list.append(v.values()[0])

            if dev.com_port not in com_list:
                self.comports = Device.objects.filter(device_type__in=DEVICE_AS_CONTROLLER, comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
                p = Process(target=net_task_process, args=(devs, len(devs), tName))
                self.d_server.set_to_dict('%s_PID' % tName, '%d' % p._parent_pid)
                p.start()
        self.d_server.save()
        return


def killall_pid(q_server):
    try:
        main_pid = q_server.get_from_file(CENTER_MAIN_PID)
        process_info = os.popen('tasklist |findstr "%s"' % main_pid).read()
        if 'python.exe' in process_info.lower():
            os.system('taskkill /PID %s /F /T' % main_pid)
    except:
        print_exc()

    return


def start_clear_data_timer():
    values = {'clear_report': 0}
    cfg = dict4ini.DictIni(os.getcwd() + '/appconfig.ini', values={'iaccess': values})
    clear_report = cfg.iaccess.clear_report
    if clear_report:
        from clear_data import ClearDataTimer
        ClearDataTimer().start()
    return


def rundatacommcenter():
    global g_devcenter
    try:
        try:
            from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485
            from process_mails import SendEmail
            printf('1.--rundatacenter--sevice pid=%d' % os.getpid(), True)
            try:
                SendEmail().start()
                start_clear_data_timer()
                delete_log()
            except Exception, e:
                pass

            q_server = queqe_server()
            d_server = start_dict_server()
            killall_pid(q_server)
            try:
                path = '%s/_fqueue/' % settings.APP_HOME
                d_server.clear_dict()
                tt = ('{0:%Y-%m-%d %X}').format(datetime.datetime.now())
                d_server.set_to_dict('CENTER_RUNING', tt)
                g_devcenter = TDevDataCommCenter(d_server, q_server)
            except Exception, e:
                print_exc()

            while True:
                try:
                    len = d_server.llen_dict(DEVOPT)
                    if len > 0:
                        try:
                            acmd = d_server.lpop_from_dict(DEVOPT)
                        except Exception, e:
                            print_exc()
                            printf('------datacommcenter main process new-edit-del device error=%s' % e, True)
                        else:
                            if acmd is None:
                                continue
                            try:
                                devinfo = pickle.loads(acmd)
                            except:
                                devinfo = None
                            else:
                                if devinfo is not None:
                                    try:
                                        op_type = int(devinfo['operatstate'])
                                        if op_type == OPERAT_ADD:
                                            dev = Device.objects.filter(id=devinfo['id'])
                                            if dev:
                                                g_devcenter.adddevice(dev[0])
                                            else:
                                                d_server.rpush_to_dict(DEVOPT, devinfo)
                                                time.sleep(10)
                                        elif op_type == OPERAT_EDIT:
                                            g_devcenter.delete_device(devinfo)
                                            dev = Device.objects.filter(id=devinfo['id'])
                                            if dev:
                                                g_devcenter.adddevice(dev[0])
                                            else:
                                                d_server.rpush_to_dict(DEVOPT, devinfo)
                                                time.sleep(10)
                                        elif op_type == OPERAT_DEL:
                                            g_devcenter.delete_device(devinfo)
                                    except Exception, e:
                                        print_exc()
                                        printf('device opreater error=%s' % e, True)

                                continue
                    else:
                        time.sleep(5)
                    if d_server.llen_dict('MONITOR_RT') > MAX_RTLOG:
                        d_server.set_to_dict('MONITOR_RT_DEL', True)
                        d_server.delete_dict('MONITOR_RT')
                        d_server.delete_dict('ALARM_RT')
                    pid_set = d_server.get_from_dict(CENTER_PROCE_LIST) or []
                    for p in pid_set:
                        pid_time = d_server.get_from_dict(CENTER_PROCE_HEART % p)
                        if pid_time:
                            now_t = time.mktime(datetime.datetime.now().timetuple())
                            if now_t - float(pid_time) > 7200:
                                printf('PID die**********', True)
                                try:
                                    d_server.close()
                                    q_server.connection.disconnect()
                                    killall_pid(q_server)
                                    printf('****kill pid finished', True)
                                except:
                                    printf('-----killall pid error', True)
                                else:
                                    break

                except Exception, e:
                    print_exc()
                    printf('datacommcenter while True error=%s' % e, True)
                    continue

                time.sleep(1)

        except Exception, e:
            print_exc()
            printf('-----while true error=%s' % e, True)

    finally:
        if d_server:
            d_server.close()
        q_server.connection.disconnect()

    return


if __name__ == '__main__':
    print 'start at:', ctime()
    rundatacommcenter()
    print 'finish'
return