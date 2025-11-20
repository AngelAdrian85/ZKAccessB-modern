Set-Location 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\zkeco_modern'
$env:INCLUDE_LEGACY='1'
$env:DJANGO_SETTINGS_MODULE='zkeco_config.settings'
& 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\.venv\Scripts\python.exe' manage.py runserver 127.0.0.1:8000 2>&1 | Out-File 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\zkeco_modern\runserver_out.log' -Append
