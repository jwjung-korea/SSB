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
import os
import regionToolset


W = 20.0
DEPTH_Z = 20.0
H_LLZO = 5.0
H_SEED = 0.5
H_LITHIUM = 5.0

COLD_X1 = 9.0
COLD_X2 = 11.0
COLD_Z1 = 9.0
COLD_Z2 = 11.0

STACK_PRESSURES = [1.0, 3.0, 5.0, 10.0]
MESH_SIZE = 0.5
TOL = 1.0e-4

SCRIPT_DIR = os.environ.get("SSB_SCRIPT_DIR")
if SCRIPT_DIR is None:
    try:
        SCRIPT_DIR = os.path.dirname(__file__)
    except NameError:
        SCRIPT_DIR = os.path.join(os.getcwd(), "simulations", "elastic_plastic_coldspot", "scripts")

REPO_ROOT = os.environ.get(
    "SSB_REPO_ROOT",
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")),
)
UMAT_PATH = os.path.join(
    REPO_ROOT,
    "simulations",
    "elastic_plastic_coldspot",
    "src",
    "umat_EP_coldspot.for",
).replace("\\", "/")

OUTPUT_DIR = os.environ.get(
    "SSB_3D_OUTPUT_DIR",
    r"C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d",
)

LI_IP_PROPS = (
    7.81e3, 0.38, 4.254e4, 37.0, 298.0, 0.15, 0.95, 10.0,
    2.0, 2.0, 0.05, 1.3e-05, 0.0, 1.0, 0.0, 103.643,
)
LI_SUB_PROPS = (
    7.81e3, 0.38, 4.254e4, 37.0, 298.0, 0.15, 0.95, 10.0,
    2.0, 2.0, 0.05, 1.3e-05, 0.0, 1.0, 0.0, 0.0,
)


def make_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def midpoint(a, b):
    return 0.5 * (a + b)


def add_controls_to_input(inp_path):
    with open(inp_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    skip_next = False
    inserted = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        new_lines.append(line)
        if "*Dynamic" in line and not inserted and i + 1 < len(lines):
            new_lines.append(lines[i + 1])
            new_lines.append("*CONTROLS, ANALYSIS=DISCONTINUOUS\n")
            new_lines.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
            new_lines.append(",,,,,,,30,,,,,,\n")
            new_lines.append("*CONTROLS, PARAMETERS=FIELD\n")
            new_lines.append("0.05, 2.0\n")
            new_lines.append("*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT\n")
            new_lines.append("0.02, 2.0\n")
            skip_next = True
            inserted = True

    with open(inp_path, "w") as f:
        f.writelines(new_lines)


def cells_in_box(cells, x1, x2, y1, y2, z1, z2):
    return cells.getByBoundingBox(
        xMin=x1 - TOL,
        xMax=x2 + TOL,
        yMin=y1 - TOL,
        yMax=y2 + TOL,
        zMin=z1 - TOL,
        zMax=z2 + TOL,
    )


def faces_in_box(faces, x1, x2, y1, y2, z1, z2):
    return faces.getByBoundingBox(
        xMin=x1 - TOL,
        xMax=x2 + TOL,
        yMin=y1 - TOL,
        yMax=y2 + TOL,
        zMin=z1 - TOL,
        zMax=z2 + TOL,
    )


make_dir(OUTPUT_DIR)
os.chdir(OUTPUT_DIR)
Mdb()

for stack_pressure in STACK_PRESSURES:
    pressure_tag = str(int(stack_pressure))
    model_name = "Lithium_Model_3D_patch_p" + pressure_tag
    job_name = "final_v2_3d_patch_p" + pressure_tag

    print("==================================================")
    print("Generating 3D square coldspot model, stack pressure = " + str(stack_pressure) + " MPa")
    print("Coldspot patch: x=" + str(COLD_X1) + "-" + str(COLD_X2) + " um, z=" + str(COLD_Z1) + "-" + str(COLD_Z2) + " um")
    print("==================================================")

    model = mdb.Model(name=model_name)

    mat_ip = model.Material(name="LITHIUM_IP")
    mat_ip.UserMaterial(type=MECHANICAL, mechanicalConstants=LI_IP_PROPS)
    mat_ip.Depvar(n=24)
    mat_ip.Density(table=((5.34e-10,),))

    mat_sub = model.Material(name="LITHIUM_SUB")
    mat_sub.UserMaterial(type=MECHANICAL, mechanicalConstants=LI_SUB_PROPS)
    mat_sub.Depvar(n=24)
    mat_sub.Density(table=((5.34e-10,),))

    mat_llzo = model.Material(name="LLZO")
    mat_llzo.Elastic(table=((150000.0, 0.25),))
    mat_llzo.Density(table=((5.1e-09,),))

    model.HomogeneousSolidSection(name="SEC_LLZO", material="LLZO", thickness=None)
    model.HomogeneousSolidSection(name="SEC_COLDSPOT_SEED", material="LITHIUM_IP", thickness=None)
    model.HomogeneousSolidSection(name="SEC_LITHIUM", material="LITHIUM_SUB", thickness=None)

    s1 = model.ConstrainedSketch(name="__llzo_profile__", sheetSize=100.0)
    s1.rectangle(point1=(0.0, 0.0), point2=(W, H_LLZO))
    p_llzo = model.Part(name="LLZO_PART", dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p_llzo.BaseSolidExtrude(sketch=s1, depth=DEPTH_Z)
    del s1

    s2 = model.ConstrainedSketch(name="__lithium_profile__", sheetSize=100.0)
    s2.rectangle(point1=(0.0, H_LLZO), point2=(W, H_LLZO + H_SEED + H_LITHIUM))
    p_lithium = model.Part(name="LITHIUM_PART", dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p_lithium.BaseSolidExtrude(sketch=s2, depth=DEPTH_Z)
    del s2

    for x in (COLD_X1, COLD_X2):
        datum = p_lithium.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=x)
        p_lithium.PartitionCellByDatumPlane(
            datumPlane=p_lithium.datums[datum.id], cells=p_lithium.cells
        )

    for z in (COLD_Z1, COLD_Z2):
        datum = p_lithium.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z)
        p_lithium.PartitionCellByDatumPlane(
            datumPlane=p_lithium.datums[datum.id], cells=p_lithium.cells
        )

    datum = p_lithium.DatumPlaneByPrincipalPlane(
        principalPlane=XZPLANE, offset=H_LLZO + H_SEED
    )
    p_lithium.PartitionCellByDatumPlane(
        datumPlane=p_lithium.datums[datum.id], cells=p_lithium.cells
    )

    p_llzo.SectionAssignment(
        region=regionToolset.Region(cells=p_llzo.cells),
        sectionName="SEC_LLZO",
    )
    p_lithium.SectionAssignment(
        region=regionToolset.Region(cells=p_lithium.cells),
        sectionName="SEC_LITHIUM",
    )

    cold_cells = cells_in_box(
        p_lithium.cells,
        COLD_X1,
        COLD_X2,
        H_LLZO,
        H_LLZO + H_SEED,
        COLD_Z1,
        COLD_Z2,
    )
    p_lithium.SectionAssignment(
        region=regionToolset.Region(cells=cold_cells),
        sectionName="SEC_COLDSPOT_SEED",
    )

    assembly = model.rootAssembly
    inst_llzo = assembly.Instance(name="LLZO_INST", part=p_llzo, dependent=ON)
    inst_lith = assembly.Instance(name="LITHIUM_INST", part=p_lithium, dependent=ON)

    y_total = H_LLZO + H_SEED + H_LITHIUM

    bottom_faces = faces_in_box(inst_llzo.faces, 0.0, W, 0.0, 0.0, 0.0, DEPTH_Z)
    assembly.Set(faces=bottom_faces, name="BOTTOM")

    left_faces = (
        faces_in_box(inst_llzo.faces, 0.0, 0.0, 0.0, H_LLZO, 0.0, DEPTH_Z)
        + faces_in_box(inst_lith.faces, 0.0, 0.0, H_LLZO, y_total, 0.0, DEPTH_Z)
    )
    assembly.Set(faces=left_faces, name="LEFT")

    right_faces = (
        faces_in_box(inst_llzo.faces, W, W, 0.0, H_LLZO, 0.0, DEPTH_Z)
        + faces_in_box(inst_lith.faces, W, W, H_LLZO, y_total, 0.0, DEPTH_Z)
    )
    assembly.Set(faces=right_faces, name="RIGHT")

    front_back_faces = (
        faces_in_box(inst_llzo.faces, 0.0, W, 0.0, H_LLZO, 0.0, 0.0)
        + faces_in_box(inst_llzo.faces, 0.0, W, 0.0, H_LLZO, DEPTH_Z, DEPTH_Z)
        + faces_in_box(inst_lith.faces, 0.0, W, H_LLZO, y_total, 0.0, 0.0)
        + faces_in_box(inst_lith.faces, 0.0, W, H_LLZO, y_total, DEPTH_Z, DEPTH_Z)
    )
    assembly.Set(faces=front_back_faces, name="FRONT_BACK")

    top_faces = faces_in_box(inst_lith.faces, 0.0, W, y_total, y_total, 0.0, DEPTH_Z)
    assembly.Surface(side1Faces=top_faces, name="TOP_SURFACE")

    llzo_top = faces_in_box(inst_llzo.faces, 0.0, W, H_LLZO, H_LLZO, 0.0, DEPTH_Z)
    assembly.Surface(side1Faces=llzo_top, name="LLZO_TOP_SURF")

    lithium_bottom = faces_in_box(inst_lith.faces, 0.0, W, H_LLZO, H_LLZO, 0.0, DEPTH_Z)
    assembly.Surface(side1Faces=lithium_bottom, name="LITHIUM_BOT_SURF")

    coldspot_cells = cells_in_box(
        inst_lith.cells,
        COLD_X1,
        COLD_X2,
        H_LLZO,
        H_LLZO + H_SEED,
        COLD_Z1,
        COLD_Z2,
    )
    assembly.Set(cells=coldspot_cells, name="COLDSPOT_PATCH")
    assembly.Set(cells=inst_lith.cells, name="LITHIUM_CELLS")

    model.ContactProperty("IntProp-1")
    model.interactionProperties["IntProp-1"].TangentialBehavior(
        formulation=PENALTY,
        directionality=ISOTROPIC,
        slipRateDependency=OFF,
        pressureDependency=OFF,
        temperatureDependency=OFF,
        dependencies=0,
        table=((0.1,),),
        maximumElasticSlip=FRACTION,
        fraction=0.005,
    )
    model.interactionProperties["IntProp-1"].NormalBehavior(
        pressureOverclosure=HARD,
        allowSeparation=ON,
        constraintEnforcementMethod=PENALTY,
    )

    model.SurfaceToSurfaceContactStd(
        name="Int-1",
        createStepName="Initial",
        main=assembly.surfaces["LLZO_TOP_SURF"],
        secondary=assembly.surfaces["LITHIUM_BOT_SURF"],
        sliding=SMALL,
        interactionProperty="IntProp-1",
    )

    model.ImplicitDynamicsStep(
        name="Step-1",
        previous="Initial",
        timePeriod=12960.0,
        nlgeom=ON,
        application=QUASI_STATIC,
        initialInc=0.001,
        minInc=1e-15,
        maxInc=1.0,
        maxNumInc=100000,
        amplitude=STEP,
        nohaf=ON,
    )

    model.DisplacementBC(
        name="BC_BOT",
        createStepName="Initial",
        region=assembly.sets["BOTTOM"],
        u1=0.0,
        u2=0.0,
    )
    model.DisplacementBC(
        name="BC_LEFT",
        createStepName="Initial",
        region=assembly.sets["LEFT"],
        u1=0.0,
    )
    model.DisplacementBC(
        name="BC_RIGHT",
        createStepName="Initial",
        region=assembly.sets["RIGHT"],
        u1=0.0,
    )
    model.DisplacementBC(
        name="BC_PLANE_STRAIN_Z",
        createStepName="Initial",
        region=assembly.sets["FRONT_BACK"],
        u3=0.0,
    )

    model.Temperature(
        name="Predef_Temp",
        createStepName="Initial",
        region=assembly.sets["LITHIUM_CELLS"],
        distributionType=UNIFORM,
        magnitudes=(0.0,),
    )

    model.Pressure(
        name="Load-1",
        createStepName="Step-1",
        region=assembly.surfaces["TOP_SURFACE"],
        magnitude=stack_pressure,
    )

    model.FieldOutputRequest(
        name="F-Output-1",
        createStepName="Step-1",
        variables=("S", "U", "RF", "LE", "SDV", "STATUS", "NT"),
    )
    model.steps["Step-1"].Restart(frequency=0)

    elem_type = mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD)
    p_llzo.setElementType(regions=(p_llzo.cells,), elemTypes=(elem_type,))
    p_lithium.setElementType(regions=(p_lithium.cells,), elemTypes=(elem_type,))

    p_llzo.seedPart(size=MESH_SIZE, deviationFactor=0.1, minSizeFactor=0.1)
    p_lithium.seedPart(size=MESH_SIZE, deviationFactor=0.1, minSizeFactor=0.1)

    p_llzo.setMeshControls(regions=p_llzo.cells, elemShape=HEX, technique=STRUCTURED)
    p_lithium.setMeshControls(regions=p_lithium.cells, elemShape=HEX, technique=STRUCTURED)
    p_llzo.generateMesh()
    p_lithium.generateMesh()
    assembly.regenerate()

    mdb.Job(
        name=job_name,
        model=model_name,
        description=(
            "3D Li/LLZO viscoplastic model with a central 2 x 2 um square "
            "coldspot patch, pressure " + str(stack_pressure)
        ),
        type=ANALYSIS,
        userSubroutine=UMAT_PATH,
        resultsFormat=ODB,
    )
    mdb.jobs[job_name].writeInput(consistencyChecking=OFF)
    add_controls_to_input(os.path.join(OUTPUT_DIR, job_name + ".inp"))

if "Model-1" in mdb.models:
    del mdb.models["Model-1"]

cae_path = os.path.join(OUTPUT_DIR, "meshOfinal_3d_patch.cae")
mdb.saveAs(cae_path)
print("==================================================")
print("Saved 3D CAE to " + cae_path)
print("Wrote 3D patch input files to " + OUTPUT_DIR)
print("==================================================")
