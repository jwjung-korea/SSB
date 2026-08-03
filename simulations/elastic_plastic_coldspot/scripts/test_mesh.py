from abaqus import *
from abaqusConstants import *
import mesh
import regionToolset

output_file = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/test_mesh_output.txt'
with open(output_file, 'w') as f:
    try:
        Mdb()
        model = mdb.Model(name='TestModel')

        # Parameters
        W = 20.0
        H1 = 5.0

        # 1. Create LLZO Part
        s1 = model.ConstrainedSketch(name='__profile__', sheetSize=100.0)
        s1.rectangle(point1=(0.0, 0.0), point2=(W, H1))
        p_llzo = model.Part(name='LLZO_PART', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        p_llzo.BaseShell(sketch=s1)
        del s1

        # Find vertical edges
        e_llzo = p_llzo.edges
        edge_left = e_llzo.findAt(((0.0, H1/2.0, 0.0),))
        edge_right = e_llzo.findAt(((W, H1/2.0, 0.0),))

        # Apply bias seed using end2Edges
        p_llzo.seedEdgeByBias(biasMethod=SINGLE, end2Edges=edge_left, number=25, ratio=5.0, constraint=FINER)
        p_llzo.seedEdgeByBias(biasMethod=SINGLE, end2Edges=edge_right, number=25, ratio=5.0, constraint=FINER)
        f.write("Seeded left and right edges with end2Edges successfully.\n")

        # Mesh the part
        p_llzo.setMeshControls(regions=p_llzo.faces, elemShape=QUAD, technique=STRUCTURED)
        p_llzo.generateMesh()

        # Find node y-coordinates on the left edge (x=0)
        f.write("Node Y coordinates along left edge (x=0) for end2Edges:\n")
        nodes = p_llzo.nodes
        left_nodes = [node for node in nodes if abs(node.coordinates[0]) < 1e-5]
        left_nodes.sort(key=lambda n: n.coordinates[1])
        for n in left_nodes:
            f.write("  Node Label: %d, Y: %.4f\n" % (n.label, n.coordinates[1]))
    except Exception as err:
        f.write("Error: " + str(err) + "\n")
