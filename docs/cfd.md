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

- geschlossene Haube und 28-mm-Adapter,
- 55-mm-Dachkante bei dem noch unbestätigten Abstand aus `params.py`,
- 200 km/h Frontalanströmung,
- Luftdichte 1,2 kg/m³ und kinematische Viskosität 1,5·10⁻⁵ m²/s,
- 5 % Turbulenzintensität und 0,1 m Längenskala,
- stationäres RANS mit k-ω-SST,
- keine Prismenschichten.

Der erste vollständige Lauf des CFD-Hashs `5acfaf80` auf dem rechnerischen
Quellcommit `5df2d37` ergab im Mittel der letzten 20 Ausgaben ungefähr 11,9 N
Widerstand, 157,7 N Auftrieb und 7,98 Nm Nickmoment. Die Zeitreihe war
stationär, aber das Ergebnis ist noch nicht physikalisch freigegeben: Das
Grobnetz besitzt 148.448 Zellen und `checkMesh` markiert etwa 3,56 % konkave
Cut-Cells. Der bisherige Strukturnachweis bleibt deshalb unverändert bei
mindestens 480 N horizontaler Hülllast. Die Zahlen der neuen offenen
Fallmatrix werden erst nach einem vollständigen, an den Quellcommit gebundenen
Pipeline-Lauf in dieses Dokument übernommen.

## Lastübergabe an CalculiX

Nur `open_front_medium` wird mit dem Modellfaktor 1,5 in einen zusätzlichen
kombinierten Rahmenlastfall übergeben. Die drei Kraftkomponenten wirken auf
der Adapter-Deckfläche; das Nickmoment `My` wird als vertikales Kräftepaar an
Front- und Heckaußenwand eingeleitet. `Mx` und `Mz` werden ausgewiesen, aber
noch nicht in das bestehende Selektormodell übertragen.

Die Auswertung enthält zusätzlich mittlere Spannungsindikatoren für die
Kleberille, den konservativen analytischen Segmentstoßnachweis und eine ideale
Gleichverteilung auf acht Belluna- beziehungsweise acht Dachschrauben. Letztere
ist ausdrücklich kein Schrauben- oder GFK-Dach-Kapazitätsnachweis.

## Nächste Gates

Vor einer Kopplung in die FEM sind mindestens erforderlich:

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
