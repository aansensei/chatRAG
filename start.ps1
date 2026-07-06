# start.ps1 — Khởi động chatRAG (backend + frontend) trong 2 cửa sổ riêng
# Dùng: .\start.ps1
# Dừng: .\stop.ps1 (nếu có) hoặc đóng 2 cửa sổ terminal

$Root = $PSScriptRoot

Write-Host "Starting chatRAG..." -ForegroundColor Cyan

Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root\backend'; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
) -WindowStyle Normal

Start-Sleep -Milliseconds 500

Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root\frontend'; npm run dev"
) -WindowStyle Normal

Write-Host "Backend  -> http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend -> http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C in each window to stop." -ForegroundColor Gray
