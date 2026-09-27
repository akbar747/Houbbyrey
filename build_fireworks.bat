@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "LOCAL_GCC=%~dp0tools\mingw64\bin\gcc.exe"
if exist "%LOCAL_GCC%" (
    set "GCC=%LOCAL_GCC%"
) else (
    set "GCC=gcc"
)
"%GCC%" --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] GCC was not found.
    echo Expected: %LOCAL_GCC%
    pause
    exit /b 1
)
echo Building fireworks.exe ...
"%GCC%" fireworks.c -O2 -std=c11 -Wall -Wextra -o fireworks.exe -lgdi32 -luser32 -lm -mwindows
if errorlevel 1 (
    echo.
    echo Build failed. Please send the error message for help.
    pause
    exit /b 1
)
echo Build successful. Starting...
start "" fireworks.exe
exit /b 0