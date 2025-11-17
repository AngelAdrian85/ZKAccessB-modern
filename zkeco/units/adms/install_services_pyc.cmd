sc create ZKECOMemCachedService binPath= "%CD%\memcached.exe -p 11211 -m 192 -d runservice" DisplayName= "memcached server" start= auto depend= TCPIP
@net start ZKECOMemCachedService

python ServiceInstantMsg.pyc --startup auto install
@net start ZKECOInstantMessage

python ServiceBackupDB.pyc --startup auto install
@net start ZKECOBackupDB

python ServiceADMS.pyc --startup auto install
@net start ZKECOWEBService

python ServiceDataCommCenter.pyc --startup auto install
@net start ZKECODataCommCenterService

python ServiceWriteData.pyc --startup auto install
@net start ZKECOWriteDataService

python ServiceZksaas_adms.pyc --startup auto install
@net start ZKECOZksaasAdmsService

python ServiceAutoCalculate.pyc --startup auto install
@net start ZKECOAutoCalculateService

