@echo off
setlocal
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0property_scraper_gui.pyw"
) else (
  start "" python "%~dp0property_scraper_gui.py"
)
