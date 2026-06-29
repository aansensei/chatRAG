@echo off
:: =============================================================================
:: WARNING: THIS SCRIPT IS DEPRECATED AND SHOULD NOT BE USED.
::
:: Workers (ocr_worker, chunk_worker, embedding_worker) are now spawned
:: automatically inside uvicorn's lifespan event in main.py, with a watchdog
:: that auto-restarts them if they crash.
::
:: Running this script WILL create DUPLICATE worker processes alongside the
:: ones already started by uvicorn, causing queue double-processing and
:: resource conflicts.
::
:: To start the application, use the root-level start.bat instead:
::   C:\Users\Thien An Nguyen\sadec\rag\start.bat
:: =============================================================================
echo.
echo  [WARNING] start_workers.bat is DEPRECATED.
echo  Workers are now managed by uvicorn lifespan in main.py.
echo  Running this script will create DUPLICATE workers.
echo  Use the root start.bat to launch the application correctly.
echo.
pause
exit /b 1
