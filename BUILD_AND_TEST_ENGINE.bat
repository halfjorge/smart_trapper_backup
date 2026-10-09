@echo off
setlocal EnableExtensions
title Smart Trapper - build and test engine
REM ==========================================================================
REM  Double-click me. I:
REM   1. save a copy of your current engine program (once),
REM   2. build the new engine,
REM   3. run OLD and NEW engines on your most recent job from TrapJobs
REM      and check that they make exactly the same traps.
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
echo  STEP 3 of 3: comparing OLD and NEW engine on your latest job...
if not exist "%OLDEXE%" (
  echo    no old engine saved, skipping the comparison.
  goto done
)
set "JOB="
for /f "delims=" %%D in ('dir /b /ad /o-d "%JOBS%" 2^>nul') do (
  if not defined JOB if exist "%JOBS%\%%D\job.json" if exist "%JOBS%\%%D\masks" set "JOB=%JOBS%\%%D"
)
if not defined JOB (
  echo    no job found in %JOBS% - skipping the comparison.
  goto done
)
echo    job: %JOB%
if exist "%CHECK%" rmdir /s /q "%CHECK%"
mkdir "%CHECK%\old" "%CHECK%\new"
for %%T in (old new) do (
  copy /y "%JOB%\job.json" "%CHECK%\%%T\" >nul
  robocopy "%JOB%\masks" "%CHECK%\%%T\masks" /E /NFL /NDL /NJH /NJS /NP >nul
  REM The old engine knows nothing about the newer settings, so compare with them switched off.
  powershell -NoProfile -Command "$p='%CHECK%\%%T\job.json'; $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; $j.PSObject.Properties.Remove('colorTrapPullbackPx'); $j.PSObject.Properties.Remove('trapShape'); [IO.File]::WriteAllText($p, ($j | ConvertTo-Json -Depth 10))"
)
echo    running OLD engine ^(this is the slow one^)...
set "T0=%TIME%"
"%OLDEXE%" "%CHECK%\old" 5 >nul 2>&1
echo      started %T0%  finished %TIME%
echo    running NEW engine...
set "T0=%TIME%"
"%EXE%" "%CHECK%\new" 5
echo      started %T0%  finished %TIME%
echo.
"%EXE%" --compare-jobs "%CHECK%\old" "%CHECK%\new" > "%CHECK%\compare.txt"
set "CMP=%ERRORLEVEL%"
type "%CHECK%\compare.txt" | findstr /c:"RESULT" /c:"DIFFERENT"
echo.
if "%CMP%"=="0" (
  echo  ============================================================
  echo   PASSED: the new engine makes exactly the same traps.
  echo  ============================================================
  rmdir /s /q "%CHECK%"
) else (
  echo  ************************************************************
  echo   The results are NOT the same. Do not use the new engine yet.
  echo   Double-click RESTORE_PREVIOUS_VERSION.bat to go back, and
  echo   send Claude a screenshot of this window.
  echo   Details: %CHECK%\compare.txt
  echo  ************************************************************
)

:done
echo.
pause
