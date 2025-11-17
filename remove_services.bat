call init.bat 

@net stop ZKECODataCommCenterService
python ServiceDataCommCenter.pyc remove

@net stop ZKECOWEBService
python ServiceADMS.pyc  remove

@net stop ZKECOInstantMessage
python ServiceInstantMsg.pyc remove

@net stop ZKECOBackupDB
python ServiceBackupDB.pyc remove

@net stop ZKECOWriteDataService
python ServiceWriteData.pyc remove

@net stop ZKECOMemCachedService 
sc delete ZKECOMemCachedService

@net stop ZKECOMYSQL
sc delete ZKECOMYSQL

