@net stop iClockADMSService
python ServiceADMS.py  remove

@net stop iClockDataCommCenterService
python ServiceDataCommCenter.py remove

@net stop worktableInstantMessage
python ServiceInstantMsg.py remove

@net stop ZKECOBackupDB
python ServiceBackupDB.py remove

@net stop iClockWriteDataService
python ServiceWriteData.py remove
pause

