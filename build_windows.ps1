$ErrorActionPreference = 'Stop'

$project = (Resolve-Path $PSScriptRoot).Path
Set-Location $project

$nativeBuild = Join-Path $project 'build\native'
cmake -S (Join-Path $project 'cpp') -B $nativeBuild -DCMAKE_BUILD_TYPE=Release
cmake --build $nativeBuild --config Release --parallel

$nativeExecutable = Join-Path $nativeBuild 'Release\KSA ENGINE.exe'
if (-not (Test-Path $nativeExecutable)) {
    $nativeExecutable = Join-Path $nativeBuild 'KSA ENGINE.exe'
}
if (-not (Test-Path $nativeExecutable)) {
    throw 'Native runtime executable was not produced by CMake.'
}

$dist = Join-Path $project 'dist'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
Copy-Item $nativeExecutable (Join-Path $dist 'KSA ENGINE.exe') -Force

Write-Host "Build complete: $project\dist\KSA ENGINE.exe"