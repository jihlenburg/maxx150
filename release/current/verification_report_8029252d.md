# Verifikationsreport Belluna-Adapterrahmen

Parameterstand: `8029252d` · H_RAISE 28.0 mm · Wandstärke effektiv 63.0 mm · **Vierkantwelle 140 mm**
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

Git-Commit: `b224eed3f4fdb7dfa360ae11a0f2bf594303b0f3` · GEOM_REV: `9`

| Datei | SHA256 |
|---|---|
| frame_8029252d.step | `6c770f61c58cf79682a46cc5ef85c3a04c431e0549d62fb909b848b239931056` |
| universal_segment_x4_8029252d.step | `5b2707d6e7cda031cc10c3faa3dbab6a0c4a2a158b8332821f41b6b269fe21b5` |
| universal_segment_x4_8029252d.stl | `4339eed4810c076efb53e4fb9191e71e3b5ee448a528f7d5a467ec71be1a9193` |
| universal_segment_x4_8029252d.3mf | `69b2054656f434d9ad1be5a4b39ae2b6fffbbfc0176f8b023834ebaa4c162f72` |
| montagenotiz_8029252d.md | `f6427fa92c87b78d227a5316b60ec38c7349bcb9216073ef98032d27990f42a1` |
