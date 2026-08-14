# Abschätzung der Klebe-, Schraub- und Dachlastpfade

Stand: 2026-07-16 · Parameterstand `8eb8b79f` · **PASS_ASSUMPTION_BASED**

> Konservative Plausibilisierung, keine Bauteilzulassung. Die untere
> Doppelraupe trägt den Primärnachweis allein; acht seitliche Holzschrauben
> bleiben eine physische, aber unqualifizierte Reserve.

## Ergebnisübersicht

| Lastfall | obere Elastikfuge allein | 8 Schrauben oben | 2×10-mm-Dachraupe allein | erforderliche Kapazität je Rückfallschraube | Holz–Dach, eine Fläche | serieller Pfad |
|---|---:|---:|---:|---:|---:|---|
| Windhülle 480 N | 157 % | 74 % | 77 % | 144 N (nicht qualifiziert) | 35 % | PASS |
| Schlechtweg | 98 % | 43 % | 44 % | 81 N (nicht qualifiziert) | 18 % | PASS |
| Schnee/Druck | 0 % | 21 % | 0 % | 38 N (nicht qualifiziert) | 0 % | PASS |
| CFD offen, mittel ×1,5 | 71 % | 32 % | 29 % | 54 N (nicht qualifiziert) | 12 % | PASS |

Die obere Belluna-Verbindung bleibt hybrid: Kleber und die acht oberen
Plattenschrauben werden nicht addiert; die Schraubengruppe trägt den vollständigen Fall mit
Lastkonzentrationsfaktor 1,5. Unten müssen die beiden 10-mm-Raupen den
vollständigen Fall allein bestehen. Die acht Holzschrauben werden weder zur
Klebung addiert noch als PASS gewertet. Der Schubgrenzwert 0,050 MPa ist kein
TDS-Schubkennwert, sondern eine bewusst niedrige Projektannahme. Reale
Grenzflächenhaftung und Alterung bleiben unbekannt.

Die CFD-Zeile ist eine zusätzliche Sensitivität aus Matrix `a3a2de8c` und
bleibt nicht freigabewirksam. Die analytische 480-N-Windhülle wird dadurch
nicht reduziert.

## Maßgebende Festwerte

- Obere Ringfuge: 14.016 mm²; 0,030 MPa normal / 0,050 MPa Schub, nicht allein
  maßgebend.
- Untere Doppelraupe: 33.313 mm² wirksam, Innenmaß 406 mm, Außenmaß 454 mm;
  vollständig über dem 30-mm-Holzrahmen, acht innere Trockenraum-Vents,
  0,030/0,050 MPa. Fläche und Volumen folgen den echten gerundeten
  R5-Parallelkonturen; eine Quadratnäherung wird nicht verwendet. 3 mm
  Padabstand plus 0,6 mm Führungsvertiefung ergeben 3,6 mm Raupenhöhe und
  rund 120 ml Nennvolumen.
- Obere ST4.2×25 in ASA-GF: 178 N je Schraube nach Detailfaktor 0,5.
- Segmentstoß unter vollen 480 N: 2K-Epoxid 77 %; ein M5 62 %; beide getrennt PASS.
- Thermische Scherbewegung der 3-mm-Fuge: 38 % des 50-%-Grenzwerts; PASS.
- Obere Schraubengruppe: Eine fehlende Schraube ergibt 83–87 %. Zwei fehlende
  Schrauben bestehen nicht in jeder Anordnung. Alle acht Belluna-Schrauben
  bleiben Pflicht.

## Konstruktive Interpretation

- Der Adapter bleibt bei 500 mm Außenmaß. Zwei getrennte 10-mm-Raupen liefern
  trotz acht 5-mm-Ventunterbrechungen rund 33.313 mm² wirksame Klebefläche.
- 16 schmale Abstandspads mit 2,5×20 mm Kontaktmaß sitzen in den trockenen inneren und äußeren
  Randstreifen nahe den acht Dachschrauben. Sie definieren nur den
  Montagespalt und werden weder von der Klebefläche abgezogen noch als
  struktureller Lastpfad angerechnet.
- Die äußere Raupe bleibt als Wassersperre geschlossen. Nur die innere Raupe
  wird an acht Stellen zur trockenen Öffnungsseite unterbrochen, damit der
  4-mm-Mittelkanal Feuchte nachführen kann. Die Unterbrechungen und der Kanal
  dürfen bei der Montage nicht mit Dichtstoff überbrückt werden.
- Erst nach vollständiger Durchhärtung der tragenden Doppelraupe wird außen
  eine etwa 7×7-mm-Sikaflex-522-Schutzkehle ergänzt (nominal rund 48 ml).
  Sie bleibt sichtbar und erneuerbar und erhält keinerlei
  Tragfähigkeitsgutschrift.
- Acht seitliche ST4.2×25 sichern den Unterkragen im Holzrahmen. Ohne
  typgeprüften Schraubgrund wird nur der je Lastfall erforderliche Wert
  ausgewiesen; die Schrauben werden nicht angerechnet.
- Ein M5 je Stoß trägt die volle 480-N-Hülle allein. Das 2K-Epoxid bildet einen davon
  getrennt geprüften Fügepfad.
- Sikaflex-522 und Carloflex 410 UV werden nur mit den stark abgeminderten
  0,030/0,050-MPa-Werten angesetzt. Produkte innerhalb einer Baugruppe nicht
  mischen.

## Oberflächenannahme für Sikaflex-522

Die tragenden Klebezonen bleiben lackfrei. ASA-GF und Belluna-Kunststoff
werden sehr fein angeschliffen, mit Sika Cleaner P gereinigt und als
ABS-Analogie mit Sika Primer-507 vorbehandelt. GFK-Gelcoat wird sehr fein
angeschliffen, gereinigt und mit Sika Aktivator-205 vorbehandelt. ASA-GF ist
nicht ausdrücklich in der Sika-Tabelle genannt; die Rechnung ist daher keine
Herstellerfreigabe. Carloflex bleibt erst nach prozesssicherer Festlegung
seines im TDS nicht namentlich genannten Kunststoffprimers eine ausführbare
Alternative.

## Modellgrenzen

- Starrer Ring und linear-elastische Lastverteilung; lokale Peelspitzen und
  Gehäusenachgiebigkeit sind nicht aufgelöst.
- Die Rahmen-FEM fixiert die Böden beider Kleberführungen flächig. Das
  beseitigt die frühere künstliche Rundnoppen-Lagerkonzentration, bildet aber
  die reale Nachgiebigkeit des 3,6-mm-Klebstoffs und des GFK-Dachs noch nicht ab.
- Die zwei unteren 10-mm-Elastikraupen sind der allein angerechnete
  Adapter-Dach-Primärpfad. Die acht unteren Seitenschrauben sind mangels
  Holz-/Dachtest nur physische Reserve.
- Die acht oberen ST4.2×25 werden mit einem abgeminderten axialen Analogiewert
  auf den resultierenden Lastvektor geprüft.
- Der einzelne M5 je Segmentstoß wird mit der vollen 480-N-Hülle geprüft;
  expliziter Bolzenkontakt und Lochspiel sind nicht aufgelöst.
- Das reale X150-GFK/XPS-Sandwich ist nicht typgeprüft; deshalb werden nur eine
  Holz/GFK-Fläche und 0,050 MPa angerechnet.
- Werkstoffkriechen unter Dauerlast ist pauschal über `DERATE_CREEP` (0,4 auf
  die dauerhaft zulässige Spannung) abgedeckt. Nicht modelliert ist das
  Setzen/die Vorspannkraftrelaxation der oberen Schraubgruppe (Kunststoff im
  Klemmpaket, beschleunigt nahe `T_MAX`): Die Schraubnachweise sind
  Tragfähigkeits-, keine Reibschlussnachweise und bleiben davon unberührt;
  gegen Lockern unter Fahrvibration gilt die Setzkontrolle nach den ersten
  Fahrten und die jährliche Prüfung (`verification.md`).
- Thermozyklen sind nur als statische Extremfälle geprüft (LF5, ΔT 65 K).
  Tag/Nacht-Zyklen (ΔT ≈ 40 K, tausendfach über die Lebensdauer) erzeugen in
  der unteren Elastikfuge eine Schubverzerrungs-Amplitude von rund 60 % des
  statischen LF5-Werts — bei 38 % statischer Auslastung gegen die bereits
  stark abgeminderte Elastikfugen-Annahme wird das als abgedeckt eingestuft,
  bleibt aber eine dokumentierte Annahme ohne Ermüdungsversuch.
- CFD, FEM und Lastpfadrechnung sind Modellplausibilisierungen, keine
  Bauteilprüfung oder Herstellerfreigabe.

## Primärquellen

- [Sikaflex-522: 1,8 MPa Zugfestigkeit, 400 % Bruchdehnung, −50 bis +90 °C](https://industry.sika.com/en/home/transportation/sealants/adhesive-sealants/sikaflex-522.html)
- [Sika-Leitfaden: zusätzliche, zugängliche Schutzdichtung sowie verzögerte Durchhärtung bei zu frühem Schließen angrenzender Fugen](https://industry.sika.com/dam/dms/global-industry/4/bonding-and-sealingwith1-componentsikaflex.pdf)
- [Sika-Kompendium: Abminderung und typische zulässige thermische Scherverformung](https://industry.sika.com/dms/getdocument.get/8ffff4cd-c90d-4d24-969d-ee4db9093cf3_global-industry/compendium-elasticbonding.pdf)
- [Sika-STP-Vorbehandlungstabelle, Version 8, 02/2026](https://industry.sika.com/dms/getdocument.get/776a779a-10a6-413c-b20b-c46467315e33/pre-treatment-chartforsilanterminatedpolymersstp-sikaflex-500ser.pdf)
- [UHU plus endfest 300: Topfzeit, Temperaturbereich und Zugscherfestigkeit](../references/datasheets/adhesives/uhu-plus-endfest-300.pdf)
- [SikaForce-710 L35 für Holz/GFK-Sandwich mit EPS/XPS-Kern](https://deu.sika.com/dms/getdocument.get/41466f3f-1639-4fc4-8298-5c9a0a2d34e1/sikaforce-710-l35.pdf)
- [URSA-XPS-Vergleichswert TR 200; nicht das X150-Material](https://ursa.de/wp-content/uploads/2023/05/DB-xps.pdf)
- [Carloflex-410-UV-Quelldokument](../references/datasheets/adhesives/carloflex-410-uv-source.md)

Die maschinenlesbare Fassung wird mit `python3 -m pipeline connections` nach
`build/analysis/load_paths/<hash>/` geschrieben.
