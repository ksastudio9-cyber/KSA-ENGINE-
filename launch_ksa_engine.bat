@echo off
setlocal
cd /d "%~dp0"

if not exist "KSA ENGINE.exe" (
    if exist "dist\KSA ENGINE.exe" (
        set "KSA_EXE=dist\KSA ENGINE.exe"
    ) else (
        echo KSA ENGINE.exe was not found.
        echo Build it with build_windows.ps1 or download the latest release.
        pause
        exit /b 1
    )
) else (
    set "KSA_EXE=KSA ENGINE.exe"
)

"%KSA_EXE%" --editor
if errorlevel 1 pause
