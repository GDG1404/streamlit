@echo off
rem CanSat 2027 - vluchtrapport in het Engels (flight report).
rem Sleep het CSV-bestand van de SD-kaart op dit bestand, of dubbelklik en sleep het in het venster.
cd /d "%~dp0"
py tools\flight_report.py %*
if errorlevel 1 pause
