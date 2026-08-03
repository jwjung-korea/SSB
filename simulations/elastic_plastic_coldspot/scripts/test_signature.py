from abaqus import *
from abaqusConstants import *
import xyPlot

# Write directly to file
with open("signature_output.txt", "w") as f:
    f.write("DOC ON session.XYDataFromPath:\n")
    try:
        f.write(str(session.XYDataFromPath.__doc__) + "\n")
    except Exception as e:
        f.write(str(e) + "\n")

    f.write("\nDOC ON xyPlot.XYDataFromPath:\n")
    try:
        f.write(str(xyPlot.XYDataFromPath.__doc__) + "\n")
    except Exception as e:
        f.write(str(e) + "\n")

print("Signature extraction completed.")
