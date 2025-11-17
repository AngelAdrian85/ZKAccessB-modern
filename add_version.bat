echo Windows Registry Editor Version 5.00>addVersion.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\ZKECOWEBService] >>addVersion.reg
echo "Version"="5.3" >>addVersion.reg
reg import addVersion.reg