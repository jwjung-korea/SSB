# Elastic-Plastic Coldspot Abaqus Model

This folder contains the reproducible files for the lithium/LLZO electrodeposition coldspot simulations.

## Layout

- `src/`: user subroutine source (`umat_EP_coldspot.for`).
- `inputs/`: Abaqus input and command files.
- `scripts/`: model generation, execution, inspection, extraction, and plotting scripts.
- `models/`: compact Abaqus CAE/JNL/REC model files.
- `results/figures/`: exported contour and comparison images.
- `results/tables/`: interface extraction CSV files.
- `results/reports/`: presentation output.
- `logs/`: compact `.log`, `.dat`, `.sta`, and text inspection outputs.
- `docs/`: original project notes preserved from the source folder.

## Original Study

The existing model compares stack pressures of 1, 3, 5, and 10 MPa for a lithium/LLZO interface with a prescribed coldspot growth-rate reduction around `x = 9-11 um`.

The next development step on this branch is to replace the hard-coded coldspot growth rate with a contact-aware current-density map for staggered electrochemical-mechanical coupling.
