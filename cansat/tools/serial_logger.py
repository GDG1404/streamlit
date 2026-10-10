r"""
CanSat 2027 — Serial logger voor de live-modus van het dashboard
=================================================================

Leest de USB-Serial van de Teensy en schrijft enkel de CSV-regels
(34 velden) naar een bestand dat het dashboard met --live volgt.
Opstarttekst ("BMP390 ... OK" enz.) wordt op het scherm getoond maar
niet in het bestand gezet, zodat het bestand ook als replay bruikbaar is.

Gebruik:
  pip install pyserial
  python serial_logger.py --list                      # poorten tonen
  python serial_logger.py COM5 C:\CanSat\cansat27_live.csv   # Windows
  python serial_logger.py /dev/ttyACM0 cansat27_live.csv  # Linux/macOS

Start daarna in een tweede venster (zelfde bestand):
  python dashboard_scherm1.py --live C:\CanSat\cansat27_live.csv

Stoppen met Ctrl+C. Sluit de Seriële Monitor van de Arduino IDE eerst:
maar één programma tegelijk kan de poort openen.
"""

import argparse
import os
import sys
import time

HEADER = ("millis,temp_C,press_hPa,alt_m,lat,lon,time_utc,"
          "gyro_x,gyro_y,gyro_z,lacc_x,lacc_y,lacc_z,grav_x,grav_y,grav_z,"
          "heading,roll,pitch,qw,qx,qy,qz,fft_peak_hz,fft_peak_amp,audio_rms,"
          "acc_peak_g,gps_course_deg,gps_speed_ms,"
          "vib_0_10_g,vib_10_30_g,vib_30_60_g,vib_60_120_g,vib_120_208_g")
N_FIELDS = len(HEADER.split(","))   # 34
OLD_FIELDS = (26, 27, 29)           # oudere versies van de sketch


def main():
    p = argparse.ArgumentParser(description="Teensy Serial → live CSV")
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
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        if "PermissionError" in str(e) or "Access is denied" in str(e) \
                or "Toegang geweigerd" in str(e):
            print(f"FOUT: {args.port} is bezet door een ander programma.\n"
                  "  - Sluit de Arduino IDE helemaal (niet alleen de Serial Monitor).\n"
                  "  - Staat serial_logger nog open in een ander venster? Stop het met Ctrl+C.\n"
                  "  - Lukt het nog niet: trek de USB-kabel uit, wacht 5 s, steek hem terug.")
        else:
            print(f"FOUT: kan {args.port} niet openen. Bestaat die poort? "
                  "Kijk met: py tools\\serial_logger.py --list")
        return 1
    with ser, open(args.out, "a", newline="", encoding="utf-8") as fh:
        if new_file:
            fh.write(HEADER + "\r\n")
        print(f"Lezen van {args.port} → {args.out}  (Ctrl+C om te stoppen)")
        n = 0
        warned_old = False
        warned_silent = False
        t_start = time.monotonic()
        try:
            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    if (n == 0 and not warned_silent
                            and time.monotonic() - t_start > 5):
                        warned_silent = True
                        print(f"\nLET OP: al 5 s niets ontvangen op {args.port}. "
                              "Is dit wel de Teensy? Kijk met --list: de Teensy "
                              "is meestal 'USB Serial Device'. Knippert het "
                              "lampje op de Teensy?")
                    continue
                parts = line.split(",")
                if len(parts) == N_FIELDS and parts[0] != "millis":
                    fh.write(line + "\r\n")
                    fh.flush()
                    n += 1
                    print(f"\r{n} rijen gelogd", end="", flush=True)
                elif len(parts) in OLD_FIELDS:
                    if not warned_old:
                        warned_old = True
                        print(f"\nLET OP: de Teensy stuurt {len(parts)} kolommen "
                              f"in plaats van {N_FIELDS}. Dat is een oude versie "
                              "van de sketch.\nUpload sensortest_fft.ino opnieuw. "
                              "Deze regels worden NIET opgeslagen.")
                elif parts[0] != "millis":
                    print(f"\n[Teensy] {line}")
        except KeyboardInterrupt:
            print(f"\nGestopt: {n} rijen in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
