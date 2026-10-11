r"""
CanSat 2027 — Meting starten met één knop (handig in Thonny)
=============================================================

Pas hieronder de twee instellingen aan en druk op Run (F5).
Dit programma doet dan alles in één keer:

  1. het zoekt de Teensy (of gebruikt de COM-poort die je opgeeft),
  2. het start de logger: de metingen gaan naar C:\CanSat\metingen\<naam>.csv,
  3. het opent scherm 1 en scherm 2 met LIVE data uit datzelfde bestand.

Stoppen: klik in Thonny op de rode Stop-knop (of Ctrl+C).
De dashboards blijven openstaan; sluit ze zelf als je klaar bent.

Vooraf: de sketch staat op de Teensy en de Arduino IDE is helemaal dicht.
"""

# ═══════════════ PAS DIT AAN ═══════════════
COM_POORT = "auto"     # "auto" = zelf de Teensy zoeken, of bv. "COM9"
BESTAND   = "test_01"  # naam van je meting (zonder .csv)
SCHERM_2  = True       # False = alleen scherm 1 (sneller op een trage laptop)
# ═══════════════════════════════════════════

import os
import subprocess
import sys
import threading
import time

MAP = os.path.dirname(os.path.abspath(__file__))       # C:\CanSat
METINGEN = os.path.join(MAP, "metingen")
TEENSY_VID = 0x16C0                                     # USB-code van PJRC


def zoek_teensy(list_ports):
    """Geeft de COM-poort van de Teensy, of None als het niet lukt."""
    poorten = list(list_ports.comports())
    teensys = [p for p in poorten if p.vid == TEENSY_VID]
    if len(teensys) == 1:
        return teensys[0].device
    if not teensys:
        print("FOUT: geen Teensy gevonden.")
        print("  - Zit de USB-kabel goed? Is het een datakabel (geen laadkabel)?")
    else:
        print("FOUT: meer dan één Teensy gevonden.")
    print("  Gevonden poorten:")
    for p in poorten:
        print(f"    {p.device:<8} {p.description}")
    print('  Vul de juiste poort zelf in bovenaan, bv. COM_POORT = "COM9"')
    return None


def vrije_naam(naam):
    """test_01 bestaat al? Dan test_01_2, test_01_3, ... (nooit overschrijven)."""
    naam = naam.strip()
    if naam.lower().endswith(".csv"):
        naam = naam[:-4]
    pad = os.path.join(METINGEN, naam + ".csv")
    i = 2
    while os.path.exists(pad):
        pad = os.path.join(METINGEN, f"{naam}_{i}.csv")
        i += 1
    return pad


def start_dashboards(csv, logger_klaar):
    """Wacht tot de logger het bestand gemaakt heeft, open dan de schermen."""
    for _ in range(100):                    # max. 10 s wachten
        if logger_klaar.is_set():           # logger is al gestopt (fout)
            return
        if os.path.exists(csv):
            break
        time.sleep(0.1)
    else:
        return
    schermen = ["dashboard_scherm1.py"] + (["dashboard_scherm2.py"] if SCHERM_2 else [])
    gestart = []
    for scherm in schermen:
        # fouten van een dashboard komen in een logbestand naast de meting
        log = csv[:-4] + "_" + scherm.replace(".py", ".log")
        proc = subprocess.Popen([sys.executable, os.path.join(MAP, "dashboard", scherm),
                                 "--live", csv],
                                cwd=os.path.join(MAP, "dashboard"),
                                stdout=open(log, "w"), stderr=subprocess.STDOUT)
        gestart.append((scherm, proc, log))
    print(f"Dashboards geopend ({len(schermen)}). Het kan even duren voor ze verschijnen.\n")

    # Een dashboard dat meteen crasht, zie je anders niet: meld het hier.
    time.sleep(15)
    for scherm, proc, log in gestart:
        if proc.poll() not in (None, 0):
            print(f"\nLET OP: {scherm} is gestopt met een fout. "
                  f"Open dit bestand om te zien waarom:\n  {log}\n")


def main():
    try:
        from serial.tools import list_ports
        import matplotlib, numpy, PIL  # noqa: F401  (nodig voor de dashboards)
    except ImportError as e:
        print(f"FOUT: het pakket '{e.name}' ontbreekt.")
        print("  In Thonny: Tools → Manage packages → zoek en installeer:")
        print("  pyserial, matplotlib, numpy en pillow")
        return 1

    poort = COM_POORT.strip()
    if poort.lower() == "auto":
        poort = zoek_teensy(list_ports)
        if poort is None:
            return 1
        print(f"Teensy gevonden op {poort}")

    os.makedirs(METINGEN, exist_ok=True)
    csv = vrije_naam(BESTAND)
    print(f"Meting wordt bewaard in: {csv}")
    print(f"Later opnieuw bekijken: dashboard_scherm1.py --replay {csv}\n")

    # De logger draait hier in dit programma (zo zie je hem in Thonny);
    # de dashboards starten apart zodra het bestand bestaat.
    sys.path.insert(0, os.path.join(MAP, "tools"))
    import serial_logger
    logger_klaar = threading.Event()
    threading.Thread(target=start_dashboards, args=(csv, logger_klaar),
                     daemon=True).start()
    sys.argv = ["serial_logger.py", poort, csv]
    try:
        return serial_logger.main()
    finally:
        logger_klaar.set()


if __name__ == "__main__":
    sys.exit(main())
