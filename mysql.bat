set path="%SystemRoot%\system32"
echo installing mysql database server ...
cd mysql
"%CD%\bin\mysqld-nt.exe" --install ZKECOMYSQL --defaults-file="%CD%\my.ini"
cd ../