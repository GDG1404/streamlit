@echo off
rem CanSat 2027 - meting starten: kies de poort van de Pico (radio) of van de Teensy (USB)
cd /d "%~dp0"
py start_meting.py
rem py niet gevonden (9009): Python ontbreekt, zie de handleiding (A6)
if errorlevel 9009 pause
