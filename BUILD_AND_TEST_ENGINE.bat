@echo off
setlocal EnableExtensions
title Smart Trapper - build and test engine
REM ==========================================================================
REM  Double-click me. I:
REM   1. save a copy of your current engine program (once),
REM   2. build the new engine,
REM   3. re-run your most recent job from TrapJobs with the NEW engine and
REM      check it makes exactly the same clean masks and traps as that run did.
REM      (New options are off unless that job used them, so a correct new
REM      engine always reproduces your last run.)
REM  Nothing in your PSDs or TrapJobs folders is changed.
REM ==========================================================================

set "ROOT=%~dp0"
set "ENGINE=%ROOT%SmartTrapperB1\engine"
set "EXE=%ENGINE%\target\release\smart_trapper_b1.exe"
set "BACKUP=%ROOT%_BACKUP_2026-10-06_before_claude"
set "OLDEXE=%BACKUP%\smart_trapper_b1_OLD.exe"
set "JOBS=%USERPROFILE%\Desktop\TrapJobs"
set "CHECK=%TEMP%\smart_trapper_check"

echo.
echo  STEP 1 of 3: saving a copy of the current engine...
if not exist "%BACKUP%" mkdir "%BACKUP%"
if exist "%OLDEXE%" (
  echo    already saved earlier - keeping that copy.
) else (
  if exist "%EXE%" (
    copy /y "%EXE%" "%OLDEXE%" >nul && echo    saved.
  ) else (
    echo    no existing engine found - nothing to save.
  )
)

echo.
echo  STEP 2 of 3: building the new engine ^(about 1-2 minutes^)...
set "CARGO=cargo"
where cargo >nul 2>nul || set "CARGO=%USERPROFILE%\.cargo\bin\cargo.exe"
pushd "%ENGINE%"
"%CARGO%" build --release
set "BUILD_ERR=%ERRORLEVEL%"
popd
if not "%BUILD_ERR%"=="0" (
  echo.
  echo  ************************************************************
  echo   BUILD FAILED. Your old engine is still in place and works.
  echo   Please take a screenshot of this window and send it to Claude.
  echo  ************************************************************
  pause
  exit /b 1
)
echo    build OK.

echo.
echo  STEP 3 of 3: re-running your latest job with the NEW engine...
set "JOB="
for /f "delims=" %%D in ('dir /b /ad /o-d "%JOBS%" 2^>nul') do (
  if not defined JOB if exist "%JOBS%\%%D\job.json" if exist "%JOBS%\%%D\masks" if exist "%JOBS%\%%D\traps.json" set "JOB=%JOBS%\%%D"
)
if not defined JOB (
  echo    no finished job found in %JOBS% - skipping the check.
  goto done
)
echo    job: %JOB%
if exist "%CHECK%" rmdir /s /q "%CHECK%"
mkdir "%CHECK%\new"
copy /y "%JOB%\job.json" "%CHECK%\new\" >nul
robocopy "%JOB%\masks" "%CHECK%\new\masks" /E /NFL /NDL /NJH /NJS /NP >nul
set "T0=%TIME%"
"%EXE%" "%CHECK%\new" 5
echo      started %T0%  finished %TIME%
echo.
"%EXE%" --compare-jobs "%JOB%" "%CHECK%\new" > "%CHECK%\compare.txt"
set "CMP=%ERRORLEVEL%"
type "%CHECK%\compare.txt" | findstr /c:"RESULT" /c:"DIFFERENT"
echo.
if "%CMP%"=="0" (
  echo  ============================================================
  echo   PASSED: the new engine reproduces your last run exactly.
  echo   Click Reload on the panel and carry on.
  echo  ============================================================
  rmdir /s /q "%CHECK%"
) else (
  echo  ************************************************************
  echo   The new engine does NOT reproduce your last run.
  echo   Do not use it yet - send Claude a screenshot of this window.
  echo   Details: %CHECK%\compare.txt
  echo  ************************************************************
)

:done
echo.
pause
