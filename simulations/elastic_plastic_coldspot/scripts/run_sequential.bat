@echo off
echo ==================================================
echo [Abaqus Sequential Runner]
echo Starting Job: final_v2_p5 (5 MPa)
echo ==================================================
call abaqus job=final_v2_p5 user=umat_EP_coldspot.for double=both cpus=4 interactive
echo --------------------------------------------------
echo Job final_v2_p5 completed.
echo --------------------------------------------------

echo ==================================================
echo Starting Job: final_v2_p10 (10 MPa)
echo ==================================================
call abaqus job=final_v2_p10 user=umat_EP_coldspot.for double=both cpus=4 interactive
echo --------------------------------------------------
echo Job final_v2_p10 completed. All Jobs Completed!
echo ==================================================
pause
