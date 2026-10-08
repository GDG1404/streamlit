"""
CanSat 2027 — test-CSV generator (zonder hardware)
===================================================

Schrijft een CSV in EXACT hetzelfde formaat als sensortest_fft.ino
(zelfde kolommen, decimalen en CRLF-regeleinden), voor een bureautest
van 2 minuten:

   0–25 s  geen GPS-fix (sketch logt dan placeholder-coördinaten)
     35 s  tik op de tafel: korte schok (~7 g in acc_peak_g)
  40–55 s  CanSat met de hand geschud (trilling ~4–5 Hz, ~0,6 g)
     60 s  handklap (piek in audio_rms)
  70–90 s  trap op gelopen (~6 m hoger)

Gebruik:
  python gen_test_csv.py test_000.csv            # in één keer (replay)
  python gen_test_csv.py cansat27_live.csv --live  # 1 regel/s (live)
"""

import argparse
import math
import os
import random
import time

COLUMNS = [  # identiek aan CSV_HEADER in sensortest_fft.ino
    "millis", "temp_C", "press_hPa", "alt_m", "lat", "lon", "time_utc",
    "gyro_x", "gyro_y", "gyro_z", "lacc_x", "lacc_y", "lacc_z",
    "grav_x", "grav_y", "grav_z", "heading", "roll", "pitch",
    "qw", "qx", "qy", "qz", "fft_peak_hz", "fft_peak_amp", "audio_rms",
    "acc_peak_g",
]
DURATION_S = 120


def make_row(t, t_ms):
    """Eén logregel zoals writeCSV() in de sketch hem opbouwt."""
    shake = 40 <= t < 55
    alt = 612.3 + random.gauss(0, 0.08) + (min(t - 70, 20) * 0.3 if t >= 70 else 0)
    press = 1014.0 * (1 - alt / 44330.0) ** 5.255
    temp = 21.4 + random.gauss(0, 0.02)
    if t >= 25:  # GPS-fix
        lat = 50.846712 + random.gauss(0, 3e-6)
        lon = 4.352417 + random.gauss(0, 3e-6)
        s = t + 25
        utc = f"09:{12 + s // 60:02d}:{s % 60:02d}"
    else:        # placeholder van de sketch
        lat, lon, utc = 50.457303, 6.221376, "00:00:00"
    a = 6.0 if shake else 0.05
    lacc = [random.gauss(0, a) for _ in range(3)]
    gyro = [random.gauss(0, 60 if shake else 0.2) for _ in range(3)]
    heading = (123.4 + (random.gauss(0, 30) if shake else 0)) % 360
    roll = random.gauss(0, 15 if shake else 0.1)
    pitch = random.gauss(0, 15 if shake else 0.1)
    h2 = math.radians(heading) / 2
    tilt = math.radians(roll) / 2   # kleine kanteling → qx ≠ 0
    q = (math.cos(h2) * math.cos(tilt), math.sin(tilt) * 0.5,
         math.sin(tilt) * 0.3, math.sin(h2) * math.cos(tilt))
    grav = (0.12 + random.gauss(0, 0.01), -0.05 + random.gauss(0, 0.01),
            9.80 + random.gauss(0, 0.005))
    if shake:
        fhz, famp = 4.5 + random.gauss(0, 0.6), 0.6 + random.gauss(0, 0.1)
    else:
        fhz, famp = random.uniform(1, 200), 0.002 + abs(random.gauss(0, 0.001))
    audio = 0.0031 + abs(random.gauss(0, 0.0004)) + (0.21 if t == 60 else 0)
    # grootste versnelling in deze seconde (incl. zwaartekracht, rust ≈ 1 g)
    if t == 35:
        peak = 7.2 + random.gauss(0, 0.3)            # korte schok
    elif shake:
        peak = 2.6 + abs(random.gauss(0, 0.5))
    else:
        peak = 1.0 + abs(random.gauss(0, 0.01))

    def f(v, n):
        return f"{v:.{n}f}"

    return ",".join([
        str(t_ms), f(temp, 2), f(press, 2), f(alt, 2), f(lat, 6), f(lon, 6), utc,
        *(f(g, 3) for g in gyro), *(f(x, 3) for x in lacc),
        *(f(g, 3) for g in grav),
        f(heading, 2), f(roll, 2), f(pitch, 2), *(f(x, 4) for x in q),
        f(fhz, 1), f(famp, 3), f(audio, 4), f(peak, 2),
    ])


def main():
    p = argparse.ArgumentParser(description="Maak een test-CSV zoals de Teensy.")
    p.add_argument("out", help="uitvoerbestand (.csv)")
    p.add_argument("--live", action="store_true",
                   help="schrijf 1 regel per seconde (test voor --live)")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    random.seed(args.seed)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(COLUMNS) + "\r\n")   # Arduino println = CRLF
        t_ms = 5212                             # eerste regel na setup()
        for t in range(DURATION_S):
            fh.write(make_row(t, t_ms) + "\r\n")
            t_ms += 1000 + random.choice([0, 0, 1])
            if args.live:
                fh.flush()
                print(f"\r{t + 1}/{DURATION_S} s", end="", flush=True)
                time.sleep(1.0)
    print(f"\n{args.out}: {DURATION_S} regels, {len(COLUMNS)} kolommen")


if __name__ == "__main__":
    main()
