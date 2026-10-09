@echo off
setlocal EnableExtensions
title Smart Trapper - restore previous version
REM Puts back the files saved on 2026-10-06 before Claude's changes.
set "ROOT=%~dp0"
set "BACKUP=%ROOT%_BACKUP_2026-10-06_before_claude"
if not exist "%BACKUP%\UXP_Trapper\main.js" (
  echo Backup folder not found: %BACKUP%
  pause
  exit /b 1
)
echo This will put back the panel and engine from before 2026-10-06.
choice /m "Continue"
if errorlevel 2 exit /b 0
copy /y "%BACKUP%\UXP_Trapper\main.js" "%ROOT%UXP_Trapper\main.js" >nul
copy /y "%BACKUP%\UXP_Trapper\styles.css" "%ROOT%UXP_Trapper\styles.css" >nul
copy /y "%BACKUP%\SmartTrapperB1\engine\src\main.rs" "%ROOT%SmartTrapperB1\engine\src\main.rs" >nul
if exist "%ROOT%SmartTrapperB1\engine\src\fast.rs" del "%ROOT%SmartTrapperB1\engine\src\fast.rs"
if exist "%BACKUP%\smart_trapper_b1_OLD.exe" copy /y "%BACKUP%\smart_trapper_b1_OLD.exe" "%ROOT%SmartTrapperB1\engine\target\release\smart_trapper_b1.exe" >nul
echo.
echo Restored. In UXP Developer Tool, click Reload on Smart Trapper.
pause
