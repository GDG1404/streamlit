r"""
CanSat 2027 — Serial logger voor de live-modus van het dashboard
=================================================================

Leest een USB-poort en schrijft de metingen naar een bestand dat het
dashboard met --live volgt. Twee soorten bronnen:

  - de Teensy aan de USB-kabel: CSV-regels met 34 velden;
  - de Pico-ontvanger (radio): per pakket de 13 waarden van de CanSat,
    gevolgd door RSSI en SNR. Kolommen die niet in het radiopakket zitten
    (gyroscoop, trillingsbanden, ...) worden 'nan' (= geen gegevens).

Opstarttekst ("BMP390 ... OK", "# Radio OK" enz.) wordt op het scherm
getoond maar niet in het bestand gezet, zodat het bestand ook als replay
bruikbaar is.

Gebruik:
  pip install pyserial
  python serial_logger.py --list                      # poorten tonen
  python serial_logger.py COM5 C:\CanSat\cansat27_live.csv   # Windows
  python serial_logger.py /dev/ttyACM0 cansat27_live.csv  # Linux/macOS

Start daarna in een tweede venster (zelfde bestand):
  python dashboard_scherm1.py --live C:\CanSat\cansat27_live.csv

Stoppen met Ctrl+C. Sluit de Seriële Monitor van de Arduino IDE en Thonny
eerst: maar één programma tegelijk kan de poort openen.
"""

import argparse
import collections
import os
import sys
import time

CSV_COLUMNS = ("millis,temp_C,press_hPa,alt_m,lat,lon,time_utc,"
               "gyro_x,gyro_y,gyro_z,lacc_x,lacc_y,lacc_z,grav_x,grav_y,grav_z,"
               "heading,roll,pitch,qw,qx,qy,qz,fft_peak_hz,fft_peak_amp,audio_rms,"
               "acc_peak_g,gps_course_deg,gps_speed_ms,"
               "vib_0_10_g,vib_10_30_g,vib_30_60_g,vib_60_120_g,"
               "vib_120_208_g").split(",")
N_FIELDS = len(CSV_COLUMNS)                 # 34: een regel van de Teensy
OLD_FIELDS = (26, 27, 29)                   # oudere versies van de sketch
# Nieuwe bestanden: de 34 kolommen + de radiokwaliteit (nan bij USB)
COLUMNS = CSV_COLUMNS + ["rssi", "snr"]
HEADER = ",".join(COLUMNS)

# Het LoRa-pakket van de vluchtcode (Cansat2027_teensy.ino, sendAndLog)
RADIO_FIELDS = ["temp_C", "press_hPa", "alt_m", "lat", "lon",
                "lacc_x", "lacc_y", "lacc_z", "heading", "roll", "pitch",
                "fft_peak_hz", "audio_rms"]
RADIO_LENGTHS = (len(RADIO_FIELDS), len(RADIO_FIELDS) + 2)   # 13, of + RSSI/SNR
# Zonder GPS-fix stuurt de vluchtcode deze plaatshouder (Elsenborn).
# Het radiopakket heeft geen GPS-tijd: die vullen we in bij een echte fix.
NO_FIX_LATLON = (50.4573, 6.22138)
NO_FIX_TIME = "00:00:00"
PACKET_INTERVAL_S = 1.0                     # de CanSat zendt 1 pakket/s

TEENSY_VID = 0x16C0
PICO_VID = 0x2E8A


def has_fix(lat, lon):
    if lat == 0 and lon == 0:
        return False
    return not (abs(lat - NO_FIX_LATLON[0]) < 1e-5
                and abs(lon - NO_FIX_LATLON[1]) < 1e-5)


def numbers(parts):
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def radio_row(parts, millis):
    """13 of 15 velden van de ontvanger → rij (kolom → tekst)."""
    row = dict(zip(RADIO_FIELDS, (p.strip() for p in parts)))
    lat, lon = float(row["lat"]), float(row["lon"])
    row["millis"] = str(millis)             # aankomsttijd op de laptop
    row["time_utc"] = (time.strftime("%H:%M:%S", time.gmtime())
                       if has_fix(lat, lon) else NO_FIX_TIME)
    if len(parts) == RADIO_LENGTHS[1]:
        row["rssi"], row["snr"] = parts[-2].strip(), parts[-1].strip()
    return row


def csv_line(row, cols):
    return ",".join(row.get(c, "nan") for c in cols)


def existing_header(path):
    """Kolommen van een bestaand bestand (aanvullen), of None."""
    try:
        with open(path, encoding="utf-8") as fh:
            first = fh.readline().strip()
    except OSError:
        return None
    return first.split(",") if first.startswith("millis,") else None


def port_label(port, list_ports):
    for p in list_ports.comports():
        if p.device == port:
            if p.vid == PICO_VID:
                return "Pico"
            if p.vid == TEENSY_VID:
                return "Teensy"
    return "USB"


class LinkStats:
    """Hoe goed komt de radio door? Voor de tabel van de afstandstest."""

    def __init__(self):
        self.times = collections.deque()    # aankomsttijden, laatste minuut
        self.n = 0
        self.first = self.last = None
        self.rssi = []
        self.snr = None
        self.bad = 0

    def add(self, t, rssi, snr):
        self.n += 1
        self.first = t if self.first is None else self.first
        self.last = t
        self.times.append(t)
        while self.times and t - self.times[0] > 60:
            self.times.popleft()
        if rssi is not None and rssi == rssi:
            self.rssi.append(rssi)
        self.snr = snr

    def last_minute(self):
        """(ontvangen, verwacht) in de laatste minuut (of sinds de start)."""
        span = min(60.0, self.last - self.first)
        expected = int(round(span / PACKET_INTERVAL_S)) + 1
        return len(self.times), max(expected, len(self.times))

    def status(self):
        got, exp = self.last_minute()
        s = f"\r{self.n} pakketten"
        if self.rssi:
            s += f" · RSSI {self.rssi[-1]:.0f} dBm"
        if self.snr is not None and self.snr == self.snr:
            s += f" · SNR {self.snr:.1f} dB"
        s += f" · laatste minuut {got}/{exp} ({100 * got / exp:.0f}%)"
        if self.bad:
            s += f" · {self.bad} beschadigd"
        return s + "   "

    def summary(self):
        if not self.n:
            return "Radio: geen enkel pakket ontvangen."
        dur = self.last - self.first
        exp = int(round(dur / PACKET_INTERVAL_S)) + 1
        s = (f"Radio: {self.n} pakketten in {dur:.0f} s → "
             f"{100 * self.n / max(exp, self.n):.0f}% van wat de CanSat zond")
        if self.rssi:
            s += (f" · RSSI gemiddeld {sum(self.rssi) / len(self.rssi):.0f} dBm"
                  f" (zwakste {min(self.rssi):.0f})")
        if self.bad:
            s += f" · {self.bad} beschadigd"
        return s


def main():
    p = argparse.ArgumentParser(description="Teensy of Pico (USB) → live CSV")
    p.add_argument("port", nargs="?", help="bv. COM5 of /dev/ttyACM0")
    p.add_argument("out", nargs="?", default="cansat27_live.csv")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--list", action="store_true", help="toon seriële poorten")
    args = p.parse_args()

    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        print("pyserial ontbreekt: py -m pip install pyserial")
        return 1

    if args.list or not args.port:
        for port in list_ports.comports():
            print(f"{port.device:<15} {port.description}")
        if not args.port:
            print("\nGeef een poort en een bestand op, bv.:\n"
                  "  py tools\\serial_logger.py COM5 metingen\\test_01.csv")
        return 0

    # De header zelf schrijven: de Teensy print hem maar één keer bij het
    # opstarten, en die is vaak al voorbij als dit script start.
    folder = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(folder, exist_ok=True)              # bv. C:\CanSat
    new_file = not os.path.exists(args.out) or os.path.getsize(args.out) == 0
    cols = COLUMNS if new_file else (existing_header(args.out) or COLUMNS)
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        if "PermissionError" in str(e) or "Access is denied" in str(e) \
                or "Toegang geweigerd" in str(e):
            print(f"FOUT: {args.port} is bezet door een ander programma.\n"
                  "  - Sluit de Arduino IDE helemaal (niet alleen de Serial Monitor).\n"
                  "  - Pico: sluit Thonny helemaal.\n"
                  "  - Staat serial_logger nog open in een ander venster? Stop het met Ctrl+C.\n"
                  "  - Lukt het nog niet: trek de USB-kabel uit, wacht 5 s, steek hem terug.")
        else:
            print(f"FOUT: kan {args.port} niet openen. Bestaat die poort? "
                  "Kijk met: py tools\\serial_logger.py --list")
        return 1
    label = port_label(args.port, list_ports)

    def reconnect(old):
        """De USB-kabel is los, of de Pico of Teensy herstartte: wachten tot de
        poort terug is en dan verder schrijven in hetzelfde bestand. Vroeger
        stopte de meting hier met een foutmelding."""
        try:
            old.close()
        except Exception:
            pass
        print(f"\nLET OP: de verbinding op {args.port} ({label}) is weg. Zit de "
              "USB-kabel nog goed?\n  Steek hem terug in: ik probeer elke 2 s "
              "opnieuw. (Stoppen: Ctrl+C)")
        while True:
            time.sleep(2)
            try:
                new = serial.Serial(args.port, args.baud, timeout=1)
            except (serial.SerialException, OSError):
                continue
            print(f"Weer verbonden met {args.port}. De meting gaat verder in "
                  "hetzelfde bestand.")
            return new

    with open(args.out, "a", newline="", encoding="utf-8") as fh:
        if new_file:
            fh.write(HEADER + "\r\n")
        print(f"Lezen van {args.port} ({label}) → {args.out}  (Ctrl+C om te stoppen)")
        n = 0
        stats = LinkStats()
        warned_old = False
        warned_silent = False
        t_start = time.monotonic()
        try:
            while True:
                try:
                    raw = ser.readline()
                except (serial.SerialException, OSError):
                    ser = reconnect(ser)
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    if (n == 0 and not warned_silent
                            and time.monotonic() - t_start > 5):
                        warned_silent = True
                        print(f"\nLET OP: al 5 s niets ontvangen op {args.port}. "
                              "Is dit wel de juiste poort? Kijk met --list.\n"
                              "  - Teensy: meestal 'USB Serial Device'. Knippert "
                              "het lampje op de Teensy?\n"
                              "  - Pico-ontvanger: flitst het lampje om de 2 s? "
                              "Dan draait main.py. Zo niet: USB-kabel uit en in.")
                    continue
                if line.startswith("#"):            # melding van de ontvanger
                    msg = line.lstrip("#").strip()
                    if msg.startswith("Beschadigd"):
                        stats.bad += 1
                    print(f"\n[{label}] {msg}")
                    continue
                parts = line.split(",")
                vals = numbers(parts) if len(parts) in RADIO_LENGTHS else None
                if len(parts) == N_FIELDS and parts[0] != "millis":
                    row = dict(zip(CSV_COLUMNS, parts))
                    fh.write(csv_line(row, cols) + "\r\n")
                    fh.flush()
                    n += 1
                    print(f"\r{n} rijen gelogd", end="", flush=True)
                elif vals is not None:
                    now = time.monotonic()
                    row = radio_row(parts, int((now - t_start) * 1000))
                    fh.write(csv_line(row, cols) + "\r\n")
                    fh.flush()
                    n += 1
                    rssi, snr = (vals[-2], vals[-1]) if len(vals) == 15 else (None, None)
                    stats.add(now, rssi, snr)
                    print(stats.status(), end="", flush=True)
                elif len(parts) in OLD_FIELDS:
                    if not warned_old:
                        warned_old = True
                        print(f"\nLET OP: de Teensy stuurt {len(parts)} kolommen "
                              f"in plaats van {N_FIELDS}. Dat is een oude versie "
                              "van de sketch.\nUpload sensortest_fft.ino opnieuw. "
                              "Deze regels worden NIET opgeslagen.")
                elif parts[0] != "millis":
                    print(f"\n[{label}] {line}")
        except KeyboardInterrupt:
            print(f"\nGestopt: {n} rijen in {args.out}")
            if stats.n or label == "Pico":
                print(stats.summary())
        finally:
            ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
