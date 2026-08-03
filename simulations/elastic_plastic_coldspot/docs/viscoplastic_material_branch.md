# Viscoplastic Lithium Material Branch

This branch changes only the lithium constitutive material definition used by the existing coldspot meshes. Geometry, mesh, contacts, boundary conditions, loads, and step definitions are intentionally left unchanged.

## What Changed

The lithium user material blocks were changed from the simplified 11-constant elastic-plastic form to the 16-constant rate-sensitive Fe-Fp-Fg form used by the original `coldspots` model:

```text
Eyoung, poisson, Apre, Qact, T0, mRate, Y0, H0,
Ysat, ahard, nhard, Omega, alpha1, alpha2, alpha3, cDot
```

Current values:

| Parameter | Value | Meaning |
|---|---:|---|
| `Eyoung` | `7.81e3 MPa` | Lithium Young's modulus |
| `poisson` | `0.38` | Poisson's ratio |
| `Apre` | `4.254e4` | Pre-exponential factor |
| `Qact` | `37 kJ/mol` | Activation energy |
| `T0` | `298 K` | Temperature |
| `mRate` | `0.15` | Rate sensitivity |
| `Y0` | `0.95 MPa` | Initial tensile resistance |
| `H0` | `10 MPa` | Hardening modulus in tension |
| `Ysat` | `2.0 MPa` | Saturation tensile resistance |
| `ahard` | `2.0` | Hardening exponent |
| `nhard` | `0.05` | Rate-dependent saturation exponent |
| `Omega` | `1.3e-05` | Molar-volume/growth factor |
| `alpha1` | `0.0` | Growth direction factor |
| `alpha2` | `1.0` | Growth direction factor |
| `alpha3` | `0.0` | Growth direction factor |
| `cDot` | `103.643` for `LITHIUM_IP`, `0.0` for `LITHIUM_SUB` | Plating/stripping concentration rate |

## Difference From Previous Branch

Previous material blocks used 11 constants:

```text
Eyoung, poisson, Y0, H0, Ysat, ahard, Omega, alpha1, alpha2, alpha3, cDot
```

The UMAT then used a rate-independent plastic correction:

```text
dGamma = (tauBar_tr - S_t) / (Gshear + H_t)
nuP_tau = dGamma / dtime
```

This branch restores a rate-sensitive viscoplastic update based on the original model:

```text
nu0 = sqrt(3) * Apre * exp(-Qact / (Rgas * T0))
g(nuP) = tauBar_tr
       - dtime * Gshear * nuP
       - S_tau * (nuP / nu0)^mRate
```

The UMAT solves this scalar equation for `nuP` each increment. In practice, lithium can relax contact stresses over time more than the simplified elastic-plastic branch.

## Files Touched

Only these categories were changed:

```text
simulations/elastic_plastic_coldspot/src/umat_EP_coldspot.for
simulations/elastic_plastic_coldspot/inputs/*.inp
```

The input edits are limited to `*User Material` lithium blocks. Contact definitions, surfaces, interactions, amplitudes, loads, boundary conditions, mesh, and analysis steps were not intentionally changed.
