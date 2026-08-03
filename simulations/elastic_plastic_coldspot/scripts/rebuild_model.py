from abaqus import *
from abaqusConstants import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
import mesh
from job import *
from sketch import *
import regionToolset

# --- Parameters ---
W = 20.0
H_LLZO = 5.0
H_SEED = 0.5
H_LITHIUM = 5.0

# --- Initialize Model Database (Once at the start) ---
Mdb()

# Loop over stack pressures to generate input files for both 5MPa and 10MPa
for STACK_PRESSURE in [5.0, 10.0]:
    print("==================================================")
    print("Generating model for STACK_PRESSURE = " + str(STACK_PRESSURE) + " MPa")
    print("==================================================")
    
    # Model name unique to each pressure
    model_name = 'Lithium_Model_p' + str(int(STACK_PRESSURE))
    myModel = mdb.Model(name=model_name)
    
    # --- Materials ---
    # LITHIUM_IP (UMAT for Seed Layer)
    mat_ip = myModel.Material(name='LITHIUM_IP')
    mat_ip.UserMaterial(type=MECHANICAL, mechanicalConstants=(7200.0, 0.38, 3.1, 5.7, 2.0, 2.0, 1.3e-05, 0.0, 1.0, 0.0, 103.643))
    mat_ip.Depvar(n=24)
    mat_ip.Density(table=((5.34e-10, ), ))
    
    # LITHIUM_SUB (UMAT for Lithium Substrate)
    mat_sub = myModel.Material(name='LITHIUM_SUB')
    mat_sub.UserMaterial(type=MECHANICAL, mechanicalConstants=(7200.0, 0.38, 3.1, 5.7, 2.0, 2.0, 1.3e-05, 0.0, 1.0, 0.0, 0.0))
    mat_sub.Depvar(n=24)
    mat_sub.Density(table=((5.34e-10, ), ))
    
    # LLZO (Elastic)
    mat_llzo = myModel.Material(name='LLZO')
    mat_llzo.Elastic(table=((150000.0, 0.25), ))
    mat_llzo.Density(table=((5.1e-09, ), ))
    
    # --- Sections ---
    myModel.HomogeneousSolidSection(name='SEC_LLZO', material='LLZO', thickness=None)
    myModel.HomogeneousSolidSection(name='SEC_SEED', material='LITHIUM_IP', thickness=None)
    myModel.HomogeneousSolidSection(name='SEC_LITHIUM', material='LITHIUM_SUB', thickness=None)
    
    # --- Part 1: LLZO_PART ---
    s1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=100.0)
    s1.rectangle(point1=(0.0, 0.0), point2=(W, H_LLZO))
    p_llzo = myModel.Part(name='LLZO_PART', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p_llzo.BaseShell(sketch=s1)
    del s1
    
    # Assign section to LLZO
    face_llzo = p_llzo.faces.findAt(((W/2.0, H_LLZO/2.0, 0.0),))
    p_llzo.SectionAssignment(region=regionToolset.Region(faces=face_llzo), sectionName='SEC_LLZO')
    
    # --- Part 2: LITHIUM_PART ---
    s2 = myModel.ConstrainedSketch(name='__profile__', sheetSize=100.0)
    s2.rectangle(point1=(0.0, H_LLZO), point2=(W, H_LLZO + H_SEED + H_LITHIUM))
    p_lithium = myModel.Part(name='LITHIUM_PART', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p_lithium.BaseShell(sketch=s2)
    del s2
    
    # Partition Lithium Part into Seed layer and Substrate layer at y = 5.5
    p_lithium.PartitionFaceByShortestPath(faces=p_lithium.faces, point1=(0.0, H_LLZO + H_SEED, 0.0), point2=(W, H_LLZO + H_SEED, 0.0))
    
    # Assign section to Seed Layer (y = 5.0 to 5.5)
    face_seed = p_lithium.faces.findAt(((W/2.0, H_LLZO + H_SEED/2.0, 0.0),))
    p_lithium.SectionAssignment(region=regionToolset.Region(faces=face_seed), sectionName='SEC_SEED')
    
    # Assign section to Lithium Substrate Layer (y = 5.5 to 10.5)
    face_lith = p_lithium.faces.findAt(((W/2.0, H_LLZO + H_SEED + H_LITHIUM/2.0, 0.0),))
    p_lithium.SectionAssignment(region=regionToolset.Region(faces=face_lith), sectionName='SEC_LITHIUM')
    
    # --- Assembly ---
    a = myModel.rootAssembly
    inst_llzo = a.Instance(name='LLZO_INST', part=p_llzo, dependent=ON)
    inst_lith = a.Instance(name='LITHIUM_INST', part=p_lithium, dependent=ON)
    
    # --- Sets & Surfaces for Assembly (Boundary Conditions and Interaction) ---
    # Bottom edge of LLZO
    edges_bot = inst_llzo.edges.findAt(((W/2.0, 0.0, 0.0),))
    a.Set(edges=edges_bot, name='BOTTOM')
    
    # Left edges (both LLZO and Lithium)
    edges_left_llzo = inst_llzo.edges.findAt(((0.0, H_LLZO/2.0, 0.0),))
    edges_left_lith = inst_lith.edges.findAt(((0.0, H_LLZO + H_SEED/2.0, 0.0),), ((0.0, H_LLZO + H_SEED + H_LITHIUM/2.0, 0.0),))
    a.Set(edges=edges_left_llzo + edges_left_lith, name='LEFT')
    
    # Right edges (both LLZO and Lithium)
    edges_right_llzo = inst_llzo.edges.findAt(((W, H_LLZO/2.0, 0.0),))
    edges_right_lith = inst_lith.edges.findAt(((W, H_LLZO + H_SEED/2.0, 0.0),), ((W, H_LLZO + H_SEED + H_LITHIUM/2.0, 0.0),))
    a.Set(edges=edges_right_llzo + edges_right_lith, name='RIGHT')
    
    # Top surface of Lithium (for stack pressure)
    edges_top = inst_lith.edges.findAt(((W/2.0, H_LLZO + H_SEED + H_LITHIUM, 0.0),))
    a.Surface(side1Edges=edges_top, name='TOP_SURFACE')
    
    # Contact Surfaces
    # Master: Top edge of LLZO (y = 5.0)
    edges_top_llzo = inst_llzo.edges.findAt(((W/2.0, H_LLZO, 0.0),))
    a.Surface(side1Edges=edges_top_llzo, name='LLZO_TOP_SURF')
    
    # Slave: Bottom edge of Lithium (y = 5.0)
    edges_bot_lith = inst_lith.edges.findAt(((W/2.0, H_LLZO, 0.0),))
    a.Surface(side1Edges=edges_bot_lith, name='LITHIUM_BOT_SURF')
    
    # Predefined temperature field (all faces of Lithium instance)
    a.Set(faces=inst_lith.faces, name='LITHIUM_NODES_SET')
    
    # --- Interaction Property and Interaction ---
    myModel.ContactProperty('IntProp-1')
    myModel.interactionProperties['IntProp-1'].TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, table=((0.1, ), ), maximumElasticSlip=FRACTION, fraction=0.005)
    myModel.interactionProperties['IntProp-1'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=PENALTY)
    
    myModel.SurfaceToSurfaceContactStd(
        name='Int-1', 
        createStepName='Initial', 
        master=a.surfaces['LLZO_TOP_SURF'], 
        slave=a.surfaces['LITHIUM_BOT_SURF'], 
        sliding=SMALL, 
        interactionProperty='IntProp-1'
    )
    
    # --- Steps ---
    myModel.ImplicitDynamicsStep(
        name='Step-1', 
        previous='Initial', 
        timePeriod=12960.0, 
        nlgeom=ON, 
        application=QUASI_STATIC,
        initialInc=0.001, 
        minInc=1e-15, 
        maxInc=1.0, 
        maxNumInc=100000,
        amplitude=STEP,
        nohaf=ON
    )
    
    # --- Boundary Conditions & Load ---
    myModel.DisplacementBC(name='BC_BOT', createStepName='Initial', region=a.sets['BOTTOM'], u1=0.0, u2=0.0)
    myModel.DisplacementBC(name='BC_LEFT', createStepName='Initial', region=a.sets['LEFT'], u1=0.0)
    myModel.DisplacementBC(name='BC_RIGHT', createStepName='Initial', region=a.sets['RIGHT'], u1=0.0)
    
    # Predefined temperature field
    myModel.Temperature(
        name='Predef_Temp', 
        createStepName='Initial', 
        region=a.sets['LITHIUM_NODES_SET'], 
        distributionType=UNIFORM, 
        crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
        magnitudes=(0.0, )
    )
    
    # Stack pressure load
    myModel.Pressure(name='Load-1', createStepName='Step-1', region=a.surfaces['TOP_SURFACE'], magnitude=STACK_PRESSURE)
    
    # --- Output Requests ---
    myModel.FieldOutputRequest(name='F-Output-1', createStepName='Step-1', variables=('S', 'U', 'RF', 'LE', 'SDV', 'STATUS', 'NT'))
    myModel.steps['Step-1'].Restart(frequency=0)
    
    # Set Element Type to CPE8
    elemType = mesh.ElemType(elemCode=CPE8, elemLibrary=STANDARD)
    p_llzo.setElementType(regions=(p_llzo.faces,), elemTypes=(elemType,))
    p_lithium.setElementType(regions=(p_lithium.faces,), elemTypes=(elemType,))
    
    # 1. Mesh Seeding for LLZO Part
    edges_horiz_llzo = p_llzo.edges.findAt(((W/2.0, 0.0, 0.0),), ((W/2.0, H_LLZO, 0.0),))
    edges_vert_left_llzo = p_llzo.edges.findAt(((0.0, H_LLZO/2.0, 0.0),))
    edges_vert_right_llzo = p_llzo.edges.findAt(((W, H_LLZO/2.0, 0.0),))
    
    p_llzo.seedEdgeBySize(edges=edges_horiz_llzo, size=0.2, constraint=FINER)
    p_llzo.seedEdgeByBias(biasMethod=SINGLE, end2Edges=edges_vert_left_llzo, number=25, ratio=5.0, constraint=FINER)
    p_llzo.seedEdgeByBias(biasMethod=SINGLE, end1Edges=edges_vert_right_llzo, number=25, ratio=5.0, constraint=FINER)
    
    # 2. Mesh Seeding for LITHIUM Part
    edges_horiz_lith = p_lithium.edges.findAt(((W/2.0, H_LLZO, 0.0),), ((W/2.0, H_LLZO + H_SEED, 0.0),), ((W/2.0, H_LLZO + H_SEED + H_LITHIUM, 0.0),))
    edges_vert_seed_left = p_lithium.edges.findAt(((0.0, H_LLZO + H_SEED/2.0, 0.0),))
    edges_vert_seed_right = p_lithium.edges.findAt(((W, H_LLZO + H_SEED/2.0, 0.0),))
    edges_vert_sub_left = p_lithium.edges.findAt(((0.0, H_LLZO + H_SEED + H_LITHIUM/2.0, 0.0),))
    edges_vert_sub_right = p_lithium.edges.findAt(((W, H_LLZO + H_SEED + H_LITHIUM/2.0, 0.0),))
    
    p_lithium.seedEdgeBySize(edges=edges_horiz_lith, size=0.2, constraint=FINER)
    p_lithium.seedEdgeByNumber(edges=edges_vert_seed_left + edges_vert_seed_right, number=10, constraint=FINER)
    p_lithium.seedEdgeByBias(biasMethod=SINGLE, end1Edges=edges_vert_sub_left, number=25, ratio=5.0, constraint=FINER)
    p_lithium.seedEdgeByBias(biasMethod=SINGLE, end2Edges=edges_vert_sub_right, number=25, ratio=5.0, constraint=FINER)
    
    # Set Structured Mesh Controls
    p_llzo.setMeshControls(regions=p_llzo.faces, elemShape=QUAD, technique=STRUCTURED)
    p_lithium.setMeshControls(regions=p_lithium.faces, elemShape=QUAD, technique=STRUCTURED)
    
    # Generate Mesh
    p_llzo.generateMesh()
    p_lithium.generateMesh()
    
    # Regenerate Assembly
    a.regenerate()
    
    # --- Create Job ---
    job_name = 'final_v2_p' + str(int(STACK_PRESSURE))
    mdb.Job(
        name=job_name, 
        model=model_name, 
        description='Modified Lithium/LLZO model with quadratic CPE8H elements and contact friction 0.1, pressure ' + str(STACK_PRESSURE), 
        type=ANALYSIS, 
        userSubroutine='C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/umat_EP_coldspot.for', 
        resultsFormat=ODB
    )
    
    # Write Input File
    mdb.jobs[job_name].writeInput(consistencyChecking=OFF)
    
    # Post-process the generated input file to add convergence controls (*CONTROLS)
    inp_filepath = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/' + job_name + '.inp'
    try:
        with open(inp_filepath, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        skip_next = False
        inserted = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            new_lines.append(line)
            if '*Dynamic' in line and not inserted and i + 1 < len(lines):
                # Append the time parameters data line immediately after *Dynamic
                new_lines.append(lines[i+1])
                # Now insert the controls
                new_lines.append('*CONTROLS, ANALYSIS=DISCONTINUOUS\n')
                new_lines.append('*CONTROLS, PARAMETERS=TIME INCREMENTATION\n')
                new_lines.append(',,,,,,,30,,,,,,\n')
                new_lines.append('*CONTROLS, PARAMETERS=FIELD\n')
                new_lines.append('0.05, 2.0\n')
                new_lines.append('*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT\n')
                new_lines.append('0.02, 2.0\n')
                skip_next = True
                inserted = True
                
        with open(inp_filepath, 'w') as f:
            f.writelines(new_lines)
        print("SUCCESS: Post-processed input file to add *CONTROLS card for " + job_name)
    except Exception as e:
        print("Error post-processing input file for " + job_name + ": " + str(e))

# Delete default model 'Model-1' if it exists to keep the tree clean
if 'Model-1' in mdb.models:
    del mdb.models['Model-1']

# Save the model database containing BOTH models and jobs
cae_output_path = 'C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/meshOfinalv3.cae'
try:
    mdb.saveAs(cae_output_path)
    print("SUCCESS: Saved CAE database containing both models to " + cae_output_path)
except Exception as e:
    print("Warning: Could not save CAE file: " + str(e))

print("==================================================")
print("SUCCESS: Both models created, CAE saved, and input files written.")
print("==================================================")
