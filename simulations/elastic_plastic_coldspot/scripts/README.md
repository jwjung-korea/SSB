# Scripts

## Contact-Aware Current Map Prototype

`generate_cdot_map.py` converts interface extraction data into `cdot_map.csv`,
which is read by `src/umat_EP_coldspot.for`.

Example:

```powershell
python scripts/generate_cdot_map.py results/tables/final_v2_p5_interface_data_t10800.csv -o cdot_map.csv --sign 1
```

The generated map keeps the average `cdot` equal to `base_cdot`, while
redistributing local `cdot` according to:

```text
weight(x) = cold_factor(x) * contact_weight(x)
```

If `COPEN`/`CPRESS` are present, they are used first. Otherwise the script
falls back to `S22_Stress` as a compression-based contact proxy.

## Butler-Volmer Current Prototype

`generate_bv_cdot_map.py` computes a local Butler-Volmer reaction current
before writing the UMAT map.

Example:

```powershell
python scripts/generate_bv_cdot_map.py results/tables/final_v2_p5_interface_data_t10800.csv -o cdot_map.csv --current-output bv_current_distribution.csv --mode plating --eta -0.05
```

Model variables:

- `j0`: reference exchange current density, in `A/m^2`. The default is `1.0`, used as a practical Li|LLZO placeholder for normalized current redistribution.
- `k-neg`: optional negative-electrode reaction rate constant, in `mol/(m^2 s)`. If supplied, the script uses `F*k-neg` instead of `j0`.
- `eta`: global overpotential, in `V`; negative favors plating by the usual BV sign convention.
- `alpha`: charge-transfer coefficient.
- `temperature`: temperature in `K`.
- `concentration-ratio`: `CLi+ / CLi,all`.
- `contact_factor`: active reaction factor from `COPEN`/`CPRESS`, or `S22_Stress` fallback.
- `cold_factor`: initial coldspot reaction factor, set to `0.1` for `x=9-11 um` with `0.5 um` ramps.
- `j0_eff = j0*contact_factor*cold_factor`, unless `k-neg` is supplied explicitly.

The script does not solve an electrolyte potential field. It uses one global
overpotential and lets mechanics enter through the effective active contact
area/reaction factor.

## 216 s Staggered Block Runner

`run_staggered_bv_blocks.py` automates repeated Abaqus blocks with a refreshed
`cdot_map.csv` every `216 s`. The default run covers `21600 s` and uses
`--mode cycling`, which alternates plating and stripping every `2160 s` to
match the original coldspot loading pattern. The first block uses the UMAT's
built-in coldspot fallback by default, then contact-aware BV maps are applied
from the second block onward.
For a strict first-block match with a previously converged baseline, pass the
baseline UMAT with `--first-umat`; restart blocks still use `--umat`.

Dry-run example:

```powershell
python simulations\elastic_plastic_coldspot\scripts\run_staggered_bv_blocks.py `
  --base-inp simulations\elastic_plastic_coldspot\inputs\final_v2_p5.inp `
  --umat simulations\elastic_plastic_coldspot\src\umat_EP_coldspot.for `
  --first-umat C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot\umat_EP_coldspot.for `
  --workdir C:\Abaqus_Work\lithium_electrodeposition\bv216_p5 `
  --job-prefix p5_bv216 `
  --dry-run
```

Actual run:

```powershell
python simulations\elastic_plastic_coldspot\scripts\run_staggered_bv_blocks.py `
  --base-inp simulations\elastic_plastic_coldspot\inputs\final_v2_p5.inp `
  --umat simulations\elastic_plastic_coldspot\src\umat_EP_coldspot.for `
  --first-umat C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot\umat_EP_coldspot.for `
  --workdir C:\Abaqus_Work\lithium_electrodeposition\bv216_p5 `
  --job-prefix p5_bv216
```

Actual run with one joined ODB at the end:

```powershell
python simulations\elastic_plastic_coldspot\scripts\run_staggered_bv_blocks.py `
  --base-inp simulations\elastic_plastic_coldspot\inputs\final_v2_p5.inp `
  --umat simulations\elastic_plastic_coldspot\src\umat_EP_coldspot.for `
  --first-umat C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot\umat_EP_coldspot.for `
  --workdir C:\Abaqus_Work\lithium_electrodeposition\bv216_p5 `
  --job-prefix p5_bv216 `
  --join-odb `
  --delete-after-join
```

The runner creates a first 216 s input, enables restart output, then runs
subsequent blocks with `oldjob=<previous block>`. Each completed block is
post-processed into an interface CSV, passed through the Butler-Volmer map
generator, and used as the next block's `cdot_map.csv`.

By default, the runner keeps every block output from `0 s` to the final time
so the full deposition/dissolution history remains available for plotting and
inspection. If disk usage becomes a problem, add `--cleanup-old-jobs` to delete
older heavy Abaqus job files after they are no longer the immediate restart
source. CSV history is still preserved unless `--cleanup-csv` is also supplied.

For the end-of-run cleanup path, `--join-odb` creates
`<job-prefix>_joined.odb` by appending the restart ODB files in order with
`abaqus restartjoin`. `--delete-after-join` then removes the intermediate heavy
Abaqus job files only after the joined ODB command succeeds. The interface and
Butler-Volmer CSV histories are kept by default; add `--delete-csv-after-join`
only if those CSV time histories are no longer needed.
