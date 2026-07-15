import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REFERENCES = ROOT / "references"


def test_referenzkatalog_ist_vollstaendig_und_unveraendert():
    catalog = json.loads((REFERENCES / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["schema"] == 1
    paths = set()
    for entry in catalog["files"]:
        path = REFERENCES / entry["path"]
        assert entry["path"] not in paths, f"doppelter Katalogeintrag: {entry['path']}"
        paths.add(entry["path"])
        assert path.is_file(), f"Referenz fehlt: {path}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
        assert entry["status"] and entry["source"]
    expected = {
        path.relative_to(REFERENCES).as_posix()
        for path in REFERENCES.rglob("*")
        if path.is_file()
        and "belluna/models" not in path.relative_to(REFERENCES).as_posix()
        and path.name not in {"README.md", "catalog.json"}
    }
    assert paths == expected, f"Katalogabweichung: fehlt={expected - paths}, extra={paths - expected}"


def test_auswahldokumentation_deckt_alle_produktklassen_ab():
    text = (REFERENCES / "README.md").read_text(encoding="utf-8")
    for product in ("RK-1300", "Carloflex 410 UV", "Sikaflex-522",
                    "SikaForce-710 L35", "Epoxyd-Minutenkleber", "Mipa"):
        assert product in text
