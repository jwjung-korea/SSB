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
