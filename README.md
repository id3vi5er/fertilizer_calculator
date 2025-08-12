# Pflanzen Düngerberechnung

Ein einfaches Tool zur Berechnung der richtigen Düngermenge für Pflanzen, basierend auf dem Biobizz-Düngeschema. Die Anwendung hilft dabei, den Überblick über mehrere Pflanzen zu behalten und die Düngung für jede Wachstumsphase zu optimieren.

## Funktionen

-   **Pflanzenverwaltung:** Fügen Sie Ihre Pflanzen mit Namen, Keimdatum und Genetik hinzu.
-   **Automatische Wochenberechnung:** Das Tool berechnet automatisch die aktuelle Lebenswoche jeder Pflanze.
-   **Düngeempfehlungen:** Erhalten Sie genaue Dosiermengen für verschiedene Biobizz-Dünger, basierend auf der Pflanzenwoche.
-   **Phasen-Presets:** Wechseln Sie einfach zwischen den Voreinstellungen für die Vegetations- und Blütephase.
-   **EC-Helper:** Ein Werkzeug, um die benötigte Düngermenge zu berechnen, um einen bestimmten EC-Zielwert im Wasser zu erreichen.
-   **Notizen:** Speichern Sie individuelle Notizen für jede Pflanze.
-   **Datenhaltung in CSV:** Alle Pflanzendaten werden lokal in der `pflanzendaten.csv`-Datei gespeichert und können einfach bearbeitet oder gesichert werden.

## Wie wird es benutzt?

### Anwendung starten

Die Anwendung kann direkt über die ausführbare Datei im `dist`-Verzeichnis gestartet werden. Suchen Sie nach `fertilizers_v2.exe` und führen Sie es aus.

### Schritt-für-Schritt-Anleitung

1.  **Neue Pflanze anlegen:**
    -   Starten Sie die Anwendung.
    -   Klicken Sie auf den Button **"Neue Pflanze anlegen"**.
    -   Geben Sie den Namen, das Keimdatum (im Format `TT.MM.JJJJ`), die Genetik und optional einige Notizen ein.
    -   Klicken Sie auf **"Speichern"**.

2.  **Dünger berechnen:**
    -   Wählen Sie die gewünschte Pflanze aus dem Dropdown-Menü aus.
    -   Die aktuelle Woche der Pflanze und die Phase (z.B. "Vegetativ") werden automatisch ausgefüllt. Sie können diese für eine manuelle Berechnung anpassen.
    -   Geben Sie die Wassermenge in Litern ein (z.B. `1.5`).
    -   Wählen Sie die Dünger aus, die Sie verwenden möchten, indem Sie die entsprechenden Kontrollkästchen aktivieren.
    -   Die benötigte Menge für jeden ausgewählten Dünger wird sofort in Millilitern (ml) angezeigt.

3.  **EC-Wert anpassen (optional):**
    -   Klicken Sie auf den **"EC-Helper"**.
    -   Geben Sie den aktuellen EC-Wert Ihres Wassers ein.
    -   Wählen Sie, ob Sie den im Hauptfenster berechneten Ziel-EC oder einen manuellen Wert verwenden möchten.
    -   Das Tool berechnet die Menge an Wachstums- oder Blütedünger, die Sie hinzufügen müssen, um den Zielwert zu erreichen.

## Datenhaltung

Die Daten Ihrer Pflanzen werden in der Datei `pflanzendaten.csv` im selben Verzeichnis wie die Anwendung gespeichert. Diese Datei hat die folgenden Spalten:

-   `Pflanzenname`: Der eindeutige Name der Pflanze.
-   `Keimdatum`: Das Datum, an dem die Pflanze gekeimt ist, im Format `TT.MM.JJJJ`.
-   `Genetik`: Die Sorte oder Genetik der Pflanze.
-   `Infos`: Zusätzliche Notizen oder Informationen.

Sie können diese Datei mit einem beliebigen Tabellenkalkulationsprogramm (z.B. Excel, LibreOffice Calc) öffnen, um die Daten manuell zu bearbeiten oder Sicherungskopien zu erstellen.

## Für Entwickler

### Aus dem Quellcode ausführen

Um das Skript direkt auszuführen, benötigen Sie Python 3.

```bash
python fertilizers_v2.py
```

Das Skript verwendet nur Standardbibliotheken von Python (`tkinter`, `csv`, `datetime`), daher sind keine externen Abhängigkeiten erforderlich.

### Executable erstellen

Um die Anwendung selbst in eine `.exe`-Datei zu packen, wird PyInstaller verwendet. Die Konfiguration ist in der `fertilizers_v2.spec`-Datei gespeichert.

1.  Installieren Sie PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Führen Sie PyInstaller mit der `.spec`-Datei aus:
    ```bash
    pyinstaller fertilizers_v2.spec
    ```

Die fertige ausführbare Datei finden Sie im `dist`-Ordner.
