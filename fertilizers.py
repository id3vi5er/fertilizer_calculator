import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import csv
from datetime import datetime, timedelta
import os
os.chdir('C:\\Users\\nratt\\Documents\\PlatformIO\\Projects\\Python\\fertilizer_calculator') # Replace with the actual directory


def read_plant_data():
    """
    Liest die Pflanzendaten aus der CSV-Datei ein.
    Erstellt die Datei, falls sie nicht existiert.

    Returns:
        Ein Dictionary mit den Pflanzennamen als Schlüssel 
        und einem Dictionary mit "Keimwoche", "Genetik" und "Infos" als Werte.
    """
    plant_data = {}
    try:
        with open('pflanzendaten.csv', 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Überspringt die Kopfzeile
            for row in reader:
                plant_name, germination_date_str, genetics, info = row
                try:
                    # Datum in datetime Objekt umwandeln
                    germination_date = datetime.strptime(germination_date_str, '%d.%m.%Y')
                    # Keimwoche berechnen
                    germination_week = germination_date.isocalendar().week
                    plant_data[plant_name] = {
                        "Keimwoche": germination_week,
                        "Genetik": genetics,
                        "Infos": info
                    }
                except ValueError:
                    print(f"Ungültiges Datumsformat für {plant_name}: {germination_date_str}")
    except FileNotFoundError:
        # Datei existiert nicht, also erstellen wir sie mit einer Kopfzeile
        with open('pflanzendaten.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Pflanzenname", "Keimdatum", "Genetik", "Infos"])
        print("Datei 'pflanzendaten.csv' wurde erstellt.")

    return plant_data

def update_week(event=None):
    """
    Aktualisiert die aktuelle Woche basierend auf der 
    ausgewählten Pflanze und dem aktuellen Datum.
    """
    try:
        selected_plant = plant_var.get()
        germination_week = plant_data[selected_plant]["Keimwoche"]
        today = datetime.today()
        year = today.year  # Aktuelles Jahr verwenden
        # Datum des ersten Tages der Keimwoche berechnen
        germination_date = datetime.strptime(f'{year}-{germination_week}-1', '%Y-%W-%w')
        current_week = (today - germination_date).days // 7 + 1
        week_entry.delete(0, tk.END)
        week_entry.insert(0, str(current_week))
        germination_date_entry.config(state="normal")  # Textfeld editierbar machen
        germination_date_entry.delete(0, tk.END)
        germination_date_entry.insert(0, str(germination_date.strftime('%d.%m.%Y')))        
        germination_date_entry.config(state="readonly")  # Textfeld schreibgeschützt machen



        # Genetik und Infos aktualisieren
        genetics_entry.config(state="normal")  # Textfeld editierbar machen
        genetics_entry.delete(0, tk.END)
        genetics_entry.insert(0, plant_data[selected_plant]["Genetik"])
        genetics_entry.config(state="readonly")  # Textfeld schreibgeschützt machen

        info_text.delete("1.0", tk.END)
        info_text.insert("1.0", plant_data[selected_plant]["Infos"])
        calculate()
        update_ec_value()

    except KeyError:
        pass  # Pflanze nicht gefunden, ignoriere den Fehler

def calculate_fertilizer_amount(week, water_amount, fertilizer_type):
    """
    Berechnet die Düngemenge für eine bestimmte Woche und Wassermenge.

    Args:
        week: Die aktuelle Blütewoche der Pflanze (int).
        water_amount: Die Menge an Wasser in Litern (float).
        fertilizer_type: Die Art des Düngers (str).

    Returns:
        Die Düngemenge in Millilitern (float) oder 0 falls die Woche nicht gefunden wurde.
    """

    fertilizer_data = {
        "CalMag - Substrate - Prevention": {
            1: 0.3, 2: 0.3, 3: 0.3, 4: 0.4, 5: 0.4,
            6: 0.5, 7: 0.6, 8: 0.7, 9: 0.8, 10: 0.8, 
            11: 0.8, 12: 0.8, 13: 0.8, 14: 0.8, 15: 0.8,
            16: 0.8, 17: 0.8, 18: 0.8, 19: 0.8, 20: 0.8
        },
        "CalMag - Substrate - Correction": {
            1: 0.5, 2: 0.5, 3: 0.5, 4: 0.6, 5: 0.6,
            6: 0.8, 7: 0.8, 8: 1.0, 9: 1.1, 10: 1.2, 
            11: 1.2, 12: 1.2, 13: 1.2, 14: 1.2, 15: 1.2,
            16: 1.2, 17: 1.2, 18: 1.2, 19: 1.2, 20: 1.2
        },
        "GreenHome Wachstumsduenger - Substrate":{
            1: 2.0, 2: 2.27, 3: 2.54, 4: 2.81, 5: 3.08,
            6: 3.35, 7: 3.62, 8: 3.89, 9: 4.16, 10: 4.45, 
            11: 4.45, 12: 4.45, 13: 4.45, 14: 4.45, 15: 4.45,
            16: 4.45, 17: 4.45, 18: 4.45, 19: 4.45, 20: 4.45
        },
        "GreenHome Bluetenduenger - Substrate":{
            1: 3, 2: 3.33, 3: 3.67, 4: 4.0, 5: 4.33,
            6: 4.67, 7: 5.0, 8: 5.33, 9: 5.67, 10: 6.0, 
            11: 6.0, 12: 6.0, 13: 6.0, 14: 6.0, 15: 6.0,
            16: 6.0, 17: 6.0, 18: 6.0, 19: 6.0, 20: 6.0
        },
        "Fish-Mix (5-1-4) - Substrate": {
            1: 0, 2: 2, 3: 2, 4: 2, 5: 3,
            6: 3, 7: 4, 8: 4, 9: 4, 10: 4, 
            11: 4, 12: 4, 12: 4, 13: 4, 14: 4,
            15: 4, 16: 4, 17: 4, 18: 4, 19: 4, 20: 4
        },
        "Root-Juice": {
            1: 4, 2: 4, 3: 4, 4: 4, 5: 4,
            6: 4, 7: 4, 8: 4, 9: 4, 10: 4, 
            11: 4, 12: 4, 13: 4, 14: 4, 15: 4,
            16: 4, 17: 4, 18: 4, 19: 4, 20: 4
        }
    }

    if fertilizer_type not in fertilizer_data:
        return "Ungültiger Düngertyp."

    if week not in fertilizer_data[fertilizer_type]:
        return 0

    dosage_per_liter = fertilizer_data[fertilizer_type][week]
    fertilizer_amount = dosage_per_liter * water_amount

    return fertilizer_amount

def calculate(fertilizer_type=None, var=None):
    """
    Liest die Eingaben aus den Eingabefeldern, berechnet die Düngemenge
    für jeden ausgewählten Dünger und zeigt das Ergebnis im entsprechenden Label an.
    """
    try:
        week = int(week_entry.get())
        water_amount = float(water_amount_entry.get())
        if fertilizer_type and var:
            if var.get() == 1:
                result = calculate_fertilizer_amount(week, water_amount, fertilizer_type)
                result_label = result_labels[fertilizer_options.index(fertilizer_type)]
                result_label.config(text=f"{result:.2f} ml")
            else:
                result_label = result_labels[fertilizer_options.index(fertilizer_type)]
                result_label.config(text="")
        else:
            for checkbox, var, result_label in zip(checkboxes, fertilizer_vars, result_labels):
                if var.get() == 1:
                    fertilizer_type = checkbox.cget("text")
                    result = calculate_fertilizer_amount(week, water_amount, fertilizer_type)
                    result_label.config(text=f"{result:.2f} ml")
                else:
                    result_label.config(text="")
    except ValueError:
        result_label.config(text="Ungültige Eingabe.")

def save_info():
    """
    Speichert die Infos in der CSV-Datei.
    """
    selected_plant = plant_var.get()
    new_info = info_text.get("1.0", tk.END).strip()
    plant_data[selected_plant]["Infos"] = new_info

    # CSV-Datei aktualisieren
    with open('pflanzendaten.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "Keimungsdatum", "Genetik", "Infos"])  # Kopfzeile schreiben
        for plant_name, data in plant_data.items():
            writer.writerow([plant_name, 
                             datetime.strptime(f'{datetime.now().year}-{data["Keimwoche"]}-1', '%Y-%W-%w').strftime('%d.%m.%Y'), 
                             data["Genetik"], 
                             data["Infos"]])
            
def neue_pflanze_hinzufuegen():
    """
    Öffnet ein neues Fenster, um Daten für eine neue Pflanze einzugeben.
    """
    def pflanze_speichern():
        """
        Speichert die Daten der neuen Pflanze in der CSV-Datei und aktualisiert das Hauptfenster.
        """
        neuer_pflanzenname = pflanzenname_entry.get()
        neues_keimdatum = keimdatum_entry.get()
        neue_genetik = genetik_entry.get()
        neue_infos = infos_text.get("1.0", tk.END).strip()

        # Überprüfen, ob alle Felder ausgefüllt sind
        if not all([neuer_pflanzenname, neues_keimdatum, neue_genetik, neue_infos]):
            fehler_label.config(text="Bitte alle Felder ausfüllen.")
            return

        try:
            # Keimwoche berechnen
            keimdatum_objekt = datetime.strptime(neues_keimdatum, '%d.%m.%Y')
            keimwoche = keimdatum_objekt.isocalendar().week

            # Pflanze zu plant_data hinzufügen
            plant_data[neuer_pflanzenname] = {
                "Keimwoche": keimwoche,
                "Genetik": neue_genetik,
                "Infos": neue_infos
            }

            # CSV-Datei aktualisieren
            with open('pflanzendaten.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Name", "Keimungsdatum", "Genetik", "Infos"])  # Kopfzeile schreiben
                for pflanzenname, daten in plant_data.items():
                    writer.writerow([pflanzenname,
                                     datetime.strptime(f'{datetime.now().year}-{daten["Keimwoche"]}-1', '%Y-%W-%w').strftime('%d.%m.%Y'),
                                     daten["Genetik"],
                                     daten["Infos"]])

            # Hauptfenster aktualisieren
            plant_dropdown['values'] = list(plant_data.keys())
            plant_var.set(neuer_pflanzenname)
            update_week()

            # Neues Fenster schließen
            neues_fenster.destroy()

        except ValueError:
            fehler_label.config(text="Ungültiges Datumsformat. Bitte verwenden Sie TT.MM.JJJJ.")

    # Neues Fenster erstellen
    neues_fenster = tk.Toplevel(window)
    neues_fenster.title("Neue Pflanze hinzufügen")

    # Eingabefelder
    pflanzenname_label = tk.Label(neues_fenster, text="Name:")
    pflanzenname_label.grid(row=0, column=0)
    pflanzenname_entry = tk.Entry(neues_fenster)
    pflanzenname_entry.grid(row=0, column=1)

    keimdatum_label = tk.Label(neues_fenster, text="Keimdatum (TT.MM.JJJJ):")
    keimdatum_label.grid(row=1, column=0)
    keimdatum_entry = tk.Entry(neues_fenster)
    keimdatum_entry.grid(row=1, column=1)

    genetik_label = tk.Label(neues_fenster, text="Genetik:")
    genetik_label.grid(row=2, column=0)
    genetik_entry = tk.Entry(neues_fenster)
    genetik_entry.grid(row=2, column=1)

    infos_label = tk.Label(neues_fenster, text="Infos:")
    infos_label.grid(row=3, column=0)
    infos_text = tk.Text(neues_fenster, height=5, width=30)
    infos_text.grid(row=3, column=1)

    # Fehleranzeige
    fehler_label = tk.Label(neues_fenster, text="", fg="red")
    fehler_label.grid(row=4, column=0, columnspan=2)

    # Speichern-Button
    speichern_button = tk.Button(neues_fenster, text="Speichern", command=pflanze_speichern)
    speichern_button.grid(row=5, column=1)

def pflanze_loeschen():
    """
    Löscht die ausgewählte Pflanze aus der CSV-Datei und aktualisiert das Hauptfenster.
    """
    selected_plant = plant_var.get()

    # Bestätigungsabfrage
    if not messagebox.askyesno("Pflanze löschen", f"Möchten Sie '{selected_plant}' wirklich löschen?"):
        return  # Abbrechen, wenn der Benutzer "Nein" klickt

    if selected_plant in plant_data:
        del plant_data[selected_plant]

        # CSV-Datei aktualisieren
        with open('pflanzendaten.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Name", "Keimungsdatum", "Genetik", "Infos"])  # Kopfzeile schreiben
            for plant_name, data in plant_data.items():
                writer.writerow([plant_name,
                                 datetime.strptime(f'{datetime.now().year}-{data["Keimwoche"]}-1', '%Y-%W-%w').strftime('%d.%m.%Y'),
                                 data["Genetik"],
                                 data["Infos"]])

        # Hauptfenster aktualisieren
        plant_dropdown['values'] = list(plant_data.keys())
        if plant_data:
            plant_var.set(list(plant_data.keys())[0])
        else:
            plant_var.set("")
        update_week()

def get_ec_value(week):
    """
    Gibt den EC-Wert für die entsprechende Woche zurück.

    Args:
        week: Die aktuelle Woche seit Keimung (int).

    Returns:
        Den EC-Wert für Erde (float) oder None, falls die Woche nicht gefunden wurde.
    """
    ec_values = {
        1: 0.4,
        2: 0.6,
        3: 0.7,
        4: 0.9,
        5: 1.0,
        6: 1.2,
        7: 1.4,
        8: 1.5,
        9: 1.6,
        10: 1.6,
        11: 1.7,
        12: 1.7,
        13: 1.8,
        14: 1.8,
        14: 1.8,
        15: 1.9,
        16: 1.9,
        17: 1.9,
        18: 2.0,
        19: 2.0,
        20: 2.0
    }
    return ec_values.get(week)

def update_ec_value():
    """
    Berechnet und aktualisiert den EC-Wert in der GUI.
    """
    try:
        week = int(week_entry.get())
        ec_value = get_ec_value(week) * 1000  # Umrechnung in uS/cm
        if ec_value is not None:
            ec_label.config(text=f"EC-Wert (Erde): {ec_value:.2f} uS/cm")
        else:
            ec_label.config(text="EC-Wert (Erde): -")
    except ValueError:
        ec_label.config(text="EC-Wert (Erde): -")

def berechne_wachstumduenger_menge(EC_ist, EC_soll, wassermenge):
    """Berechnet die benötigte Menge an Dünger in ml, um einen Soll-EC-Wert in einer gegebenen Wassermenge zu erreichen.

    Args:
        EC_ist: Der aktuelle EC-Wert des Wassers in µS/cm.
        EC_soll: Der gewünschte EC-Wert des Wassers in µS/cm.
        wassermenge_liter: Die Menge des Wassers in Litern.

    Returns:
        Die benötigte Menge an Wachstumsdünger in ml.
    """

    benötigte_ec_zunahme = EC_soll - EC_ist
    benötigte_menge_ml = (benötigte_ec_zunahme / 478) * wassermenge
    return benötigte_menge_ml



def berechne_bluetenduenger_menge(EC_ist, EC_soll, wassermenge):
    """Berechnet die benötigte Menge an Stoff B in ml, um einen Soll-EC-Wert in einer gegebenen Wassermenge zu erreichen.

    Args:
      EC_ist: Der aktuelle EC-Wert des Wassers in µS/cm.
      EC_soll: Der gewünschte EC-Wert des Wassers in µS/cm.
      wassermenge: Die Menge des Wassers in Litern.

    Returns:
      Die benötigte Menge an Blüetendünger in ml.
    """
    benötigte_ec_zunahme = EC_soll - EC_ist
    benötigte_menge_ml = (benötigte_ec_zunahme / 430) * wassermenge
    return benötigte_menge_ml

def ec_berechnen():
    """
    Öffnet ein neues Fenster, um den EC-Ist-Wert einzugeben
    und die benötigte Menge an Dünger zu berechnen.
    """
    def duenger_berechnen():
        """
        Berechnet die benötigte Menge an Wachstums- und Blütedünger 
        und zeigt das Ergebnis an.
        """
        try:
            EC_ist = float(ec_ist_entry.get())
            wassermenge = float(water_amount_entry.get())

            # EC-Sollwert basierend auf der Auswahl im Dropdown-Menü ermitteln
            if ec_soll_var.get() == "vorhanden":
                EC_soll_text = ec_label.cget("text")
                EC_soll = float(EC_soll_text.split(":")[1].strip().split()[0])
            else:
                EC_soll = float(ec_soll_entry.get())

            # Funktionen zur Berechnung der Düngermengen aufrufen
            benoetigte_menge_wachstumduenger = berechne_wachstumduenger_menge(EC_ist, EC_soll, wassermenge)
            benoetigte_menge_bluetenduenger = berechne_bluetenduenger_menge(EC_ist, EC_soll, wassermenge)

            # Ergebnis anzeigen
            ergebnis_label.config(text=f"Benötigte Menge Wachstumsdünger: {benoetigte_menge_wachstumduenger:.2f} ml\n"
                                     f"Benötigte Menge Blütedünger: {benoetigte_menge_bluetenduenger:.2f} ml")

        except ValueError:
            ergebnis_label.config(text="Ungültige Eingabe. Zahl eingegeben und Pflanze ausgewählt?")
        except IndexError:
            ergebnis_label.config(text="Fehler beim Lesen des Soll-EC-Werts.")

    # Neues Fenster erstellen
    neues_fenster = tk.Toplevel(window)
    neues_fenster.title("EC-Berechnung")

    # Eingabefelder
    ec_ist_label = tk.Label(neues_fenster, text="Aktueller EC-Wert (µS/cm):")
    ec_ist_label.grid(row=0, column=0)
    ec_ist_entry = tk.Entry(neues_fenster)
    ec_ist_entry.grid(row=0, column=1)

    # Dropdown-Menü für EC-Sollwert
    ec_soll_var = tk.StringVar(neues_fenster)
    ec_soll_var.set("vorhanden")  # Standardwert
    ec_soll_optionen = ["vorhanden", "manuell"]
    ec_soll_dropdown = tk.OptionMenu(neues_fenster, ec_soll_var, *ec_soll_optionen)
    ec_soll_dropdown.grid(row=3, column=0)

    # Eingabefeld für manuellen EC-Sollwert
    ec_soll_label = tk.Label(neues_fenster, text="Soll-EC-Wert (µS/cm):")
    ec_soll_label.grid(row=1, column=0)
    ec_soll_entry = tk.Entry(neues_fenster)
    ec_soll_entry.grid(row=1, column=1)

    # Ergebnisanzeige
    ergebnis_label = tk.Label(neues_fenster, text="")
    ergebnis_label.grid(row=4, column=0, columnspan=2)

    # Berechnen-Button
    berechnen_button = tk.Button(neues_fenster, text="Düngermengen berechnen", command=duenger_berechnen)
    berechnen_button.grid(row=2, column=1)

# def ec_berechnen():
#     """
#     Öffnet ein neues Fenster, um den EC-Ist-Wert einzugeben 
#     und die benötigte Menge an Stoff B zu berechnen.
#     """
#     def stoffbluetenduenger_berechnen():
#         """
#         Berechnet die benötigte Menge an GreenHome Bluetenduenger - Substrate und zeigt das Ergebnis an.
#         """
#         try:
#             EC_ist = float(ec_ist_entry.get())
#             # EC-Sollwert aus dem Hauptfenster lesen
#             EC_soll_text = ec_label.cget("text")
#             EC_soll = float(EC_soll_text.split(":")[1].strip().split()[0])  # Extrahiere den Sollwert aus dem Label-Text
#             wassermenge = float(water_amount_entry.get())  # Wassermenge aus dem Hauptfenster verwenden

#             # Hier die Funktion zur Berechnung von Stoff B aufrufen
#             benoetigte_menge_bluetenduenger = berechne_bluetenduenger_menge(EC_ist, EC_soll, wassermenge)

#             # Ergebnis anzeigen
#             ergebnis_label.config(text=f"Benötigte Menge GreenHome Bluetenduenger: {benoetigte_menge_bluetenduenger:.2f} ml")

#         except ValueError:
#             ergebnis_label.config(text="Ungültige Eingabe. Zahl eingegeben und Pflanze ausgewählt?")
#         except IndexError:
#             ergebnis_label.config(text="Fehler beim Lesen des Soll-EC-Werts.")

#     # Neues Fenster erstellen
#     neues_fenster = tk.Toplevel(window)
#     neues_fenster.title("EC-Berechnung")

#     # Eingabefelder
#     ec_ist_label = tk.Label(neues_fenster, text="Aktueller EC-Wert (µS/cm):")
#     ec_ist_label.grid(row=0, column=0)
#     ec_ist_entry = tk.Entry(neues_fenster)
#     ec_ist_entry.grid(row=0, column=1)

#     # Ergebnisanzeige
#     ergebnis_label = tk.Label(neues_fenster, text="")
#     ergebnis_label.grid(row=2, column=0, columnspan=2)

#     # Berechnen-Button
#     berechnen_button = tk.Button(neues_fenster, text="Bluetenduengermenge berechnen", command=stoffbluetenduenger_berechnen)
#     berechnen_button.grid(row=1, column=1)

# GUI erstellen
window = tk.Tk()
window.title("Düngerberechnung")


# Pflanzendaten einlesen
plant_data = read_plant_data()

# Dropdown-Menü für Pflanzenauswahl
plant_label = tk.Label(window, text="Pflanze:")
plant_label.grid(row=0, column=0)
plant_var = tk.StringVar()
plant_dropdown = ttk.Combobox(window, textvariable=plant_var)
plant_dropdown['values'] = list(plant_data.keys())
plant_dropdown.grid(row=0, column=1)
plant_dropdown.bind("<<ComboboxSelected>>", update_week)

#EC-Wert zum gießen
ec_label = tk.Label(window, text="EC-Wert (Erde): -")
ec_label.grid(row=0, column=2)

# Genetik-Anzeige
genetics_label = tk.Label(window, text="Genetik:")
genetics_label.grid(row=1, column=0)
genetics_entry = tk.Entry(window, state="readonly", width=30) # Breite auf 30 erhöht
genetics_entry.grid(row=1, column=1)

# Button zum Öffnen des neuen Fensters
ec_button = tk.Button(window, text="EC-Helper", command=ec_berechnen)
ec_button.grid(row=1, column=2)  # Button im Hauptfenster platzieren

# Wochen seit Keimung
week_label = tk.Label(window, text="Woche seit Keimung:")
week_label.grid(row=2, column=0)
week_entry = tk.Entry(window)
week_entry.grid(row=2, column=1)
germination_date_entry = tk.Entry(window, state="readonly", width=10)
germination_date_entry.grid(row=2, column=2)

# Gießmenge festlegen:
water_amount_label = tk.Label(window, text="Wassermenge (Liter):")
water_amount_label.grid(row=3, column=0)
water_amount_entry = tk.Entry(window)
water_amount_entry.grid(row=3, column=1)
water_amount_entry.delete(0, tk.END)
water_amount_entry.insert(0, str(1.0))
water_amount_entry.bind("<Return>", lambda event: calculate())  # calculate() bei <Return> aufrufen


# Checkboxen für Düngertypen
# fertilizer_label = tk.Label(window, text="Düngertypen:")
# fertilizer_label.grid(row=4, column=0)
fertilizer_options = ["CalMag - Substrate - Prevention", "CalMag - Substrate - Correction", "GreenHome Wachstumsduenger - Substrate", "GreenHome Bluetenduenger - Substrate", "Fish-Mix (5-1-4) - Substrate", "Root-Juice"]

fertilizer_vars = []
checkboxes = []
# for i, option in enumerate(fertilizer_options):
#     var = tk.IntVar()
#     fertilizer_vars.append(var)
#     checkbox = tk.Checkbutton(window, text=option, variable=var, command=lambda option=option, var=var: calculate(option, var))
#     checkbox.grid(row=i+5, column=1, sticky="w")
#     checkboxes.append(checkbox)

result_labels = []  # Liste für die Ergebnis-Labels

for i, option in enumerate(fertilizer_options):
    var = tk.IntVar()
    fertilizer_vars.append(var)
    checkbox = tk.Checkbutton(window, text=option, variable=var, command=lambda option=option, var=var: calculate(option, var))
    checkbox.grid(row=i+5, column=0, sticky="w")
    checkboxes.append(checkbox)

    # Label für das Ergebnis in der dritten Spalte
    result_label = tk.Label(window, text="")
    result_label.grid(row=i+5, column=1, sticky="w")
    result_labels.append(result_label)

# Infos-Anzeige und Speichern-Button
info_label = tk.Label(window, text="Infos:")
info_label.grid(row=12, column=0)
info_text = tk.Text(window, height=5, width=30)
info_text.grid(row=12, column=1)



save_button = tk.Button(window, text="Infos speichern", command=save_info)
save_button.grid(row=13, column=1)

# Button zum Hinzufügen neuer Pflanzen
neue_pflanze_button = tk.Button(window, text="Neue Pflanze anlegen", command=neue_pflanze_hinzufuegen)
neue_pflanze_button.grid(row=14, column=1)

# Button zum Löschen von Pflanzen
loeschen_button = tk.Button(window, text="Pflanze löschen", command=pflanze_loeschen)
loeschen_button.grid(row=14, column=2)



window.mainloop()