from datetime import datetime, timedelta, timezone
import os

def format_ical_datetime(dt):
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y%m%dT%H%M%S")

def eingabe_datum(prompt):
    aktuelles_jahr = datetime.now().year
    while True:
        val = input(prompt).strip()
        if val.endswith('.'):
            val = val[:-1].strip()
        try:
            if len(val.split('.')) == 2:
                dt = datetime.strptime(f"{val}.{aktuelles_jahr}", "%d.%m.%Y").date()
            else:
                dt = datetime.strptime(val, "%d.%m.%Y").date()
            return dt
        except ValueError:
            print("❌ Ungültiges Datum! Bitte im Format TT.MM, TT.MM. oder TT.MM.JJJJ eingeben.")

def parse_zeit(zeit_str):
    zeit_str = zeit_str.strip()
    if zeit_str.isdigit():
        zeit_str += ":00"
    try:
        return datetime.strptime(zeit_str, "%H:%M").time()
    except ValueError:
        return None

def eingabe_zeitbereich(prompt, optional=False):
    while True:
        val = input(prompt).strip()
        if optional and val == "":
            return None, None
        if '-' not in val:
            print("❌ Bitte im Format 'Start-Ende' eingeben, z.B. 17-21 oder 16:30-21:45")
            continue
        start_str, end_str = val.split('-', 1)
        start_time = parse_zeit(start_str)
        end_time = parse_zeit(end_str)
        if start_time is None or end_time is None:
            print("❌ Ungültige Zeitangabe! Beispiel: 17-21 oder 16:30-21:45")
            continue
        return start_time, end_time

def lese_events_aus_ics(dateipfad):
    if not os.path.exists(dateipfad):
        return []
    try:
        with open(dateipfad, 'r', encoding='utf-8') as f:
            content = f.read()
        events = []
        start = 0
        while True:
            start_event = content.find("BEGIN:VEVENT", start)
            if start_event == -1:
                break
            end_event = content.find("END:VEVENT", start_event)
            if end_event == -1:
                break
            event_block = content[start_event:end_event + len("END:VEVENT")]
            events.append(event_block.strip())
            start = end_event + len("END:VEVENT")
        return events
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen der Datei: {e}")
        return []

def create_event(uid, start_dt_utc, end_dt_utc, titel, beschreibung, reminder1_dt, reminder2_dt):
    return (
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{format_ical_datetime(datetime.now(timezone.utc))}Z\r\n"
        f"DTSTART:{format_ical_datetime(start_dt_utc)}Z\r\n"
        f"DTEND:{format_ical_datetime(end_dt_utc)}Z\r\n"
        f"SUMMARY:{titel}\r\n"
        f"DESCRIPTION:{beschreibung}\r\n"
        "BEGIN:VALARM\r\n"
        f"TRIGGER;VALUE=DATE-TIME:{format_ical_datetime(reminder1_dt)}Z\r\n"
        "DESCRIPTION:Erinnerung an Arbeit - 15:00 Uhr am Vortag\r\n"
        "ACTION:DISPLAY\r\n"
        "END:VALARM\r\n"
        "BEGIN:VALARM\r\n"
        f"TRIGGER;VALUE=DATE-TIME:{format_ical_datetime(reminder2_dt)}Z\r\n"
        "DESCRIPTION:Erinnerung an Arbeit - 07:00 Uhr am Tag\r\n"
        "ACTION:DISPLAY\r\n"
        "END:VALARM\r\n"
        "\r\nEND:VEVENT"
    )

berlin_offset = timedelta(hours=2)  # Berlin Sommerzeit, ggf anpassen

def main():
    events = lese_events_aus_ics("arbeit.ics")

    while True:
        print("\n=== Neuen Arbeitstermin eingeben ===")
        datum = eingabe_datum("Datum (TT.MM, TT.MM. oder TT.MM.JJJJ): ")
        start_time, end_time = eingabe_zeitbereich("Arbeitszeit (z.B. 17-21 oder 16:30-21:45): ")
        pause_start_time, pause_end_time = eingabe_zeitbereich("Pause (z.B. 12-12:30) oder leer lassen: ", optional=True)

        start_dt = datetime.combine(datum, start_time)
        end_dt = datetime.combine(datum, end_time)

        titel = f"Arbeit {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        beschreibung = ""
        if pause_start_time and pause_end_time:
            beschreibung = f"Pause: {pause_start_time.strftime('%H:%M')}-{pause_end_time.strftime('%H:%M')}"

        reminder1_dt = datetime.combine(datum - timedelta(days=1), datetime.strptime("15:00", "%H:%M").time()) - berlin_offset
        reminder2_dt = datetime.combine(datum, datetime.strptime("07:00", "%H:%M").time()) - berlin_offset

        start_dt_utc = start_dt - berlin_offset
        end_dt_utc = end_dt - berlin_offset

        uid = f"{datum.strftime('%Y%m%d')}-{start_time.strftime('%H%M')}-{end_time.strftime('%H%M')}@local"

        event = create_event(uid, start_dt_utc, end_dt_utc, titel, beschreibung, reminder1_dt, reminder2_dt)
        events.append(event)

        nochmal = input("Weitere Termine eingeben? (y für ja, Enter für nein): ").strip().lower()
        if nochmal != 'y':
            break

    ical_start = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Arbeit ICS Generator//DE\r\n"
    ical_end = "\r\nEND:VCALENDAR\r\n"

    ical_content = ical_start + "\r\n\r\n".join(events) + ical_end

    with open("arbeit.ics", "w", encoding="utf-8") as f:
        f.write(ical_content)

    print("\n✅ Alle Termine wurden in 'arbeit.ics' gespeichert. Importiere sie in Google Calendar.")

if __name__ == "__main__":
    main()
