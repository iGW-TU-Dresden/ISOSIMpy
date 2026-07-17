# Verwendung von PyTracerLab
## Verwendung der grafischen Benutzeroberfläche
Im Allgemeinen ist die Verwendung der grafischen Benutzeroberfläche (GUI) strikter und weniger vielseitig als die Verwendung des zugrunde liegenden Pakets. Konkret setzt die App eine bestimmte Struktur der Zeitreihendaten voraus, lässt sich nicht gut skalieren, um viele unterschiedliche Datensätze zu verarbeiten, und bietet nur begrenzte Nachbearbeitungsfunktionen. Dennoch ist die GUI eine sehr benutzerfreundliche Option, um Analysen von Grundwasserlaufzeitverteilungen mit Lumped-Parameter-Modellen durchzuführen.

Die GUI ist in verschiedene **Tabs** gegliedert. Diese **Tabs** repräsentieren den typischen Arbeitsablauf und sollten in ihrer vorliegenden Reihenfolge betrachtet werden. Die einzelnen **Tabs** werden im Folgenden ausführlicher beschrieben.

```{warning}
PyTracerLab befindet sich noch in aktiver Entwicklung. Während die allgemeine Funktionalität gut getestet ist, weist die GUI noch einige Probleme auf, an denen wir aktiv arbeiten.
```

```{warning}
PyTracerLab unterstützt derzeit keinerlei Vorverarbeitungsschritte der Eingangsdaten. Niederschlagsgewichtung, Gasaustausch usw. müssen vom Nutzer vorab durchgeführt werden.
```

```{tip}
Um Probleme bei der Verwendung der GUI zu vermeiden, führen Sie bitte alle Schritte auf allen Tabs in der Reihenfolge durch, in der sie auf dem Tab dargestellt sind. Legen Sie zum Beispiel auf dem Eingabe-Tab zuerst die zeitliche Auflösung fest, dann den bzw. die Tracer, laden Sie anschließend die entsprechenden Eingangsdaten und danach die entsprechenden Beobachtungsdaten.
```

### 1. Der Eingabe-Tab
In diesem **Tab** werden Datensätze geladen und die grundlegendsten Einstellungen für die anschließende Modellierung vorgenommen.
- Auswahl der zeitlichen Auflösung (jährliche oder monatliche Daten in Zeitreihen und Modellsimulationen)
- Auswahl von einem oder zwei Tracern, die in der Analyse berücksichtigt werden sollen ($^3\mathrm{H}$ oder $^14\mathrm{C}$)
- Auswahl und Laden der Tracer-Eingangszeitreihendatei über den sich öffnenden Dateidialog; Details zur Vorbereitung von Tracer-Eingangszeitreihendateien finden Sie [hier](#preparing-datasets-de)
- Auswahl und Laden der Tracer-Beobachtungszeitreihendatei über den sich öffnenden Dateidialog; Details zur Vorbereitung von Tracer-Beobachtungszeitreihendateien finden Sie [hier](#preparing-datasets-de)

```{important}
In den Tracer-Eingangsdaten und den Beobachtungsdaten sollten dieselben Einheiten der Tracer-Konzentration verwendet werden. Einheiten werden intern nicht überprüft. **Wenn die Einheiten nicht übereinstimmen, werden unerwünschte und falsche Ergebnisse erzielt!**
```

![Ein Bild des Eingabe-Tabs.](tab01.png)

### 2. Der Modell-Tab
```{warning}
Die Struktur eines Lumped-Parameter-Modells sollte stets auf einem konzeptionellen Verständnis des untersuchten Grundwasserströmungssystems beruhen. Zu diesem Thema gibt es umfangreiche Literatur. Wenn Sie noch nie von Dingen wie „Exponential Model“, „Binary Mixing Model“ oder „Convolution Integral“ gehört haben, sollten Sie sich in diese Themen einlesen, bevor Sie fortfahren. Lumped-Parameter-Modelle sind einfach zu verwenden, aber schwer zu meistern – entsprechende Modellierungsergebnisse sollten stets sorgfältig interpretiert werden, bevor Schlussfolgerungen gezogen werden.
```
In diesem **Tab** werden die verschiedenen Modellteile ausgewählt, die in die Simulationen einbezogen werden.
- Auswahl von bis zu 4 parallel zu verwendenden Modelleinheiten
    - verfügbare Einheiten:
        - Piston-Flow Model (**PM**)
        - Exponential Model (**EM**)
        - Exponential Piston-Flow Model (**EPM**)
        - Dispersion Model (**DM**)
    - jede Einheit ist mit einem entsprechenden Anteil der gesamten Systemantwort bzw. -ausgabe verknüpft; die Anteile aller aktiven Einheiten müssen sich zu eins summieren, andernfalls wird ein Fehler ausgelöst und das Modell läuft nicht
- Angabe, ob ein stationärer Tracer-Eingang berücksichtigt werden soll, der für die Zeit vor dem Beginn der Datensätze gilt
- Angabe der Warmlauf-Zeitspanne
    - dies stellt den stationären Tracer-Eingang für die Dauer der hier angegebenen Anzahl von Tracer-Halbwertszeiten voran
    - der Modell-Warmlauf hilft, unerwünschte Unregelmäßigkeiten zu entfernen, die in frühen Phasen von Simulationen auftreten können; weitere Details finden Sie [hier](#model-warmup-de)
    - im Fall von zwei Tracern wird **die längere der beiden Halbwertszeiten verwendet**

```{important}
Der stationäre Eingangswert wird in denselben Einheiten interpretiert, die in den Tracer-Eingangs- und Beobachtungsdatensätzen verwendet werden. Einheiten werden intern nicht überprüft. **Wenn die Einheiten nicht übereinstimmen, werden unerwünschte und falsche Ergebnisse erzielt!**
```

![Ein Bild des Modell-Tabs.](tab02.png)

### 3. Der Parameter-Tab
In diesem **Tab** werden Einstellungen zu den Modellparametern vorgenommen, dazu, wie sie während der Kalibrierung begrenzt werden und welche aktuellen Werte sie annehmen.
- Angabe der unteren Grenze, des aktuellen Werts, der oberen Grenze und des Kalibrierungsstatus für alle Modellparameter; die verschiedenen Modellparameter sind in Zeilen organisiert
    - der für einen Parameter angegebene Wert wird als sein Wert für die einfache Simulation und als Startwert für die Kalibrierung verwendet
    - Parameter, die auf *fixed* gesetzt sind, bleiben während der Kalibrierung auf ihrem angegebenen Wert

```{important}
Zeiteinheiten von Parametern sind stets in Jahren. Halbwertszeiten werden intern umgerechnet, aber andere Parameter mit Zeiteinheiten werden in Monaten interpretiert.
```

![Ein Bild des Parameter-Tabs.](tab03.png)

### 4. Der Simulations-Tab
In diesem **Tab** können Simulationen durchgeführt, Modellparameter automatisch kalibriert, Ergebnisse geplottet und Berichte erzeugt werden.
- Durchführung einer Modellsimulation mit den aktuellen Parametern
- Durchführung einer Modellkalibrierung
    - Auswahl eines Solvers
    - Änderung der Solver-Parameter (erfordert mindestens ein grundlegendes Verständnis der Solver)
    - Ausführung der automatischen Kalibrierung
- Plotten der Ergebnisse der aktuellen Simulation / der kalibrierten Modellsimulation
- Erstellung eines Berichts einschließlich der kalibrierten Parameter, Fehlermetriken und weiterer Modelldetails in einer Textdatei; verwendet einen Dateidialog zum Speichern der Berichtsdatei

```{tip}
Alle Plots, die PyTracerLab erzeugt, können in der Plot-Ansicht interaktiv angepasst werden. Weitere Details dazu, wie das Erscheinungsbild von Plots geändert werden kann, finden Sie in der (matplotlib-Dokumentation)[https://matplotlib.org/stable/users/explain/figure/interactive.html].
```

![Ein Bild des Simulations-Tabs.](tab04.png)

![Ein Beispiel-Plot nach der Parameterinferenz (Kalibrierung) mit einem MCMC-Sampler; Fall eines Tracers.](plot.png)

![Ein Beispielbericht nach der Parameterinferenz (Kalibrierung); Fall eines Tracers.](report.png)

(preparing-datasets-de)=
## Vorbereitung der Datensätze
Datensätze müssen auf eine bestimmte Weise vorbereitet werden, damit die App die Daten einlesen kann. Dateien müssen stets CSVs sein. Die Tracer-Eingangs- und Beobachtungszeitreihendaten müssen dieselbe Länge haben. Zeitstempel, die in der Tracer-Eingangsreihe vorhanden sind, für die aber keine Beobachtung verfügbar ist, müssen als fehlende Werte markiert werden (siehe unten). Es wird angenommen, dass die Zeitreihen keine Lücken aufweisen und vor der Verwendung in PyTracerLab entsprechend aufbereitet werden.

Unten kann anstelle von „# Date, CTracer“ oder „# Date, CTracer1, CTracer2“ jede andere Beschreibung verwendet werden. **Die erste Zeile in der Datei wird beim Einlesen übersprungen!**

### Monatliche Daten
#### Ein einzelner Tracer
**Monatliche Tracer-Eingangsreihen** sollten das folgende Format haben, wenn **ein einzelner Tracer** betrachtet wird:

```
# Date, CTracer
1996-01, 1.03
1996-02, 2.12
1996-03, 0.08
...
2009-11, 0.05
```

**Monatliche Tracer-Beobachtungsreihen** sollten das folgende Format haben, wenn **ein einzelner Tracer** betrachtet wird („nan“, falls zu diesem Zeitstempel keine Beobachtung verfügbar ist):

```
# Date, CTracer
1996-01, nan
1996-02, 0.17
1996-03, nan
...
2009-11, nan
```

#### Zwei Tracer
**Monatliche Tracer-Eingangsreihen** sollten das folgende Format haben, wenn **zwei Tracer** betrachtet werden:
```
# Date, CTracer1, CTracer2
1996-01, 1.03, 0.01
1996-02, 2.12, 0.06
1996-03, 0.08, 0.02
...
2009-11, 0.05, 1.25
```

**Monatliche Tracer-Beobachtungsreihen** sollten das folgende Format haben, wenn **zwei Tracer** betrachtet werden („nan“, falls zu diesem Zeitstempel keine Beobachtung verfügbar ist):
```
# Date, CTracer1, CTracer2
1996-01, nan, nan
1996-02, 1.14, 0.01
1996-03, nan, nan
1996-04, 1.17, nan
1996-05, nan, 0.05
...
2009-11, nan, nan
```

### Jährliche Daten
#### Ein einzelner Tracer
**Jährliche Tracer-Eingangsreihen** sollten das folgende Format haben, wenn **ein einzelner Tracer** betrachtet wird:

```
# Date, CTracer
1996, 1.03
1997, 2.12
1998, 0.08
...
2009, 0.05
```

**Jährliche Tracer-Beobachtungsreihen** sollten das folgende Format haben, wenn **ein einzelner Tracer** betrachtet wird („nan“, falls zu diesem Zeitstempel keine Beobachtung verfügbar ist):

```
# Date, CTracer
1996, nan
1997, 0.17
1998, nan
...
2009, nan
```

#### Zwei Tracer
**Jährliche Tracer-Eingangsreihen** sollten das folgende Format haben, wenn **zwei Tracer** betrachtet werden:
```
# Date, CTracer1, CTracer2
1996, 1.03, 0.01
1997, 2.12, 0.06
1998, 0.08, 0.02
...
2009, 0.05, 1.25
```

**Jährliche Tracer-Beobachtungsreihen** sollten das folgende Format haben, wenn **zwei Tracer** betrachtet werden („nan“, falls zu diesem Zeitstempel keine Beobachtung verfügbar ist):
```
# Date, CTracer1, CTracer2
1996, nan, nan
1997, 1.14, 0.01
1998, nan, nan
1998, 1.16, nan
1998, nan, 0.06
...
2009, nan, nan
```

(model-warmup-de)=
## Modell-Warmlauf
