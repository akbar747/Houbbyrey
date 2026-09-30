@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "JAVAC=javac"
set "JAVA=java"
if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\javac.exe" set "JAVAC=%JAVA_HOME%\bin\javac.exe"
    if exist "%JAVA_HOME%\bin\java.exe" set "JAVA=%JAVA_HOME%\bin\java.exe"
)
"%JAVAC%" -version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] JDK was not found.
    echo Please install JDK 17 or newer, or set JAVA_HOME.
    pause
    exit /b 1
)
echo Building SnakeGame ...
if not exist out mkdir out
"%JAVAC%" -encoding UTF-8 -d out SnakeGame.java
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo Build successful. Starting...
start "" "%JAVA%" -cp out SnakeGame
exit /b 0
