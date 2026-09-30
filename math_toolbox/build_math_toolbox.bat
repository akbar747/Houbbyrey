@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "LOCAL_GCC=%~dp0..\tools\mingw64\bin\gcc.exe"
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
echo Building math_toolbox.exe ...
"%GCC%" math_toolbox.c -O2 -std=c11 -Wall -Wextra -municode -mwindows -o math_toolbox.exe -lgdi32 -luser32
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo Build successful. Starting...
start "" math_toolbox.exe
exit /b 0