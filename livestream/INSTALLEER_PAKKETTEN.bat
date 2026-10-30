@echo off
rem CanSat 2027 - installeert de Python-pakketten voor het streamdashboard (een keer)
cd /d "%~dp0"
py -m pip install -r requirements.txt
echo.
echo Klaar. Staat hierboven "Successfully installed" of "Requirement already satisfied"? Dan is het gelukt.
pause
