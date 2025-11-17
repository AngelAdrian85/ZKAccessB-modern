call init.bat 

@net stop memcached
sc delete memcached

sc create ZKECOMemCachedService binPath= "%CD%\memcached.exe -p 11211 -m 512 -d runservice" DisplayName= "ZKECOMemCached Service" start= auto depend= TCPIP
@net start ZKECOMemCachedService



python ServiceBackupDB.pyc --startup auto install

python ServiceADMS.pyc --startup auto install
