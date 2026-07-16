# Verifikationsreport Belluna-Adapterrahmen

Parameterstand: `78f560c8` · H_RAISE 28.0 mm · Wandstärke effektiv 63.0 mm · **Vierkantwelle 140 mm**
Material: **Würth ASA GF15, Verkehrsschwarz RAL 9017 ähnlich (Art.-Nr. 4954641200)** · E 3000 MPa · ρ 1100 kg/m³ · HDT/B(0,45 MPa) 99 °C; 1,82-MPa-Wert fehlt

## FEM-Lastfälle
| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |
|---|---|---|---|---|
| LF1_wind | 1.29 | 11.25 | 0.008 (≤ 0.5) | PASS |
| LF2_schlechtweg | 0.44 | 11.25 | 0.002 (≤ 0.5) | PASS |
| LF3_klemmung | 2.74 | 4.50 | 0.015 (≤ 0.5) | PASS |
| LF4_schnee | 0.22 | 11.25 | 0.001 (≤ 0.5) | PASS |

## Stoß-Submodell
max vM 2.41 MPa ≤ 11.25 MPa → PASS

## Analytische Nachweise
- Haubenfreigang über Dachkante: **OFFEN** — kein Überlapp laut Schätzwerten (EDGE_DIST=250, EDGE_H=55); vor Druckfreigabe messen (Messpunkte B1/B2)
- Elastikfugen-Auslastung (Thermik, LF5; vollständig gefügter 540-mm-Rahmen): 41 % → PASS
- Materialtemperatur: T_MAX 85 °C; Würth nennt nur HDT/B(0,45 MPa) 99 °C, keinen 1,82-MPa-Wert. Weißer RAL-9003-Decklack ist Pflicht; Temperatur-Abminderung 0.50 angewendet
- Stoß analytisch: τ 0.27/5.62 MPa, 2×M5 je 3.49 MPa, ein M5 im Restfall 6.98/11.25 MPa → PASS
- Klebfugen-Schub aus Last: 0.011 ≤ 0.05 N/mm² → PASS
- Seitenschrauben-Auszug: 178 N zulässig ≥ 100 N erforderlich → PASS
- Fertigungslogik: 1 rotationsidentisches Universal-Segment ×4; Belluna-Vollmaterialrippen ±140/±165 auf jeder Seite, zwei M5 je Segmentstoß, geschlossener Unterkragen
- Belluna-Kragenpassung: nominal 1.5 mm Radialluft mit **gemessenem** A3a=397 mm
- Dachinterface: 25-mm-Elastikfuge vollständig über nachzurüstendem Holzrahmen ≥30 mm; keine Holzverschraubung. X150-Dach ist 35 mm stark; Holzrahmen-Status vor Montage offen

# Gesamtergebnis: **PASS mit Vorbehalt** (offene Mess-/Einbauvoraussetzungen vor Druck und Montage prüfen)

## Datei-Manifest

Git-Commit: `ba09897ac3e3d130885a5d73a99a6a0cf9d9c3fd` · GEOM_REV: `7`

| Datei | SHA256 |
|---|---|
| frame_78f560c8.step | `63ded6a5091adb911967ffeaec24dac9346123b8e67cf9eff3de6ffbc9d48d7c` |
| universal_segment_x4_78f560c8.step | `f54fac9d938024ee968cdcbafd0c21590dab2a4dfad13f640df0d0502dcc0c0f` |
| universal_segment_x4_78f560c8.stl | `99a6daa78f7949ad72dc71a743594d3c7efd53fdc8623c0e1e66e0658a15adfd` |
| universal_segment_x4_78f560c8.3mf | `f0aae486b71cef545ef2d94adc176a259d41b0991e4b35d3c92b99b5485eda4f` |
| montagenotiz_78f560c8.md | `6fc5360be77ce6ccb561452427bad686ed65a03b4d442a698ec648948c7c16c3` |
