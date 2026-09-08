@echo off
setlocal
cd /d "%~dp0"

if not exist "KSA.exe" (
    if exist "dist\KSA.exe" (
        set "KSA_EXE=dist\KSA.exe"
    ) else (
        echo KSA.exe was not found.
        echo Build it with build_windows.ps1 or download the latest release.
        pause
        exit /b 1
    )
) else (
    set "KSA_EXE=KSA.exe"
)

"%KSA_EXE%" --editor
if errorlevel 1 pause
