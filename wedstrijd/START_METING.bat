@echo off
rem CanSat 2027 - meting starten: de poort van de Teensy (USB) of de Pico (radio), of oefen
cd /d "%~dp0"
py start_meting.py
rem py niet gevonden (9009): Python ontbreekt, zie de handleiding (A2)
if errorlevel 9009 pause
