# CFD-Modell und Windlasten

## Zweck und Status

Die CFD-Stufe schätzt globale Kräfte und Momente auf den Belluna Super Fan.
Sie ergänzt den konservativen analytischen Windlastansatz, ersetzt ihn aber
nicht. Alle Ergebnisse tragen bis zur vollständigen Varianten- und
Konvergenzprüfung den Status `PRELIMINARY_CFD` und `INFORMATIONAL_ONLY`.

```sh
python3 -m pipeline cfd
```

Der Befehl erzeugt die Geometrie und drei Fälle neu, prüft die Oberflächen,
vernetzt mit `snappyHexMesh`, initialisiert mit `potentialFoam`, rechnet
stationär mit `simpleFoam`/k-ω-SST und schreibt je Fall `result.json` sowie
`report.md`. Danach entstehen eine gemeinsame Netzsensitivität und ein
separater, ausdrücklich nicht freigabewirksamer CalculiX-Strukturcheck.

## Geometrie und Provenienz

Quelle ist die maßstäbliche Produktdarstellung auf Seite 10 der
[Belluna-Einbauanleitung](../references/belluna/manuals/belluna-super-fan-installation.pdf):

| Größe | Dokumentierter Wert |
|---|---:|
| Haubenlänge | 593 mm |
| Haubenbreite | 420 mm |
| Montageplatte | 450 mm |
| Höhe geschlossen | 127 mm über Montageebene |
| Höhe vollständig geöffnet | 182 mm über Montageebene |

`reference_models/belluna_aero.py` loftet daraus eine glatte aerodynamische
Hülle. Die Zwischenquerschnitte sind visuell aus Seiten- und Draufsicht
rekonstruiert. Sicken, Antriebe, Schrauben und kleine Radien fehlen bewusst.
Die 28-mm-Plinthe und die 55-mm-Dachkante sind getrennte Oberflächen. Das
Modell ist als `AERODYNAMIC_ENVELOPE_RECONSTRUCTION` gekennzeichnet und kein
Belluna-Hersteller-CAD.

STEP bleibt in Millimetern; die OpenFOAM-STLs werden direkt in Metern
geschrieben. Ein separates Manifest bindet Anleitung, Quellcommit,
Modellklassifikation und SHA-256 aller Geometriedateien.

## Fallmatrix

Die reproduzierbare Matrix enthält:

| Fall | Haube | Nahfeld | Belluna-Oberfläche | Zweck |
|---|---|---:|---:|---|
| `closed_front_coarse` | geschlossen | 2 | 3–4 | Vergleichsbasis |
| `open_front_coarse` | vollständig offen | 2 | 3–4 | Zustandsvergleich |
| `open_front_medium` | vollständig offen | 3 | 4–5 | Netzsensitivität |

Alle Fälle verwenden:

- den jeweils in der Tabelle genannten Haubenzustand und den 28-mm-Adapter,
- 55-mm-Dachkante bei dem noch unbestätigten Abstand aus `params.py`,
- 200 km/h Frontalanströmung,
- Luftdichte 1,2 kg/m³ und kinematische Viskosität 1,5·10⁻⁵ m²/s,
- 5 % Turbulenzintensität und 0,1 m Längenskala,
- stationäres RANS mit k-ω-SST,
- keine Prismenschichten.

Der OpenFOAM-Lauf auf Quellcommit `4a9e437` und die korrigierte
Gesamtbaugruppen-Auswertung auf `59775a0` ergeben Matrix `a3a2de8c`. Die
äußere 500-mm-Aerogeometrie stimmt wieder mit dem aktuellen Hybridadapter
`652716b5` überein. Doppelraupe, Entlüftungen und seitliche Schraubpfade liegen
im Dachinterface und verändern die umströmte Hülle nicht. Der nachgeschaltete
CalculiX-Strukturcheck wurde für `652716b5` neu gerechnet. Unabhängig davon
bleibt nur die analytische 480-N-Hülle freigabewirksam. Die Tabelle summiert
jeweils **Belluna plus direkt angeströmte Adapteroberfläche**; alle Momente
sind auf die Mitte der Adapterbasis `(0, 0, 0)` transformiert. Gemittelt werden
die letzten 20 Kraftausgaben (100 Solveriterationen):

| Fall | CFD-Hash | Zellen | Fx [N] | Fy [N] | Fz [N] | My [Nm] | Widerstands-CoV |
|---|---|---:|---:|---:|---:|---:|---:|
| geschlossen, grob | `826d6dae` | 148.448 | 30,92 | 0,03 | 167,74 | +9,99 | 0,01 % |
| offen, grob | `656cdb1a` | 204.572 | 51,67 | 2,50 | 178,62 | −1,02 | 0,95 % |
| offen, mittel | `6840c107` | 1.001.494 | 42,42 | 1,14 | 187,19 | −0,17 | 0,74 % |

Das um Faktor 4,90 größere offene Mittelnetz ändert den Widerstand gegenüber
dem Grobnetz noch um 21,8 % und den Auftrieb um 4,6 %. Das Basismoment `My`
wandert von −1,02 auf −0,17 Nm; seine große relative Änderung ist wegen der
Nähe zu null kein sinnvoller Konvergenzmaßstab. `Fy`, `Mx` und `Mz` sind bei
der symmetrischen Frontalanströmung ebenfalls klein. Die Hauptkomponenten
zeigen: Der Auftrieb ist vergleichsweise stabiler, der Widerstand noch nicht.

Keines der Netze besteht alle `checkMesh`-Prüfungen. Das offene Mittelnetz
senkt den Anteil konkaver Cut-Cells von 3,22 % auf 2,73 %, enthält aber 16
stark verzerrte Flächen und eine Zelle knapp unter dem Determinantenlimit.
Außerdem erreicht der stationäre Mittelnetzlauf bei Iteration 500 nicht alle
gesetzten Residualziele; die offene Ablöseströmung bleibt leicht
oszillierend. Globale Kraftgrößen sind damit als Vorabschätzung brauchbar,
lokale Druckspitzen oder Strömungsdetails nicht.

## Lastübergabe an CalculiX

Nur `open_front_medium` wird mit dem Modellfaktor 1,5 in einen zusätzlichen
kombinierten Rahmenlastfall übergeben. Die drei Kraftkomponenten wirken auf
der Adapter-Deckfläche; das Nickmoment `My` wird als vertikales Kräftepaar an
Front- und Heckaußenwand eingeleitet. `Mx` und `Mz` werden ausgewiesen, aber
noch nicht in das bestehende Selektormodell übertragen.

Die aktuelle Strukturkopplung enthält zusätzlich mittlere
Spannungsindikatoren für die Doppelraupe, den konservativen analytischen
Segmentstoßnachweis und eine ideale Gleichverteilung auf acht
Belluna-Schrauben. Die acht unteren Seitenschrauben werden auch hier bewusst
nicht als Tragfähigkeit angerechnet.

Der Lauf `a3a2de8c` übergibt nach Faktor 1,5:

| Komponente | Übergebene Last | Vergleich | Einordnung |
|---|---:|---:|---|
| horizontal, resultierend | 63,65 N | 480 N LF1-Hülle | 13,3 % |
| Auftrieb +z | 280,79 N | 255,06 N LF2-Vertikalbetrag | 110,1 %; Gegenrichtung, daher nicht als durch LF2 abgedeckt behauptet |
| Nickmoment `My` um Basis | −0,251 Nm | 88,8 Nm LF1-Hülle | 0,3 % |
| Roll-/Giermoment um Basis | 0,110 / 0,320 Nm | — | ausgewiesen; äquivalentes `Mx/Mz` im CalculiX-Fall nicht eingeleitet |

Der kombinierte Produktionsnetz-FEM-Fall ergibt 0,227 MPa von Mises bei
11,25 MPa Kurzzeitzulässigkeit und 0,00070 mm Deckflächenverformung bei
0,5 mm Grenzwert. Das ist nur 2,0 % Spannungs- und 0,14 %
Verformungsauslastung im idealisierten monolithischen Rahmenmodell.

Lastpfad-Indikatoren nach Modellfaktor:

- Doppelraupe 33.439 mm²: 0,00190 MPa mittlere Schubspannung und
  0,00840 MPa mittlere Zugspannung. Maßgebend bleiben die strengeren
  0,050/0,030-MPa-Projektwerte unter der analytischen 480-N-Hülle.
- Konservativ ein einzelner Segmentstoß unter der vollen Horizontallast:
  0,0509/5,625 MPa Schub und 0,926/11,25 MPa Lochleibung mit einem M5.
- Ideale Verteilung der Auftriebslast auf acht Belluna-Schrauben: 35,1 N je
  Schraube gegenüber 356 N rechnerischer ASA-Wand-Auszugreferenz.
- Die zwei 10-mm-Raupen sind der allein angerechnete Adapter-Dach-Primärpfad.
  Acht seitliche ST4.2×25 sind physisch vorhanden, bleiben mangels geprüfter
  Holz-/GFK-/Gewindetragfähigkeit jedoch unbewertete Reserve. Der vollständige
  annahmenbasierte Nachweis steht in [Lastpfade](load-paths.md).

Die kleine Rahmenauslastung bedeutet deshalb nicht, dass die Gesamtmontage
mit demselben Sicherheitsfaktor freigegeben wäre. Die derzeit plausibel
schwächeren beziehungsweise unsichereren Glieder sind Haftung des gewählten
Dichtstoffs auf Lack und X150-GFK, der nachgerüstete Holzrahmen, das lokale
GFK-Dach und die reale Lastverteilung in der Doppelraupe. Die bestehende
480-N-Horizontallast bleibt unverändert freigabewirksam.

## Nächste Gates

Vor einer **freigabewirksamen** Kopplung in die FEM sind mindestens
erforderlich:

1. Feinnetz ergänzen und Grob-/Mittel-/Feinnetz-Konvergenz für Kräfte und
   Momente bewerten.
2. Verbesserung oder begründete Akzeptanz der konkaven Cut-Cells.
3. Geschlossene und vollständig geöffnete Haube.
4. Frontal-, Heck-, ±30°- und 90°-Anströmung.
5. Sensitivität für Dachkantenabstand und vorgeschaltete Grenzschicht.
6. Plausibilisierung gegen eine einfache Kraft- oder Druckmessung.

Erst danach darf eine Lastkomponente automatisch an CalculiX übergeben
werden. Bis dahin gilt komponentenweise mindestens die bestehende analytische
Hülllast; CFD darf sie nur erhöhen, nicht reduzieren.
