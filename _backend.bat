@echo off
set PYTHONPATH=%~dp0backend
cd /d "%~dp0backend"
:loop
python -m uvicorn main:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul
goto loop
