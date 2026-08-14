# Nachweise und Freigabestatus

## Rechnerische Gates

Die rechnerische Gate-Kette prüft vor jeder Release-Paketierung:

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
kompletten Baugruppe. Die beiden Kleberführungsböden werden als starre,
verteilte Lagerflächen angesetzt; die 16 Abstandspads sind nur Montageanschläge
und werden nicht fixiert. Klebstoff- und Dachnachgiebigkeit bleiben dennoch
unaufgelöst. Netz- und Modellgrenzen sind im jeweiligen Report sichtbar zu halten.

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

Zerstörende, typgeprüfte Druck-, Klebe- und Sandwichcoupons auf
Originalsubstraten stehen derzeit realistisch nicht zur Verfügung. Sie werden deshalb **nicht als angeblich bald
schließbare Voraussetzung behandelt**. Für den Prototypenentscheid gilt
stattdessen die reproduzierbare Abschätzung in [`load-paths.md`](load-paths.md):
stark abgeminderte Grenzflächenwerte, nur eine angerechnete Holz/GFK-Fläche,
1,5-fache Schrauben-Lastkonzentration und keine Addition von Kleber- und
Schraubentragfähigkeit.

Eine benannte Ausnahme entsteht bei der Heki-Demontage: Der ausgebaute
Dachausschnitt ist Originalsubstrat (gealtertes GFK samt Lackaufbau). Er wird
aufbewahrt und für eine einfache Haftprobe genutzt — Sikaflex-522-Raupe nach
Vorbehandlungstabelle applizieren, nach TDS-Durchhärtung von Hand schälen bzw.
mit Kofferwaage abscheren, Bruchbild fotografisch dokumentieren (Adhäsions-
oder Kohäsionsbruch). Das ersetzt keine typgeprüften Coupons, stützt aber
erstmals die Grenzflächenannahmen am realen Substrat; überwiegender
Adhäsionsbruch wäre ein Eskalationssignal **vor** der Verklebung. Dieses
Zeitfenster existiert nur einmal.

Eine zweite, ungeplante Rückmeldung vom realen Bauteil betrifft die
Segmentstöße. WEICON RK-1300 hat dort nicht getragen, ein handelsüblicher
2K-Epoxidklebstoff dagegen schon (Nutzerbefund 2026-08-14). Daraus folgt eine
belastbare Negativaussage und eine schwache Positivaussage: der MMA-Weg ist
ausgeschieden, die Eignung des Epoxidwegs ist gezeigt, aber nicht beziffert.
Der ausgewählte UHU plus endfest 300 ist damit **nicht** quantitativ qualifiziert.
Der Bemessungswert bleibt deshalb bei 0,50 MPa, und der Stoß bleibt so
ausgelegt, dass ein M5 je Stoß die volle 480-N-Hülle auch ohne jede Klebwirkung
trägt.

Am realen Einbau weiterhin unmittelbar prüfbar und deshalb erforderlich sind:

- Ebenheit, Öffnungsmaß und Trockenpassung des realen Segmentsatzes.
- Ein Klebeversuch mit dem tatsächlich gekauften Gebinde an zwei Druckresten
  derselben Charge: K240 anschleifen, verkleben, nach 24 h von Hand brechen und
  das Bruchbild fotografieren. Bricht die Fuge adhäsiv, also blank von der
  Druckoberfläche ab, ist das ein Eskalationssignal **vor** der Rahmenmontage.
- Reales Ausschnittmaß und Zustand des Dachkerns bei Demontage.
- Durchgehender, vollflächig gebundener 30-mm-Rahmen aus Nadelvollholz mit
  ρk ≥ 350 kg/m³ und Faser längs zur jeweiligen Rahmenseite. Beide 10-mm-
  Raupen müssen vollständig über ihm liegen. Die äußere Raupe muss rundum
  geschlossen bleiben; die acht Vents der inneren Raupe und der 4-mm-
  Mittelkanal müssen zur trockenen Öffnungsseite frei bleiben.
- Alle 16 Abstandspads (2,5×20 mm Kontaktmaß) müssen gleichzeitig und ohne
  Kippeln auf dem vom Holzrahmen hinterfütterten GFK aufliegen. Sie
  definieren 3 mm Dachabstand; zusammen mit den 0,6-mm-Führungen entstehen
  3,6 mm Raupenhöhe. Kein Pad darf mit Dichtstoff unterfüttert werden. Keine
  Zwingen, Gurte oder vertikale Verschraubung verwenden: nur gleichmäßig bis
  zum ersten Padkontakt anpressen und danach gegen Verschieben sichern.
- Die acht seitlichen ST4.2×25 mit 3-mm-Vorbohrung und abgedichteten Köpfen;
  sie ersetzen den Klebnachweis nicht und werden rechnerisch nicht angerechnet.
- Vollständige Durchhärtung der unteren Sikaflex-Doppelraupe nach aktuellem
  Produktdatenblatt vor weiterer Montage, Fahrt oder Belastung.
- Erst danach die etwa 7×7 mm große äußere Sikaflex-522-Schutzkehle auf
  trockenem GFK und vollständig ausgehärteter 2K-PUR-Lackflanke herstellen.
  Sie ist zugänglicher, erneuerbarer Wetterschutz und kein angerechneter
  Lastpfad; ausschließlich Sika Tooling Agent N zum Glätten verwenden.
- Flutungstest nach Montage sowie jährliche Sicht-/Handprüfung der äußeren
  Schutzkehle, aller übrigen Nähte,
  der unteren Doppelraupe, der oberen und unteren Schrauben sowie der Lackkanten.
- Setzkontrolle der oberen Schraubgruppe nach den ersten Fahrten
  (Größenordnung 500 km): Kunststoff im Klemmpaket setzt und relaxiert
  (siehe Modellgrenzen in [`load-paths.md`](load-paths.md)); handfest
  kontrollieren, FDM-Gewinde nicht überdrehen.

Ohne Werkstoffversuche bleibt das Ergebnis ehrlich
`PASS_ASSUMPTION_BASED`; den Status `PROTOTYPE_ONLY` halten die offenen
physischen Gates (reale Maße, Einbaukontrollen), nicht die Coupons. Die
Rechnung ist keine Zulassung. Das ist eine benannte Erkenntnisgrenze, kein
verstecktes Versprechen späterer Prüfwerte.

## Günstige Validierungen ohne Gate-Charakter

Geplante Versuche, die zentrale Annahmen zu Messwerten machen, ohne neue
Freigabe-Gates zu erzeugen (Reihenfolge nach Aufwand):

1. **PLA-Passformdruck als FEM-Korrelation**: den ohnehin geplanten
   Passformdruck zusätzlich mit definierter Last prüfen (bekannte Gewichte
   über die Plattenschnittstelle, Messuhr auf Durchbiegung) und mit der
   E-Modul-skalierten FEM-Vorhersage vergleichen. Akzeptanz: Ort und Form der
   Maximalverformung stimmen überein, Betrag innerhalb Faktor 2.
2. **Z-Zugstäbe aus dem realen Druckprozess**: gedruckte Z- und XY-Stäbe
   (gleiches Druckprofil und gleiche Nachbehandlung wie die Serienteile —
   derzeit ungetempert, s. `docs/design.md`) bis zum Bruch belasten
   (Hebel plus Gewichte genügt). Akzeptanz: Z/XY-Verhältnis ≥ dem angesetzten
   `DERATE_Z` 0,5 — bestätigt die Konservativität der Schätzung, die Würth
   mangels FDM-Z-Werten offenlässt. Ersetzt keinen typgeprüften Coupon,
   liefert aber Prozess-Istwerte.
3. **Dachtemperatur-Logging**: IR-/Loggermessung der weiß lackierten
   Dachoberfläche an einem heißen Sommertag. Akzeptanz: Maximum ≤ `T_MAX`
   85 °C; darüber Eskalation (Werkstoff- und Lackentscheid neu bewerten).
4. **Demontage-Haftprobe** auf dem ausgebauten Dachausschnitt (siehe oben):
   Bruchbild dokumentieren; überwiegender Kohäsionsbruch stützt die
   Grenzflächenannahmen.

Der deterministische Toleranz-Sweep (`python3 scripts/toleranz_sweep.py`)
gehört als Planungsschritt **vor** die Messkampagne: Er zeigt je Messfeld, ob
das erwartete Messband ein analytisches Gate oder die Parameter-Validierung
kippen kann, und beziffert die Freigang-Regimegrenzen der B-Messungen.

## Nachvollziehbarkeit

Jeder Engineering-Report enthält Parameter-Hash, GEOM_REV, Git-Revision und
SHA-256 der exportierten Dateien. Der Fit-Report bindet zusätzlich den
Quellcommit und den SHA-256 des verwendeten Belluna-Rekonstruktionsmodells.
`release/current/manifest.json` wiederholt Prüfsummen, Stückzahl und
Orientierung für die tatsächlich ausgelieferten STEP-/STL-Dateien.
