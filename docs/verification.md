# Nachweise und Freigabestatus

## Rechnerische Gates

Die Engineering-Stufe prüft vor jedem Export:

1. Parameterkonsistenz und geometrische Invarianten.
2. Wasserdichte, valide B-Reps und vier rotationsidentische Segmente.
3. FDM-Überhänge und definierte massive Schraub-/Stoßzonen.
4. FEM-Lastfälle Fahrtwind, Schlechtweg, Montagehüllkurve und Schnee.
5. Stoß-Submodell, Klebfugenschub und Thermik.
6. Haubenfreigang und Wellenwahl.
7. Digitalen Belluna-Passungscheck als separate `fit`-Stufe.
8. Annahmenbasierten Lastpfadcheck für obere Acht-Schrauben-Gruppe, untere
   2×10-mm-Doppelraupe, den einzelnen M5 je Segmentstoß und
   Holzrahmen–Dachsandwich. Die acht unteren Seitenschrauben werden als
   physische Reserve ausgewiesen, aber nicht als Tragfähigkeit angerechnet.

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

## Aktuelle Ersatzstrategie für nicht verfügbare Werkstoffversuche

Zerstörende Druck-, Klebe- und Sandwichcoupons stehen derzeit realistisch
nicht zur Verfügung. Sie werden deshalb **nicht als angeblich bald
schließbare Voraussetzung behandelt**. Für den Prototypenentscheid gilt
stattdessen die reproduzierbare Abschätzung in [`load-paths.md`](load-paths.md):
stark abgeminderte Grenzflächenwerte, nur eine angerechnete Holz/GFK-Fläche,
1,5-fache Schrauben-Lastkonzentration und keine Addition von Kleber- und
Schraubentragfähigkeit.

Am realen Einbau weiterhin unmittelbar prüfbar und deshalb erforderlich sind:

- Ebenheit, Öffnungsmaß und Trockenpassung des realen Segmentsatzes.
- Reales Ausschnittmaß und Zustand des Dachkerns bei Demontage.
- Durchgehender, vollflächig gebundener 30-mm-Rahmen aus Nadelvollholz mit
  ρk ≥ 350 kg/m³ und Faser längs zur jeweiligen Rahmenseite. Beide 10-mm-
  Raupen müssen vollständig über ihm liegen. Die äußere Raupe muss rundum
  geschlossen bleiben; die acht Vents der inneren Raupe und der 4-mm-
  Mittelkanal müssen zur trockenen Öffnungsseite frei bleiben.
- Die acht seitlichen ST4.2×25 mit 3-mm-Vorbohrung und abgedichteten Köpfen;
  sie ersetzen den Klebnachweis nicht und werden rechnerisch nicht angerechnet.
- Vollständige Durchhärtung der unteren Sikaflex-Doppelraupe nach aktuellem
  Produktdatenblatt vor weiterer Montage, Fahrt oder Belastung.
- Flutungstest nach Montage sowie jährliche Sicht-/Handprüfung aller Nähte,
  der unteren Doppelraupe, der oberen und unteren Schrauben sowie der Lackkanten.

Ohne Werkstoffversuche bleibt das Ergebnis ehrlich
`PASS_ASSUMPTION_BASED` und der Projektstatus `PROTOTYPE_ONLY`; die Rechnung
ist keine Zulassung. Das ist eine benannte Erkenntnisgrenze, kein verstecktes
Versprechen späterer Prüfwerte.

## Nachvollziehbarkeit

Jeder Engineering-Report enthält Parameter-Hash, GEOM_REV, Git-Revision und
SHA-256 der exportierten Dateien. Der Fit-Report bindet zusätzlich den
Quellcommit und den SHA-256 des verwendeten Belluna-Rekonstruktionsmodells.
`release/current/manifest.json` wiederholt Prüfsummen, Stückzahl und
Orientierung für die tatsächlich ausgelieferten STEP-/STL-Dateien.
