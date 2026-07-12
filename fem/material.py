"""Homogenisierte ASA-Materialkarte für CalculiX (Spec §6).
Steifigkeit mit INFILL_FACTOR abgemindert (Perimeter + 40 % Gyroid);
Festigkeitsbewertung erfolgt NICHT hier, sondern gegen params.allowables()."""
import params as PRM


def fem_material_dict(p: PRM.Params = PRM.P) -> dict:
    return {
        "Name": "ASA-homogenisiert",
        "YoungsModulus": f"{p.E_BASE * p.INFILL_FACTOR} MPa",
        "PoissonRatio": str(p.NU),
        "Density": f"{p.RHO} kg/m^3",
    }
