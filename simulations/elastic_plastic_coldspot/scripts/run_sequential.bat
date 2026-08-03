@echo off
set "ABAQUS_CMD=%~dp0abaqus2024_with_oneapi.bat"
if not exist "%ABAQUS_CMD%" set "ABAQUS_CMD=abaqus"

echo ==================================================
echo [Abaqus Sequential Runner]
echo Starting Job: final_v2_p5 (5 MPa)
echo ==================================================
call "%ABAQUS_CMD%" job=final_v2_p5 user=umat_EP_coldspot.for double=both cpus=4 interactive
echo --------------------------------------------------
echo Job final_v2_p5 completed.
echo --------------------------------------------------

echo ==================================================
echo Starting Job: final_v2_p10 (10 MPa)
echo ==================================================
call "%ABAQUS_CMD%" job=final_v2_p10 user=umat_EP_coldspot.for double=both cpus=4 interactive
echo --------------------------------------------------
echo Job final_v2_p10 completed. All Jobs Completed!
echo ==================================================
pause
