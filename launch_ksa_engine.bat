@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)
if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo Failed to create Python environment.
        pause
        exit /b 1
    )
)
 .venv\Scripts\python.exe -c "import pygame" >nul 2>nul
if errorlevel 1 (
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install KSA ENGINE requirements.
        pause
        exit /b 1
    )
)
.venv\Scripts\python.exe -m ksa_engine --editor
if errorlevel 1 pause
