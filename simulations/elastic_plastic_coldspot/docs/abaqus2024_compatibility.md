# Abaqus 2024 Compatibility

This branch was checked with Abaqus 2024 using the viscoplastic lithium material update.

## Local Verification

The installed launcher resolves to Abaqus 2024:

```bat
C:\SIMULIA\Commands\abaqus.bat information=release
```

The existing `final_v2_p5.inp` model with `umat_EP_coldspot.for` passed datacheck in Abaqus 2024 after loading the Intel oneAPI compiler environment:

```text
Abaqus JOB abq2024_p5_datacheck COMPLETED
Intel Fortran Classic 2021.13.1
```

## User Subroutine Setup

Abaqus 2024 did not find the compiler environment by itself:

```text
verify -user_std
result : Compilers are not found.
```

Calling Intel oneAPI first fixed it:

```bat
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
C:\SIMULIA\Commands\abaqus.bat verify -user_std
```

The result was:

```text
Abaqus/Standard with user subroutines verification
result : PASS
```

For convenience, use:

```bat
simulations\elastic_plastic_coldspot\scripts\abaqus2024_with_oneapi.bat
```

This wrapper calls oneAPI `setvars.bat` and then `C:\SIMULIA\Commands\abq2024.bat`.

## Run Existing Viscoplastic Coldspot Inputs

From a scratch working directory, call the wrapper with the input and UMAT paths:

```bat
C:\Users\jwjung020625\Documents\Codex\2026-08-02\rm\SSB\simulations\elastic_plastic_coldspot\scripts\abaqus2024_with_oneapi.bat ^
  job=final_v2_p5 ^
  input=C:\Users\jwjung020625\Documents\Codex\2026-08-02\rm\SSB\simulations\elastic_plastic_coldspot\inputs\final_v2_p5.inp ^
  user=C:\Users\jwjung020625\Documents\Codex\2026-08-02\rm\SSB\simulations\elastic_plastic_coldspot\src\umat_EP_coldspot.for ^
  double=both cpus=4 interactive
```

The legacy `run_sim.bat` and `run_sequential.bat` scripts now use the wrapper when it is present.

## Scope

This compatibility change does not convert the existing 2D mechanical coldspot model into an Abaqus 2024 native electrochemical battery model. It only makes the current viscoplastic UMAT-based model compile and run under Abaqus 2024.

The native Butler-Volmer battery path remains a separate model-conversion task requiring electrochemical element types such as `QEC3D8` and procedures such as `*COUPLED THERMAL-ELECTROCHEMICAL` or `*COUPLED TEMPERATURE-DISPLACEMENT, ELECTROCHEMICAL`.
