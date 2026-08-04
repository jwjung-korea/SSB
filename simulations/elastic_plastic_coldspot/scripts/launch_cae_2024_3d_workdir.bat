@echo off
setlocal

set "JOB_WORKDIR=C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d"

if not exist "%JOB_WORKDIR%" mkdir "%JOB_WORKDIR%"

call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" >NUL
cd /d "%JOB_WORKDIR%"
call "C:\SIMULIA\Commands\abq2024.bat" cae %*

endlocal
