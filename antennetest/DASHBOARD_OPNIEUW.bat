@echo off
rem CanSat 2027 - een dashboard opnieuw openen terwijl de meting loopt
rem (bv. een venster per ongeluk gesloten). De meting zelf loopt door.
cd /d "%~dp0"
py start_meting.py --opnieuw
if errorlevel 9009 pause
