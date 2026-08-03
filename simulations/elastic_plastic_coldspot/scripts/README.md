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
