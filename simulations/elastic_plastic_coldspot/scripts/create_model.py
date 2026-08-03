from abaqus import *
from abaqusConstants import *
import regionToolset

# --- Parameters ---
W = 20.0
H1 = 5.0
H2 = 0.5
H3 = 5.0

# --- Create Model ---
Mdb()
myModel = mdb.Model(name='Lithium_Model')

# --- Create Materials ---
# LITHIUM_IP (UMAT)
mat_ip = myModel.Material(name='LITHIUM_IP')
mat_ip.UserMaterial(type=MECHANICAL, mechanicalConstants=(7200.0, 0.38, 3.1, 5.7, 2.0, 2.0, 1.3e-05, 0.0, 1.0, 0.0, 103.643))
mat_ip.Depvar(n=24)

# LITHIUM_SUB (UMAT)
mat_sub = myModel.Material(name='LITHIUM_SUB')
mat_sub.UserMaterial(type=MECHANICAL, mechanicalConstants=(7200.0, 0.38, 3.1, 5.7, 2.0, 2.0, 1.3e-05, 0.0, 1.0, 0.0, 0.0))
mat_sub.Depvar(n=24)

# LLZO (Elastic)
mat_llzo = myModel.Material(name='LLZO')
mat_llzo.Elastic(table=((150000.0, 0.25), ))

# --- Create Sections ---
myModel.HomogeneousSolidSection(name='SEC_LLZO', material='LLZO', thickness=None)
myModel.HomogeneousSolidSection(name='SEC_SEED', material='LITHIUM_IP', thickness=None)
myModel.HomogeneousSolidSection(name='SEC_LITHIUM', material='LITHIUM_SUB', thickness=None)

# --- Create Parts ---
s = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
s.rectangle(point1=(0.0, 0.0), point2=(W, H1+H2+H3))
p = myModel.Part(name='LITHIUM_SE', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del s

# --- Partition the Part into 3 Layers ---
f = p.faces
pickedFaces = f[0:1]
p.PartitionFaceByShortestPath(faces=pickedFaces, point1=(0.0, H1, 0.0), point2=(W, H1, 0.0))

# Re-select the face for the second partition
f = p.faces
face_for_p2 = f.findAt(((W/2.0, H1 + 0.1, 0.0),))
p.PartitionFaceByShortestPath(faces=face_for_p2, 
    point1=(0.0, H1+H2, 0.0), point2=(W, H1+H2, 0.0))

# --- Assign Sections ---
f = p.faces
# Bottom (LLZO)
face_llzo = f.findAt(((W/2.0, H1/2.0, 0.0),))
p.SectionAssignment(region=regionToolset.Region(faces=face_llzo), 
    sectionName='SEC_LLZO')

# Middle (SEED)
face_seed = f.findAt(((W/2.0, H1 + H2/2.0, 0.0),))
p.SectionAssignment(region=regionToolset.Region(faces=face_seed), 
    sectionName='SEC_SEED')

# Top (LITHIUM)
face_lithium = f.findAt(((W/2.0, H1 + H2 + H3/2.0, 0.0),))
p.SectionAssignment(region=regionToolset.Region(faces=face_lithium), 
    sectionName='SEC_LITHIUM')

# --- Assembly ---
a = myModel.rootAssembly
inst = a.Instance(name='LITHIUM_INST', part=p, dependent=OFF)

# --- Sets and Surfaces for BCs/Load ---
# Bottom edge
e = inst.edges
edges_bot = e.findAt(((W/2.0, 0.0, 0.0),))
a.Set(edges=edges_bot, name='BOTTOM')

# Left edges
edges_left = e.findAt(((0.0, H1/2.0, 0.0),), ((0.0, H1+H2/2.0, 0.0),), ((0.0, H1+H2+H3/2.0, 0.0),))
a.Set(edges=edges_left, name='LEFT')

# Right edges
edges_right = e.findAt(((W, H1/2.0, 0.0),), ((W, H1+H2/2.0, 0.0),), ((W, H1+H2+H3/2.0, 0.0),))
a.Set(edges=edges_right, name='RIGHT')

# Top edge
edges_top = e.findAt(((W/2.0, H1+H2+H3, 0.0),))
a.Set(edges=edges_top, name='TOP_NODES')
a.Surface(side1Edges=edges_top, name='TOP_SURFACE')

# --- Step ---
myModel.StaticStep(name='Step-1', previous='Initial', 
    timePeriod=21600.0, nlgeom=ON, stabilizationMethod=DAMPING_FACTOR, 
    stabilizationMagnitude=0.002, initialInc=0.001, minInc=1e-07, maxInc=1.0, 
    maxNumInc=100000)

# --- BCs and Loads ---
a = myModel.rootAssembly
region = a.sets['BOTTOM']
myModel.DisplacementBC(name='BC_BOT', createStepName='Initial', 
    region=region, u1=0.0, u2=0.0)

region = a.sets['LEFT']
myModel.DisplacementBC(name='BC_LEFT', createStepName='Initial', 
    region=region, u1=0.0)

region = a.sets['RIGHT']
myModel.DisplacementBC(name='BC_RIGHT', createStepName='Initial', 
    region=region, u1=0.0)

region = a.surfaces['TOP_SURFACE']
myModel.Pressure(name='Load-1', createStepName='Step-1', 
    region=region, magnitude=0.1)

# --- Field Output ---
myModel.FieldOutputRequest(name='F-Output-1', createStepName='Step-1', 
    variables=('S', 'U', 'RF', 'LE', 'SDV', 'STATUS', 'NT'))

print("All done! Model created successfully.")
