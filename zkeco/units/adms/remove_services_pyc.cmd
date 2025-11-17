@net stop ZKECOWEBService
python ServiceADMS.pyc  remove

@net stop ZKECODataCommCenterService
python ServiceDataCommCenter.pyc remove

@net stop ZKECOInstantMessage
python ServiceInstantMsg.pyc remove

@net stop ZKECOBackupDB
python ServiceBackupDB.pyc remove

@net stop ZKECOWriteDataService
python ServiceWriteData.pyc remove

@net stop ZKECOZksaasAdmsService
python ServiceZksaas_adms.pyc remove

@net stop ZKECOAutoCalculateService
python ServiceAutoCalculate.pyc remove

@net stop memcached
sc delete memcached

