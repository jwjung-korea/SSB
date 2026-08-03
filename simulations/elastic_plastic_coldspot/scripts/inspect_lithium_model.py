from abaqus import *
from abaqusConstants import *
import sys

cae_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/meshOfinalv2.cae'
output_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/inspect_lithium_model.txt'

with open(output_path, 'w') as f:
    try:
        openMdb(cae_path)
        model = mdb.models['Lithium_Model']
        f.write("Model: Lithium_Model\n")
        f.write("Parts:\n")
        for part_name in model.parts.keys():
            part = model.parts[part_name]
            f.write("  Part: " + str(part_name) + "\n")
            f.write("    Num Faces: " + str(len(part.faces)) + "\n")
            f.write("    Num Edges: " + str(len(part.edges)) + "\n")
            f.write("    Num Vertices: " + str(len(part.vertices)) + "\n")
            f.write("    Sections:\n")
            for sa in part.sectionAssignments:
                f.write("      Section name: " + str(sa.sectionName) + ", Region: " + str(sa.region) + "\n")
        f.write("Assembly Instances:\n")
        a = model.rootAssembly
        for inst_name in a.instances.keys():
            inst = a.instances[inst_name]
            f.write("  Instance: " + str(inst_name) + ", Part: " + str(inst.partName) + "\n")
            f.write("  Sets: " + str(list(a.sets.keys())) + "\n")
            f.write("  Surfaces: " + str(list(a.surfaces.keys())) + "\n")
    except Exception as e:
        f.write("Error: " + str(e) + "\n")
