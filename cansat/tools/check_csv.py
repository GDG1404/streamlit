"""
CanSat 2027 — CSV-controle
==========================

Controleert of een CSV van de Teensy (bv. test_000.csv van de SD-kaart)
door het dashboard gelezen kan worden, en vat de metingen samen.

Gebruik:
  python check_csv.py test_000.csv

Exitcode 0 = in orde, 1 = fouten gevonden.
"""

import argparse
import sys

COLUMNS = [  # identiek aan CSV_COLUMNS in dashboard_scherm1.py
    "millis", "temp_C", "press_hPa", "alt_m", "lat", "lon", "time_utc",
    "gyro_x", "gyro_y", "gyro_z", "lacc_x", "lacc_y", "lacc_z",
    "grav_x", "grav_y", "grav_z", "heading", "roll", "pitch",
    "qw", "qx", "qy", "qz", "fft_peak_hz", "fft_peak_amp", "audio_rms",
]
NO_FIX_TIME = "00:00:00"
MAX_ERRORS_SHOWN = 10


def main():
    p = argparse.ArgumentParser(description="Controleer een CanSat-CSV.")
    p.add_argument("csv")
    args = p.parse_args()

    with open(args.csv, encoding="utf-8", newline="") as fh:
        lines = [l.strip() for l in fh.read().split("\n")]
    lines = [l for l in lines if l]
    if not lines:
        print("FOUT: bestand is leeg")
        return 1

    errors = []
    header = lines[0].split(",")
    if header != COLUMNS:
        missing = [c for c in COLUMNS if c not in header]
        extra = [c for c in header if c not in COLUMNS]
        errors.append(f"header klopt niet (ontbreekt: {missing}, extra: {extra}, "
                      f"{len(header)} i.p.v. {len(COLUMNS)} kolommen)")

    rows = []
    for n, line in enumerate(lines[1:], start=2):
        parts = line.split(",")
        if parts[0] == "millis":
            errors.append(f"regel {n}: herhaalde header (herstart van de Teensy?)")
            continue
        if len(parts) != len(COLUMNS):
            errors.append(f"regel {n}: {len(parts)} velden i.p.v. {len(COLUMNS)}")
            continue
        row = {}
        try:
            for k, v in zip(COLUMNS, parts):
                row[k] = v if k == "time_utc" else float(v)
        except ValueError:
            errors.append(f"regel {n}: geen getal in kolom '{k}': {v!r}")
            continue
        if rows and row["millis"] <= rows[-1]["millis"]:
            errors.append(f"regel {n}: millis loopt niet op "
                          f"({rows[-1]['millis']:.0f} → {row['millis']:.0f})")
        rows.append(row)

    print(f"Bestand : {args.csv}")
    print(f"Rijen   : {len(rows)} geldig van {len(lines) - 1}")
    if len(rows) >= 2:
        dur = (rows[-1]["millis"] - rows[0]["millis"]) / 1000
        print(f"Duur    : {dur:.0f} s  →  {(len(rows) - 1) / dur:.2f} rijen/s"
              if dur > 0 else "Duur    : 0 s")
        fix = [r for r in rows if r["time_utc"] != NO_FIX_TIME]
        print(f"GPS-fix : {len(fix)}/{len(rows)} rijen"
              + (f", eerste fix na {(fix[0]['millis'] - rows[0]['millis']) / 1000:.0f} s"
                 if fix else "  (geen fix: buiten testen, antenne vrij zicht)"))
        print("\nKolom          min        max      (controleer of dit logisch is)")
        for k in ("temp_C", "press_hPa", "alt_m", "lacc_z", "gyro_z",
                  "grav_z", "fft_peak_hz", "fft_peak_amp", "audio_rms"):
            vals = [r[k] for r in rows]
            print(f"  {k:<12} {min(vals):>9.3f}  {max(vals):>9.3f}")
        flat = [k for k in COLUMNS if k not in ("millis", "time_utc")
                and len({r[k] for r in rows}) == 1]
        if flat:
            print(f"\nLET OP: deze kolommen veranderen nooit (sensor niet "
                  f"gevonden of niet aangesloten?): {', '.join(flat)}")

    if errors:
        print(f"\n{len(errors)} FOUT(EN):")
        for e in errors[:MAX_ERRORS_SHOWN]:
            print(f"  - {e}")
        if len(errors) > MAX_ERRORS_SHOWN:
            print(f"  ... en nog {len(errors) - MAX_ERRORS_SHOWN}")
        return 1
    print("\nOK: het dashboard kan dit bestand lezen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
