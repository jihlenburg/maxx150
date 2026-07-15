# Referenzen

Dieser Ordner enthält unveränderte Herstellerunterlagen, Fahrzeugreferenzen
und die projektseitige Belluna-Rekonstruktion. Er ist **keine** Ablage für
generierte Projektartefakte; diese liegen unter `build/` beziehungsweise
`release/current/`.

## Klassifikation

- `belluna/manuals/`: unveränderte Belluna-Einbauanleitung.
- `belluna/models/`: aus Fotos und Messwerten rekonstruierte STEP-/STL-Modelle.
  Sie sind kein Hersteller-CAD. Erzeugung: `python3 -m pipeline references`.
- `vehicle/`: vom Fahrzeughalter bereitgestellte Referenzbilder.
- `datasheets/adhesives/`: eingesetzte oder qualifizierte Kleb-/Dichtstoffe.
- `datasheets/adhesives/evaluated-not-selected/`: bewertete, bewusst nicht
  gewählte Produkte.
- `datasheets/coatings/`: Primer und Decklack.
- `datasheets/materials/`: Materialherkunft und Herstellerlinks.

`catalog.json` dokumentiert Quelle, Projektstatus und SHA-256 der statischen
Dateien. Der Test `test_reference_catalog.py` schützt die Ablage gegen stille
Änderungen oder fehlende Unterlagen.

## Produktstatus

| Funktion | Produkt | Status |
|---|---|---|
| Segmentstöße | WEICON RK-1300 | ausgewählt; Originalmaterial-Coupon Pflicht |
| Dach/Belluna | Carloflex 410 UV weiß | Belluna-Referenzweg; öffentliche TDS nicht verfügbar |
| Dach/Belluna | Sikaflex-522 weiß | qualifizierte Alternative; nicht mit Carloflex mischen |
| Holz/GFK/XPS | SikaForce-710 L35 + SikaForce-010 | ausgewählt; professioneller Misch-/Pressprozess |
| Segmentstöße | WEICON Epoxyd-Minutenkleber | bewertet, nicht gewählt |
| Dach/Belluna | Sikaflex-521 UV | bewertet, durch 522 abgelöst |
| Lackaufbau | Mipa Plastic-Grundierfiller + PUR HS | ausgewählt; Haftcoupon Pflicht |

Sicherheitsdatenblätter werden wegen ihrer häufigeren Aktualisierung nicht als
eingefrorene Kopien gepflegt. Vor Verarbeitung ist stets die aktuelle Fassung
vom Hersteller abzurufen.
