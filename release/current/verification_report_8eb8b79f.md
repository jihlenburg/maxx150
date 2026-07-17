# Verifikationsreport Belluna-Adapterrahmen

Parameterstand: `8eb8b79f` · H_RAISE 28.0 mm · Wandstärke effektiv 63.0 mm · **Vierkantwelle 140 mm**
Material: **Würth ASA GF15, Verkehrsschwarz RAL 9017 ähnlich (Art.-Nr. 4954641200)** · E 3000 MPa · ρ 1100 kg/m³ · HDT/B(0,45 MPa) 99 °C; 1,82-MPa-Wert fehlt

## FEM-Lastfälle
| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |
|---|---|---|---|---|
| LF1_wind | 0.65 | 11.25 | 0.004 (≤ 0.5) | PASS |
| LF2_schlechtweg | 0.12 | 11.25 | 0.001 (≤ 0.5) | PASS |
| LF3_klemmung | 0.76 | 4.50 | 0.008 (≤ 0.5) | PASS |
| LF4_schnee | 0.06 | 11.25 | 0.001 (≤ 0.5) | PASS |

## Stoß-Submodell
max vM 3.37 MPa ≤ 11.25 MPa → PASS

## Analytische Nachweise
- Haubenfreigang über Dachkante: **OFFEN** — kein Überlapp laut Schätzwerten (EDGE_DIST=250, EDGE_H=55); vor Druckfreigabe messen (Messpunkte B1/B2)
- Elastikfugen-Auslastung (Thermik, LF5; vollständig gefügter 500-mm-Rahmen): 38 % → PASS
- Materialtemperatur: T_MAX 85 °C; Würth nennt nur HDT/B(0,45 MPa) 99 °C, keinen 1,82-MPa-Wert. Weißer RAL-9003-Decklack ist Pflicht; Temperatur-Abminderung 0.50 angewendet
- Stoß analytisch: τ 0.38/5.62 MPa, 1×M5 je 6.98 MPa/11.25 MPa → PASS
- Klebfugen-Schub aus Last: 0.014 ≤ 0.05 N/mm² → PASS
- Seitenschrauben-Auszug: 178 N zulässig ≥ 100 N erforderlich → PASS
- Fertigungslogik: 1 rotationsidentisches Universal-Segment ×4; Belluna-Vollmaterialrippen ±140/±165 auf jeder Seite, 1 M5 je Segmentstoß, Hybrid-Unterkragen
- Belluna-Kragenpassung: nominal 1.5 mm Radialluft mit **gemessenem** A3a=397 mm
- Dachinterface: 2×10-mm-Elastikraupe vollständig über nachzurüstendem Holzrahmen ≥30 mm; 8 seitliche Rückfallschrauben werden rechnerisch nicht angerechnet. X150-Dach ist 35 mm stark; Holzrahmen-Status vor Montage offen

# Gesamtergebnis: **PASS mit Vorbehalt** (offene Mess-/Einbauvoraussetzungen vor Druck und Montage prüfen)

## Datei-Manifest

Git-Commit: `6c5d3517d4e7c1550701f112a8b76b3607c69d5a` · GEOM_REV: `10`

| Datei | SHA256 |
|---|---|
| frame_8eb8b79f.step | `0145b91ee00d65c850f49524f62542607f6f7115cf4381003b1a721431b9481d` |
| universal_segment_x4_8eb8b79f.step | `d48444b3afd927f0b3dbd2dbb8ca766b97bc7aa6afc55df7b21337729d799144` |
| universal_segment_x4_8eb8b79f.stl | `40da5109b71d5772a0f19312ba4cf4c6cc985fa55ae8e95669a2c36519101e60` |
| universal_segment_x4_8eb8b79f.3mf | `c8b41d2fbd7e81b83d3717eb17a9d21da4d2501545db2f133669820d293183b3` |
| montagenotiz_8eb8b79f.md | `e0791de36e661ec4fbf2c24c4342eb9445d97bb0cdd8cc1df8019ddcc76e9ef8` |
