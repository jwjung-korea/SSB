"""Generate contact-aware Butler-Volmer current and UMAT cdot maps.

This is a staggered-coupling helper for Abaqus 2017-style workflows:

1. Abaqus solves the mechanical/contact block.
2. An interface CSV provides x-position and contact proxy data.
3. This script computes local reaction current density j_n(x).
4. The current distribution is converted to ``cdot_map.csv`` for the UMAT.

No electrolyte Laplace solve is included here. The electrochemical driving
force is a global overpotential, while contact and coldspot fields modify the
effective active reaction area/exchange current density along the interface.

Conventions:
    - Butler-Volmer current density is positive for anodic stripping.
    - Plating generally has negative BV current for negative overpotential.
    - UMAT cdot is positive for plating/growth and negative for stripping.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


FARADAY = 96485.33212  # C/mol
GAS_CONSTANT = 8.314462618  # J/(mol K)


def cold_factor(x_um: float) -> float:
    """Initial interfacial defect factor used for the x=9-11 um coldspot."""
    if x_um < 8.5:
        return 1.0
    if x_um <= 9.0:
        return 1.0 - 0.9 * (x_um - 8.5) / 0.5
    if x_um < 11.0:
        return 0.1
    if x_um <= 11.5:
        return 0.1 + 0.9 * (x_um - 11.0) / 0.5
    return 1.0


def smooth_pressure_weight(pressure_mpa: float, pressure_scale_mpa: float,
                           open_weight: float) -> float:
    """Map contact pressure to a 0-1 active-area factor."""
    p = max(pressure_mpa, 0.0)
    if pressure_scale_mpa <= 0.0:
        return 1.0 if p > 0.0 else open_weight
    return open_weight + (1.0 - open_weight) * (
        1.0 - math.exp(-p / pressure_scale_mpa)
    )


def contact_factor(row: dict[str, str], pressure_scale_mpa: float,
                   open_tol_um: float, open_weight: float) -> float:
    """Build an active contact factor from COPEN/CPRESS or S22 fallback."""
    if "COPEN" in row and row["COPEN"] != "":
        copen = float(row["COPEN"])
        if copen > open_tol_um:
            return open_weight
        if "CPRESS" in row and row["CPRESS"] != "":
            return smooth_pressure_weight(float(row["CPRESS"]),
                                          pressure_scale_mpa, open_weight)
        return 1.0

    if "CPRESS" in row and row["CPRESS"] != "":
        return smooth_pressure_weight(float(row["CPRESS"]), pressure_scale_mpa,
                                      open_weight)

    if "S22_Stress" in row and row["S22_Stress"] != "":
        # Abaqus compression is commonly negative in the current exports.
        return smooth_pressure_weight(-float(row["S22_Stress"]),
                                      pressure_scale_mpa, open_weight)

    return 1.0


def bv_current_density(j0_a_m2: float, eta_v: float, alpha: float,
                       temperature_k: float, concentration_ratio: float) -> float:
    """Return Butler-Volmer reaction current density in A/m^2."""
    exponent = FARADAY * eta_v / (GAS_CONSTANT * temperature_k)
    concentration_term = max(concentration_ratio, 0.0) ** alpha
    anodic = math.exp(alpha * exponent)
    cathodic = math.exp(-(1.0 - alpha) * exponent)
    return j0_a_m2 * concentration_term * (anodic - cathodic)


def normalize(values: list[float]) -> list[float]:
    """Normalize magnitudes so the arithmetic mean is one."""
    if not values:
        raise ValueError("No interface points found.")
    mean_value = sum(values) / float(len(values))
    if mean_value <= 0.0:
        return [1.0 for _ in values]
    return [v / mean_value for v in values]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("interface_csv", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("cdot_map.csv"))
    parser.add_argument("--current-output", type=Path,
                        default=Path("bv_current_distribution.csv"))
    parser.add_argument("--mode", choices=("plating", "stripping"),
                        default="plating")

    parser.add_argument("--base-cdot", type=float, default=103.643,
                        help="Mean UMAT cdot magnitude to preserve.")
    parser.add_argument("--j0", type=float, default=1.0,
                        help="Reference exchange current density in A/m^2. "
                             "Default is a practical Li|LLZO placeholder.")
    parser.add_argument("--k-neg", type=float, default=None,
                        help="Negative-electrode reaction rate constant in "
                             "mol/(m^2 s). If supplied, F*k-neg overrides j0.")
    parser.add_argument("--eta", type=float, default=-0.05,
                        help="Global overpotential in V. Negative favors plating.")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="Charge transfer coefficient.")
    parser.add_argument("--temperature", type=float, default=298.15,
                        help="Temperature in K.")
    parser.add_argument("--concentration-ratio", type=float, default=1.0,
                        help="CLi+ / CLi,all in the BV prefactor.")

    parser.add_argument("--pressure-scale", type=float, default=1.0,
                        help="MPa scale for pressure-based active contact.")
    parser.add_argument("--open-tol", type=float, default=1e-6,
                        help="Gap tolerance in micrometers for COPEN.")
    parser.add_argument("--open-weight", type=float, default=1e-6,
                        help="Residual active factor for open contact.")
    args = parser.parse_args()

    mode_sign = 1.0 if args.mode == "plating" else -1.0
    reference_j0 = FARADAY * args.k_neg if args.k_neg is not None else args.j0
    rows = read_rows(args.interface_csv)

    records: list[dict[str, float]] = []
    for row in rows:
        x = float(row["X_coordinate"])
        a_contact = contact_factor(row, args.pressure_scale, args.open_tol,
                                   args.open_weight)
        a_cold = cold_factor(x)
        active_factor = a_contact * a_cold
        j0_eff = reference_j0 * active_factor
        j_bv = bv_current_density(j0_eff, args.eta, args.alpha,
                                  args.temperature,
                                  args.concentration_ratio)
        records.append({
            "x": x,
            "contact_factor": a_contact,
            "cold_factor": a_cold,
            "active_factor": active_factor,
            "j0_eff_A_m2": j0_eff,
            "eta_V": args.eta,
            "j_bv_A_m2": j_bv,
            "j_reaction_magnitude_A_m2": abs(j_bv),
        })

    records.sort(key=lambda item: item["x"])
    normalized = normalize([r["j_reaction_magnitude_A_m2"] for r in records])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.current_output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "cdot"])
        for record, factor in zip(records, normalized):
            cdot = mode_sign * args.base_cdot * factor
            writer.writerow([f"{record['x']:.8g}", f"{cdot:.12g}"])

    with args.current_output.open("w", newline="") as f:
        fieldnames = [
            "x", "contact_factor", "cold_factor", "active_factor",
            "j0_eff_A_m2", "eta_V", "j_bv_A_m2",
            "j_reaction_magnitude_A_m2", "normalized_current_factor", "cdot"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record, factor in zip(records, normalized):
            cdot = mode_sign * args.base_cdot * factor
            out = dict(record)
            out["normalized_current_factor"] = factor
            out["cdot"] = cdot
            writer.writerow(out)


if __name__ == "__main__":
    main()
