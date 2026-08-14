# Referenzen

Dieser Ordner enthält unveränderte Herstellerunterlagen, nachvollziehbare
Quellenprotokolle, Fahrzeugreferenzen und die projektseitige
Belluna-Rekonstruktion. Er ist **keine** Ablage für generierte
Projektartefakte; diese liegen unter `build/` beziehungsweise
`release/current/`.

## Klassifikation

- `belluna/manuals/`: unveränderte Belluna-Einbauanleitung.
- `belluna/models/`: aus Fotos und Messwerten rekonstruierte STEP-/STL-Modelle.
  Sie sind kein Hersteller-CAD. Erzeugung: `python3 -m pipeline references`.
- `vehicle/`: vom Fahrzeughalter bereitgestellte Referenzbilder.
- `datasheets/adhesives/`: eingesetzte oder qualifizierte Kleb-/Dichtstoffe.
  Wenn eine bereitgestellte Binärdatei nicht im Repo liegt, hält ein
  Quellenprotokoll Originalname, SHA-256 und die verwendeten Kennwerte fest.
- `datasheets/adhesives/evaluated-not-selected/`: bewertete, bewusst nicht
  gewählte sowie abgelöste Produkte. Der Status `evaluated_field_failure`
  kennzeichnet dabei ein Produkt, das nicht am Schreibtisch, sondern erst am
  realen Bauteil ausgeschieden ist.
- `datasheets/process/`: eingefrorene Hersteller-Prozessgrundlagen für
  Vorbehandlung, Aushärtung und Fugenbearbeitung.
- `datasheets/coatings/`: Primer und Decklack.
- `datasheets/materials/`: Materialherkunft und Herstellerlinks.

`catalog.json` dokumentiert Quelle, Projektstatus und SHA-256 der statischen
Dateien. Der Test `test_reference_catalog.py` schützt die Ablage gegen stille
Änderungen oder fehlende Unterlagen.

## Produktstatus

| Funktion | Produkt | Status |
|---|---|---|
| Segmentstöße | UHU plus endfest (90 min), 2K-Epoxid | ausgewählt; rechnerisch auf 0,50 MPa abgemindert |
| Segmentstöße | WEICON RK-1300 | am realen Bauteil gescheitert, 2026-08-14 durch UHU plus endfest ersetzt |
| Dach/Belluna | Sikaflex-522 weiß | Standardweg; 0,030 MPa normal / 0,050 MPa Schub, Vorbehandlung namentlich dokumentiert |
| Äußere Schutzkehle | Sika Abglättmittel N | ausgewähltes, wasserbasiertes Sika-Glättmittel; Verträglichkeit am ausgehärteten Originallack vorprüfen |
| Dach/Belluna | Carloflex 410 UV weiß | Belluna-konforme Alternative mit denselben Projektgrenzwerten; erst einsetzen, wenn der im TDS nicht benannte Kunststoffprimer prozesssicher festgelegt ist |
| Holz/GFK/XPS | SikaForce-710 L35 + SikaForce-010 | ausgewählt; professioneller Misch-/Pressprozess |
| Segmentstöße | WEICON Epoxyd-Minutenkleber | bewertet, nicht gewählt; Tg 44,7 °C liegt unter `T_MAX`. Auch als 2K-Epoxid kein Ersatz für das ausgewählte UHU-Produkt |
| Dach/Belluna | Sikaflex-521 UV | bewertet, durch 522 abgelöst |
| Lackaufbau | Mipa Plastic-Grundierfiller + PUR HS | ausgewählt; Klebezonen bleiben lackfrei |

Sicherheitsdatenblätter werden wegen ihrer häufigeren Aktualisierung nicht als
eingefrorene Kopien gepflegt. Vor Verarbeitung ist stets die aktuelle Fassung
vom Hersteller abzurufen.
