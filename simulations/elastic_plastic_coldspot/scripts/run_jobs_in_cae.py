from abaqus import *
from abaqusConstants import *

print("==================================================")
print("Submitting final_v2_p5 (5 MPa)...")
print("==================================================")
mdb.jobs['final_v2_p5'].submit()
mdb.jobs['final_v2_p5'].waitForCompletion()
print("Job final_v2_p5 completed.")

print("==================================================")
print("Submitting final_v2_p10 (10 MPa)...")
print("==================================================")
mdb.jobs['final_v2_p10'].submit()
mdb.jobs['final_v2_p10'].waitForCompletion()
print("Job final_v2_p10 completed. All jobs done!")
print("==================================================")
