@echo off
title chatRAG Launcher
set PYTHONPATH=%~dp0backend

:: Embed missing chunks in background (non-blocking)
cd /d "%~dp0backend"
echo [chatRAG] Embedding missing chunks in background...
start /b python scripts/migrate_to_bge_m3.py > nul 2>&1

:: Start frontend in separate window
echo [chatRAG] Starting frontend...
start "chatRAG Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Backend with auto-restart loop
echo [chatRAG] Backend starting on :8000...
:loop
python -m uvicorn main:app --host 0.0.0.0 --port 8000
echo [chatRAG] Server crashed or stopped. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
