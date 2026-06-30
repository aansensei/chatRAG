$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidsFile = Join-Path $root ".start.pids.json"

Write-Host "Stopping any running uvicorn / worker processes..." -ForegroundColor Cyan
Get-Process | Where-Object { $_.ProcessName -match "^(python|uvicorn)" } | ForEach-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmd -match "(main:app|workers\.(ocr|chunk|embedding)_worker)") {
        Write-Host "  killing pid=$($_.Id) -- $cmd"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path $pidsFile) {
    $pids = Get-Content $pidsFile | ConvertFrom-Json
    foreach ($name in @("api","ocr","chunk","embed")) {
        $procId = $pids.$name
        if ($procId) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "  stopped $name (pid=$procId)"
            } catch {
                # already gone
            }
        }
    }
    Remove-Item $pidsFile -Force -ErrorAction SilentlyContinue
}
Write-Host "All stopped." -ForegroundColor Green
