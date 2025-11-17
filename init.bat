SET INSTALL_PATH=%CD%
SET PRJ_NAME=mysite
path =%INSTALL_PATH%\Python26;%INSTALL_PATH%\Python26\Scripts;%PATH%;%SystemRoot%\system32
set PYTHONPATH=%1;%INSTALL_PATH%\zkeco\python-support;%INSTALL_PATH%\Python26;%INSTALL_PATH%\Python26\Lib\site-packages;%INSTALL_PATH%;%INSTALL_PATH%\zkeco\units\adms
SET DJANGO_SETTINGS_MODULE=%PRJ_NAME%.settings
cd zkeco\units\adms