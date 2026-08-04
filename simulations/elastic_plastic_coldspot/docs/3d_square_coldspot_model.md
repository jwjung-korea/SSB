# 3D Square Coldspot Model

This branch adds a 3D mechanical version of the Li/LLZO coldspot model for
Abaqus 2024.

## Geometry

- LLZO: `x = 0-20 um`, `y = 0-5 um`, `z = 0-20 um`
- Lithium: `x = 0-20 um`, `y = 5-10.5 um`, `z = 0-20 um`
- Contact interface: `y = 5 um`, spanning a `20 x 20 um` `x-z` plane
- Coldspot patch: `x = 9-11 um`, `z = 9-11 um`, `y = 5-5.5 um`

The important change from a simple extrusion is that the coldspot is not a long
stripe through the full thickness. It is a square patch on the 3D interface.

## Materials

Only the central coldspot seed patch uses `LITHIUM_IP` with nonzero `cDot`.
The surrounding lithium uses `LITHIUM_SUB` with `cDot = 0`.

The viscoplastic UMAT constants are the same as the 2024-compatible
viscoplastic branch:

- `LITHIUM_IP`: `cDot = 103.643`
- `LITHIUM_SUB`: `cDot = 0`
- `LLZO`: elastic, `E = 150 GPa`, `nu = 0.25`

## Boundary Conditions

- Bottom LLZO face: `U1 = U2 = 0`
- Left and right side faces: `U1 = 0`
- Front and back faces: `U3 = 0`
- Top lithium face: pressure load of `1`, `3`, `5`, or `10 MPa`

`U3 = 0` on the front and back faces keeps the first 3D model close to the
old plane-strain interpretation while still allowing a finite `x-z` contact
surface and a square coldspot patch.

## Generated Files

Run:

```bat
simulations\elastic_plastic_coldspot\scripts\abaqus2024_with_oneapi.bat cae noGUI=simulations\elastic_plastic_coldspot\scripts\rebuild_model_3d.py
```

The script writes:

- `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d\meshOfinal_3d_patch.cae`
- `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d\final_v2_3d_patch_p1.inp`
- `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d\final_v2_3d_patch_p3.inp`
- `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d\final_v2_3d_patch_p5.inp`
- `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d\final_v2_3d_patch_p10.inp`

The generated files are intentionally kept outside git because they are Abaqus
outputs. The script is the source of truth.

## Opening CAE

Use this launcher when working on the generated 3D model in CAE:

```bat
simulations\elastic_plastic_coldspot\scripts\launch_cae_2024_3d_workdir.bat
```

It does two things before opening CAE:

- loads the Intel oneAPI compiler environment for UMAT jobs
- changes the working directory to
  `C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot_3d`

This matters for killing jobs from CAE. If CAE starts a job from `C:\Temp`,
`abaqus terminate job=<job-name>` issued from the model folder cannot find the
job client id. When that happens, either terminate from `C:\Temp` or reopen CAE
with the launcher above and set the CAE work directory to the model folder.

## Abaqus 2024 Datacheck

The representative `5 MPa` input was checked with:

```bat
simulations\elastic_plastic_coldspot\scripts\abaqus2024_with_oneapi.bat job=final_v2_3d_patch_p5_datacheck input=final_v2_3d_patch_p5.inp user=simulations\elastic_plastic_coldspot\src\umat_EP_coldspot.for double=both cpus=4 datacheck interactive
```

Result: `Abaqus JOB final_v2_3d_patch_p5_datacheck COMPLETED`.

## Next Step Toward Butler-Volmer

This is still the mechanical UMAT model using `C3D8` elements. For native
Abaqus 2024 Butler-Volmer coupling, the mechanical 3D geometry should be used
as the starting point, then converted to electrochemical-capable `QEC3D*`
elements with electrochemical procedures, electrolyte/electrode transport
properties, and a Butler-Volmer interface reaction on the `x-z` contact plane.
