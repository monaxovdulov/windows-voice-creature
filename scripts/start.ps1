$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonw = Join-Path $projectRoot ".venv\Scripts\pythonw.exe"
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install uv first: https://docs.astral.sh/uv/"
}

if (-not (Test-Path -LiteralPath $pythonw) -and -not (Test-Path -LiteralPath $python)) {
    Push-Location $projectRoot
    try {
        uv sync
    }
    finally {
        Pop-Location
    }
}

if (Test-Path -LiteralPath $pythonw) {
    Start-Process -FilePath $pythonw -ArgumentList @("-m", "screen_creature") -WorkingDirectory $projectRoot
    exit 0
}

if (Test-Path -LiteralPath $python) {
    Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @("-m", "screen_creature") -WorkingDirectory $projectRoot
    exit 0
}

throw "Python environment was not created. Run: uv sync"
