# Verifikationsreport Belluna-Adapterrahmen

Parameterstand: `83aeba39` · H_RAISE 28.0 mm · Wandstärke effektiv 63.0 mm · **Vierkantwelle 140 mm**
Material: **Würth ASA GF15, Verkehrsschwarz RAL 9017 ähnlich (Art.-Nr. 4954641200)** · E 3000 MPa · ρ 1100 kg/m³ · HDT/B(0,45 MPa) 99 °C; 1,82-MPa-Wert fehlt

## FEM-Lastfälle
| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |
|---|---|---|---|---|
| LF1_wind | 0.74 | 11.25 | 0.001 (≤ 0.5) | PASS |
| LF2_schlechtweg | 0.37 | 11.25 | 0.001 (≤ 0.5) | PASS |
| LF3_klemmung | 1.35 | 4.50 | 0.004 (≤ 0.5) | PASS |
| LF4_schnee | 0.11 | 11.25 | 0.000 (≤ 0.5) | PASS |

## Stoß-Submodell
max vM 3.38 MPa ≤ 11.25 MPa → PASS

## Analytische Nachweise
- Haubenfreigang über Dachkante: **OFFEN** — kein Überlapp laut Schätzwerten (EDGE_DIST=250, EDGE_H=55); vor Druckfreigabe messen (Messpunkte B1/B2)
- Elastikfugen-Auslastung (Thermik, LF5; vollständig gefügter 500-mm-Rahmen): 38 % → PASS
- Materialtemperatur: T_MAX 85 °C; Würth nennt nur HDT/B(0,45 MPa) 99 °C, keinen 1,82-MPa-Wert. Weißer RAL-9003-Decklack ist Pflicht; Temperatur-Abminderung 0.50 angewendet
- Stoß analytisch: τ 0.38/5.62 MPa, Lochleibung 6.98/11.25 MPa → PASS
- Klebfugen-Schub aus Last: 0.034 ≤ 0.1 N/mm² → PASS
- Seitenschrauben-Auszug: 356 N zulässig ≥ 100 N erforderlich → PASS
- Fertigungslogik: 1 rotationsidentisches Universal-Segment ×4; Belluna-Vollmaterialrippen ±140/±165 auf jeder Seite, Dachschrauben unabhängig umlaufend ±140
- Belluna-Kragenpassung: nominal 1.5 mm Radialluft mit **gemessenem** A3a=397 mm
- Dachinterface: 8× ST4.2×25 in nachzurüstenden Holzrahmen ≥30 mm; X150-Dach ist 35 mm gesamt und besitzt im Bestand keinen Schraubgrund; Status vor Montage offen

# Gesamtergebnis: **PASS mit Vorbehalt** (offene Mess-/Einbauvoraussetzungen vor Druck und Montage prüfen)

## Datei-Manifest

Git-Commit: `1a7bd3289a95c4659ffbc3401632c657e754ba49` · GEOM_REV: `6`

| Datei | SHA256 |
|---|---|
| frame_83aeba39.step | `3f92289f000c167b1f99354301b86df0e5dcf2db79caf474c15abc107d3235aa` |
| universal_segment_x4_83aeba39.step | `a9f77eb746e41f373b6b41400b457d48c064c9210cec80875900f0dedb674735` |
| universal_segment_x4_83aeba39.stl | `8d9153845ae6f593282acf560ce12112ff4978c5aa2a671019bbd27c6d01b212` |
| universal_segment_x4_83aeba39.3mf | `a93f27b839aa6248f57c048517c84b4f38d1034227751ac08e3dfa421f3e8691` |
| montagenotiz_83aeba39.md | `d06e8f891fcf4bbd8962663944e78c0c5e6565c038799711a9a710dabfa855ed` |
