"""
Pflanzen Düngerberechnung v1.2
Hauptmodul für die Anwendung zur Düngerberechnung für Pflanzen.

Diese Anwendung ermöglicht es Benutzern:
- Pflanzendaten (Name, Keimdatum, Genetik, Notizen) zu speichern und zu verwalten.
- Automatisch die aktuelle Wachstumswoche einer Pflanze zu berechnen.
- Die benötigte Düngemenge basierend auf der Woche, Wassermenge und Düngertyp zu kalkulieren.
- Düngeschemata und EC-Zielwerte aus einer externen JSON-Datei (`fertilizer_config.json`) zu laden.
- Einen EC-Helper zu verwenden, um die Nährlösung an einen EC-Zielwert anzupassen.

Die Pflanzendaten werden in `pflanzendaten.csv` gespeichert.
Die Düngerkonfiguration (Schemata, EC-Werte) wird aus `fertilizer_config.json` geladen.
"""
import tkinter as tk
from tkinter import ttk  # Import themed widgets
import tkinter.messagebox as messagebox
import tkinter.scrolledtext as scrolledtext # For scrolled text area
import csv
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional # For type hinting
import json # Import json module
import sys # For sys.exit

# --- Konstanten ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(SCRIPT_DIR, 'pflanzendaten.csv')
CONFIG_FILENAME = os.path.join(SCRIPT_DIR, 'fertilizer_config.json') # Config file name
CSV_HEADER = ["Pflanzenname", "Keimdatum", "Genetik", "Infos"]
EC_FACTOR_WACHSTUM = 478 # EC increase in µS/cm per ml/L for Wachstumsdünger
EC_FACTOR_BLUETE = 430   # EC increase in µS/cm per ml/L for Blütendünger

# --- Datenmanagement ---

def read_plant_data() -> Dict[str, Dict[str, Any]]:
    """
    Liest die Pflanzendaten aus der CSV-Datei (`pflanzendaten.csv`).
    Erstellt die CSV-Datei mit einer Kopfzeile, falls sie nicht existiert.

    Returns:
        Dict[str, Dict[str, Any]]: Ein Dictionary, bei dem jeder Schlüssel ein Pflanzenname ist.
        Der Wert ist ein weiteres Dictionary mit den Details der Pflanze:
        - "Keimdatum": datetime-Objekt des Keimdatums.
        - "Genetik": String, der die Genetik der Pflanze beschreibt.
        - "Infos": String für zusätzliche Informationen oder Notizen zur Pflanze.
        Gibt ein leeres Dictionary zurück, wenn die Datei nicht gelesen werden kann oder leer ist (nach Erstellung).
    """
    plant_data: Dict[str, Dict[str, Any]] = {}
    try:
        with open(CSV_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            try:
                header = next(reader)
                if header != CSV_HEADER:
                    print(f"Warnung: Unerwartete Kopfzeile in {CSV_FILENAME}: {header}")
                    # Optional: Fehler auslösen oder Standard annehmen
            except StopIteration:
                # Datei ist leer, sollte aber nicht passieren, wenn sie erstellt wurde
                print(f"Warnung: CSV-Datei '{CSV_FILENAME}' ist leer oder enthält keine Kopfzeile.")
                # Header neu schreiben?
                # with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as outfile:
                #    writer = csv.writer(outfile)
                #    writer.writerow(CSV_HEADER)
                return plant_data # Leeres Dictionary zurückgeben

            for i, row in enumerate(reader, start=2): # start=2 wegen Kopfzeile
                if len(row) == len(CSV_HEADER):
                    plant_name, germination_date_str, genetics, info = row
                    try:
                        # Datum in datetime Objekt umwandeln
                        germination_date = datetime.strptime(germination_date_str, '%d.%m.%Y')
                        if plant_name in plant_data:
                             print(f"Warnung: Doppelter Pflanzenname '{plant_name}' in Zeile {i}. Überspringe.")
                             continue
                        plant_data[plant_name] = {
                            "Keimdatum": germination_date,
                            "Genetik": genetics,
                            "Infos": info
                        }
                    except ValueError:
                        print(f"Warnung: Ungültiges Datumsformat '{germination_date_str}' für Pflanze '{plant_name}' in Zeile {i}. Überspringe Eintrag.")
                    except Exception as e:
                        print(f"Fehler beim Verarbeiten der Zeile {i} für '{plant_name}': {row} - {e}. Überspringe Eintrag.")
                else:
                    print(f"Warnung: Zeile {i} hat unerwartete Spaltenanzahl ({len(row)} statt {len(CSV_HEADER)}). Überspringe: {row}")

    except FileNotFoundError:
        print(f"Datei '{CSV_FILENAME}' nicht gefunden. Erstelle neue Datei.")
        try:
            with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(CSV_HEADER)
            print(f"Datei '{CSV_FILENAME}' wurde erfolgreich erstellt.")
        except IOError as e:
            messagebox.showerror("Fehler beim Erstellen der Datei", f"Konnte CSV-Datei nicht erstellen:\n{e}")
    except IOError as e:
        messagebox.showerror("Fehler beim Lesen", f"Konnte CSV-Datei nicht lesen:\n{e}")
    except Exception as e:
         messagebox.showerror("Unerwarteter Fehler", f"Ein Fehler ist beim Lesen der Pflanzendaten aufgetreten:\n{e}")

    return plant_data

def save_plant_data_to_csv(data_to_save: Dict[str, Dict[str, Any]]):
    """
    Speichert das übergebene Pflanzendaten-Dictionary in die CSV-Datei (`pflanzendaten.csv`).
    Überschreibt die vorhandene Datei vollständig mit den neuen Daten.

    Args:
        data_to_save (Dict[str, Dict[str, Any]]): Das Dictionary mit den Pflanzendaten,
            das gespeichert werden soll. Die Struktur entspricht der von `read_plant_data` zurückgegebenen.
    """
    try:
        with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_HEADER) # Kopfzeile schreiben
            for plant_name, data in data_to_save.items():
                keimdatum_obj = data.get("Keimdatum")
                if isinstance(keimdatum_obj, datetime): # Sicherstellen, dass Keimdatum ein datetime-Objekt ist
                    date_str = keimdatum_obj.strftime('%d.%m.%Y') # Formatierung für CSV
                    writer.writerow([
                        plant_name,
                        date_str,
                        data.get("Genetik", ""), # Fallback auf leeren String, falls nicht vorhanden
                        data.get("Infos", "")    # Fallback auf leeren String
                    ])
                else:
                    # Log, falls ein Eintrag nicht korrekt verarbeitet werden kann
                    print(f"Warnung: Ungültiges oder fehlendes Keimdatum-Objekt für '{plant_name}' beim Speichern. Überspringe.")
    except IOError as e:
         messagebox.showerror("Speicherfehler", f"Fehler beim Schreiben der CSV-Datei '{CSV_FILENAME}':\n{e}")
    except Exception as e:
         messagebox.showerror("Unerwarteter Speicherfehler", f"Ein Fehler ist beim Speichern der Pflanzendaten aufgetreten:\n{e}")

# --- Düngeberechnungen ---

def calculate_fertilizer_amount(week: int, water_amount: float, fertilizer_type: str) -> Optional[float]:
    """
    Berechnet die benötigte Düngemenge basierend auf der Wachstumswoche, Wassermenge und dem Düngertyp.
    Verwendet die global geladenen Düngeschemata aus `F_DATA`.

    Args:
        week (int): Die aktuelle Woche seit der Keimung der Pflanze.
        water_amount (float): Die Menge an Wasser in Litern, für die der Dünger berechnet werden soll.
        fertilizer_type (str): Der Name des Düngers (Schlüssel in `F_DATA`).

    Returns:
        Optional[float]: Die berechnete Düngemenge in Millilitern.
                         Gibt `None` zurück, wenn Konfigurationsdaten fehlen oder der Düngertyp unbekannt ist.
                         Gibt `0.0` zurück, wenn keine Dosierung für die Woche definiert ist oder
                         das Düngeschema für den Typ leer ist.
    """
    # Prüfen, ob die globalen Düngemitteldaten (F_DATA) geladen wurden.
    if F_DATA is None:
        messagebox.showerror("Konfigurationsfehler", "Düngemitteldaten nicht geladen. Anwendung kann nicht fortgesetzt werden.")
        return None

    # Prüfen, ob der angegebene Düngertyp in den geladenen Daten existiert.
    if fertilizer_type not in F_DATA:
        print(f"Warnung: Unbekannter Düngertyp '{fertilizer_type}'")
        return None # Düngertyp nicht in Konfiguration gefunden.

    current_fertilizer_schedule = F_DATA[fertilizer_type]
    # Prüfen, ob für diesen Dünger ein Schema vorhanden ist.
    if not current_fertilizer_schedule: # Leeres Schema
        print(f"Warnung: Leeres Düngeschema für '{fertilizer_type}'")
        return 0.0 # Kein Schema vorhanden, also keine Düngermenge.

    # Bestimme die effektiv anzuwendende Woche für die Dosierung.
    # Liegt die aktuelle Woche außerhalb des definierten Schemas, wird die höchste definierte Woche verwendet.
    # Die Schlüssel in current_fertilizer_schedule (Wochennummern) sind bereits Integer.
    max_defined_week = max(current_fertilizer_schedule.keys()) if current_fertilizer_schedule else 1
    effective_week = min(week, max_defined_week) if week > 0 else 1 # Mindestens Woche 1 verwenden.

    dosage_per_liter = current_fertilizer_schedule.get(effective_week)

    # Wenn für die effektive Woche keine Dosierung definiert ist.
    if dosage_per_liter is None:
        # Dieser Fall sollte durch die min/max Logik eigentlich nicht eintreten, dient als Sicherheitsnetz.
        print(f"Warnung: Keine Dosierung für Woche {effective_week} bei '{fertilizer_type}' gefunden.")
        return 0.0 # Keine Dosierung definiert, also keine Düngermenge.

    fertilizer_amount = dosage_per_liter * water_amount
    return fertilizer_amount

def get_ec_value(week: int) -> Optional[float]:
    """
    Gibt den Ziel-EC-Wert (in mS/cm) für die entsprechende Wachstumswoche zurück.
    Verwendet die global geladenen EC-Zielwerte aus `EC_TARGET_VALUES`.

    Args:
        week (int): Die aktuelle Woche seit der Keimung.

    Returns:
        Optional[float]: Der EC-Zielwert für Erde (in mS/cm) für die angegebene Woche.
                         Gibt `None` zurück, wenn Konfigurationsdaten fehlen oder keine Werte definiert sind.
    """
    # Prüfen, ob die globalen EC-Zielwerte (EC_TARGET_VALUES) geladen wurden.
    if EC_TARGET_VALUES is None:
        messagebox.showerror("Konfigurationsfehler", "EC-Zielwerte nicht geladen. Anwendung kann nicht fortgesetzt werden.")
        return None
    # Prüfen, ob überhaupt EC-Werte vorhanden sind.
    if not EC_TARGET_VALUES: # Leeres Dictionary
        print("Warnung: EC-Zielwerte sind leer.")
        return None # Keine EC-Werte definiert.

    # Bestimme die effektiv anzuwendende Woche für den EC-Wert.
    # Liegt die aktuelle Woche außerhalb der definierten EC-Werte, wird der Wert der höchsten definierten Woche verwendet.
    # Die Schlüssel in EC_TARGET_VALUES (Wochennummern) sind bereits Integer.
    max_defined_week = max(EC_TARGET_VALUES.keys()) if EC_TARGET_VALUES else 1
    effective_week = min(week, max_defined_week) if week > 0 else 1 # Mindestens Woche 1.
    return EC_TARGET_VALUES.get(effective_week)


# --- Konfigurationsladung ---
def load_fertilizer_config() -> tuple[Optional[Dict[str, Dict[int, float]]], Optional[Dict[int, float]]]:
    """
    Lädt Düngemitteldaten (Schemata) und EC-Zielwerte aus der JSON-Konfigurationsdatei (`fertilizer_config.json`).

    Die Funktion liest die JSON-Datei, extrahiert die Abschnitte "fertilizer_data" und "ec_values".
    Wichtig: Die Wochenschlüssel in der JSON-Datei (z.B. "1", "2") werden in Integer-Schlüssel
    für die Python-Dictionaries konvertiert. Dosierungen und EC-Werte werden als float interpretiert.

    Returns:
        tuple[Optional[Dict[str, Dict[int, float]]], Optional[Dict[int, float]]]:
        Ein Tupel bestehend aus zwei Elementen:
        1.  Ein Dictionary für Düngemitteldaten (`processed_f_data`):
            - Schlüssel: Düngername (str).
            - Wert: Ein weiteres Dictionary mit Integer-Wochennummern als Schlüssel und float-Dosierungen als Werte.
        2.  Ein Dictionary für EC-Zielwerte (`processed_ec_values`):
            - Schlüssel: Integer-Wochennummer.
            - Wert: float EC-Zielwert.
        Im Fehlerfall (z.B. Datei nicht gefunden, JSON-Fehler) wird `(None, None)` zurückgegeben
        und eine Fehlermeldung über `messagebox.showerror` angezeigt.

    Fehlerbehandlung:
        - `FileNotFoundError`: Wenn `CONFIG_FILENAME` nicht existiert.
        - `json.JSONDecodeError`: Wenn die JSON-Datei fehlerhaft formatiert ist.
        - `ValueError`: Wenn Wochenschlüssel oder Werte nicht korrekt in int/float konvertiert werden können.
        - Allgemeine `Exception`: Für andere unerwartete Fehler beim Laden.
    """
    try:
        with open(CONFIG_FILENAME, 'r', encoding='utf-8') as f:
            config_json = json.load(f) # JSON-Datei einlesen

        # Verarbeitung der Düngemitteldaten
        fertilizer_data_json = config_json.get("fertilizer_data", {}) # Default: leeres Dict
        processed_f_data: Dict[str, Dict[int, float]] = {}
        for f_type, schedule_json in fertilizer_data_json.items():
            processed_schedule: Dict[int, float] = {}
            for week_str, dosage in schedule_json.items():
                try:
                    # Konvertiere Wochenschlüssel zu Integer und Dosierung zu Float
                    processed_schedule[int(week_str)] = float(dosage)
                except ValueError:
                    # Log für fehlerhafte Einträge in den Schemata
                    print(f"Warnung: Ungültiger Wochenschlüssel oder Dosierungswert für {f_type} in Woche '{week_str}'. Überspringe.")
            processed_f_data[f_type] = processed_schedule

        # Verarbeitung der EC-Zielwerte
        ec_values_json = config_json.get("ec_values", {}) # Default: leeres Dict
        processed_ec_values: Dict[int, float] = {}
        for week_str, ec_val in ec_values_json.items():
            try:
                # Konvertiere Wochenschlüssel zu Integer und EC-Wert zu Float
                processed_ec_values[int(week_str)] = float(ec_val)
            except ValueError:
                # Log für fehlerhafte EC-Werte
                print(f"Warnung: Ungültiger Wochenschlüssel oder EC-Wert '{week_str}'. Überspringe.")

        return processed_f_data, processed_ec_values

    except FileNotFoundError:
        messagebox.showerror("Konfigurationsfehler", f"Konfigurationsdatei '{CONFIG_FILENAME}' nicht gefunden. Bitte stellen Sie sicher, dass die Datei existiert.")
        return None, None # Signalisiert Fehler
    except json.JSONDecodeError as e:
        messagebox.showerror("Konfigurationsfehler", f"Fehler beim Lesen der JSON-Konfigurationsdatei '{CONFIG_FILENAME}':\n{e}\nBitte überprüfen Sie die Syntax der Datei.")
        return None, None # Signalisiert Fehler
    except Exception as e: # Fängt andere unerwartete Fehler ab
        messagebox.showerror("Unerwarteter Fehler", f"Ein unerwarteter Fehler ist beim Laden der Konfiguration aufgetreten:\n{e}")
        return None, None # Signalisiert Fehler

# Globale Variablen für Konfigurationsdaten
# Werden durch initialize_config_and_exit_on_error() initialisiert.
F_DATA: Optional[Dict[str, Dict[int, float]]] = None
EC_TARGET_VALUES: Optional[Dict[int, float]] = None

def initialize_config_and_exit_on_error(app_window: tk.Tk) -> bool:
    """
    Initialisiert die Konfiguration durch Aufruf von `load_fertilizer_config()`.
    Speichert die geladenen Daten in den globalen Variablen `F_DATA` und `EC_TARGET_VALUES`.

    Bei einem Ladefehler (wenn `load_fertilizer_config` (None, None) zurückgibt):
    - Zeigt eine kritische Fehlermeldung an.
    - Zerstört das Hauptfenster der Anwendung (`app_window`), um die Ausführung zu beenden.
    - Gibt `False` zurück.

    Bei erfolgreichem Laden:
    - Prüft zusätzlich, ob die geladenen Daten (`F_DATA`, `EC_TARGET_VALUES`) leer sind und zeigt ggf. eine Warnung.
    - Gibt `True` zurück.

    Args:
        app_window (tk.Tk): Das Hauptfenster der Tkinter-Anwendung. Wird benötigt, um die
                            Anwendung im Fehlerfall sauber zu beenden.
    Returns:
        bool: `True`, wenn die Konfiguration erfolgreich geladen wurde (und Daten nicht kritisch leer sind),
              `False` bei einem Ladefehler, der zum Beenden der Anwendung führt.
    """
    global F_DATA, EC_TARGET_VALUES
    F_DATA, EC_TARGET_VALUES = load_fertilizer_config()

    # Kritischer Fehler: Konnte Konfiguration nicht laden.
    if F_DATA is None or EC_TARGET_VALUES is None:
        # Die spezifische Fehlermeldung (Datei nicht gefunden, JSON-Syntax etc.)
        # wurde bereits in load_fertilizer_config() via messagebox angezeigt.
        messagebox.showerror("Kritischer Fehler", "Konfiguration konnte nicht geladen werden. Die Anwendung wird beendet.")
        app_window.destroy() # Schließt das Hauptfenster und beendet die Tkinter-Loop effektiv.
        return False # Signalisiert, dass Initialisierung fehlgeschlagen ist.

    # Warnung, falls Konfigurationsdaten zwar geladen, aber leer sind.
    # Dies könnte auf eine leere, aber valide, JSON-Datei hindeuten.
    if not F_DATA or not EC_TARGET_VALUES:
        messagebox.showwarning("Konfigurationswarnung",
                               "Düngemitteldaten oder EC-Zielwerte sind leer. "
                               "Bitte überprüfen Sie die Konfigurationsdatei (`fertilizer_config.json`). "
                               "Die Anwendung startet, aber einige Funktionen könnten eingeschränkt sein.")
        # Optional: Hier könnte man auch beenden, wenn leere Configs als kritisch betrachtet werden.
        # app_window.destroy()
        # return False
    return True # Signalisiert erfolgreiche Initialisierung.


def berechne_wachstumduenger_menge_fuer_ec(EC_ist: float, EC_soll: float, wassermenge_liter: float) -> float:
    """
    Berechnet die benötigte Menge Wachstumsdünger (in ml), um einen Ziel-EC-Wert zu erreichen.

    Args:
        EC_ist (float): Der aktuelle EC-Wert der Nährlösung in µS/cm.
        EC_soll (float): Der gewünschte Ziel-EC-Wert der Nährlösung in µS/cm.
        wassermenge_liter (float): Die Gesamtmenge der Nährlösung in Litern.

    Returns:
        float: Die benötigte Menge Wachstumsdünger in ml. Gibt 0.0 zurück, wenn der
               aktuelle EC-Wert bereits über oder gleich dem Ziel-EC-Wert ist.
    """
    if EC_ist >= EC_soll:
        return 0.0 # Kein Dünger benötigt, wenn EC bereits erreicht oder überschritten.
    benötigte_ec_zunahme = EC_soll - EC_ist # Differenz zum Ziel-EC
    # Berechnung der Düngermenge:
    # (Gewünschte EC-Änderung / EC-Änderung pro ml Dünger pro Liter Wasser) * Gesamtmenge Wasser in Litern
    benötigte_menge_ml = (benötigte_ec_zunahme / EC_FACTOR_WACHSTUM) * wassermenge_liter
    return max(0.0, benötigte_menge_ml) # Sicherstellen, dass kein negativer Wert zurückgegeben wird.

def berechne_bluetenduenger_menge_fuer_ec(EC_ist: float, EC_soll: float, wassermenge_liter: float) -> float:
    """
    Berechnet die benötigte Menge Blütedünger (in ml), um einen Ziel-EC-Wert zu erreichen.

    Args:
        EC_ist (float): Der aktuelle EC-Wert der Nährlösung in µS/cm.
        EC_soll (float): Der gewünschte Ziel-EC-Wert der Nährlösung in µS/cm.
        wassermenge_liter (float): Die Gesamtmenge der Nährlösung in Litern.

    Returns:
        float: Die benötigte Menge Blütedünger in ml. Gibt 0.0 zurück, wenn der
               aktuelle EC-Wert bereits über oder gleich dem Ziel-EC-Wert ist.
    """
    if EC_ist >= EC_soll:
        return 0.0 # Kein Dünger benötigt, wenn EC bereits erreicht oder überschritten.
    benötigte_ec_zunahme = EC_soll - EC_ist
    # Menge in ml = (Gewünschte EC-Änderung / EC-Änderung pro ml/L) * Liter
    benötigte_menge_ml = (benötigte_ec_zunahme / EC_FACTOR_BLUETE) * wassermenge_liter
    return max(0.0, benötigte_menge_ml) # Sicherstellen, dass nicht negativ

# --- GUI Callbacks und Hilfsfunktionen ---

def update_week(event=None):
    """
    Aktualisiert die GUI-Felder im Hauptfenster (Woche, Keimdatum, Genetik, Infos, EC-Zielwert)
    basierend auf der aktuell im Dropdown-Menü ausgewählten Pflanze.
    Wird aufgerufen, wenn eine Pflanze im Dropdown ausgewählt wird (`<<ComboboxSelected>>` Event).

    Args:
        event (Optional[tk.Event]): Das Tkinter-Event-Objekt (standardmäßig None, da auch manuell aufrufbar).

    Side effects:
        - Modifiziert den Inhalt und Zustand verschiedener Tkinter Entry-, Label- und Text-Widgets.
        - Deaktiviert den "Infos speichern"-Button, wenn keine Pflanze ausgewählt ist.
        - Ruft `calculate()` und `update_ec_value()` auf, um abhängige Werte neu zu berechnen und anzuzeigen.
    """
    try:
        selected_plant = plant_var.get() # Name der ausgewählten Pflanze

        # Fall: Keine Pflanze ausgewählt oder die Auswahl ist ungültig.
        if not selected_plant or selected_plant not in plant_data:
            # Alle relevanten GUI-Felder leeren oder zurücksetzen.
            week_entry.delete(0, tk.END)
            germination_date_entry.config(state="normal") # Kurzzeitig editierbar machen zum Leeren
            germination_date_entry.delete(0, tk.END)
            germination_date_entry.config(state="readonly")
            genetics_entry.config(state="normal")
            genetics_entry.delete(0, tk.END)
            genetics_entry.config(state="readonly")
            info_text.config(state="normal")
            info_text.delete("1.0", tk.END)
            info_text.config(state="disabled") # Textfeld deaktivieren
            ec_label.config(text="Plan-EC (Erde): -") # EC-Label zurücksetzen
            for label in result_labels: # Alle Ergebnis-Labels für Dünger leeren
                label.config(text="")
            save_button.config(state="disabled") # Speichern-Button deaktivieren
            return

        # Fall: Gültige Pflanze ausgewählt -> Felder mit Pflanzendaten füllen.
        plant_info = plant_data[selected_plant]
        germination_date = plant_info["Keimdatum"]
        today = datetime.today()

        # Berechnung der aktuellen Wachstumswoche.
        delta_days = (today - germination_date).days
        current_week = max(1, (delta_days // 7 + 1)) # Woche beginnt bei 1.

        week_entry.delete(0, tk.END)
        week_entry.insert(0, str(current_week)) # Woche im Eingabefeld anzeigen.

        # Keimdatum anzeigen (schreibgeschützt).
        germination_date_entry.config(state="normal")
        germination_date_entry.delete(0, tk.END)
        germination_date_entry.insert(0, germination_date.strftime('%d.%m.%Y'))
        germination_date_entry.config(state="readonly")

        # Genetik anzeigen (schreibgeschützt).
        genetics_entry.config(state="normal")
        genetics_entry.delete(0, tk.END)
        genetics_entry.insert(0, plant_info["Genetik"])
        genetics_entry.config(state="readonly")

        # Infos/Notizen anzeigen (bearbeitbar).
        info_text.config(state="normal")
        info_text.delete("1.0", tk.END)
        info_text.insert("1.0", plant_info["Infos"])
        # info_text bleibt bearbeitbar.

        save_button.config(state="normal") # Speichern-Button aktivieren.

        # Düngerberechnungen und EC-Zielwert basierend auf der neuen Woche aktualisieren.
        calculate()
        update_ec_value()

    except Exception as e:
         messagebox.showerror("Fehler beim Aktualisieren", f"Ein unerwarteter Fehler ist in update_week aufgetreten:\n{e}")
         # Optional: Hier könnten Felder ebenfalls geleert werden, um inkonsistenten Zustand zu vermeiden.


def calculate(fertilizer_type: Optional[str] = None, var: Optional[tk.IntVar] = None):
    """
    Berechnet die Düngermengen für die ausgewählten Düngertypen und aktualisiert deren Anzeige-Labels.
    Diese Funktion wird aufgerufen, wenn eine Dünger-Checkbox geändert wird oder wenn
    Woche oder Wassermenge im Hauptfenster geändert werden (manuell oder durch Pflanzenauswahl).

    Args:
        fertilizer_type (Optional[str]): Der spezifische Düngertyp, dessen Checkbox geändert wurde.
                                         Wenn `None`, werden alle aktiven Dünger neu berechnet (z.B. bei Wochenänderung).
        var (Optional[tk.IntVar]): Die Tkinter-Variable der geänderten Checkbox (nicht direkt verwendet,
                                   aber Teil des Checkbox-Command-Callbacks).

    Side effects:
        - Aktualisiert die Text-Labels (`result_labels`) neben den Dünger-Checkboxes mit den
          berechneten Mengen oder leert sie.
        - Zeigt eine Fehlermeldung, wenn Eingabewerte (Woche, Wassermenge) ungültig sind.
    """
    try:
        week_str = week_entry.get()
        # Wenn keine Woche eingetragen ist (z.B. keine Pflanze gewählt), keine Berechnung durchführen.
        if not week_str:
             for result_label in result_labels: # Alle Ergebnis-Labels leeren.
                 result_label.config(text="")
             return

        week = int(week_str) # Woche als Integer.
        water_amount_str = water_amount_entry.get()
        # Wassermenge als Float, Standard 0.0 wenn leer.
        water_amount = float(water_amount_str) if water_amount_str else 0.0

        # Wenn keine positive Wassermenge, keine Berechnung.
        if water_amount <= 0:
            for result_label in result_labels: # Alle Ergebnis-Labels leeren.
                 result_label.config(text="")
            # Optional: Warnung anzeigen, dass Wassermenge positiv sein muss.
            # messagebox.showwarning("Ungültige Eingabe", "Bitte eine positive Wassermenge eingeben.")
            return

        # Iteriere durch alle Düngeroptionen, ihre Checkbox-Variablen und Ergebnis-Labels.
        for i, (checkbox, f_var, result_label) in enumerate(zip(checkboxes, fertilizer_vars, result_labels)):
            current_fertilizer_type = fertilizer_options[i] # Name des aktuellen Düngers.

            # Wenn ein spezifischer fertilizer_type übergeben wurde (von einer Checkbox-Änderung),
            # dann nur diesen einen Dünger neu berechnen. Sonst alle.
            if fertilizer_type is not None and current_fertilizer_type != fertilizer_type:
                continue # Nächster Dünger in der Schleife.

            if f_var.get() == 1: # Wenn die Checkbox für diesen Dünger aktiviert ist.
                # Rufe die Hauptberechnungsfunktion auf.
                result = calculate_fertilizer_amount(week, water_amount, current_fertilizer_type)
                if result is not None:
                    result_label.config(text=f"{result:.2f} ml") # Ergebnis anzeigen.
                else:
                     result_label.config(text="Fehler") # Fehler bei der Berechnung (z.B. Config nicht geladen).
            else: # Checkbox nicht aktiviert.
                result_label.config(text="") # Ergebnis-Label leeren.

    except ValueError:
        # Falls Konvertierung von Woche oder Wassermenge zu Zahl fehlschlägt.
        for result_label in result_labels: # Alle Ergebnis-Labels leeren.
             result_label.config(text="")
        # Optional: Direkteres Feedback an den Benutzer über die fehlerhafte Eingabe.
        # messagebox.showerror("Ungültige Eingabe", "Bitte gültige Zahlen für Woche und Wassermenge eingeben.")
    except Exception as e: # Fängt andere unerwartete Fehler während der Berechnung ab.
        messagebox.showerror("Berechnungsfehler", f"Ein Fehler ist bei der Berechnung aufgetreten:\n{e}")


def update_ec_value():
    """
    Berechnet und aktualisiert das "Plan-EC (Erde)" Label in der GUI.
    Der EC-Wert wird basierend auf der aktuellen Woche der ausgewählten Pflanze ermittelt.
    Verwendet `get_ec_value()`, um den Wert aus der geladenen Konfiguration zu holen.

    Side effects:
        - Aktualisiert das `ec_label` im Hauptfenster.
        - Zeigt "-" an, wenn keine Woche oder kein EC-Wert für die Woche gefunden wird.
        - Zeigt "Fehler" an bei unerwarteten Problemen.
    """
    try:
        week_str = week_entry.get() # Aktuelle Woche aus dem Eingabefeld.
        if not week_str: # Wenn keine Woche vorhanden (z.B. keine Pflanze ausgewählt).
            ec_label.config(text="Plan-EC (Erde): -")
            return

        week = int(week_str)
        ec_value_ms = get_ec_value(week) # EC-Wert in mS/cm aus der Konfiguration holen.

        if ec_value_ms is not None:
            ec_value_us = ec_value_ms * 1000 # Umrechnung von mS/cm in µS/cm.
            ec_label.config(text=f"Plan-EC (Erde): {ec_value_us:.0f} µS/cm") # Anzeige ohne Nachkommastellen.
        else:
            ec_label.config(text="Plan-EC (Erde): -") # Kein Wert für die Woche definiert.
    except ValueError: # Falls die Woche keine gültige Zahl ist.
        ec_label.config(text="Plan-EC (Erde): -")
    except Exception as e: # Andere Fehler.
        ec_label.config(text="Plan-EC (Erde): Fehler")
        print(f"Fehler in update_ec_value: {e}")


def save_info():
    """
    Speichert die im Textfeld "Notizen zur Pflanze" eingegebenen Informationen
    für die aktuell ausgewählte Pflanze. Die Daten werden in der globalen `plant_data`
    Variable aktualisiert und dann in die CSV-Datei geschrieben.

    Side effects:
        - Modifiziert `plant_data`.
        - Ruft `save_plant_data_to_csv` auf, um die Daten persistent zu speichern.
        - Zeigt eine Bestätigungs- oder Fehlermeldung per `messagebox`.
    """
    selected_plant = plant_var.get() # Aktuell ausgewählte Pflanze.
    # Sicherstellen, dass eine gültige Pflanze ausgewählt ist.
    if not selected_plant or selected_plant not in plant_data:
         messagebox.showwarning("Keine Pflanze ausgewählt", "Bitte zuerst eine Pflanze auswählen, um Infos zu speichern.")
         return

    try:
        new_info = info_text.get("1.0", tk.END).strip() # Inhalt des Textfeldes holen.
        plant_data[selected_plant]["Infos"] = new_info # Infos in plant_data aktualisieren.
        save_plant_data_to_csv(plant_data) # Alle Pflanzendaten in CSV speichern.
        messagebox.showinfo("Gespeichert", f"Infos für '{selected_plant}' wurden gespeichert.")
    except Exception as e:
        messagebox.showerror("Fehler beim Speichern", f"Konnte Infos nicht speichern:\n{e}")

def neue_pflanze_hinzufuegen():
    """
    Öffnet ein modales Dialogfenster (`Toplevel`) zur Eingabe der Daten für eine neue Pflanze.
    Das Fenster enthält Eingabefelder für Name, Keimdatum, Genetik und Infos.
    Nach dem Speichern wird die neue Pflanze zu `plant_data` hinzugefügt, in die CSV-Datei
    gespeichert und die Haupt-GUI aktualisiert.
    """

    def pflanze_speichern():
        """
        Interne Hilfsfunktion des `neue_pflanze_hinzufuegen`-Dialogs.
        Validiert die Eingaben aus dem Dialogfenster. Wenn valide, wird die neue Pflanze
        gespeichert, die Haupt-GUI aktualisiert und der Dialog geschlossen.
        Bei Fehlern wird eine Meldung im Dialog angezeigt.
        """
        neuer_pflanzenname = pflanzenname_entry.get().strip()
        neues_keimdatum_str = keimdatum_entry.get().strip()
        neue_genetik = genetik_entry.get().strip()
        # Infos sind optional, daher kein .strip() nötig, wenn leer erlaubt.
        neue_infos = infos_text_new.get("1.0", tk.END).strip()

        # --- Eingabevalidierung ---
        errors = [] # Liste für Fehlermeldungen.
        if not neuer_pflanzenname:
            errors.append("Pflanzenname fehlt.")
        elif neuer_pflanzenname in plant_data: # Prüfen auf existierenden Pflanzennamen.
            errors.append(f"Pflanzenname '{neuer_pflanzenname}' existiert bereits.")

        if not neues_keimdatum_str:
            errors.append("Keimdatum fehlt.")
        else:
            try:
                keimdatum_objekt = datetime.strptime(neues_keimdatum_str, '%d.%m.%Y')
                # Zusätzliche Prüfung: Keimdatum nicht in der Zukunft.
                if keimdatum_objekt > datetime.now():
                    errors.append("Keimdatum darf nicht in der Zukunft liegen.")
            except ValueError:
                errors.append("Ungültiges Keimdatum (Format TT.MM.JJJJ).")

        if not neue_genetik: # Genetik ist ein Pflichtfeld.
            errors.append("Genetik fehlt.")
        # Infos sind optional, daher keine explizite Prüfung auf Vorhandensein.

        # Wenn Validierungsfehler aufgetreten sind:
        if errors:
            fehler_label.config(text="\n".join(errors)) # Fehler im Dialog anzeigen.
            return # Funktion hier beenden, nicht speichern.
        # --- Ende Validierung ---

        try:
            # Erneutes Parsen des Datums ist nicht nötig, wenn keimdatum_objekt oben schon gültig war.
            # Aber zur Sicherheit, falls Logik geändert wird:
            keimdatum_objekt = datetime.strptime(neues_keimdatum_str, '%d.%m.%Y')

            # Neue Pflanze zum globalen plant_data Dictionary hinzufügen.
            plant_data[neuer_pflanzenname] = {
                "Keimdatum": keimdatum_objekt,
                "Genetik": neue_genetik,
                "Infos": neue_infos
            }

            save_plant_data_to_csv(plant_data) # Alle Pflanzendaten in CSV speichern.

            # Hauptfenster-Dropdown aktualisieren und neue Pflanze auswählen.
            plant_keys = list(plant_data.keys())
            plant_dropdown['values'] = plant_keys # Aktualisierte Liste im Dropdown.
            plant_var.set(neuer_pflanzenname) # Neue Pflanze als ausgewählt setzen.
            update_week() # GUI-Felder im Hauptfenster aktualisieren.

            new_plant_window.destroy() # Dialogfenster schließen.
            messagebox.showinfo("Erfolg", f"Pflanze '{neuer_pflanzenname}' erfolgreich hinzugefügt.")

        except Exception as e: # Fängt Fehler beim Speichern oder Aktualisieren der GUI ab.
             fehler_label.config(text=f"Speicherfehler: {e}")


    # --- Dialogfenster für neue Pflanze erstellen ---
    new_plant_window = tk.Toplevel(window) # Toplevel-Fenster erstellen.
    new_plant_window.title("Neue Pflanze hinzufügen")
    new_plant_window.transient(window) # Macht das Fenster modal (bleibt über dem Hauptfenster).
    new_plant_window.grab_set()     # Erzwingt den Eingabefokus auf dieses Fenster.
    new_plant_window.resizable(False, False) # Größe des Fensters nicht änderbar.

    # Grid-Layout Konfiguration für das Dialogfenster.
    new_plant_window.columnconfigure(1, weight=1) # Spalte 1 (Eingabefelder) dehnt sich aus.

    # Eingabefelder und Labels erstellen und im Grid platzieren.
    ttk.Label(new_plant_window, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    pflanzenname_entry = ttk.Entry(new_plant_window, width=40)
    pflanzenname_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Keimdatum (TT.MM.JJJJ):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    keimdatum_entry = ttk.Entry(new_plant_window, width=40)
    keimdatum_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Genetik:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    genetik_entry = ttk.Entry(new_plant_window, width=40)
    genetik_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Infos:").grid(row=3, column=0, padx=10, pady=5, sticky="nw") # nw = north-west (oben linksbündig)
    # ScrolledText für mehrzeilige Infos mit Scrollbar.
    infos_text_new = scrolledtext.ScrolledText(new_plant_window, height=6, width=40, wrap=tk.WORD)
    infos_text_new.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

    # Label zur Anzeige von Validierungsfehlern.
    fehler_label = ttk.Label(new_plant_window, text="", foreground="red", wraplength=300) # wraplength für Zeilenumbruch.
    fehler_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # Frame für die Buttons "Speichern" und "Abbrechen".
    button_frame = ttk.Frame(new_plant_window)
    button_frame.grid(row=5, column=0, columnspan=2, pady=10)

    speichern_button = ttk.Button(button_frame, text="Speichern", command=pflanze_speichern)
    speichern_button.pack(side=tk.RIGHT, padx=5) # Rechts im Frame.

    abbrechen_button = ttk.Button(button_frame, text="Abbrechen", command=new_plant_window.destroy)
    abbrechen_button.pack(side=tk.RIGHT, padx=5) # Rechts neben Speichern.

    pflanzenname_entry.focus_set() # Setzt den Fokus initial auf das Namensfeld.
    new_plant_window.wait_window() # Hält die Ausführung an, bis das Dialogfenster geschlossen wird.


def pflanze_loeschen():
    """
    Löscht die aktuell im Hauptfenster ausgewählte Pflanze.
    Zeigt eine Bestätigungsdialogbox vor dem Löschen an.
    Aktualisiert `plant_data`, speichert in CSV und aktualisiert die Haupt-GUI.

    Side effects:
        - Modifiziert `plant_data` (entfernt einen Eintrag).
        - Ruft `save_plant_data_to_csv` auf.
        - Aktualisiert das Pflanzen-Dropdown und andere GUI-Elemente durch `update_week`.
        - Zeigt Bestätigungs- oder Fehlermeldungen.
    """
    selected_plant = plant_var.get() # Ausgewählte Pflanze.
    # Prüfen, ob eine Pflanze ausgewählt wurde.
    if not selected_plant or selected_plant not in plant_data:
        messagebox.showwarning("Keine Pflanze ausgewählt", "Bitte zuerst eine Pflanze zum Löschen auswählen.")
        return

    # Bestätigungsdialog anzeigen.
    if messagebox.askyesno("Pflanze löschen", f"Möchten Sie die Pflanze '{selected_plant}' wirklich unwiderruflich löschen?"):
        try:
            del plant_data[selected_plant] # Pflanze aus dem Dictionary entfernen.
            save_plant_data_to_csv(plant_data) # Änderungen in CSV speichern.

            # Hauptfenster-Dropdown aktualisieren.
            plant_keys = list(plant_data.keys())
            plant_dropdown['values'] = plant_keys
            if plant_keys: # Wenn noch Pflanzen vorhanden sind.
                plant_var.set(plant_keys[0]) # Erste verbleibende Pflanze auswählen.
            else: # Keine Pflanzen mehr vorhanden.
                plant_var.set("") # Dropdown leeren.

            update_week() # GUI-Felder basierend auf der neuen Auswahl (oder keiner Auswahl) aktualisieren.
            messagebox.showinfo("Gelöscht", f"Pflanze '{selected_plant}' wurde gelöscht.")
        except Exception as e:
            messagebox.showerror("Fehler beim Löschen", f"Konnte Pflanze nicht löschen:\n{e}")

def ec_berechnen():
    """
    Öffnet ein modales Dialogfenster ("EC-Helper") zur Berechnung der benötigten Düngermenge,
    um einen bestimmten EC-Zielwert in der Nährlösung zu erreichen.

    Der Dialog erlaubt die Eingabe des aktuellen EC-Werts und des Ziel-EC-Werts
    (entweder manuell oder übernommen aus dem Hauptfenster-Planwert).
    Die benötigte Wassermenge wird aus dem Hauptfenster übernommen.
    Das Ergebnis zeigt die benötigte Menge für Wachstums- ODER Blütedünger.
    """

    def toggle_ec_soll_entry(*args):
        """
        Aktiviert oder deaktiviert das manuelle Eingabefeld für den Soll-EC-Wert,
        abhängig von der Auswahl im Dropdown-Menü ("vorhanden" vs. "manuell").
        Wird als Callback für die `ec_soll_var` Variable verwendet.
        """
        if ec_soll_var.get() == "manuell":
            ec_soll_entry.config(state="normal") # Eingabefeld aktivieren.
            ec_soll_entry.focus_set() # Fokus auf das aktivierte Feld setzen.
        else:
            ec_soll_entry.config(state="disabled") # Eingabefeld deaktivieren.

    def duenger_berechnen():
        """
        Interne Hilfsfunktion des EC-Helper Dialogs.
        Berechnet die benötigte Düngermenge (Wachstums- oder Blütedünger),
        um den Ziel-EC zu erreichen. Validiert Eingaben und zeigt Ergebnisse oder Fehler
        im `ergebnis_label` des Dialogs an.
        """
        try:
            # Aktuellen EC-Wert (Ist-EC) aus dem Eingabefeld holen und validieren.
            ec_ist_str = ec_ist_entry.get()
            if not ec_ist_str:
                raise ValueError("Aktueller EC-Wert fehlt.")
            ec_ist = float(ec_ist_str) # Konvertierung zu float.
            if ec_ist < 0:
                 raise ValueError("Aktueller EC-Wert darf nicht negativ sein.")

            # Wassermenge aus dem Hauptfenster holen und validieren.
            wassermenge_str = water_amount_entry.get() # Aus dem Hauptfenster-Widget.
            if not wassermenge_str:
                 raise ValueError("Wassermenge im Hauptfenster fehlt.")
            wassermenge = float(wassermenge_str)
            if wassermenge <= 0:
                 raise ValueError("Wassermenge muss positiv sein.")

            # Ziel-EC-Wert (Soll-EC) ermitteln.
            ec_soll: float
            if ec_soll_var.get() == "vorhanden": # Option "vorhanden" (aus Hauptfenster) gewählt.
                ec_soll_text = ec_label.cget("text") # Text aus dem Plan-EC Label des Hauptfensters.
                # Format z.B.: "Plan-EC (Erde): 1200 µS/cm"
                if ":" not in ec_soll_text or "µS/cm" not in ec_soll_text: # Grundlegende Formatprüfung.
                     raise ValueError("Ziel-EC-Wert im Hauptfenster nicht verfügbar oder ungültig.")
                # Extrahiere den Zahlenwert.
                ec_soll_str = ec_soll_text.split(":")[1].strip().split()[0]
                ec_soll = float(ec_soll_str)
            else: # Option "manuell" gewählt.
                ec_soll_str = ec_soll_entry.get() # Wert aus dem manuellen Eingabefeld.
                if not ec_soll_str:
                     raise ValueError("Manueller Soll-EC-Wert fehlt.")
                ec_soll = float(ec_soll_str)
                if ec_soll <= 0: # Soll-EC sollte positiv sein.
                     raise ValueError("Soll-EC-Wert muss positiv sein.")

            # Wenn aktueller EC bereits Ziel erreicht oder überschreitet.
            if ec_ist >= ec_soll:
                 ergebnis_label.config(text="Aktueller EC ist bereits über oder gleich dem Soll-EC.\nKein Dünger benötigt.", foreground="blue")
                 return

            # Berechnung für beide Düngerarten (Wachstum und Blüte).
            menge_wachstum = berechne_wachstumduenger_menge_fuer_ec(ec_ist, ec_soll, wassermenge)
            menge_bluete = berechne_bluetenduenger_menge_fuer_ec(ec_ist, ec_soll, wassermenge)

            # Ergebnis im Dialog anzeigen.
            ergebnis_text = (
                f"Um {ec_soll:.0f} µS/cm zu erreichen, fügen Sie hinzu:\n\n"
                f"-> ENTWEDER {menge_wachstum:.2f} ml Wachstumsdünger\n"
                f"-> ODER {menge_bluete:.2f} ml Blütedünger\n\n"
                f"(Berechnet für {wassermenge:.2f} L Wasser)"
            )
            ergebnis_label.config(text=ergebnis_text, foreground="black")

        except ValueError as ve: # Fängt spezifische Fehler bei der Eingabevalidierung.
            ergebnis_label.config(text=f"Eingabefehler: {ve}", foreground="red")
        except Exception as e: # Fängt andere unerwartete Fehler.
            ergebnis_label.config(text=f"Fehler: {e}", foreground="red")

    # --- Dialogfenster für EC-Berechnung erstellen ---
    ec_window = tk.Toplevel(window)
    ec_window.title("EC-Helper: Dünger berechnen")
    ec_window.transient(window) # Modal.
    ec_window.grab_set()     # Eingabefokus.
    ec_window.resizable(False, False) # Größe nicht änderbar.

    # Grid-Konfiguration für das Dialogfenster.
    ec_window.columnconfigure(1, weight=1) # Spalte für Eingabefelder dehnt sich aus.

    # Einführendes Label mit Erklärung des Helfers.
    intro_text = "Hilfsmittel zur Anpassung Ihrer Nährlösung an einen bestimmten EC-Zielwert, wenn der EC-Wert Ihres aktuellen Wassers bekannt ist."
    intro_label = ttk.Label(ec_window, text=intro_text, wraplength=350, justify=tk.LEFT)
    intro_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,15), sticky="ew")

    # Eingabefelder für aktuellen EC und Ziel-EC.
    ttk.Label(ec_window, text="Aktueller EC (µS/cm):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    ec_ist_entry = ttk.Entry(ec_window, width=25)
    ec_ist_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(ec_window, text="Soll-EC (µS/cm):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    ec_soll_frame = ttk.Frame(ec_window) # Frame, um Dropdown und Entry nebeneinander zu platzieren.
    ec_soll_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
    ec_soll_frame.columnconfigure(1, weight=1) # Entry-Feld im Frame dehnt sich aus.

    ec_soll_var = tk.StringVar(value="vorhanden") # Variable für Dropdown-Auswahl (Default: "vorhanden").
    ec_soll_var.trace_add("write", toggle_ec_soll_entry) # Ruft toggle_ec_soll_entry bei Änderung auf.

    # Dropdown für Auswahl "vorhanden" (aus Hauptfenster) oder "manuell".
    ec_soll_dropdown = ttk.OptionMenu(ec_soll_frame, ec_soll_var, "vorhanden", "vorhanden", "manuell")
    ec_soll_dropdown.grid(row=0, column=0, padx=(0, 5))

    ec_soll_entry = ttk.Entry(ec_soll_frame, width=15, state="disabled") # Manuelles Eingabefeld, initial deaktiviert.
    ec_soll_entry.grid(row=0, column=1, sticky="ew")

    # Button zum Starten der Berechnung.
    berechnen_button = ttk.Button(ec_window, text="Düngermengen berechnen", command=duenger_berechnen)
    berechnen_button.grid(row=3, column=0, columnspan=2, pady=10)

    # Label zur Anzeige der Ergebnisse oder Fehlermeldungen.
    ergebnis_label = ttk.Label(ec_window, text="Ergebnis der Berechnung wird hier angezeigt. Bitte alle Werte eingeben.", wraplength=350, justify=tk.LEFT)
    ergebnis_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    ec_ist_entry.focus_set() # Initialer Fokus auf das erste Eingabefeld.
    toggle_ec_soll_entry() # Initialen Status des manuellen EC-Soll-Feldes setzen.
    ec_window.wait_window() # Warten, bis das Dialogfenster geschlossen wird.


# --- Haupt-GUI Erstellung ---
# Hauptfenster der Anwendung erstellen.
window = tk.Tk()
window.title("Pflanzen Düngerberechnung v1.2") # Fenstertitel.
window.minsize(550, 550) # Mindestgröße des Fensters.

# Optional: Theming für ein moderneres Aussehen der ttk Widgets.
style = ttk.Style()
# Verfügbare Themes können je nach System variieren ('clam', 'alt', 'default', 'classic', 'vista', 'xpnative').
# style.theme_use('clam')

# Grid-Layout Konfiguration für das Hauptfenster.
# Spalte 1 (mittlere Spalte, wo viele Eingabefelder sind) soll sich ausdehnen, wenn Fenstergröße geändert wird.
window.columnconfigure(1, weight=1)

# --- Widgets-Erstellung und -Platzierung ---

# Frame für Pflanzenauswahl und Basisinformationen (Genetik, Woche, Keimdatum).
plant_info_frame = ttk.LabelFrame(window, text="Pflanzeninformationen")
plant_info_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew") # ew = east-west (horizontal ausdehnen)
plant_info_frame.columnconfigure(1, weight=1) # Spalte für Dropdown und Genetik dehnt sich aus.

# Pflanzenauswahl (Dropdown-Menü).
ttk.Label(plant_info_frame, text="Pflanze:").grid(row=0, column=0, padx=5, pady=5, sticky="w") # w = west (linksbündig)
plant_var = tk.StringVar() # Variable zur Speicherung der Auswahl.
plant_dropdown = ttk.Combobox(plant_info_frame, textvariable=plant_var, state="readonly") # Schreibgeschützt.
plant_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
plant_dropdown.bind("<<ComboboxSelected>>", update_week) # Event bei Auswahl einer Pflanze.

# Anzeige des EC-Zielwerts (Plan-EC).
ec_label = ttk.Label(plant_info_frame, text="Plan-EC (Erde): -", font=('TkDefaultFont', 9, 'bold'))
ec_label.grid(row=0, column=2, padx=10, pady=5, sticky="e") # e = east (rechtsbündig)

# Anzeige der Genetik.
ttk.Label(plant_info_frame, text="Genetik:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
genetics_entry = ttk.Entry(plant_info_frame, state="readonly") # Schreibgeschützt.
genetics_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew") # Nimmt Platz über 2 Spalten.

# Anzeige und Eingabe der Wachstumswoche.
ttk.Label(plant_info_frame, text="Woche seit Keimung:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
week_entry = ttk.Entry(plant_info_frame, width=10) # Schmaleres Feld.
week_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
week_entry.bind("<Return>", lambda event: calculate()) # Neuberechnung bei Enter.

# Anzeige des Keimdatums.
ttk.Label(plant_info_frame, text="Keimdatum:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
germination_date_entry = ttk.Entry(plant_info_frame, state="readonly", width=12)
germination_date_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")

# Frame für Berechnungseingaben (Wassermenge).
calc_input_frame = ttk.LabelFrame(window, text="Berechnungsgrundlage")
calc_input_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
calc_input_frame.columnconfigure(1, weight=1) # Spalte für Eingabefeld dehnt sich leicht.

# Eingabe der Wassermenge.
ttk.Label(calc_input_frame, text="Wassermenge (Liter):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
water_amount_entry = ttk.Entry(calc_input_frame, width=10)
water_amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
water_amount_entry.insert(0, "1.0") # Standardwert 1.0 Liter.
water_amount_entry.bind("<Return>", lambda event: calculate()) # Neuberechnung bei Enter.

# Button zum Öffnen des EC-Helpers.
ec_button = ttk.Button(calc_input_frame, text="EC-Helper", command=ec_berechnen)
ec_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")

# Frame für Düngerauswahl und Anzeige der Ergebnisse.
fertilizer_frame = ttk.LabelFrame(window, text="Düngerauswahl & Ergebnisse (ml pro angegebene Wassermenge)")
fertilizer_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="nsew") # nsew = alle Richtungen (dehnt sich aus)
fertilizer_frame.columnconfigure(0, weight=1) # Spalte für Checkbox-Texte dehnt sich aus.
fertilizer_frame.columnconfigure(1, minsize=80) # Mindestbreite für Ergebnis-Labels.
window.rowconfigure(2, weight=1) # Zeile 2 im Hauptfenster (dieser Frame) dehnt sich vertikal aus.

# Düngeroptionen - Liste wird dynamisch gefüllt, wenn F_DATA geladen ist.
# Fallback-Liste, falls F_DATA aus irgendeinem Grund nicht korrekt geladen wird und das Programm nicht vorher beendet.
fertilizer_options = [
    "CalMag - Substrate - Prevention", "CalMag - Substrate - Correction",
    "GreenHome Wachstumsduenger - Substrate", "GreenHome Bluetenduenger - Substrate",
    "Fish-Mix (5-1-4) - Substrate", "Root-Juice"
]
if F_DATA: # Wenn F_DATA erfolgreich aus der Konfigurationsdatei geladen wurde.
    fertilizer_options = list(F_DATA.keys()) # Verwende die Düngernamen aus der Konfiguration.

# Listen zur Speicherung der Tkinter-Variablen für Checkboxen und der Ergebnis-Labels.
fertilizer_vars = []
checkboxes = []
result_labels = []

# Erstellung der Checkboxen und Ergebnis-Labels für jeden Düngertyp.
for i, option_text in enumerate(fertilizer_options):
    var = tk.IntVar() # Tkinter-Variable für den Zustand der Checkbox (0 oder 1).
    fertilizer_vars.append(var)

    # Lambda-Funktion für den Checkbox-Befehl, um den aktuellen Düngertyp zu binden.
    cmd = lambda opt=option_text, v=var: calculate(opt, v)

    checkbox = ttk.Checkbutton(fertilizer_frame, text=option_text, variable=var, command=cmd)
    checkbox.grid(row=i, column=0, padx=5, pady=2, sticky="w") # Links im Frame platziert.
    checkboxes.append(checkbox)

    result_label = ttk.Label(fertilizer_frame, text="", width=10, anchor="e") # Rechtsbündig für Mengenangabe.
    result_label.grid(row=i, column=1, padx=5, pady=2, sticky="e") # Rechts im Frame platziert.
    result_labels.append(result_label)

# Frame für Notizen zur Pflanze.
info_frame = ttk.LabelFrame(window, text="Notizen zur Pflanze")
info_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
info_frame.columnconfigure(0, weight=1) # Textfeld soll sich horizontal ausdehnen.

# Mehrzeiliges Textfeld für Notizen.
info_text = scrolledtext.ScrolledText(info_frame, height=6, width=50, wrap=tk.WORD, state="disabled") # Initial deaktiviert.
info_text.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Button zum Speichern der Notizen.
save_button = ttk.Button(info_frame, text="Infos speichern", command=save_info, state="disabled") # Initial deaktiviert.
save_button.grid(row=1, column=1, padx=5, pady=5, sticky="e") # Rechtsbündig im Frame.

# Frame für Aktionen (Neue Pflanze, Pflanze löschen).
action_frame = ttk.Frame(window)
action_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="e") # Rechtsbündig im Fenster.

neue_pflanze_button = ttk.Button(action_frame, text="Neue Pflanze anlegen", command=neue_pflanze_hinzufuegen)
neue_pflanze_button.pack(side=tk.LEFT, padx=5) # Buttons nebeneinander.

loeschen_button = ttk.Button(action_frame, text="Pflanze löschen", command=pflanze_loeschen)
loeschen_button.pack(side=tk.LEFT, padx=5)


# --- Initialisierung der Anwendung ---
# 1. Lade Konfiguration (Düngeschemata, EC-Werte). Bei Fehler wird Anwendung beendet.
if initialize_config_and_exit_on_error(window):
    # 2. Lade Pflanzendaten aus CSV.
    plant_data = read_plant_data()
    # 3. Fülle das Dropdown-Menü mit Pflanzennamen.
    plant_dropdown['values'] = list(plant_data.keys())
    # 4. Wähle ggf. die erste Pflanze aus und aktualisiere die GUI.
    if plant_data:
        plant_var.set(list(plant_data.keys())[0]) # Erste Pflanze als Standard auswählen.
        update_week() # GUI-Felder basierend auf dieser Auswahl aktualisieren.
    else:
        update_week() # GUI-Felder leeren, wenn keine Pflanzen vorhanden sind.

    # 5. Starte die Tkinter Hauptschleife.
    window.mainloop()
# Wenn initialize_config_and_exit_on_error() False zurückgibt (kritischer Ladefehler),
# wurde window.destroy() bereits aufgerufen, und die mainloop wird nicht gestartet.