"""Homogenisierte ASA-Materialkarte für CalculiX (Spec §6).
Steifigkeit mit INFILL_FACTOR abgemindert (Perimeter + 40 % Gyroid);
Festigkeitsbewertung erfolgt NICHT hier, sondern gegen params.allowables()."""
import params as PRM


def fem_material_dict(p: PRM.Params = PRM.P) -> dict:
    """CalculiX-Materialkarte für den homogenisierten ASA-Druckkörper:
    E-Modul mit INFILL_FACTOR abgemindert (MPa), Querkontraktion NU und Dichte
    RHO (kg/m^3). Enthält bewusst keine Festigkeit -- die wird gegen
    ``params.allowables()`` bewertet."""
    return {
        "Name": "ASA-homogenisiert",
        "YoungsModulus": f"{p.E_BASE * p.INFILL_FACTOR} MPa",
        "PoissonRatio": str(p.NU),
        "Density": f"{p.RHO} kg/m^3",
    }
