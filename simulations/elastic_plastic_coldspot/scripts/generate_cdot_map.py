"""Generate a UMAT cdot map for staggered contact-current coupling.

The UMAT reads ``cdot_map.csv`` from the Abaqus job working directory.
This script converts interface data from an ODB extraction step into that
map. It preserves the total applied current by normalizing the local weights.

Expected input columns:
    X_coordinate

Optional contact columns, used in this priority order:
    COPEN, CPRESS
    CPRESS
    S22_Stress

If no contact information is available, the first block can still be seeded
from the prescribed coldspot factor alone.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def cold_factor(x: float) -> float:
    """Initial electrochemical defect: 10% conductance near x=9-11 um."""
    if x < 8.5:
        return 1.0
    if x <= 9.0:
        return 1.0 - 0.9 * (x - 8.5) / 0.5
    if x < 11.0:
        return 0.1
    if x <= 11.5:
        return 0.1 + 0.9 * (x - 11.0) / 0.5
    return 1.0


def pressure_weight(value: float, pressure_scale: float, open_weight: float) -> float:
    p = max(value, 0.0)
    if pressure_scale <= 0.0:
        return max(open_weight, p)
    return open_weight + (1.0 - open_weight) * (1.0 - math.exp(-p / pressure_scale))


def row_weight(row: dict[str, str], pressure_scale: float, open_tol: float,
               open_weight: float) -> float:
    if "COPEN" in row and row["COPEN"] != "":
        copen = float(row["COPEN"])
        if copen > open_tol:
            return open_weight
        if "CPRESS" in row and row["CPRESS"] != "":
            return pressure_weight(float(row["CPRESS"]), pressure_scale, open_weight)
        return 1.0

    if "CPRESS" in row and row["CPRESS"] != "":
        return pressure_weight(float(row["CPRESS"]), pressure_scale, open_weight)

    if "S22_Stress" in row and row["S22_Stress"] != "":
        # Abaqus compression is often negative for S22 in these exports.
        return pressure_weight(-float(row["S22_Stress"]), pressure_scale,
                               open_weight)

    return 1.0


def normalize_weights(xs: list[float], weights: list[float]) -> list[float]:
    if not xs:
        raise ValueError("No interface points found.")

    total_weight = sum(weights)
    if total_weight <= 0.0:
        return [1.0 for _ in weights]

    mean_weight = total_weight / float(len(weights))
    return [w / mean_weight for w in weights]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("interface_csv", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("cdot_map.csv"))
    parser.add_argument("--base-cdot", type=float, default=103.643)
    parser.add_argument("--sign", type=float, choices=(-1.0, 1.0), default=1.0,
                        help="Use -1 for stripping blocks and +1 for plating.")
    parser.add_argument("--pressure-scale", type=float, default=1.0,
                        help="MPa scale for CPRESS/S22 contact weighting.")
    parser.add_argument("--open-tol", type=float, default=1e-6,
                        help="Gap tolerance above which COPEN is treated open.")
    parser.add_argument("--open-weight", type=float, default=1e-6,
                        help="Residual conductance for open contact.")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    with args.interface_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    points: list[tuple[float, float]] = []
    raw_weights: list[float] = []
    for row in rows:
        x = float(row["X_coordinate"])
        w = cold_factor(x) * row_weight(row, args.pressure_scale, args.open_tol,
                                        args.open_weight)
        points.append((x, w))

    points.sort(key=lambda item: item[0])
    xs = [x for x, _ in points]
    raw_weights = [w for _, w in points]
    norm_weights = normalize_weights(xs, raw_weights)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "cdot"])
        for x, w in zip(xs, norm_weights):
            writer.writerow([f"{x:.8g}", f"{args.sign * args.base_cdot * w:.12g}"])


if __name__ == "__main__":
    main()
