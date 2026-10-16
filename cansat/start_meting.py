r"""
CanSat 2027 — Meting starten met één knop (handig in Thonny)
=============================================================

Druk op Run (F5). Het programma stelt drie vragen:

  1. Op welke poort zit de Teensy (USB-kabel) of de Pico-ontvanger (radio)?
  2. Hoe heet je meting?
  3. Welk dashboard wil je zien?

Daarna start de logger (de metingen gaan naar de map 'metingen' naast dit
bestand, bv. metingen\test_01.csv) en opent het de dashboards met LIVE
data uit datzelfde bestand.

Op elke vraag mag je gewoon op Enter drukken: dan neemt het programma
het voorstel tussen [haakjes].

Stoppen: klik in Thonny op de rode Stop-knop (of Ctrl+C).
Staan de dashboards daarna nog open? Sluit ze dan zelf.

Vooraf:
  - Teensy: de sketch staat al op de Teensy. Sluit alle vensters van de
    Arduino IDE (kruisje rechtsboven). Alleen de Serial Monitor sluiten
    is niet genoeg: dan blijft de USB-poort bezet.
  - Pico-ontvanger: main.py staat op de Pico. Thonny mag niet met de Pico
    verbonden zijn: kies rechtsonder in Thonny 'Local Python 3'. Trek
    daarna de USB-kabel van de Pico uit en steek hem terug.

Dit bestand hoort in de map CanSat, naast de mappen 'dashboard' en 'tools'.
"""

import os
import re
import subprocess
import sys
import threading
import time

MAP = os.path.dirname(os.path.abspath(__file__))       # C:\CanSat
METINGEN = os.path.join(MAP, "metingen")
TEENSY_VID = 0x16C0                                     # USB-code van PJRC
PICO_VID = 0x2E8A                                       # USB-code van Raspberry Pi
DASHBOARDS = {"1": ["dashboard_scherm1.py"],
              "2": ["dashboard_scherm2.py"],
              "3": ["dashboard_scherm1.py", "dashboard_scherm2.py"],
              "0": []}


def vraag(tekst, voorstel=""):
    """input() met een voorstel: Enter = het voorstel nemen."""
    extra = f" [{voorstel}]" if voorstel else ""
    antwoord = input(f"{tekst}{extra}: ").strip()
    return antwoord or voorstel


# ── vraag 1: de poort ──
def kies_poort(list_ports):
    while True:
        poorten = sorted(list_ports.comports(), key=lambda p: p.device)
        teensys = [p.device for p in poorten if p.vid == TEENSY_VID]
        picos = [p.device for p in poorten if p.vid == PICO_VID]
        print("\n1) Op welke poort zit de Teensy (USB-kabel) of de Pico (radio)?")
        if not poorten:
            print("   Geen enkele poort gevonden. Zit de USB-kabel goed?")
            print("   Is het een datakabel (geen laadkabel)?")
        for i, p in enumerate(poorten, 1):
            merk = ("   ← Teensy" if p.device in teensys else
                    "   ← Pico (ontvanger)" if p.device in picos else "")
            print(f"   {i}. {p.device:<8} {p.description}{merk}")
        print("   Typ het nummer uit de lijst, of de naam (bv. COM9).")
        print("   Typ 'r' om de lijst opnieuw te zoeken (bv. na het insteken).")
        # één Pico: die (radiotest); anders één Teensy: die (USB-test)
        voorstel = (picos[0] if len(picos) == 1 else
                    teensys[0] if len(teensys) == 1 else "")
        antwoord = vraag("   Poort", voorstel)
        if antwoord.lower() == "r" or not antwoord:
            continue
        if antwoord.isdigit():
            nr = int(antwoord)
            if 1 <= nr <= len(poorten):
                return poorten[nr - 1].device
            print(f"   Nummer {nr} staat niet in de lijst.")
            continue
        if antwoord.upper().startswith("COM"):
            antwoord = antwoord.upper()
        return antwoord


# ── vraag 2: de naam ──
def volgende_testnaam():
    """test_01, test_02, ...: het eerste nummer dat nog vrij is."""
    i = 1
    while os.path.exists(os.path.join(METINGEN, f"test_{i:02d}.csv")):
        i += 1
    return f"test_{i:02d}"


def kies_naam():
    print("\n2) Hoe heet je meting? Bv. schudtest, buiten_gps, test_03")
    while True:
        naam = vraag("   Naam", volgende_testnaam())
        if naam.lower().endswith(".csv"):
            naam = naam[:-4]
        # spaties en vreemde tekens worden _ (veilig als bestandsnaam)
        naam = re.sub(r"[^A-Za-z0-9_-]+", "_", naam).strip("_")
        if not naam:
            print("   Gebruik letters, cijfers, - of _.")
            continue
        pad = os.path.join(METINGEN, naam + ".csv")
        if os.path.exists(pad):
            print(f"   {naam}.csv bestaat al. Kies een andere naam "
                  "(een oude meting overschrijven we nooit).")
            continue
        return pad


# ── vraag 3: de dashboards ──
def kies_dashboards():
    print("\n3) Welk dashboard wil je zien?")
    print("   1 = scherm 1 (grafieken)")
    print("   2 = scherm 2 (3D-baan, kaart en oriëntatie)")
    print("   3 = allebei")
    print("   0 = geen (alleen opslaan)")
    while True:
        keuze = vraag("   Keuze", "3")
        if keuze in DASHBOARDS:
            return DASHBOARDS[keuze]
        print("   Typ 0, 1, 2 of 3.")


def start_dashboards(csv, schermen, logger_klaar):
    """Wacht tot de logger het bestand gemaakt heeft, open dan de schermen."""
    for _ in range(100):                    # max. 10 s wachten
        if logger_klaar.is_set():           # logger is al gestopt (fout)
            return
        if os.path.exists(csv):
            break
        time.sleep(0.1)
    else:
        return
    # Windows: geen leeg zwart venster per dashboard. Zo sluit Ctrl+C in
    # dit venster de dashboards ook niet mee af.
    vlag = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    gestart = []
    for scherm in schermen:
        # fouten van een dashboard komen in een logbestand naast de meting
        log = csv[:-4] + "_" + scherm.replace(".py", ".log")
        proc = subprocess.Popen([sys.executable, os.path.join(MAP, "dashboard", scherm),
                                 "--live", csv],
                                cwd=os.path.join(MAP, "dashboard"),
                                stdout=open(log, "w"), stderr=subprocess.STDOUT,
                                creationflags=vlag)
        gestart.append((scherm, proc, log))
    print(f"Dashboards geopend ({len(schermen)}). Het kan even duren voor ze verschijnen.\n")

    # Een dashboard dat meteen crasht, zie je anders niet: meld het hier.
    time.sleep(15)
    for scherm, proc, log in gestart:
        if proc.poll() not in (None, 0):
            print(f"\nLET OP: {scherm} is gestopt met een fout. "
                  f"Open dit bestand om te zien waarom:\n  {log}\n")


def main():
    if not (os.path.isfile(os.path.join(MAP, "tools", "serial_logger.py"))
            and os.path.isdir(os.path.join(MAP, "dashboard"))):
        print("FOUT: start_meting.py staat in de verkeerde map.")
        print(f"  Nu staat het in: {MAP}")
        print("  Zet het in de map CanSat, naast de mappen 'dashboard' en 'tools'.")
        return 1
    try:
        from serial.tools import list_ports
        import matplotlib, numpy, PIL  # noqa: F401  (nodig voor de dashboards)
    except ImportError as e:
        naam = {"serial": "pyserial", "PIL": "pillow"}.get(e.name, e.name)
        print(f"FOUT: het pakket '{naam}' ontbreekt.")
        print("  In Thonny: Tools → Manage packages → zoek en installeer:")
        print("  pyserial, matplotlib, numpy en pillow")
        print("  In de opdrachtprompt: py -m pip install pyserial matplotlib numpy pillow")
        return 1

    print("CanSat 2027 — meting starten")
    print("Druk op Enter om het voorstel tussen [haakjes] te nemen.")
    os.makedirs(METINGEN, exist_ok=True)
    try:
        poort = kies_poort(list_ports)
        csv = kies_naam()
        schermen = kies_dashboards()
    except (KeyboardInterrupt, EOFError):
        print("\nGestopt. Er is niets opgeslagen.")
        return 1

    print(f"\nPoort     : {poort}")
    print(f"Bestand   : {csv}")
    print(f"Dashboard : {', '.join(schermen) if schermen else 'geen'}")
    print(f"Later opnieuw bekijken: dashboard_scherm1.py --replay {csv}\n")

    # De logger draait hier in dit programma (zo zie je hem in Thonny);
    # de dashboards starten apart zodra het bestand bestaat.
    sys.path.insert(0, os.path.join(MAP, "tools"))
    import serial_logger
    logger_klaar = threading.Event()
    if schermen:
        threading.Thread(target=start_dashboards,
                         args=(csv, schermen, logger_klaar), daemon=True).start()
    sys.argv = ["serial_logger.py", poort, csv]
    try:
        return serial_logger.main()
    finally:
        logger_klaar.set()


if __name__ == "__main__":
    code = main()
    # Dubbelgeklikt in de Verkenner? Dan sluit Windows het venster meteen,
    # ook na een foutmelding. Wacht dus op Enter. (In Thonny niet nodig.)
    if ("thonny" not in sys.modules and sys.stdin is not None
            and sys.stdin.isatty()):
        try:
            input("\nDruk op Enter om dit venster te sluiten.")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(code)
