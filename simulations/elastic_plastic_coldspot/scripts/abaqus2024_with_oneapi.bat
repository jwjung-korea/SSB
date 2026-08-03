@echo off
setlocal

set "ONEAPI_SETVARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
set "ABAQUS_2024=C:\SIMULIA\Commands\abq2024.bat"

if exist "%ONEAPI_SETVARS%" goto have_oneapi
echo ERROR: Intel oneAPI setvars.bat was not found:
echo   "%ONEAPI_SETVARS%"
exit /b 1
:have_oneapi

if exist "%ABAQUS_2024%" goto have_abaqus
echo ERROR: Abaqus 2024 launcher was not found:
echo   "%ABAQUS_2024%"
exit /b 1
:have_abaqus

call "%ONEAPI_SETVARS%" >NUL
call "%ABAQUS_2024%" %*

endlocal
