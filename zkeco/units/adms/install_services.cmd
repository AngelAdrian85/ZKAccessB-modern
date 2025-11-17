sc create memcached binPath= "%CD%\memcached.exe -p 11211 -l 127.0.0.1 -m 192 -d runservice" DisplayName= "memcached server" start= auto depend= TCPIP
python ServiceADMS.py  --startup auto install
python ServiceDataCommCenter.py --startup auto install
python ServiceBackupDB.py --startup auto install
pause
