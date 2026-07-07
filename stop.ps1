# stop.ps1 — Dừng chatRAG (backend + ocr/chunk/embedding workers + frontend)
# Dùng: .\stop.ps1
# Chạy cái này khi không dùng chatRAG nữa, để giải phóng VRAM cho GPU nghỉ —
# đặc biệt quan trọng trên GPU nhỏ (4GB), tránh tình trạng embedding bị treo/chậm
# do GPU phải cõng nhiều tiến trình cùng lúc trong thời gian dài.

Write-Host "Stopping chatRAG..." -ForegroundColor Cyan

# Backend (uvicorn) + các worker con của nó (ocr/chunk/embedding) — đây là
# nhóm tiến trình ăn VRAM nhiều nhất vì giữ model embedding load trên GPU.
$backendProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -match 'uvicorn main:app|workers\.(ocr|chunk|embedding)_worker'
}
if ($backendProcs) {
    $backendProcs | ForEach-Object {
        Write-Host "  Killing PID $($_.ProcessId): $($_.CommandLine)" -ForegroundColor Yellow
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Backend + workers stopped." -ForegroundColor Green
} else {
    Write-Host "Backend not running." -ForegroundColor Gray
}

# Frontend dev server (vite)
$frontendProcs = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {
    $_.CommandLine -match 'vite'
}
if ($frontendProcs) {
    $frontendProcs | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "Frontend not running." -ForegroundColor Gray
}

# Ollama giữ model LLM (vd gemma3:4b) load sẵn trên GPU để trả lời nhanh —
# cũng chiếm VRAM đáng kể. Hỏi trước vì có thể bạn đang dùng Ollama cho việc khác.
$unload = Read-Host "Cũng gỡ model Ollama khỏi GPU luôn? (y/N)"
if ($unload -eq "y") {
    $model = $env:OLLAMA_MODEL
    if (-not $model) { $model = "gemma3:4b" }
    ollama stop $model 2>$null
    Write-Host "Đã gỡ model Ollama '$model' khỏi GPU." -ForegroundColor Green
}

Write-Host "Done." -ForegroundColor Cyan
