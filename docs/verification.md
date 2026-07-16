# Nachweise und Freigabestatus

## Rechnerische Gates

Die Engineering-Stufe prüft vor jedem Export:

1. Parameterkonsistenz und geometrische Invarianten.
2. Wasserdichte, valide B-Reps und vier rotationsidentische Segmente.
3. FDM-Überhänge und definierte massive Schraub-/Stoßzonen.
4. FEM-Lastfälle Fahrtwind, Schlechtweg, Montagehüllkurve und Schnee.
5. Stoß-Submodell, Schraubenauszug, Klebfugenschub und Thermik.
6. Haubenfreigang und Wellenwahl.
7. Digitalen Belluna-Passungscheck als separate `fit`-Stufe.

Der FEM-Ansatz ist bewusst konservativ: Der globale Rahmen wird monolithisch
gerechnet, der Segmentstoß separat. Das ist kein Kontakt-/Ermüdungsmodell der
kompletten Baugruppe. Netz- und Modellgrenzen sind im jeweiligen Report
sichtbar zu halten.

Die optionale CFD-Stufe rekonstruiert die äußere Belluna-Hülle aus der
Einbauanleitung. Ihre Ergebnisse sind bis zu Netzkonvergenz, Variantenmatrix
und Korrelation ausdrücklich `INFORMATIONAL_ONLY`. Sie dürfen die bestehende
480-N-Windhülllast nicht reduzieren; ein höherer Wert würde dagegen als
Hinweis für eine Eskalation behandelt.

## Releasezustände

| Zustand | Bedeutung |
|---|---|
| `BLOCKED` | ein rechnerisches Gate ist fehlgeschlagen; kein Paket |
| `PROTOTYPE_ONLY` | rechnerische Gates bestanden, mindestens ein physisches oder gemessenes Gate offen |
| `RELEASED` | rechnerische und dokumentierte physische Gates geschlossen |

Die Release-Pipeline leitet den Status aus dem Engineering-Report ab und
schreibt ihn in `release/current/manifest.json`. Ein Dateiname allein ist
keine Freigabe.

## Noch erforderliche physische Nachweise

- XY-/Z-Prüfkörper aus realer Maschine, Düse und Charge.
- Stoßcoupon mit RK-1300 auf dem gelieferten Segmentmaterial.
- Haftcoupons des gewählten Dichtstoffs auf Rohteil, Mipa-Lack und X150-GFK.
- SikaForce-Coupon auf realem GFK/XPS/Holz-Sandwich einschließlich Pressdruck.
- Ebenheit, Öffnungsmaß und Trockenpassung eines realen Segmentsatzes.
- Reales Ausschnittmaß und Holzrahmenprüfung bei Demontage.
- Thermozyklus, Flutungstest und Sichtkontrolle nach der ersten Saison.

Bis diese Punkte dokumentiert geschlossen sind, bleibt das Projekt
`PROTOTYPE_ONLY`, unabhängig davon, wie groß die rechnerischen Reserven sind.

## Nachvollziehbarkeit

Jeder Engineering-Report enthält Parameter-Hash, GEOM_REV, Git-Revision und
SHA-256 der exportierten Dateien. Der Fit-Report bindet zusätzlich den
Quellcommit und den SHA-256 des verwendeten Belluna-Rekonstruktionsmodells.
`release/current/manifest.json` wiederholt Prüfsummen, Stückzahl und
Orientierung für die tatsächlich ausgelieferten STEP-/STL-Dateien.
