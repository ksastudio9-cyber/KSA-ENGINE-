$ErrorActionPreference = 'Stop'

$project = (Resolve-Path $PSScriptRoot).Path
Set-Location $project

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
}

$python = Join-Path $project '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt pyinstaller
& $python -m PyInstaller --noconfirm --clean --windowed --name 'KSA ENGINE' --icon 'assets\ksa-engine-k.ico' --add-data 'assets;assets' --collect-all pygame 'desktop_launcher.py'

Write-Host "Build complete: $project\dist\KSA ENGINE\KSA ENGINE.exe"