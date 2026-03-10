$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Virtual environment not found: $python"
}

$backendCommand = "Set-Location '$root'; & '$python' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null

Start-Sleep -Seconds 2

Set-Location $root
& $python -m streamlit run app.py
