from abaqus import *
from abaqusConstants import *
import sys

cae_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/meshOfinalv2.cae'
output_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/inspect_output.txt'

with open(output_path, 'w') as f:
    try:
        openMdb(cae_path)
        f.write("Models in CAE:\n")
        for model_name in mdb.models.keys():
            f.write("  Model: " + str(model_name) + "\n")
            model = mdb.models[model_name]
            f.write("    Parts: " + str(list(model.parts.keys())) + "\n")
            f.write("    Steps: " + str(list(model.steps.keys())) + "\n")
            f.write("    Interactions: " + str(list(model.interactions.keys())) + "\n")
        f.write("Jobs in Mdb: " + str(list(mdb.jobs.keys())) + "\n")
    except Exception as e:
        f.write("Error: " + str(e) + "\n")
