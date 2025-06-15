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
import copy # For deep copying schemes
from tkinter import simpledialog # For simple input dialogs

# --- Konstanten ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(SCRIPT_DIR, 'pflanzendaten.csv')
CONFIG_FILENAME = os.path.join(SCRIPT_DIR, 'fertilizer_config.json') # Config file name
APP_STATUS_FILENAME = os.path.join(SCRIPT_DIR, 'app_status.json') # For storing app status like timestamps
CSV_HEADER = ["Pflanzenname", "Keimdatum", "Genetik", "Infos"]

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
    if F_DATA is None or fertilizer_type not in F_DATA:
        print(f"Warnung: Unbekannter Düngertyp '{fertilizer_type}' oder F_DATA nicht initialisiert.")
        return None # Düngertyp nicht in Konfiguration gefunden oder F_DATA leer.

    fertilizer_details = F_DATA[fertilizer_type] # Enthält 'schedule' und 'ec_contribution_factor'
    current_fertilizer_schedule = fertilizer_details.get("schedule")

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
def load_fertilizer_config() -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[Dict[str, float]]]:
    """
    Lädt die gesamte Düngerkonfiguration aus der JSON-Datei (`fertilizer_config.json`),
    einschließlich aller Schemata, des aktiven Schemas und der Standard-EC-Faktoren.

    Die Funktion liest die JSON-Datei und verarbeitet die Struktur:
    - "active_scheme_name": Name des standardmäßig aktiven Schemas.
    - "schemes": Ein Dictionary, das alle verfügbaren Düngeschemata enthält.
        - Jedes Schema enthält "fertilizer_data" und "ec_values".
        - Wochenschlüssel in "schedule" und "ec_values" werden zu Integer konvertiert.
        - Dosierungen, EC-Werte und "ec_contribution_factor" werden als float interpretiert.
    - "default_ec_factors": Enthält Standard-EC-Faktoren für "growth" und "bloom".

    Returns:
        tuple[Optional[Dict[str, Any]], Optional[str], Optional[Dict[str, float]]]:
        Ein Tupel bestehend aus drei Elementen:
        1.  `all_schemes_data` (Dict[str, Any]): Ein Dictionary aller geladenen Schemata.
            - Schlüssel: Schemaname (str).
            - Wert: Ein Dictionary mit den Daten des Schemas, einschließlich
              verarbeiteter "fertilizer_data" und "ec_values".
        2.  `active_scheme_name` (str): Der Name des aktiven Schemas.
        3.  `default_ec_factors` (Dict[str, float]): Die Standard-EC-Faktoren.
        Im Fehlerfall (z.B. Datei nicht gefunden, JSON-Fehler, fehlende Hauptschlüssel)
        wird `(None, None, None)` zurückgegeben und eine Fehlermeldung angezeigt.

    Fehlerbehandlung:
        - `FileNotFoundError`, `json.JSONDecodeError`, `ValueError`, `Exception` wie zuvor.
        - Zusätzliche Prüfungen auf das Vorhandensein von "schemes", "active_scheme_name",
          "default_ec_factors" in der JSON-Datei.
    """
    try:
        with open(CONFIG_FILENAME, 'r', encoding='utf-8') as f:
            config_json = json.load(f)

        active_scheme_name = config_json.get("active_scheme_name")
        schemes_json = config_json.get("schemes")
        default_ec_factors_json = config_json.get("default_ec_factors")

        if not active_scheme_name or not schemes_json or default_ec_factors_json is None:
            messagebox.showerror("Konfigurationsfehler",
                                 f"Wichtige Schlüssel ('active_scheme_name', 'schemes', 'default_ec_factors') "
                                 f"fehlen in '{CONFIG_FILENAME}'.")
            return None, None, None

        all_schemes_data: Dict[str, Any] = {}
        for scheme_name, scheme_content in schemes_json.items():
            fertilizer_data_json = scheme_content.get("fertilizer_data", {})
            processed_f_data: Dict[str, Dict[str, Any]] = {}
            for f_type, f_details_json in fertilizer_data_json.items():
                schedule_json = f_details_json.get("schedule", {})
                processed_schedule: Dict[int, float] = {}
                for week_str, dosage in schedule_json.items():
                    try:
                        processed_schedule[int(week_str)] = float(dosage)
                    except ValueError:
                        print(f"Warnung: Ungültiger Wochenschlüssel oder Dosierung für {f_type} in Woche '{week_str}' im Schema '{scheme_name}'. Überspringe.")

                ec_contribution = f_details_json.get("ec_contribution_factor")
                if ec_contribution is None:
                     print(f"Warnung: Fehlender 'ec_contribution_factor' für {f_type} im Schema '{scheme_name}'. Setze auf Placeholder 0.0.")
                     ec_contribution_float = 0.0
                else:
                    try:
                        ec_contribution_float = float(ec_contribution)
                    except ValueError:
                        print(f"Warnung: Ungültiger 'ec_contribution_factor' ({ec_contribution}) für {f_type} im Schema '{scheme_name}'. Setze auf Placeholder 0.0.")
                        ec_contribution_float = 0.0

                processed_f_data[f_type] = {
                    "schedule": processed_schedule,
                    "ec_contribution_factor": ec_contribution_float
                }

            ec_values_json = scheme_content.get("ec_values", {})
            processed_ec_values: Dict[int, float] = {}
            for week_str, ec_val in ec_values_json.items():
                try:
                    processed_ec_values[int(week_str)] = float(ec_val)
                except ValueError:
                    print(f"Warnung: Ungültiger Wochenschlüssel oder EC-Wert '{week_str}' im Schema '{scheme_name}'. Überspringe.")

            all_schemes_data[scheme_name] = {
                "fertilizer_data": processed_f_data,
                "ec_values": processed_ec_values
            }

        processed_default_ec_factors: Dict[str, float] = {}
        if isinstance(default_ec_factors_json, dict):
            for key, value in default_ec_factors_json.items():
                try:
                    processed_default_ec_factors[key] = float(value)
                except ValueError:
                    messagebox.showerror("Konfigurationsfehler", f"Ungültiger Wert für default_ec_factor '{key}': {value}. Muss eine Zahl sein.")
                    return None, None, None
        else:
            messagebox.showerror("Konfigurationsfehler", f"Struktur für 'default_ec_factors' ist ungültig in '{CONFIG_FILENAME}'.")
            return None, None, None

        return all_schemes_data, active_scheme_name, processed_default_ec_factors

    except FileNotFoundError:
        messagebox.showerror("Konfigurationsfehler", f"Konfigurationsdatei '{CONFIG_FILENAME}' nicht gefunden.")
        return None, None, None
    except json.JSONDecodeError as e:
        messagebox.showerror("Konfigurationsfehler", f"Fehler beim Lesen der JSON-Konfigurationsdatei '{CONFIG_FILENAME}':\n{e}")
        return None, None, None
    except Exception as e:
        messagebox.showerror("Unerwarteter Fehler", f"Ein unerwarteter Fehler ist beim Laden der Konfiguration aufgetreten:\n{e}")
        return None, None, None

# Globale Variablen für Konfigurationsdaten
F_DATA: Optional[Dict[str, Dict[str, Any]]] = None # Hält 'schedule' und 'ec_contribution_factor' des aktiven Schemas
EC_TARGET_VALUES: Optional[Dict[int, float]] = None # Hält 'ec_values' des aktiven Schemas
ALL_SCHEMES: Optional[Dict[str, Any]] = None
ACTIVE_SCHEME_NAME: Optional[str] = None
DEFAULT_EC_FACTORS: Optional[Dict[str, float]] = None

def initialize_config_and_exit_on_error(app_window: tk.Tk) -> bool:
    """
    Initialisiert die Konfiguration: Lädt alle Schemata, setzt das aktive Schema und Standard-EC-Faktoren.
    Aktualisiert globale Variablen `ALL_SCHEMES`, `ACTIVE_SCHEME_NAME`, `DEFAULT_EC_FACTORS`,
    sowie `F_DATA` und `EC_TARGET_VALUES` basierend auf dem aktiven Schema.

    Bei einem Ladefehler oder wenn das aktive Schema nicht in den geladenen Schemata gefunden wird:
    - Zeigt eine kritische Fehlermeldung.
    - Zerstört das Hauptfenster der Anwendung (`app_window`).
    - Gibt `False` zurück.

    Args:
        app_window (tk.Tk): Das Hauptfenster der Tkinter-Anwendung.
    Returns:
        bool: `True` bei erfolgreicher Initialisierung, `False` sonst.
    """
    global ALL_SCHEMES, ACTIVE_SCHEME_NAME, DEFAULT_EC_FACTORS, F_DATA, EC_TARGET_VALUES

    loaded_schemes, active_name, loaded_defaults = load_fertilizer_config()

    if loaded_schemes is None or active_name is None or loaded_defaults is None:
        # Fehlermeldung wurde bereits in load_fertilizer_config angezeigt
        if not app_window.winfo_exists(): # Prüfen, ob Fenster noch existiert, falls es schon zerstört wurde
             sys.exit(1) # Beenden, wenn Fenster nicht mehr da ist
        messagebox.showerror("Kritischer Fehler", "Konfiguration konnte nicht vollständig geladen werden. Die Anwendung wird beendet.")
        app_window.destroy()
        return False

    ALL_SCHEMES = loaded_schemes
    ACTIVE_SCHEME_NAME = active_name
    DEFAULT_EC_FACTORS = loaded_defaults

    if ACTIVE_SCHEME_NAME not in ALL_SCHEMES:
        messagebox.showerror("Kritischer Fehler",
                             f"Das aktive Schema '{ACTIVE_SCHEME_NAME}' wurde nicht in den geladenen Schemata gefunden. "
                             f"Die Anwendung wird beendet.")
        app_window.destroy()
        return False

    active_scheme_data = ALL_SCHEMES[ACTIVE_SCHEME_NAME]
    F_DATA = active_scheme_data.get("fertilizer_data")
    EC_TARGET_VALUES = active_scheme_data.get("ec_values")

    if F_DATA is None or EC_TARGET_VALUES is None:
        messagebox.showerror("Kritischer Fehler",
                             f"Daten für das aktive Schema '{ACTIVE_SCHEME_NAME}' sind unvollständig (fertilizer_data oder ec_values fehlt). "
                             f"Die Anwendung wird beendet.")
        app_window.destroy()
        return False

    if not F_DATA or not EC_TARGET_VALUES: # Prüft auf leere Dictionaries
         messagebox.showwarning("Konfigurationswarnung",
                               f"Düngemitteldaten oder EC-Zielwerte für das aktive Schema '{ACTIVE_SCHEME_NAME}' sind leer. "
                                "Bitte überprüfen Sie die Konfigurationsdatei. "
                                "Die Anwendung startet, aber einige Funktionen könnten eingeschränkt sein.")
    return True

# --- App Status Management ---
def load_app_status() -> Dict[str, Any]:
    """
    Lädt den Anwendungsstatus aus APP_STATUS_FILENAME.
    Gibt Standardwerte zurück, wenn die Datei nicht existiert oder ungültig ist.
    """
    defaults = {"last_ec_helper_usage": None}
    try:
        with open(APP_STATUS_FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return defaults
    except json.JSONDecodeError:
        print(f"Warnung: Fehler beim Lesen der Statusdatei '{APP_STATUS_FILENAME}'. Verwende Standardwerte.")
        return defaults

def save_app_status(status_data: Dict[str, Any]):
    """
    Speichert den übergebenen Status in APP_STATUS_FILENAME.
    """
    try:
        with open(APP_STATUS_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
    except IOError as e:
        messagebox.showerror("Fehler beim Speichern des Status", f"Konnte Statusdatei nicht schreiben:\n{e}")


def berechne_menge_fuer_ec_anpassung(EC_ist: float, EC_soll: float, wassermenge_liter: float, ec_factor: float) -> float:
    """
    Berechnet die benötigte Menge Dünger (in ml), um einen Ziel-EC-Wert zu erreichen,
    basierend auf dem spezifischen EC-Faktor des Düngers.

    Args:
        EC_ist (float): Der aktuelle EC-Wert der Nährlösung in µS/cm.
        EC_soll (float): Der gewünschte Ziel-EC-Wert der Nährlösung in µS/cm.
        wassermenge_liter (float): Die Gesamtmenge der Nährlösung in Litern.

    Returns:
        float: Die benötigte Menge Wachstumsdünger in ml. Gibt 0.0 zurück, wenn der
               aktuelle EC-Wert bereits über oder gleich dem Ziel-EC-Wert ist.
    """
    if EC_ist >= EC_soll:
        return 0.0
    if ec_factor <= 0:
        print("Warnung: EC-Faktor ist Null oder negativ. Berechnung nicht möglich.")
        return 0.0 # Oder raise ValueError
    benötigte_ec_zunahme = EC_soll - EC_ist
    benötigte_menge_ml = (benötigte_ec_zunahme / ec_factor) * wassermenge_liter
    return max(0.0, benötigte_menge_ml)

# --- GUI Callbacks und Hilfsfunktionen ---

def save_config_to_json():
    """
    Speichert den aktuellen Zustand von ALL_SCHEMES, ACTIVE_SCHEME_NAME und
    DEFAULT_EC_FACTORS zurück in die fertilizer_config.json Datei.
    """
    if ALL_SCHEMES is None or ACTIVE_SCHEME_NAME is None or DEFAULT_EC_FACTORS is None:
        messagebox.showerror("Fehler", "Konfigurationsdaten sind nicht vollständig geladen. Kann nicht speichern.")
        return False

    config_to_save = {
        "active_scheme_name": ACTIVE_SCHEME_NAME,
        "schemes": ALL_SCHEMES,
        "default_ec_factors": DEFAULT_EC_FACTORS
    }
    try:
        with open(CONFIG_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2) # indent für Lesbarkeit
        return True
    except IOError as e:
        messagebox.showerror("Speicherfehler", f"Fehler beim Schreiben der Konfigurationsdatei '{CONFIG_FILENAME}':\n{e}")
        return False
    except Exception as e:
        messagebox.showerror("Unerwarteter Speicherfehler", f"Ein Fehler ist beim Speichern der Konfiguration aufgetreten:\n{e}")
        return False

active_scheme_label: Optional[ttk.Label] = None # Globale Variable für das Label

def update_main_ui_for_active_scheme():
    """
    Aktualisiert die Haupt-GUI, wenn das aktive Schema wechselt.
    Dies beinhaltet das Neuladen von F_DATA, EC_TARGET_VALUES,
    das Neuaufbauen der Dünger-Checkboxes und das Aktualisieren des Active-Scheme-Labels.
    """
    global F_DATA, EC_TARGET_VALUES, fertilizer_options, fertilizer_vars, checkboxes, result_labels

    if ALL_SCHEMES is None or ACTIVE_SCHEME_NAME is None or ACTIVE_SCHEME_NAME not in ALL_SCHEMES:
        messagebox.showerror("Fehler", "Aktives Schema konnte nicht geladen werden.")
        return

    active_scheme_data = ALL_SCHEMES[ACTIVE_SCHEME_NAME]
    F_DATA = active_scheme_data.get("fertilizer_data")
    EC_TARGET_VALUES = active_scheme_data.get("ec_values")

    if F_DATA is None or EC_TARGET_VALUES is None:
        messagebox.showerror("Fehler", f"Daten für Schema '{ACTIVE_SCHEME_NAME}' sind unvollständig.")
        # Optional: Setze F_DATA und EC_TARGET_VALUES auf leere Dicts, um weitere Fehler zu vermeiden
        F_DATA = {}
        EC_TARGET_VALUES = {}
        # return # Frühzeitiger Ausstieg oder mit leeren Daten weitermachen?

    # Dünger-Checkboxes neu erstellen/aktualisieren
    # Zuerst alte Widgets entfernen, falls vorhanden
    for cb in checkboxes:
        cb.destroy()
    for lbl in result_labels:
        lbl.destroy()

    fertilizer_options = list(F_DATA.keys()) if F_DATA else []
    fertilizer_vars = []
    checkboxes = []
    result_labels = []

    for i, option_text in enumerate(fertilizer_options):
        var = tk.IntVar()
        fertilizer_vars.append(var)
        cmd = lambda opt=option_text, v=var: calculate(opt, v)
        checkbox = ttk.Checkbutton(fertilizer_frame, text=option_text, variable=var, command=cmd)
        checkbox.grid(row=i, column=0, padx=5, pady=2, sticky="w")
        checkboxes.append(checkbox)
        result_label = ttk.Label(fertilizer_frame, text="", width=10, anchor="e")
        result_label.grid(row=i, column=1, padx=5, pady=2, sticky="e")
        result_labels.append(result_label)

    if active_scheme_label:
        active_scheme_label.config(text=f"Aktives Schema: {ACTIVE_SCHEME_NAME}")

    update_week() # Aktualisiert Berechnungen und EC-Werte basierend auf dem neuen Schema


def open_scheme_manager_window():
    """
    Öffnet das Fenster zur Verwaltung von Düngeschemata.
    """
    scheme_window = tk.Toplevel(window)
    scheme_window.title("Düngeschemata Verwalten")
    scheme_window.transient(window)
    scheme_window.grab_set()
    scheme_window.resizable(True, True)
    scheme_window.minsize(700, 450)

    # --- Helper: Parse Fertilizer Display Name ---
    def parse_fertilizer_display_name(display_name: str) -> str:
        if "(EC:" in display_name and display_name.endswith(")"):
            return display_name.split(" (EC:")[0].strip()
        print(f"Warnung: Konnte Düngernamen nicht aus '{display_name}' extrahieren.")
        return display_name # Fallback, though should not happen with consistent listbox population

    paned_window = ttk.PanedWindow(scheme_window, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    schemes_frame_container = ttk.Frame(paned_window, width=250)
    paned_window.add(schemes_frame_container, weight=1)
    ttk.Label(schemes_frame_container, text="Verfügbare Schemata:").pack(anchor="w", padx=5, pady=(0,5))
    scheme_listbox_frame = ttk.Frame(schemes_frame_container)
    scheme_listbox_frame.pack(fill=tk.BOTH, expand=True)
    scheme_listbox = tk.Listbox(scheme_listbox_frame, exportselection=False)
    scheme_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scheme_scrollbar = ttk.Scrollbar(scheme_listbox_frame, orient=tk.VERTICAL, command=scheme_listbox.yview)
    scheme_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    scheme_listbox.config(yscrollcommand=scheme_scrollbar.set)

    fertilizers_frame_container = ttk.Frame(paned_window)
    paned_window.add(fertilizers_frame_container, weight=2)
    ttk.Label(fertilizers_frame_container, text="Dünger im ausgewählten Schema:").pack(anchor="w", padx=5, pady=(0,5))
    fertilizer_listbox_frame = ttk.Frame(fertilizers_frame_container)
    fertilizer_listbox_frame.pack(fill=tk.BOTH, expand=True)
    fertilizer_listbox = tk.Listbox(fertilizer_listbox_frame, exportselection=False)
    fertilizer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    fertilizer_scrollbar = ttk.Scrollbar(fertilizer_listbox_frame, orient=tk.VERTICAL, command=fertilizer_listbox.yview)
    fertilizer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    fertilizer_listbox.config(yscrollcommand=fertilizer_scrollbar.set)

    # --- Populating and Refreshing Lists ---
    def refresh_fertilizer_list_for_selected_scheme():
        selected_indices = scheme_listbox.curselection()
        if selected_indices:
            s_name = scheme_listbox.get(selected_indices[0])
            populate_fertilizer_listbox(s_name)
        else:
            populate_fertilizer_listbox(None) # Clear if no scheme selected

    scheme_window.refresh_fertilizer_list_for_selected_scheme = refresh_fertilizer_list_for_selected_scheme

    def populate_fertilizer_listbox(selected_scheme_name: Optional[str] = None):
        fertilizer_listbox.delete(0, tk.END)
        if selected_scheme_name and ALL_SCHEMES and selected_scheme_name in ALL_SCHEMES:
            scheme_fertilizer_data = ALL_SCHEMES[selected_scheme_name].get("fertilizer_data", {})
            for f_name, f_details in sorted(scheme_fertilizer_data.items()): # Sort for consistent order
                ec_factor = f_details.get("ec_contribution_factor", "N/A")
                fertilizer_listbox.insert(tk.END, f"{f_name} (EC: {ec_factor})")

    def on_scheme_select(event=None): # event can be None if called manually
        refresh_fertilizer_list_for_selected_scheme()

    scheme_listbox.bind("<<ListboxSelect>>", on_scheme_select)

    def populate_scheme_listbox():
        # ... (keep existing populate_scheme_listbox logic, ensure it calls on_scheme_select at the end if needed)
        current_selection_index = scheme_listbox.curselection()
        scheme_listbox.delete(0, tk.END)
        if ALL_SCHEMES:
            for i, scheme_name_key in enumerate(sorted(ALL_SCHEMES.keys())): # Sort for consistent order
                scheme_listbox.insert(tk.END, scheme_name_key)
                if scheme_name_key == ACTIVE_SCHEME_NAME:
                    scheme_listbox.itemconfig(tk.END, {'bg':'lightblue'})

        restored_selection = False
        if current_selection_index:
            try:
                # Try to restore based on index, but if list changed, this might be wrong
                # A better way would be to store and restore by name if possible
                scheme_listbox.selection_set(current_selection_index[0])
                scheme_listbox.activate(current_selection_index[0])
                scheme_listbox.see(current_selection_index[0])
                restored_selection = True
            except tk.TclError:
                 pass # Index out of bounds

        if not restored_selection and ACTIVE_SCHEME_NAME and ALL_SCHEMES:
             try:
                idx = list(sorted(ALL_SCHEMES.keys())).index(ACTIVE_SCHEME_NAME)
                scheme_listbox.selection_set(idx)
                scheme_listbox.activate(idx)
                scheme_listbox.see(idx)
             except (ValueError, tk.TclError):
                 pass

        on_scheme_select() # Populate fertilizer list for current selection

    populate_scheme_listbox()

    # --- Scheme Action Buttons ---
    scheme_button_frame = ttk.Frame(schemes_frame_container)
    scheme_button_frame.pack(fill=tk.X, pady=(5,0))
    # ... (keep existing set_active_scheme, create_new_scheme, delete_selected_scheme, rename_selected_scheme functions) ...
    def set_active_scheme():
        global ACTIVE_SCHEME_NAME
        selected_indices = scheme_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie ein Schema aus der Liste aus.", parent=scheme_window)
            return
        selected_scheme_name = scheme_listbox.get(selected_indices[0])
        if selected_scheme_name == ACTIVE_SCHEME_NAME:
            messagebox.showinfo("Information", f"Schema '{selected_scheme_name}' ist bereits aktiv.", parent=scheme_window)
            return
        ACTIVE_SCHEME_NAME = selected_scheme_name
        if save_config_to_json():
            update_main_ui_for_active_scheme()
            populate_scheme_listbox()
            messagebox.showinfo("Erfolg", f"Schema '{selected_scheme_name}' wurde als aktiv gesetzt.", parent=scheme_window)

    set_active_button = ttk.Button(scheme_button_frame, text="Als Aktiv", command=set_active_scheme)
    set_active_button.pack(side=tk.LEFT, padx=2)

    def create_new_scheme():
        global ALL_SCHEMES
        if ALL_SCHEMES is None: return
        new_scheme_name = simpledialog.askstring("Neues Schema", "Name für das neue Schema:", parent=scheme_window)
        if not new_scheme_name: return
        if new_scheme_name in ALL_SCHEMES:
            messagebox.showerror("Fehler", f"Schema '{new_scheme_name}' existiert bereits.", parent=scheme_window)
            return
        source_scheme_name = None
        selected_indices = scheme_listbox.curselection()
        if selected_indices: source_scheme_name = scheme_listbox.get(selected_indices[0])
        elif "Default Scheme" in ALL_SCHEMES: source_scheme_name = "Default Scheme"
        if source_scheme_name and source_scheme_name in ALL_SCHEMES:
            ALL_SCHEMES[new_scheme_name] = copy.deepcopy(ALL_SCHEMES[source_scheme_name])
        else:
            ALL_SCHEMES[new_scheme_name] = {"fertilizer_data": {}, "ec_values": {}}
        if save_config_to_json():
            populate_scheme_listbox()
            messagebox.showinfo("Erfolg", f"Schema '{new_scheme_name}' erstellt.", parent=scheme_window)
        else: del ALL_SCHEMES[new_scheme_name]

    create_scheme_button = ttk.Button(scheme_button_frame, text="Neu", command=create_new_scheme)
    create_scheme_button.pack(side=tk.LEFT, padx=2)

    def delete_selected_scheme():
        global ALL_SCHEMES, ACTIVE_SCHEME_NAME
        if ALL_SCHEMES is None: return
        selected_indices = scheme_listbox.curselection()
        if not selected_indices: return
        scheme_to_delete = scheme_listbox.get(selected_indices[0])
        if len(ALL_SCHEMES) <= 1:
            messagebox.showerror("Fehler", "Letztes Schema kann nicht gelöscht werden.", parent=scheme_window)
            return
        if not messagebox.askyesno("Bestätigen", f"Schema '{scheme_to_delete}' wirklich löschen?", parent=scheme_window):
            return

        original_scheme_data_backup = copy.deepcopy(ALL_SCHEMES[scheme_to_delete]) # Backup for potential rollback
        original_active_scheme_name_backup = ACTIVE_SCHEME_NAME

        del ALL_SCHEMES[scheme_to_delete]
        active_scheme_changed = False
        if scheme_to_delete == ACTIVE_SCHEME_NAME:
            ACTIVE_SCHEME_NAME = list(ALL_SCHEMES.keys())[0]
            active_scheme_changed = True
        if save_config_to_json():
            populate_scheme_listbox()
            if active_scheme_changed: update_main_ui_for_active_scheme()
            messagebox.showinfo("Erfolg", f"Schema '{scheme_to_delete}' gelöscht.", parent=scheme_window)
        else: # Rollback if save failed
            ALL_SCHEMES[scheme_to_delete] = original_scheme_data_backup
            ACTIVE_SCHEME_NAME = original_active_scheme_name_backup
            messagebox.showerror("Fehler", "Löschen fehlgeschlagen, Speichern nicht möglich.", parent=scheme_window)
            populate_scheme_listbox() # Refresh to show rolled-back state


    delete_scheme_button = ttk.Button(scheme_button_frame, text="Löschen", command=delete_selected_scheme)
    delete_scheme_button.pack(side=tk.LEFT, padx=2)

    def rename_selected_scheme():
        global ALL_SCHEMES, ACTIVE_SCHEME_NAME
        if ALL_SCHEMES is None: return
        selected_indices = scheme_listbox.curselection()
        if not selected_indices: return
        old_name = scheme_listbox.get(selected_indices[0])
        new_name = simpledialog.askstring("Schema Umbenennen", f"Neuer Name für '{old_name}':", initialvalue=old_name, parent=scheme_window)
        if not new_name or new_name == old_name: return
        if new_name in ALL_SCHEMES:
            messagebox.showerror("Fehler", f"Schema '{new_name}' existiert bereits.", parent=scheme_window)
            return

        ALL_SCHEMES[new_name] = ALL_SCHEMES.pop(old_name)
        active_renamed = False
        if old_name == ACTIVE_SCHEME_NAME:
            ACTIVE_SCHEME_NAME = new_name
            active_renamed = True
        if save_config_to_json():
            populate_scheme_listbox()
            if active_renamed: update_main_ui_for_active_scheme()
            messagebox.showinfo("Erfolg", f"Schema '{old_name}' zu '{new_name}' umbenannt.", parent=scheme_window)
        else: # Rollback
            ALL_SCHEMES[old_name] = ALL_SCHEMES.pop(new_name)
            if active_renamed: ACTIVE_SCHEME_NAME = old_name
            messagebox.showerror("Fehler", "Umbenennen fehlgeschlagen, Speichern nicht möglich.", parent=scheme_window)
            populate_scheme_listbox()

    rename_scheme_button = ttk.Button(scheme_button_frame, text="Umbenennen", command=rename_selected_scheme)
    rename_scheme_button.pack(side=tk.LEFT, padx=2)

    # --- Fertilizer Action Buttons ---
    fertilizer_button_frame = ttk.Frame(fertilizers_frame_container)
    fertilizer_button_frame.pack(fill=tk.X, pady=(5,0))

    def call_add_fertilizer_dialog():
        selected_scheme_indices = scheme_listbox.curselection()
        if not selected_scheme_indices:
            messagebox.showwarning("Keine Schema-Auswahl", "Bitte zuerst ein Schema auswählen.", parent=scheme_window)
            return
        current_scheme_name = scheme_listbox.get(selected_scheme_indices[0])
        open_fertilizer_dialog(scheme_window, current_scheme_name, existing_fertilizer_name=None)

    def call_edit_fertilizer_dialog():
        selected_scheme_indices = scheme_listbox.curselection()
        if not selected_scheme_indices:
            messagebox.showwarning("Keine Schema-Auswahl", "Bitte zuerst ein Schema auswählen.", parent=scheme_window)
            return
        current_scheme_name = scheme_listbox.get(selected_scheme_indices[0])

        selected_fertilizer_indices = fertilizer_listbox.curselection()
        if not selected_fertilizer_indices:
            messagebox.showwarning("Keine Dünger-Auswahl", "Bitte einen Dünger zum Bearbeiten auswählen.", parent=scheme_window)
            return

        display_name = fertilizer_listbox.get(selected_fertilizer_indices[0])
        actual_fertilizer_name = parse_fertilizer_display_name(display_name)

        if not actual_fertilizer_name or not ALL_SCHEMES or current_scheme_name not in ALL_SCHEMES or \
           actual_fertilizer_name not in ALL_SCHEMES[current_scheme_name]["fertilizer_data"]:
            messagebox.showerror("Fehler", f"Dünger '{actual_fertilizer_name}' nicht in Schema '{current_scheme_name}' gefunden.", parent=scheme_window)
            refresh_fertilizer_list_for_selected_scheme()
            return
        open_fertilizer_dialog(scheme_window, current_scheme_name, existing_fertilizer_name=actual_fertilizer_name)

    def delete_selected_fertilizer():
        selected_scheme_indices = scheme_listbox.curselection()
        if not selected_scheme_indices:
            messagebox.showwarning("Keine Schema-Auswahl", "Bitte zuerst ein Schema auswählen.", parent=scheme_window)
            return
        current_scheme_name = scheme_listbox.get(selected_scheme_indices[0])

        selected_fertilizer_indices = fertilizer_listbox.curselection()
        if not selected_fertilizer_indices:
            messagebox.showwarning("Keine Dünger-Auswahl", "Bitte einen Dünger zum Löschen auswählen.", parent=scheme_window)
            return

        display_name = fertilizer_listbox.get(selected_fertilizer_indices[0])
        actual_fertilizer_name = parse_fertilizer_display_name(display_name)

        if not messagebox.askyesno("Bestätigen", f"Dünger '{actual_fertilizer_name}' aus Schema '{current_scheme_name}' wirklich löschen?", parent=scheme_window):
            return

        if ALL_SCHEMES and current_scheme_name in ALL_SCHEMES and \
           "fertilizer_data" in ALL_SCHEMES[current_scheme_name] and \
           actual_fertilizer_name in ALL_SCHEMES[current_scheme_name]["fertilizer_data"]:

            # Backup for potential rollback if save fails
            original_fertilizer_scheme_data_backup = copy.deepcopy(ALL_SCHEMES[current_scheme_name]["fertilizer_data"])

            del ALL_SCHEMES[current_scheme_name]["fertilizer_data"][actual_fertilizer_name]

            if save_config_to_json():
                messagebox.showinfo("Erfolg", f"Dünger '{actual_fertilizer_name}' gelöscht.", parent=scheme_window)
                refresh_fertilizer_list_for_selected_scheme()
                if ACTIVE_SCHEME_NAME == current_scheme_name:
                    update_main_ui_for_active_scheme()
            else:
                ALL_SCHEMES[current_scheme_name]["fertilizer_data"] = original_fertilizer_scheme_data_backup # Rollback
                messagebox.showerror("Speicherfehler", "Löschen fehlgeschlagen, Speichern nicht möglich. Änderungen zurückgerollt.", parent=scheme_window)
                refresh_fertilizer_list_for_selected_scheme()
        else:
            messagebox.showerror("Fehler", f"Konnte Dünger '{actual_fertilizer_name}' nicht finden.", parent=scheme_window)
            refresh_fertilizer_list_for_selected_scheme()

    add_fert_button = ttk.Button(fertilizer_button_frame, text="Hinzufügen", command=call_add_fertilizer_dialog)
    add_fert_button.pack(side=tk.LEFT, padx=2)
    edit_fert_button = ttk.Button(fertilizer_button_frame, text="Bearbeiten", command=call_edit_fertilizer_dialog)
    edit_fert_button.pack(side=tk.LEFT, padx=2)
    delete_fert_button = ttk.Button(fertilizer_button_frame, text="Löschen", command=delete_selected_fertilizer)
    delete_fert_button.pack(side=tk.LEFT, padx=2)

    # Overall Close Button
    overall_close_button_frame = ttk.Frame(scheme_window)
    overall_close_button_frame.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
    close_button = ttk.Button(overall_close_button_frame, text="Schließen", command=scheme_window.destroy)
    close_button.pack(side=tk.RIGHT)

    on_scheme_select() # Populate fertilizer list for current selection

    scheme_window.wait_window()

# --- Helper functions for parsing/formatting fertilizer schedule strings ---
def parse_schedule_string(schedule_str: str) -> Optional[Dict[int, float]]:
    """
    Parses a schedule string like "1:0.5, 2:1.0, 10:1.2" into {1: 0.5, 2: 1.0, 10: 1.2}.
    Returns None if parsing fails due to format errors.
    """
    schedule_dict: Dict[int, float] = {}
    if not schedule_str.strip(): # Handle empty string as valid (empty schedule)
        return schedule_dict

    parts = schedule_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue # Skip empty parts if there are trailing commas etc.
        try:
            week_str, dosage_str = part.split(':')
            week = int(week_str.strip())
            dosage = float(dosage_str.strip())
            if week <= 0: # Weeks should be positive
                raise ValueError("Wochennummer muss positiv sein.")
            schedule_dict[week] = dosage
        except ValueError as e:
            messagebox.showerror("Formatfehler im Schema", f"Ungültiger Eintrag im Schema: '{part}'.\nFehler: {e}\nErwartetes Format: 'Woche:Dosierung', z.B. '1:0.5, 2:1.0'.")
            return None
    return schedule_dict

def format_schedule_dict(schedule_dict: Dict[int, float]) -> str:
    """
    Formats a schedule dictionary like {1: 0.5, 2: 1.0} into "1:0.5, 2:1.0".
    """
    if not schedule_dict:
        return ""
    # Sort by week number for consistent output
    return ", ".join(f"{week}:{dosage}" for week, dosage in sorted(schedule_dict.items()))

# --- Fertilizer Add/Edit Dialog ---
def open_fertilizer_dialog(parent_window: tk.Toplevel, current_scheme_name: str, existing_fertilizer_name: Optional[str] = None):
    """
    Opens a dialog to add or edit a fertilizer for the given scheme.
    If existing_fertilizer_name is provided, it's an edit operation.
    """
    is_edit_mode = existing_fertilizer_name is not None
    title = "Dünger Bearbeiten" if is_edit_mode else "Neuen Dünger Hinzufügen"

    dialog = tk.Toplevel(parent_window)
    dialog.title(title)
    dialog.transient(parent_window)
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.minsize(400, 300)

    fertilizer_data_to_edit = {}
    original_name_for_edit = existing_fertilizer_name

    if is_edit_mode and ALL_SCHEMES and current_scheme_name in ALL_SCHEMES and \
       existing_fertilizer_name and existing_fertilizer_name in ALL_SCHEMES[current_scheme_name]["fertilizer_data"]:
        fertilizer_data_to_edit = ALL_SCHEMES[current_scheme_name]["fertilizer_data"][existing_fertilizer_name]

    # --- Widgets ---
    main_frame = ttk.Frame(dialog, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Düngername:").grid(row=0, column=0, sticky="w", pady=2)
    name_var = tk.StringVar(value=existing_fertilizer_name if is_edit_mode else "")
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=40)
    name_entry.grid(row=0, column=1, sticky="ew", pady=2)

    ttk.Label(main_frame, text="EC Beitrag (µS/cm pro ml/L):").grid(row=1, column=0, sticky="w", pady=2)
    ec_var = tk.StringVar(value=str(fertilizer_data_to_edit.get("ec_contribution_factor", "0.0")))
    ec_entry = ttk.Entry(main_frame, textvariable=ec_var, width=10)
    ec_entry.grid(row=1, column=1, sticky="w", pady=2)

    ttk.Label(main_frame, text="Düngeschema (Woche:Dosierung, ...):").grid(row=2, column=0, sticky="nw", pady=2)
    schedule_text = scrolledtext.ScrolledText(main_frame, height=10, width=50, wrap=tk.WORD)
    schedule_text.grid(row=2, column=1, sticky="ew", pady=2)
    schedule_text.insert("1.0", format_schedule_dict(fertilizer_data_to_edit.get("schedule", {})))

    main_frame.columnconfigure(1, weight=1) # Allow text widget to expand

    # --- Save/Cancel Buttons ---
    button_dialog_frame = ttk.Frame(main_frame)
    button_dialog_frame.grid(row=3, column=0, columnspan=2, pady=(10,0), sticky="e")

    def on_save():
        new_name = name_var.get().strip()
        ec_factor_str = ec_var.get().strip()
        schedule_str = schedule_text.get("1.0", tk.END).strip()

        if not new_name:
            messagebox.showerror("Fehler", "Düngername darf nicht leer sein.", parent=dialog)
            return

        try:
            ec_factor = float(ec_factor_str)
        except ValueError:
            messagebox.showerror("Fehler", "EC Beitrag muss eine gültige Zahl sein.", parent=dialog)
            return

        parsed_schedule = parse_schedule_string(schedule_str)
        if parsed_schedule is None: # Error already shown by parse_schedule_string
            return

        # Check for duplicate name (only if name changed or in add mode)
        if new_name != original_name_for_edit and new_name in ALL_SCHEMES[current_scheme_name]["fertilizer_data"]:
            messagebox.showerror("Fehler", f"Ein Dünger mit dem Namen '{new_name}' existiert bereits in diesem Schema.", parent=dialog)
            return

        updated_fertilizer_data = {
            "schedule": parsed_schedule,
            "ec_contribution_factor": ec_factor
        }

        # Update ALL_SCHEMES
        if is_edit_mode and original_name_for_edit and original_name_for_edit != new_name:
            # Name changed, remove old entry
            del ALL_SCHEMES[current_scheme_name]["fertilizer_data"][original_name_for_edit]

        ALL_SCHEMES[current_scheme_name]["fertilizer_data"][new_name] = updated_fertilizer_data

        if save_config_to_json():
            messagebox.showinfo("Erfolg", f"Dünger '{new_name}' gespeichert.", parent=dialog)
            # Refresh fertilizer list in the scheme manager window (passed as parent_window)
            # This requires access to scheme_listbox and fertilizer_listbox from parent.
            # A bit of a hack, ideally use a callback or make populate_fertilizer_listbox more accessible.
            # For now, let's assume parent_window is the scheme_manager_window.

            # Find the fertilizer_listbox in the parent (scheme_manager) window
            # This is not ideal, direct reference or callback would be better.
            # Assuming scheme_listbox is accessible via parent_window.scheme_listbox_ref or similar if set.
            # For now, we re-populate based on current selection in scheme_listbox.

            # Find the scheme_listbox (which is a child of parent_window's child frames)
            # This is getting complex. Let's assume a refresh function on parent_window if possible,
            # or pass the listbox reference.
            # For now, just call populate_fertilizer_listbox directly assuming it's in scope.
            # This will only work if open_fertilizer_dialog is defined *inside* open_scheme_manager_window
            # or if scheme_listbox & fertilizer_listbox are made more globally accessible (not great).

            # Correct way: call a refresh method on the parent window or pass references.
            # Let's try to find the listbox:
            schemes_lb = None
            fertilizer_lb = None
            # This is a simplified search, real UI might be more nested.
            for child_widget in parent_window.winfo_children():
                 if isinstance(child_widget, ttk.PanedWindow): # The PanedWindow
                     for pane_child in child_widget.winfo_children(): # schemes_frame, fertilizers_frame
                         for sub_child in pane_child.winfo_children(): # e.g. fertilizer_listbox_frame
                             if isinstance(sub_child, ttk.Frame):
                                 for f_lb_candidate in sub_child.winfo_children():
                                     if isinstance(f_lb_candidate, tk.Listbox) and f_lb_candidate.master is sub_child:
                                         # This is heuristic, need a better way
                                         # Assuming the *second* listbox found this way is fertilizer_listbox
                                         if schemes_lb is None: # First one is likely schemes_lb
                                             schemes_lb = f_lb_candidate
                                         else:
                                             fertilizer_lb = f_lb_candidate
                                             break
                                 if fertilizer_lb: break
                         if fertilizer_lb: break
                     if fertilizer_lb: break

            if fertilizer_lb and schemes_lb:
                 selected_scheme_indices = schemes_lb.curselection()
                 if selected_scheme_indices:
                     s_name = schemes_lb.get(selected_scheme_indices[0])
                     # Manually call populate_fertilizer_listbox with the correct name and listbox
                     # This is still not ideal as populate_fertilizer_listbox is not designed for this
                     # We need a dedicated refresh function for the fertilizer list in scheme manager.
                     # For now, let's assume the parent can refresh itself.
                     # The original `populate_fertilizer_listbox` is defined within `open_scheme_manager_window`
                     # and is not directly callable here.
                     # This will require refactoring `populate_fertilizer_listbox`
                     # or adding a specific refresh method to scheme_manager.

                     # Let's try to find the scheme_listbox from parent_window and call its on_select manually
                     # This is also not ideal, but might work for now
                     # Assume scheme_listbox is named 'scheme_listbox_ref' on parent_window
                     if hasattr(parent_window, 'refresh_fertilizer_list_for_selected_scheme'):
                         parent_window.refresh_fertilizer_list_for_selected_scheme()


            if ACTIVE_SCHEME_NAME == current_scheme_name:
                update_main_ui_for_active_scheme()
            dialog.destroy()
        else:
            # Save failed, error message already shown by save_config_to_json
            # Potentially roll back changes in ALL_SCHEMES if needed (complex)
            pass

    save_button = ttk.Button(button_dialog_frame, text="Speichern", command=on_save)
    save_button.pack(side=tk.LEFT, padx=5)
    cancel_button = ttk.Button(button_dialog_frame, text="Abbrechen", command=dialog.destroy)
    cancel_button.pack(side=tk.LEFT, padx=5)

    name_entry.focus_set()
    dialog.wait_window()


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

            selected_fertilizer_name = fertilizer_ec_combo.get()
            if not selected_fertilizer_name:
                raise ValueError("Bitte einen Dünger auswählen.")

            if F_DATA is None or selected_fertilizer_name not in F_DATA or \
               "ec_contribution_factor" not in F_DATA[selected_fertilizer_name]:
                raise ValueError(f"EC Faktor für '{selected_fertilizer_name}' nicht gefunden.")

            ec_factor = F_DATA[selected_fertilizer_name]["ec_contribution_factor"]
            if not isinstance(ec_factor, (int, float)) or ec_factor <= 0:
                raise ValueError(f"Ungültiger EC Faktor ({ec_factor}) für '{selected_fertilizer_name}'.")

            benoetigte_menge = berechne_menge_fuer_ec_anpassung(ec_ist, ec_soll, wassermenge, ec_factor)

            final_ergebnis_text = (
                f"Um {ec_soll:.0f} µS/cm mit '{selected_fertilizer_name}' zu erreichen:\n\n"
                f"-> Benötigte Menge: {benoetigte_menge:.2f} ml\n"
                f"(EC-Faktor: {ec_factor:.0f}, berechnet für {wassermenge:.2f} L Wasser)"
            )
            ergebnis_label.config(text=final_ergebnis_text, foreground="black")

            # Timestamp speichern und Label aktualisieren
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_to_save = {"last_ec_helper_usage": current_timestamp}
            save_app_status(status_to_save)
            if last_used_label: # Check if label exists
                last_used_label.config(text=f"EC Helper last used: {current_timestamp}")

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

    ec_soll_entry = ttk.Entry(ec_soll_frame, width=15, state="disabled")
    ec_soll_entry.grid(row=0, column=1, sticky="ew")

    ttk.Label(ec_window, text="Dünger auswählen:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    fertilizer_ec_combo_var = tk.StringVar()
    fertilizer_ec_combo = ttk.Combobox(ec_window, textvariable=fertilizer_ec_combo_var, state="readonly", width=30)

    fertilizer_names = list(F_DATA.keys()) if F_DATA else []
    fertilizer_ec_combo['values'] = fertilizer_names
    if fertilizer_names:
        fertilizer_ec_combo.set(fertilizer_names[0])
    fertilizer_ec_combo.grid(row=3, column=1, padx=10, pady=5, sticky="ew")


    # Button zum Starten der Berechnung.
    berechnen_button = ttk.Button(ec_window, text="Düngermenge berechnen", command=duenger_berechnen)
    berechnen_button.grid(row=4, column=0, columnspan=2, pady=10)
    if not fertilizer_names: # Disable button if no fertilizers
        berechnen_button.config(state="disabled")


    # Label zur Anzeige der Ergebnisse oder Fehlermeldungen.
    ergebnis_label = ttk.Label(ec_window, text="Ergebnis der Berechnung wird hier angezeigt. Bitte alle Werte eingeben.", wraplength=350, justify=tk.LEFT)
    ergebnis_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    ec_ist_entry.focus_set()
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
plant_info_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
plant_info_frame.columnconfigure(1, weight=1)

# Pflanzenauswahl (Dropdown-Menü).
ttk.Label(plant_info_frame, text="Pflanze:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
plant_var = tk.StringVar()
plant_dropdown = ttk.Combobox(plant_info_frame, textvariable=plant_var, state="readonly")
plant_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
plant_dropdown.bind("<<ComboboxSelected>>", update_week)

# Anzeige des EC-Zielwerts (Plan-EC).
ec_label = ttk.Label(plant_info_frame, text="Plan-EC (Erde): -", font=('TkDefaultFont', 9, 'bold'))
ec_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

# Anzeige der Genetik.
ttk.Label(plant_info_frame, text="Genetik:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
genetics_entry = ttk.Entry(plant_info_frame, state="readonly")
genetics_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

# Anzeige und Eingabe der Wachstumswoche.
ttk.Label(plant_info_frame, text="Woche seit Keimung:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
week_entry = ttk.Entry(plant_info_frame, width=10)
week_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w") # sticky "w" to align left
week_entry.bind("<Return>", lambda event: calculate())

# Anzeige des Keimdatums.
ttk.Label(plant_info_frame, text="Keimdatum:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
germination_date_entry = ttk.Entry(plant_info_frame, state="readonly", width=12)
germination_date_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w") # sticky "w"

# Label für aktuelles Schema
active_scheme_label = ttk.Label(plant_info_frame, text="Aktives Schema: -", font=('TkDefaultFont', 9, 'italic'))
active_scheme_label.grid(row=3, column=0, columnspan=4, padx=5, pady=(5,10), sticky="w")


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

# Label für den letzten EC-Helper Aufruf
last_used_label: Optional[ttk.Label] = None # Declare as global for access in ec_berechnen

# Frame für Düngerauswahl und Anzeige der Ergebnisse.
fertilizer_frame = ttk.LabelFrame(window, text="Düngerauswahl & Ergebnisse (ml pro angegebene Wassermenge)")
fertilizer_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="nsew") # nsew = alle Richtungen (dehnt sich aus)
fertilizer_frame.columnconfigure(0, weight=1) # Spalte für Checkbox-Texte dehnt sich aus.
fertilizer_frame.columnconfigure(1, minsize=80) # Mindestbreite für Ergebnis-Labels.
window.rowconfigure(2, weight=1) # Zeile 2 im Hauptfenster (dieser Frame) dehnt sich vertikal aus.

# Düngeroptionen - Diese Liste wird nun NACH der Konfigurationsinitialisierung gefüllt.
fertilizer_options: list[str] = [] # Platzhalter, wird später gefüllt

# Listen zur Speicherung der Tkinter-Variablen für Checkboxen und der Ergebnis-Labels.
fertilizer_vars: list[tk.IntVar] = []
checkboxes: list[ttk.Checkbutton] = []
result_labels: list[ttk.Label] = []

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
action_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="e")

manage_schemes_button = ttk.Button(action_frame, text="Manage Schemes", command=open_scheme_manager_window)
manage_schemes_button.pack(side=tk.LEFT, padx=5)

neue_pflanze_button = ttk.Button(action_frame, text="Neue Pflanze anlegen", command=neue_pflanze_hinzufuegen)
neue_pflanze_button.pack(side=tk.LEFT, padx=5)

loeschen_button = ttk.Button(action_frame, text="Pflanze löschen", command=pflanze_loeschen)
loeschen_button.pack(side=tk.LEFT, padx=5)


# --- Initialisierung der Anwendung ---
# 1. Lade Konfiguration. Bei Fehler wird Anwendung beendet.
if initialize_config_and_exit_on_error(window):
    # Globale Konfigurationsvariablen sind jetzt gesetzt (ALL_SCHEMES, ACTIVE_SCHEME_NAME, F_DATA, etc.)
    # last_used_label is already global due to its definition outside any function.

    # 2. Haupt-UI basierend auf dem aktiven Schema initialisieren
    # Dies beinhaltet das Setzen von F_DATA, EC_TARGET_VALUES, Düngeroptionen, Checkboxes, etc.
    update_main_ui_for_active_scheme() # Ruft auch update_week() intern auf.
                                     # Stellt sicher, dass active_scheme_label Text bekommt.

    # Erstelle das Label für den Zeitstempel im calc_input_frame
    # Needs to be after calc_input_frame is defined, but before mainloop
    # Position it below the water amount entry or EC-Helper button
    # Let's try to place it in a new row within calc_input_frame or a separate status bar frame
    # For simplicity, adding to calc_input_frame for now.
    last_used_label = ttk.Label(calc_input_frame, text="EC Helper last used: Not yet")
    last_used_label.grid(row=1, column=0, columnspan=3, padx=5, pady=(5,0), sticky="w")


    # Lade und zeige den letzten EC-Helper Zeitstempel an
    app_status = load_app_status()
    last_ec_timestamp = app_status.get("last_ec_helper_usage")
    if last_ec_timestamp:
        last_used_label.config(text=f"EC Helper last used: {last_ec_timestamp}")

    # 3. Lade Pflanzendaten aus CSV.
    plant_data = read_plant_data()
    # 4. Fülle das Dropdown-Menü mit Pflanzennamen.
    plant_dropdown['values'] = list(plant_data.keys())
    # 5. Wähle ggf. die erste Pflanze aus und aktualisiere die GUI.
    if plant_data:
        plant_var.set(list(plant_data.keys())[0])
        # update_week() wird bereits durch update_main_ui_for_active_scheme aufgerufen,
        # aber wenn keine Pflanze ausgewählt ist, müssen die Felder ggf. initial geleert werden.
        # Wenn eine Pflanze ausgewählt wird, triggert das sowieso update_week.
        # Ein expliziter Aufruf hier ist sicher, um den Zustand nach Pflanzenauswahl zu setzen.
        update_week()
    else:
        # Stellt sicher, dass die pflanzenspezifischen Felder leer sind, wenn keine Pflanzen vorhanden sind.
        update_week()

    # 6. Starte die Tkinter Hauptschleife.
    window.mainloop()
# Wenn initialize_config_and_exit_on_error() False zurückgibt,
# wurde window.destroy() bereits aufgerufen und die mainloop wird nicht gestartet (oder sys.exit wurde aufgerufen).