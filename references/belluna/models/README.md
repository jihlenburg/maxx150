# Belluna-Referenzmodelle

Die Dateien in diesem Ordner sind eine **vermessene Projekt-Rekonstruktion**
der Belluna-Karosseriebefestigungsplatte einschließlich Metallclips und
Dichtring. Sie stammen nicht von Belluna und dürfen nicht als Hersteller-CAD
weitergegeben oder bezeichnet werden.

Quelle der Geometrie: `reference_models/belluna.py`.

Reproduzierbarer Export:

```sh
python3 -m pipeline references
```

`manifest.json` trennt gemessene von weiterhin angenommenen Abmessungen und
enthält die Prüfsummen sämtlicher STEP-/STL-Dateien.
