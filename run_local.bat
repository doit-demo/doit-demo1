@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required.
  pause
  exit /b 1
)
python collector\solar_notice_collector.py
if errorlevel 1 (
  echo Collector failed.
  pause
  exit /b 1
)
start "DSOLAR Monitor" "solar-notice-monitor.html"
