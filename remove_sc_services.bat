
@net stop ZKECODataCommCenterService
sc delete ZKECODataCommCenterService

@net stop ZKECOWEBService
sc delete ZKECOWEBService

@net stop ZKECOInstantMessage
sc delete ZKECOInstantMessage

@net stop ZKECOBackupDB
sc delete ZKECOBackupDB

@net stop ZKECOWriteDataService
sc delete ZKECOWriteDataService

@net stop ZKECOMemCachedService 
sc delete ZKECOMemCachedService

@net stop memcached 
sc delete memcached 

@net stop ZKECOMYSQL
sc delete ZKECOMYSQL

