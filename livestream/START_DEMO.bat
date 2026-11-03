@echo off
rem CanSat 2027 - streamdashboard met een nagebootste vlucht (zonder hardware)
cd /d "%~dp0"
py stream\stream_dashboard.py --demo
if errorlevel 1 pause
