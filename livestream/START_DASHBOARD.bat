@echo off
rem CanSat 2027 - streamdashboard: kies de poort van de Teensy (droogtest) of van de ontvanger
cd /d "%~dp0"
py stream\stream_dashboard.py
if errorlevel 1 pause
