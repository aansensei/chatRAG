$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$logs = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$apiLog    = Join-Path $logs "api-$ts.log"
$ocrLog    = Join-Path $logs "ocr-$ts.log"
$chunkLog  = Join-Path $logs "chunk-$ts.log"
$embedLog  = Join-Path $logs "embed-$ts.log"

$python = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$uvicorn = if (Test-Path ".venv\Scripts\uvicorn.exe") { ".\.venv\Scripts\uvicorn.exe" } else { "uvicorn" }

Write-Host "chatRAG starting..." -ForegroundColor Cyan
Write-Host "  python : $python"
Write-Host "  cwd    : $root"
Write-Host "  logs   : $logs"
Write-Host ""

function Start-Bg($name, $cmd, $logPath) {
    $p = Start-Process -FilePath $cmd[0] -ArgumentList $cmd[1..($cmd.Length - 1)] `
        -RedirectStandardOutput $logPath -RedirectStandardError "$logPath.err" `
        -WindowStyle Hidden -PassThru
    Write-Host ("  {0,-8} pid={1}  log -> {2}" -f $name, $p.Id, (Split-Path -Leaf $logPath))
    return $p.Id
}

$pids = @{}
$pids.api   = Start-Bg "api"   @($uvicorn, "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000") $apiLog
$pids.ocr   = Start-Bg "ocr"   @($python, "-m", "workers.ocr_worker") $ocrLog
$pids.chunk = Start-Bg "chunk" @($python, "-m", "workers.chunk_worker") $chunkLog
$pids.embed = Start-Bg "embed" @($python, "-m", "workers.embedding_worker") $embedLog

$pids | ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $root ".start.pids.json")

Write-Host ""
Write-Host "OK. API: http://localhost:8000" -ForegroundColor Green
Write-Host "Tail latest log: Get-Content -Wait $apiLog"
Write-Host "Stop everything: .\stop.ps1"
