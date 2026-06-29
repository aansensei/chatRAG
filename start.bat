@echo off
title chatRAG Launcher

:: Set PYTHONPATH so workers and modules resolve correctly from the backend folder
set PYTHONPATH=%~dp0backend

:: Backend with auto-restart loop
cd /d "%~dp0backend"
echo [chatRAG] Backend starting...

:loop
python -m uvicorn main:app --host 0.0.0.0 --port 8000
echo [chatRAG] Server crashed or stopped. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
