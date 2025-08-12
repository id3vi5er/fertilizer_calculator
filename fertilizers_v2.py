import tkinter as tk
from tkinter import ttk  # Import themed widgets
import tkinter.messagebox as messagebox
import tkinter.scrolledtext as scrolledtext # For scrolled text area
import csv
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional # For type hinting

# --- Konstanten ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(SCRIPT_DIR, 'pflanzendaten.csv')
CSV_HEADER = ["Pflanzenname", "Keimdatum", "Genetik", "Infos"]
EC_FACTOR_WACHSTUM = 478 # EC increase in µS/cm per ml/L for Wachstumsdünger
EC_FACTOR_BLUETE = 430   # EC increase in µS/cm per ml/L for Blütendünger

# --- Datenmanagement ---

def read_plant_data() -> Dict[str, Dict[str, Any]]:
    """
    Liest die Pflanzendaten aus der CSV-Datei ein.
    Erstellt die Datei mit Kopfzeile, falls sie nicht existiert.

    Returns:
        Ein Dictionary mit Pflanzennamen als Schlüssel und einem Dictionary
        mit "Keimdatum" (datetime object), "Genetik" und "Infos" als Werte.
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
    Speichert das übergebene Pflanzendaten-Dictionary in die CSV-Datei.
    Überschreibt die vorhandene Datei.
    """
    try:
        with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_HEADER)
            for plant_name, data in data_to_save.items():
                keimdatum_obj = data.get("Keimdatum")
                if isinstance(keimdatum_obj, datetime):
                    date_str = keimdatum_obj.strftime('%d.%m.%Y')
                    writer.writerow([
                        plant_name,
                        date_str,
                        data.get("Genetik", ""),
                        data.get("Infos", "")
                    ])
                else:
                    print(f"Warnung: Ungültiges oder fehlendes Keimdatum-Objekt für '{plant_name}' beim Speichern. Überspringe.")
    except IOError as e:
         messagebox.showerror("Speicherfehler", f"Fehler beim Schreiben der CSV-Datei '{CSV_FILENAME}':\n{e}")
    except Exception as e:
         messagebox.showerror("Unerwarteter Speicherfehler", f"Ein Fehler ist beim Speichern der Pflanzendaten aufgetreten:\n{e}")

# --- Düngeberechnungen ---

def calculate_fertilizer_amount(week: int, water_amount: float, fertilizer_type: str) -> Optional[float]:
    """
    Berechnet die Düngemenge für eine bestimmte Woche und Wassermenge.

    Args:
        week: Die aktuelle Woche seit Keimung (int).
        water_amount: Die Menge an Wasser in Litern (float).
        fertilizer_type: Die Art des Düngers (str).

    Returns:
        Die Düngemenge in Millilitern (float) oder None bei ungültigem Typ/Woche.
    """
    # Dosierungen pro Liter Wasser (ml/L) - Biobizz Schema
    fertilizer_data = {
        # Biobizz Hauptdünger
        "Bio-Grow": {1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 4, 9: 4, 10: 4, 11: 0, 12: 0},
        "Bio-Bloom": {1: 0, 2: 0, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4, 11: 0, 12: 0},
        "Top-Max": {1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 4, 9: 4, 10: 4, 11: 0, 12: 0},
        "Bio-Heaven": {1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 5, 11: 0, 12: 0},
        "Alg-A-Mic": {1: 0, 2: 0, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 4, 9: 4, 10: 4, 11: 0, 12: 0},
        "Acti-Vera": {1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 5, 11: 0, 12: 0},
        "Root-Juice": {1: 4, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0},
        # Fish-Mix als Alternative zu Bio-Grow in der Veg-Phase
        "Fish-Mix": {1: 2, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0},
        # CalMag Schedules
        "CalMag - Prevention (Biobizz)": {
            1: 0.3, 2: 0.3, 3: 0.3, 4: 0.3, 5: 0.3, 6: 0.5, 7: 0.5, 8: 0.8, 9: 0.8, 10: 0.8
        },
        "CalMag - Correction (Biobizz)": {
            1: 0.0, 2: 0.18, 3: 0.38, 4: 0.59, 5: 0.74, 6: 0.89, 7: 1.04, 8: 1.2,
            9: 1.43, 10: 1.66, 11: 1.89, 12: 2.12, 13: 2.35, 14: 2.58, 15: 2.81, 16: 3.04
        }
    }

    if fertilizer_type not in fertilizer_data:
        print(f"Warnung: Unbekannter Düngertyp '{fertilizer_type}'")
        return None

    # Wähle die maximale definierte Woche, wenn die aktuelle Woche darüber liegt
    max_defined_week = max(fertilizer_data[fertilizer_type].keys())
    effective_week = min(week, max_defined_week) if week > 0 else 1 # Mindestens Woche 1 verwenden, falls week <= 0

    dosage_per_liter = fertilizer_data[fertilizer_type].get(effective_week)

    if dosage_per_liter is None:
        # Sollte durch min/max nicht passieren, aber sicherheitshalber
        print(f"Warnung: Keine Dosierung für Woche {effective_week} bei '{fertilizer_type}' gefunden.")
        return 0.0 # Oder None? Hier 0.0 um Fehler zu vermeiden

    fertilizer_amount = dosage_per_liter * water_amount
    return fertilizer_amount

def get_ec_value(week: int) -> Optional[float]:
    """
    Gibt den Ziel-EC-Wert (in mS/cm) für die entsprechende Woche zurück.

    Args:
        week: Die aktuelle Woche seit Keimung (int).

    Returns:
        Den EC-Zielwert für Erde (in mS/cm) oder None, falls die Woche nicht definiert ist.
    """
    # EC-Werte in mS/cm (1 mS/cm = 1000 µS/cm)
    ec_values = {
        1: 0.4, 2: 0.6, 3: 0.7, 4: 0.9, 5: 1.0, 6: 1.2, 7: 1.4, 8: 1.5, 9: 1.6, 10: 1.6,
        11: 1.7, 12: 1.7, 13: 1.8, 14: 1.8, 15: 1.9, 16: 1.9, 17: 1.9, 18: 2.0, 19: 2.0, 20: 2.0
    }
    # Wähle die maximale definierte Woche, wenn die aktuelle Woche darüber liegt
    max_defined_week = max(ec_values.keys())
    effective_week = min(week, max_defined_week) if week > 0 else 1 # Mindestens Woche 1
    return ec_values.get(effective_week)

def berechne_wachstumduenger_menge_fuer_ec(EC_ist: float, EC_soll: float, wassermenge_liter: float) -> float:
    """Berechnet die benötigte Menge Wachstumsdünger in ml."""
    if EC_ist >= EC_soll:
        return 0.0
    benötigte_ec_zunahme = EC_soll - EC_ist
    # Menge in ml = (Gewünschte EC-Änderung / EC-Änderung pro ml/L) * Liter
    benötigte_menge_ml = (benötigte_ec_zunahme / EC_FACTOR_WACHSTUM) * wassermenge_liter
    return max(0.0, benötigte_menge_ml) # Sicherstellen, dass nicht negativ

def berechne_bluetenduenger_menge_fuer_ec(EC_ist: float, EC_soll: float, wassermenge_liter: float) -> float:
    """Berechnet die benötigte Menge Blütendünger in ml."""
    if EC_ist >= EC_soll:
        return 0.0
    benötigte_ec_zunahme = EC_soll - EC_ist
    # Menge in ml = (Gewünschte EC-Änderung / EC-Änderung pro ml/L) * Liter
    benötigte_menge_ml = (benötigte_ec_zunahme / EC_FACTOR_BLUETE) * wassermenge_liter
    return max(0.0, benötigte_menge_ml) # Sicherstellen, dass nicht negativ

# --- GUI Callbacks und Hilfsfunktionen ---

def update_week(event=None):
    """
    Aktualisiert die GUI-Felder (Woche, Keimdatum, Genetik, Infos, EC)
    basierend auf der ausgewählten Pflanze.
    """
    try:
        selected_plant = plant_var.get()
        if not selected_plant or selected_plant not in plant_data:
            # Keine oder ungültige Pflanze ausgewählt -> Felder leeren
            week_entry.delete(0, tk.END)
            germination_date_entry.config(state="normal")
            germination_date_entry.delete(0, tk.END)
            germination_date_entry.config(state="readonly")
            genetics_entry.config(state="normal")
            genetics_entry.delete(0, tk.END)
            genetics_entry.config(state="readonly")
            info_text.config(state="normal")
            info_text.delete("1.0", tk.END)
            info_text.config(state="disabled") # Deaktivieren, wenn keine Pflanze
            ec_label.config(text="EC-Ziel (Erde): -")
            for label in result_labels:
                label.config(text="")
            save_button.config(state="disabled") # Speichern-Button deaktivieren
            return

        # Pflanze ausgewählt -> Felder füllen
        plant_info = plant_data[selected_plant]
        germination_date = plant_info["Keimdatum"]
        today = datetime.today()

        delta_days = (today - germination_date).days
        current_week = max(1, (delta_days // 7 + 1)) # Mindestens Woche 1

        week_entry.delete(0, tk.END)
        week_entry.insert(0, str(current_week))

        germination_date_entry.config(state="normal")
        germination_date_entry.delete(0, tk.END)
        germination_date_entry.insert(0, germination_date.strftime('%d.%m.%Y'))
        germination_date_entry.config(state="readonly")

        genetics_entry.config(state="normal")
        genetics_entry.delete(0, tk.END)
        genetics_entry.insert(0, plant_info["Genetik"])
        genetics_entry.config(state="readonly")

        info_text.config(state="normal")
        info_text.delete("1.0", tk.END)
        info_text.insert("1.0", plant_info["Infos"])
        # info_text bleibt normal, da bearbeitbar

        save_button.config(state="normal") # Speichern-Button aktivieren

        # Berechnungen und EC-Wert aktualisieren
        calculate()
        update_ec_value()

    except Exception as e:
         messagebox.showerror("Fehler beim Aktualisieren", f"Ein unerwarteter Fehler ist in update_week aufgetreten:\n{e}")
         # Ggf. GUI Felder leeren
         # ... (Code zum Leeren wie oben)


def calculate(fertilizer_type: Optional[str] = None, var: Optional[tk.IntVar] = None):
    """
    Berechnet die Düngermenge für ausgewählte Dünger und aktualisiert die Labels.
    Wird durch Checkbox-Änderungen oder manuell aufgerufen.
    """
    try:
        # Prüfen, ob eine Pflanze ausgewählt ist (indirekt über Woche)
        week_str = week_entry.get()
        if not week_str:
             # Keine Woche -> keine Berechnung
             for result_label in result_labels:
                 result_label.config(text="")
             return

        week = int(week_str)
        water_amount_str = water_amount_entry.get()
        water_amount = float(water_amount_str) if water_amount_str else 0.0

        if water_amount <= 0:
            # Keine Wassermenge -> keine Berechnung (oder Warnung?)
            for result_label in result_labels:
                 result_label.config(text="")
            # Optional: messagebox.showwarning("Ungültige Eingabe", "Bitte eine positive Wassermenge eingeben.")
            return

        # Berechne alle oder nur einen bestimmten Dünger
        for i, (checkbox, f_var, result_label) in enumerate(zip(checkboxes, fertilizer_vars, result_labels)):
            current_fertilizer_type = fertilizer_options[i]

            # Nur den geänderten berechnen, wenn Typ übergeben wurde
            if fertilizer_type is not None and current_fertilizer_type != fertilizer_type:
                continue

            if f_var.get() == 1: # Wenn Checkbox aktiviert ist
                result = calculate_fertilizer_amount(week, water_amount, current_fertilizer_type)
                if result is not None:
                    result_label.config(text=f"{result:.2f} ml")
                else:
                     result_label.config(text="Fehler") # Bei ungültigem Typ
            else: # Checkbox nicht aktiviert
                result_label.config(text="")

    except ValueError:
        # Fehler bei Konvertierung von Woche oder Wassermenge
        for result_label in result_labels:
             result_label.config(text="") # Alle Ergebnisse leeren
        # Optional: Direkteres Feedback geben
        # messagebox.showerror("Ungültige Eingabe", "Bitte gültige Zahlen für Woche und Wassermenge eingeben.")
    except Exception as e:
        messagebox.showerror("Berechnungsfehler", f"Ein Fehler ist bei der Berechnung aufgetreten:\n{e}")


def update_ec_value():
    """Berechnet und aktualisiert das EC-Zielwert-Label in der GUI."""
    try:
        week_str = week_entry.get()
        if not week_str:
            ec_label.config(text="EC-Ziel (Erde): -")
            return

        week = int(week_str)
        ec_value_ms = get_ec_value(week) # Wert in mS/cm

        if ec_value_ms is not None:
            ec_value_us = ec_value_ms * 1000 # Umrechnung in µS/cm
            ec_label.config(text=f"EC-Ziel (Erde): {ec_value_us:.0f} µS/cm") # Ohne Nachkommastellen
        else:
            ec_label.config(text="EC-Ziel (Erde): -")
    except ValueError:
        ec_label.config(text="EC-Ziel (Erde): -") # Bei ungültiger Woche
    except Exception as e:
        ec_label.config(text="EC-Ziel (Erde): Fehler")
        print(f"Fehler in update_ec_value: {e}")


def save_info():
    """Speichert die geänderten Infos für die aktuelle Pflanze."""
    selected_plant = plant_var.get()
    if not selected_plant or selected_plant not in plant_data:
         messagebox.showwarning("Keine Pflanze ausgewählt", "Bitte zuerst eine Pflanze auswählen, um Infos zu speichern.")
         return

    try:
        new_info = info_text.get("1.0", tk.END).strip()
        plant_data[selected_plant]["Infos"] = new_info
        save_plant_data_to_csv(plant_data)
        messagebox.showinfo("Gespeichert", f"Infos für '{selected_plant}' wurden gespeichert.")
    except Exception as e:
        messagebox.showerror("Fehler beim Speichern", f"Konnte Infos nicht speichern:\n{e}")

def neue_pflanze_hinzufuegen():
    """Öffnet ein modales Fenster zur Eingabe einer neuen Pflanze."""

    def pflanze_speichern():
        """Validiert Eingaben und speichert die neue Pflanze."""
        neuer_pflanzenname = pflanzenname_entry.get().strip()
        neues_keimdatum_str = keimdatum_entry.get().strip()
        neue_genetik = genetik_entry.get().strip()
        # Infos sind optional, daher kein .strip() nötig wenn leer erlaubt
        neue_infos = infos_text_new.get("1.0", tk.END).strip()

        # --- Validierung ---
        errors = []
        if not neuer_pflanzenname:
            errors.append("Pflanzenname fehlt.")
        elif neuer_pflanzenname in plant_data:
            errors.append(f"Pflanzenname '{neuer_pflanzenname}' existiert bereits.")

        if not neues_keimdatum_str:
            errors.append("Keimdatum fehlt.")
        else:
            try:
                keimdatum_objekt = datetime.strptime(neues_keimdatum_str, '%d.%m.%Y')
                if keimdatum_objekt > datetime.now():
                    errors.append("Keimdatum darf nicht in der Zukunft liegen.")
            except ValueError:
                errors.append("Ungültiges Keimdatum (Format TT.MM.JJJJ).")

        if not neue_genetik:
            errors.append("Genetik fehlt.")
        # Infos sind optional, keine Prüfung

        if errors:
            fehler_label.config(text="\n".join(errors))
            return
        # --- Ende Validierung ---

        try:
            # Keimdatum nochmal holen (falls oben nur geprüft)
            keimdatum_objekt = datetime.strptime(neues_keimdatum_str, '%d.%m.%Y')

            # Pflanze zu plant_data hinzufügen
            plant_data[neuer_pflanzenname] = {
                "Keimdatum": keimdatum_objekt,
                "Genetik": neue_genetik,
                "Infos": neue_infos
            }

            save_plant_data_to_csv(plant_data)

            # Hauptfenster aktualisieren
            plant_keys = list(plant_data.keys())
            plant_dropdown['values'] = plant_keys
            plant_var.set(neuer_pflanzenname)
            update_week() # Aktualisiert alle abhängigen Felder

            new_plant_window.destroy()
            messagebox.showinfo("Erfolg", f"Pflanze '{neuer_pflanzenname}' erfolgreich hinzugefügt.")

        except Exception as e:
             fehler_label.config(text=f"Speicherfehler: {e}")


    # --- Fenster für neue Pflanze erstellen ---
    new_plant_window = tk.Toplevel(window)
    new_plant_window.title("Neue Pflanze hinzufügen")
    new_plant_window.transient(window) # Modal über Hauptfenster
    new_plant_window.grab_set()     # Eingabefokus erzwingen
    new_plant_window.resizable(False, False) # Größe nicht änderbar

    # Grid-Konfiguration
    new_plant_window.columnconfigure(1, weight=1)

    # Eingabefelder (mit ttk)
    ttk.Label(new_plant_window, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    pflanzenname_entry = ttk.Entry(new_plant_window, width=40)
    pflanzenname_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Keimdatum (TT.MM.JJJJ):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    keimdatum_entry = ttk.Entry(new_plant_window, width=40)
    keimdatum_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Genetik:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    genetik_entry = ttk.Entry(new_plant_window, width=40)
    genetik_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(new_plant_window, text="Infos:").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
    # ScrolledText für potenziell längere Infos
    infos_text_new = scrolledtext.ScrolledText(new_plant_window, height=6, width=40, wrap=tk.WORD)
    infos_text_new.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

    # Fehleranzeige
    fehler_label = ttk.Label(new_plant_window, text="", foreground="red", wraplength=300)
    fehler_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # Buttons Frame
    button_frame = ttk.Frame(new_plant_window)
    button_frame.grid(row=5, column=0, columnspan=2, pady=10)

    speichern_button = ttk.Button(button_frame, text="Speichern", command=pflanze_speichern)
    speichern_button.pack(side=tk.RIGHT, padx=5)

    abbrechen_button = ttk.Button(button_frame, text="Abbrechen", command=new_plant_window.destroy)
    abbrechen_button.pack(side=tk.RIGHT, padx=5)

    pflanzenname_entry.focus_set() # Fokus auf erstes Feld
    new_plant_window.wait_window() # Warten bis Fenster geschlossen wird


def pflanze_loeschen():
    """Löscht die ausgewählte Pflanze nach Bestätigung."""
    selected_plant = plant_var.get()
    if not selected_plant or selected_plant not in plant_data:
        messagebox.showwarning("Keine Pflanze ausgewählt", "Bitte zuerst eine Pflanze zum Löschen auswählen.")
        return

    if messagebox.askyesno("Pflanze löschen", f"Möchten Sie die Pflanze '{selected_plant}' wirklich unwiderruflich löschen?"):
        try:
            del plant_data[selected_plant]
            save_plant_data_to_csv(plant_data)

            # Hauptfenster aktualisieren
            plant_keys = list(plant_data.keys())
            plant_dropdown['values'] = plant_keys
            if plant_keys:
                plant_var.set(plant_keys[0]) # Erste verbleibende auswählen
            else:
                plant_var.set("") # Combobox leeren

            update_week() # GUI aktualisieren (leert Felder etc.)
            messagebox.showinfo("Gelöscht", f"Pflanze '{selected_plant}' wurde gelöscht.")
        except Exception as e:
            messagebox.showerror("Fehler beim Löschen", f"Konnte Pflanze nicht löschen:\n{e}")

def ec_berechnen():
    """Öffnet ein modales Fenster zur Berechnung der benötigten Düngermenge für Ziel-EC."""

    def toggle_ec_soll_entry(*args):
        """Aktiviert/Deaktiviert das manuelle EC-Soll-Feld."""
        if ec_soll_var.get() == "manuell":
            ec_soll_entry.config(state="normal")
            ec_soll_entry.focus_set()
        else:
            ec_soll_entry.config(state="disabled")

    def duenger_berechnen():
        """Berechnet die benötigte Menge Wachstums- ODER Blütedünger."""
        try:
            # EC-Ist Wert holen und validieren
            ec_ist_str = ec_ist_entry.get()
            if not ec_ist_str:
                raise ValueError("Aktueller EC-Wert fehlt.")
            ec_ist = float(ec_ist_str)
            if ec_ist < 0:
                 raise ValueError("Aktueller EC-Wert darf nicht negativ sein.")

            # Wassermenge aus Hauptfenster holen und validieren
            wassermenge_str = water_amount_entry.get()
            if not wassermenge_str:
                 raise ValueError("Wassermenge im Hauptfenster fehlt.")
            wassermenge = float(wassermenge_str)
            if wassermenge <= 0:
                 raise ValueError("Wassermenge muss positiv sein.")

            # EC-Sollwert ermitteln
            if ec_soll_var.get() == "vorhanden":
                ec_soll_text = ec_label.cget("text") # Format: "EC-Ziel (Erde): 1200 µS/cm"
                if ":" not in ec_soll_text or "µS/cm" not in ec_soll_text:
                     raise ValueError("Ziel-EC-Wert im Hauptfenster nicht verfügbar oder ungültig.")
                ec_soll_str = ec_soll_text.split(":")[1].strip().split()[0]
                ec_soll = float(ec_soll_str)
            else: # manuell
                ec_soll_str = ec_soll_entry.get()
                if not ec_soll_str:
                     raise ValueError("Manueller Soll-EC-Wert fehlt.")
                ec_soll = float(ec_soll_str)
                if ec_soll <= 0:
                     raise ValueError("Soll-EC-Wert muss positiv sein.")

            if ec_ist >= ec_soll:
                 ergebnis_label.config(text="Aktueller EC ist bereits über oder gleich dem Soll-EC.\nKein Dünger benötigt.", foreground="blue")
                 return

            # Berechnung für beide Düngerarten durchführen
            menge_wachstum = berechne_wachstumduenger_menge_fuer_ec(ec_ist, ec_soll, wassermenge)
            menge_bluete = berechne_bluetenduenger_menge_fuer_ec(ec_ist, ec_soll, wassermenge)

            # Ergebnis anzeigen (Erklären, dass es Alternativen sind)
            ergebnis_text = (
                f"Um {ec_soll:.0f} µS/cm zu erreichen, fügen Sie hinzu:\n\n"
                f"-> ENTWEDER {menge_wachstum:.2f} ml Wachstumsdünger\n"
                f"-> ODER {menge_bluete:.2f} ml Blütedünger\n\n"
                f"(Berechnet für {wassermenge:.2f} L Wasser)"
            )
            ergebnis_label.config(text=ergebnis_text, foreground="black")

        except ValueError as ve:
            ergebnis_label.config(text=f"Eingabefehler: {ve}", foreground="red")
        except Exception as e:
            ergebnis_label.config(text=f"Fehler: {e}", foreground="red")

    # --- Fenster für EC-Berechnung erstellen ---
    ec_window = tk.Toplevel(window)
    ec_window.title("EC-Helper: Dünger berechnen")
    ec_window.transient(window)
    ec_window.grab_set()
    ec_window.resizable(False, False)

    # Grid
    ec_window.columnconfigure(1, weight=1)

    # Eingabefelder
    ttk.Label(ec_window, text="Aktueller EC (µS/cm):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    ec_ist_entry = ttk.Entry(ec_window, width=25)
    ec_ist_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

    ttk.Label(ec_window, text="Soll-EC (µS/cm):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    ec_soll_frame = ttk.Frame(ec_window) # Frame für Dropdown und Entry
    ec_soll_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
    ec_soll_frame.columnconfigure(1, weight=1)

    ec_soll_var = tk.StringVar(value="vorhanden") # Standard: Wert aus Hauptfenster nehmen
    ec_soll_var.trace_add("write", toggle_ec_soll_entry) # Callback bei Änderung

    ec_soll_dropdown = ttk.OptionMenu(ec_soll_frame, ec_soll_var, "vorhanden", "vorhanden", "manuell")
    ec_soll_dropdown.grid(row=0, column=0, padx=(0, 5))

    ec_soll_entry = ttk.Entry(ec_soll_frame, width=15, state="disabled") # Standardmäßig deaktiviert
    ec_soll_entry.grid(row=0, column=1, sticky="ew")

    # Berechnen Button
    berechnen_button = ttk.Button(ec_window, text="Düngermengen berechnen", command=duenger_berechnen)
    berechnen_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Ergebnisanzeige
    ergebnis_label = ttk.Label(ec_window, text="Geben Sie den aktuellen EC-Wert ein.", wraplength=350, justify=tk.LEFT)
    ergebnis_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    ec_ist_entry.focus_set()
    toggle_ec_soll_entry() # Initialen Status des Entry-Felds setzen
    ec_window.wait_window()


# --- Haupt-GUI Erstellung ---
window = tk.Tk()
window.title("Pflanzen Düngerberechnung v1.1")
window.minsize(550, 550) # Mindestgröße für bessere Lesbarkeit

# Style (optional, für besseres Aussehen)
style = ttk.Style()
# style.theme_use('clam') # Alternativen: 'alt', 'default', 'classic', 'vista', 'xpnative'

# Grid Konfiguration für Hauptfenster
window.columnconfigure(1, weight=1) # Spalte 1 soll sich ausdehnen

# --- Widgets ---

# Frame für Pflanzenauswahl und Basisinfos
plant_info_frame = ttk.LabelFrame(window, text="Pflanzeninformationen")
plant_info_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
plant_info_frame.columnconfigure(1, weight=1)

ttk.Label(plant_info_frame, text="Pflanze:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
plant_var = tk.StringVar()
plant_dropdown = ttk.Combobox(plant_info_frame, textvariable=plant_var, state="readonly") # Readonly verhindert Tippen
plant_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
plant_dropdown.bind("<<ComboboxSelected>>", update_week)

# EC-Ziel Label (aktualisiert durch update_week)
ec_label = ttk.Label(plant_info_frame, text="EC-Ziel (Erde): -", font=('TkDefaultFont', 9, 'bold'))
ec_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")

ttk.Label(plant_info_frame, text="Genetik:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
genetics_entry = ttk.Entry(plant_info_frame, state="readonly")
genetics_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew") # Über 2 Spalten

ttk.Label(plant_info_frame, text="Woche seit Keimung:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
week_entry = ttk.Entry(plant_info_frame, width=10) # Schmaler machen
week_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
# Bind Enter key on week entry to recalculate
week_entry.bind("<Return>", lambda event: calculate())

ttk.Label(plant_info_frame, text="Keimdatum:").grid(row=2, column=2, padx=5, pady=5, sticky="w") # Label für Datum
germination_date_entry = ttk.Entry(plant_info_frame, state="readonly", width=12)
germination_date_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w") # Eigene Spalte für Datum

# Frame für Berechnungs-Inputs
calc_input_frame = ttk.LabelFrame(window, text="Berechnung")
calc_input_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
calc_input_frame.columnconfigure(1, weight=1)

ttk.Label(calc_input_frame, text="Wassermenge (Liter):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
water_amount_entry = ttk.Entry(calc_input_frame, width=10)
water_amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
water_amount_entry.insert(0, "1.0") # Standardwert
water_amount_entry.bind("<Return>", lambda event: calculate())

# EC-Helper Button neben Wassermenge
ec_button = ttk.Button(calc_input_frame, text="EC-Helper", command=ec_berechnen)
ec_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")

# Frame für Düngerauswahl und Ergebnisse
fertilizer_frame = ttk.LabelFrame(window, text="Düngerauswahl & Ergebnisse (ml)")
fertilizer_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="nsew") # Soll sich vertikal ausdehnen
fertilizer_frame.columnconfigure(0, weight=1) # Checkbox-Spalte soll sich ausdehnen
fertilizer_frame.columnconfigure(1, minsize=80) # Mindestbreite für Ergebnisse
window.rowconfigure(2, weight=1) # Zeile 2 im Hauptfenster soll sich ausdehnen

fertilizer_options = [
    "Bio-Grow", "Bio-Bloom", "Top-Max", "Bio-Heaven", "Alg-A-Mic", "Acti-Vera",
    "Root-Juice", "Fish-Mix", "CalMag - Prevention (Biobizz)", "CalMag - Correction (Biobizz)"
]
fertilizer_vars = []
checkboxes = []
result_labels = []

for i, option in enumerate(fertilizer_options):
    var = tk.IntVar()
    fertilizer_vars.append(var)

    # Verwende lambda mit Standardargumenten, um aktuelle Werte zu binden!
    cmd = lambda opt=option, v=var: calculate(opt, v)

    checkbox = ttk.Checkbutton(fertilizer_frame, text=option, variable=var, command=cmd)
    checkbox.grid(row=i, column=0, padx=5, pady=2, sticky="w")
    checkboxes.append(checkbox)

    result_label = ttk.Label(fertilizer_frame, text="", width=10, anchor="e") # Rechtsbündig
    result_label.grid(row=i, column=1, padx=5, pady=2, sticky="e")
    result_labels.append(result_label)

# Frame für Infos
info_frame = ttk.LabelFrame(window, text="Notizen zur Pflanze")
info_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
info_frame.columnconfigure(0, weight=1) # Textfeld soll sich ausdehnen

info_text = scrolledtext.ScrolledText(info_frame, height=6, width=50, wrap=tk.WORD, state="disabled") # Start deaktiviert
info_text.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

save_button = ttk.Button(info_frame, text="Infos speichern", command=save_info, state="disabled") # Start deaktiviert
save_button.grid(row=1, column=1, padx=5, pady=5, sticky="e") # Rechts im Frame

# Frame für Aktionen (Neue Pflanze, Löschen)
action_frame = ttk.Frame(window)
action_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="e") # Rechtsbündig

neue_pflanze_button = ttk.Button(action_frame, text="Neue Pflanze anlegen", command=neue_pflanze_hinzufuegen)
neue_pflanze_button.pack(side=tk.LEFT, padx=5)

loeschen_button = ttk.Button(action_frame, text="Pflanze löschen", command=pflanze_loeschen)
loeschen_button.pack(side=tk.LEFT, padx=5)


# --- Initialisierung ---
plant_data = read_plant_data()
plant_dropdown['values'] = list(plant_data.keys())
if plant_data:
    plant_var.set(list(plant_data.keys())[0]) # Erste Pflanze auswählen, falls vorhanden
    update_week() # GUI initial befüllen
else:
    update_week() # Felder leeren, Buttons deaktivieren etc.

window.mainloop()