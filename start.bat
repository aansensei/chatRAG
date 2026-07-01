@echo off
title chatRAG
set PYTHONPATH=%~dp0backend

:: Embed missing chunks (non-blocking)
cd /d "%~dp0backend"
start /b python scripts/migrate_to_bge_m3.py > nul 2>&1

:: Backend — single server at http://localhost:8000
echo [chatRAG] Starting backend at http://localhost:8000 ...
start /min "chatRAG Backend" cmd /k "%~dp0_backend.bat"

timeout /t 2 /nobreak >nul

:: Vite watch — auto-rebuilds to backend/app/static on every file save
:: Refresh browser manually after save (F5)
echo [chatRAG] Vite watch mode — edit frontend, F5 to refresh at http://localhost:8000
cd /d "%~dp0frontend"
npm run watch
