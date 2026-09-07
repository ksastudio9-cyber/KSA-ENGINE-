$ErrorActionPreference = 'Stop'

$project = (Resolve-Path $PSScriptRoot).Path
Set-Location $project

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
}

$python = Join-Path $project '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt pyinstaller

$nativeBuild = Join-Path $project 'build\native'
cmake -S (Join-Path $project 'cpp') -B $nativeBuild -DCMAKE_BUILD_TYPE=Release
cmake --build $nativeBuild --config Release --parallel

$nativeExecutable = Join-Path $nativeBuild 'Release\ksa_engine_cpp.exe'
if (-not (Test-Path $nativeExecutable)) {
    $nativeExecutable = Join-Path $nativeBuild 'ksa_engine_cpp.exe'
}
if (-not (Test-Path $nativeExecutable)) {
    throw 'Native runtime executable was not produced by CMake.'
}

& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name 'KSA' --icon 'assets\ksa-engine-k.ico' --add-data 'assets;assets' --add-binary "$nativeExecutable;." --collect-all pygame 'desktop_launcher.py'

Write-Host "Build complete: $project\dist\KSA.exe"