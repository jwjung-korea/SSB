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

## Contact-Aware Coupling Prototype

`src/umat_EP_coldspot.for` now checks for `cdot_map.csv` in the Abaqus job working directory. If present, it linearly interpolates `cdot` from that map using the integration point `x` coordinate. If the map is absent, the original hard-coded coldspot behavior is retained as a fallback.

`scripts/generate_cdot_map.py` creates that map from interface extraction data. This supports a staggered workflow:

```text
Abaqus mechanical/contact block
-> extract interface contact/stress data
-> generate cdot_map.csv
-> run the next Abaqus block with updated local growth rates
```
