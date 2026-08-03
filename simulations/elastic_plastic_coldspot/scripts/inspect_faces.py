from abaqus import *
from abaqusConstants import *
import sys

cae_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/meshOfinalv2.cae'
output_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/inspect_faces.txt'

with open(output_path, 'w') as f:
    try:
        openMdb(cae_path)
        model = mdb.models['Lithium_Model']
        part = model.parts['LITHIUM_SE']
        f.write("Section Assignments in Part LITHIUM_SE:\n")
        for sa in part.sectionAssignments:
            f.write("  Section: " + str(sa.sectionName) + "\n")
            # Get the face indices in the region
            # Region can have faces
            try:
                face_indices = [face.index for face in sa.region.faces]
                f.write("    Faces: " + str(face_indices) + "\n")
                # For each face, print centroid
                for face in sa.region.faces:
                    f.write("      Face " + str(face.index) + " Centroid: " + str(face.pointOn[0]) + "\n")
            except Exception as e_region:
                f.write("    Region error: " + str(e_region) + "\n")
    except Exception as e:
        f.write("Error: " + str(e) + "\n")
