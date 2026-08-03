from abaqus import *
from abaqusConstants import *

output_file = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/inspect_inst_output.txt'
with open(output_file, 'w') as f:
    try:
        Mdb()
        myModel = mdb.Model(name='Lithium_Model')
        W = 20.0
        H_LLZO = 5.0
        H_SEED = 0.5
        H_LITHIUM = 5.0

        # Part
        s2 = myModel.ConstrainedSketch(name='__profile__', sheetSize=100.0)
        s2.rectangle(point1=(0.0, H_LLZO), point2=(W, H_LLZO + H_SEED + H_LITHIUM))
        p_lithium = myModel.Part(name='LITHIUM_PART', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        p_lithium.BaseShell(sketch=s2)
        del s2

        p_lithium.PartitionFaceByShortestPath(faces=p_lithium.faces, point1=(0.0, H_LLZO + H_SEED, 0.0), point2=(W, H_LLZO + H_SEED, 0.0))

        # Assembly
        a = myModel.rootAssembly
        inst_lith = a.Instance(name='LITHIUM_INST', part=p_lithium, dependent=OFF)

        f.write("Instance faces type: " + str(type(inst_lith.faces)) + "\n")
        f.write("Instance faces count: " + str(len(inst_lith.faces)) + "\n")
        f.write("Instance cells count: " + str(len(inst_lith.cells) if hasattr(inst_lith, 'cells') else "No cells") + "\n")
    except Exception as err:
        f.write("Error: " + str(err) + "\n")
