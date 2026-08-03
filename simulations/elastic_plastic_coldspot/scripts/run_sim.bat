@echo off
set USERNAME=user
set USER=user
set "ABAQUS_CMD=%~dp0abaqus2024_with_oneapi.bat"
if not exist "%ABAQUS_CMD%" set "ABAQUS_CMD=abaqus"

for %%I in ("%~dp0..\inputs\final_v2_p1.inp") do set "INPUT_FILE=%%~fI"
for %%U in ("%~dp0..\src\umat_EP_coldspot.for") do set "UMAT_FILE=%%~fU"

call "%ABAQUS_CMD%" job=final_v2_p1 input="%INPUT_FILE%" user="%UMAT_FILE%" double=both cpus=4 interactive
