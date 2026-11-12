"""Tests the flight code (vluchtcode/Cansat2027_teensy) on the computer.

The sketch is compiled with mock libraries (folder mock/) and runs in a
simulated world: a virtual clock, I2C traffic that takes time, a BMP390 that
returns the previous conversion (as Adafruit_BMP3XX does), an LSM6DSO with
its own clock and FIFO, a GPS, a radio and an SD card. The real arduinoFFT
library does the FFT. Every scenario has a known truth (a 37 Hz vibration of
0.5 g, a flight to 955 m, a lost GPS fix ...) and the checks compare what the
sketch logged with that truth.

  python run_tests.py <path to arduinoFFT/src> [scenario ...]
  python run_tests.py <path to arduinoFFT/src> --sketch other.ino [scenario ...]

It does not replace a test on the real hardware: the mock sensors behave as
the datasheets and the library sources say, not as measured.
"""
import csv
import os
import subprocess
import sys

import build as builder

here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.dirname(os.path.dirname(here))
args = sys.argv[1:]
if not args:
    sys.exit(__doc__)
fft_src = args.pop(0)
sketch = os.path.join(repo, "vluchtcode", "Cansat2027_teensy", "Cansat2027_teensy.ino")
if "--sketch" in args:
    i = args.index("--sketch")
    sketch = args[i + 1]
    del args[i:i + 2]
only = args
which = "sketch"
if builder.build(sketch, which, fft_src) != 0:
    sys.exit("the sketch does not compile")
DUR = {"slowbus": 40, "slowbus_nofifo": 40, "tone": 40, "sdstall": 40, "fifo_empty": 40, "fifo_tag": 40, "fifo_stops": 90,
       "flight": 520, "nofilter": 520, "spike": 500, "spike1s": 500, "false_then_real": 1420, "slow": 620,
       "gpsloss": 520, "gpsback": 520, "gpssilent": 520, "nobmp": 520, "nolsm": 520, "nosd": 520, "rest": 60}
results = []

def check(name, ok, detail=""):
    results.append(ok)
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{detail}]" if detail != "" else ""))

def run(sc):
    out = os.path.join(here, "build", "out", sc)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.check_call([os.path.join(here, "build", which), sc, out, str(DUR[sc])])
    st = dict(l.strip().split("=", 1) for l in open(out + "/stats.txt") if "=" in l)
    files = {}
    for f in sorted(os.listdir(out)):
        if f.startswith("sd_"):
            files[f[3:]] = list(csv.DictReader(open(os.path.join(out, f), newline="")))
    packets = [(float(l.split(";", 1)[0]), l.strip().split(";", 1)[1].split(",")) for l in open(out + "/packets.csv")]
    serial = []
    for l in open(out + "/serial.txt"):
        head, _, rest = l.rstrip("\n").partition(";")
        try:
            serial.append((float(head), rest))
        except ValueError:                      # a line break inside a printed text
            if serial:
                serial.append((serial[-1][0], l.rstrip("\n")))
    buzzer = [(float(l.split(";")[0]), int(l.split(";")[1])) for l in open(out + "/buzzer.txt")]
    return st, files, packets, serial, buzzer

def t_of(r): return int(r["millis"]) / 1000.0
def f(r, c): return float(r[c])
def med(rows, c): 
    v = sorted(f(r, c) for r in rows); return v[len(v) // 2]
def when(serial, text): 
    return [t for t, l in serial if text in l]

def tone_checks(sc):
    st, files, packets, serial, buzzer = run(sc)
    rows = [r for r in files["cansat27_000.csv"] if t_of(r) > (62 if sc == "fifo_stops" else 16)]
    hz, amp, b3, b4 = med(rows, "fft_peak_hz"), med(rows, "fft_peak_amp"), med(rows, "vib_30_60_g"), med(rows, "vib_60_120_g")
    check(f"{sc}: 37 Hz is reported as 37 Hz", abs(hz - 37) < 0.4, hz)
    check(f"{sc}: 0.5 g is reported as 0.5 g", abs(amp - 0.5) < 0.03, amp)
    check(f"{sc}: band 30-60 Hz = 0.354 g (Z), band 60-120 Hz = 0.141 g (X)", abs(b3 - 0.3536) < 0.01 and abs(b4 - 0.1414) < 0.008, (b3, b4))
    others = max(med(rows, c) for c in ("vib_0_10_g", "vib_10_30_g", "vib_120_208_g"))
    check(f"{sc}: the other bands stay below 0.03 g", others < 0.03, others)
    if sc.startswith("slowbus"):
        check(f"{sc}: falls back to 100 kHz and says so", st["wire_clock"] == "100000" and bool(when(serial, "antwoorden niet op de hoge snelheid")), st["wire_clock"])
        lines = [l for t, l in serial if "Controle" in l]
        if sc == "slowbus":
            check(f"{sc}: with the FIFO nothing is lost, no warning", "LET OP" not in lines[-1] and "leesfouten" not in lines[-1], lines[-1])
        else:
            check(f"{sc}: without the FIFO the control line warns that samples are filled in", "LET OP: meer dan 5 % ingevuld" in lines[-1], lines[-1])
    else:
        check(f"{sc}: I2C at 400 kHz", st["wire_clock"] == "400000", st["wire_clock"])
    check(f"{sc}: 34 columns, 19 values per packet", all(len(r) == 34 for r in rows) and all(len(p) == 19 for _, p in packets))
    aud = med(rows, "audio_rms")
    check(f"{sc}: audio RMS 0.020", abs(aud - 0.02) < 0.001, aud)
    fifo_on = bool(when(serial, "FIFO aan"))
    if sc in ("tone", "sdstall"):
        check(f"{sc}: the FIFO is used", fifo_on)
        lines = [l for t, l in serial if "Controle" in l]
        check(f"{sc}: the control line shows the measured rate 422.1", bool(lines) and all("422.1 per seconde" in l or "422.0 per seconde" in l for l in lines[1:]), lines[-1:])
    if sc in ("fifo_empty", "fifo_tag"):
        check(f"{sc}: a FIFO that does not work is switched off at the start", not fifo_on and bool(when(serial, "zonder FIFO")))
        lines = [l for t, l in serial if "Controle" in l]
        check(f"{sc}: polling keeps the 416 Hz grid", all("echt +" in l for l in lines), lines[-1])
    if sc == "fifo_stops":
        t = when(serial, "FIFO viel uit")
        check(f"{sc}: a FIFO that stops is noticed, the Teensy reads itself", fifo_on and len(t) == 1 and 50 < t[0] < 62, t)
    return rows

def flight_common(sc, st, files, packets, serial, buzzer, t_launch=90.0):
    rows = files["cansat27_000.csv"]
    t_ap, t_land = float(st["t_apogee"]), float(st["t_land"])
    det = when(serial, "LANCERING GEDETECTEERD")
    check(f"{sc}: launch detected once, within 6 s", len(det) == 1 and 0 < det[0] - t_launch < 6, det)
    return rows, t_ap, t_land, det

def true_h(tau, H=955.0, vd=8.5):
    a, tb = 150.0, 1.5
    h1, v1 = 0.5 * a * tb * tb, a * tb
    d = v1 * v1 / (2 * (H - h1)); ta = tb + v1 / d
    if tau < tb: return 0.5 * a * tau * tau
    if tau < ta: u = tau - tb; return h1 + v1 * u - 0.5 * d * u * u
    return max(0.0, H - vd * (tau - ta))


for sc in (only or list(DUR)):
    print(f"--- {sc}")
    if sc in ("tone", "sdstall", "fifo_empty", "fifo_tag", "fifo_stops", "slowbus", "slowbus_nofifo"):
        tone_checks(sc)
        continue
    st, files, packets, serial, buzzer = run(sc)
    if sc == "rest":
        rows = files["cansat27_000.csv"]
        tail = rows[20:]
        check("rest: no launch", not when(serial, "LANCERING"))
        check("rest: quiet bands (< 0.002 g), peak g about 1", max(med(tail, c) for c in tail[0] if c.startswith("vib_")) < 0.002 and abs(med(tail, "acc_peak_g") - 1) < 0.02,
              [med(tail, c) for c in tail[0] if c.startswith("vib_")])
        check("rest: altitude steady within 0.5 m", max(f(r, "alt_m") for r in tail) - min(f(r, "alt_m") for r in tail) < 0.5)
        check("rest: before the first fix time 00:00:00 and the no-fix position", rows[5]["time_utc"] == "00:00:00" and rows[5]["lat"].startswith("50.4573") and rows[5]["lon"].startswith("6.2213") and packets[5][1][3] == "50.45730")
        check("rest: with a fix the real position and time", tail[-1]["time_utc"] != "00:00:00" and tail[-1]["lat"].startswith("50.4583") and packets[-1][1][3] == "50.45831", (tail[-1]["time_utc"], tail[-1]["lat"]))
        dts = [int(b["millis"]) - int(a["millis"]) for a, b in zip(rows, rows[1:])]
        check("rest: one row per second", min(dts) >= 999 and max(dts) <= 1003, (min(dts), max(dts)))
    elif sc in ("flight", "nofilter"):
        rows, t_ap, t_land, det = flight_common(sc, st, files, packets, serial, buzzer)
        top = max(rows, key=lambda r: f(r, "alt_m"))
        ground = med(rows[30:80], "alt_m")
        check(f"{sc}: apogee 955 m above the pad (+-10 m)", abs(f(top, "alt_m") - ground - 955) < 10, round(f(top, "alt_m") - ground, 1))
        check(f"{sc}: apogee at the right moment (+-1.2 s)", abs(t_of(top) - t_ap) < 1.2, (t_of(top), t_ap))
        # the altitude of every row against the truth at that moment
        err = []
        for r in rows:
            t = t_of(r)
            if 90 <= t <= t_land:
                tau = t - 90
                err.append(abs(f(r, "alt_m") - ground - true_h(tau)))
        check(f"{sc}: altitude never more than 0.15 s behind (34 m at 225 m/s)", max(err) < 34, round(max(err), 1))
        desc = [e for r, e in zip([r for r in rows if 90 <= t_of(r) <= t_land], err) if t_of(r) > t_ap + 3]
        check(f"{sc}: under the parachute within 4 m", max(desc) < 4, round(max(desc), 1))
        land = when(serial, "LANDING GEDETECTEERD")
        check(f"{sc}: flight ends 6 min after the detected launch", len(land) == 1 and abs(land[0] - det[0] - 360) < 2, land)
        check(f"{sc}: the SD file is closed then", "closed@" in st["files"], st["files"])
        check(f"{sc}: no packets after the end", packets[-1][0] <= land[0] + 0.5 and len(packets) > 400, packets[-1][0])
        on = [t for t, v in buzzer if v == 1 and t > land[0] - 1]
        off = [t for t, v in buzzer if v == 0 and t > land[0] - 1]
        check(f"{sc}: buzzer 3 s on, 7 s off", len(on) >= 5 and all(abs((b - a) - 10) < 0.05 for a, b in zip(on, on[1:])) and all(abs((o - a) - 3) < 0.05 for a, o in zip(on, off)), on[:3])
        check(f"{sc}: no buzzer during the flight", not [t for t, v in buzzer if v == 1 and 10 < t < land[0] - 1])
        boost = [r for r in rows if 90 <= t_of(r) <= 92.5]
        check(f"{sc}: the launch shock is in acc_peak_g (>= 15.9 g)", max(f(r, "acc_peak_g") for r in boost) >= 15.9, max(f(r, "acc_peak_g") for r in boost))
        landrow = [r for r in rows if t_land - 0.2 <= t_of(r) <= t_land + 1.5]
        check(f"{sc}: the landing shock is in acc_peak_g", max(f(r, "acc_peak_g") for r in landrow) >= 15.9, max(f(r, "acc_peak_g") for r in landrow))
        motor = [r for r in rows if 91.6 <= t_of(r) <= 93.2]
        check(f"{sc}: motor vibration found near 140 Hz", any(abs(f(r, "fft_peak_hz") - 140) < 3 or f(r, "vib_120_208_g") > 0.1 for r in motor), [(r["fft_peak_hz"], r["vib_120_208_g"]) for r in motor])
        chute = [r for r in rows if t_ap + 8 <= t_of(r) <= t_land - 5]
        check(f"{sc}: under the parachute the 0-10 Hz band dominates (swinging 0.05 g -> 0.038 g RMS)", abs(med(chute, "vib_0_10_g") - 0.0381) < 0.004 and med(chute, "vib_30_60_g") < 0.005, med(chute, "vib_0_10_g"))
        check(f"{sc}: GPS position moves and has a time", chute[-1]["time_utc"] != "00:00:00" and f(chute[-1], "lon") > 6.2225)
    elif sc in ("spike", "spike1s"):
        det = when(serial, "LANCERING GEDETECTEERD")
        check(f"{sc}: a pressure glitch does not start the flight", not det, det[:2])
        check(f"{sc}: still logging at the end", len(files["cansat27_000.csv"]) > DUR[sc] - 15 and "open" in st["files"], st["files"])
    elif sc == "false_then_real":
        det = when(serial, "LANCERING GEDETECTEERD")
        land = when(serial, "LANDING GEDETECTEERD")
        check("false start: detected at the lift (64..70 s)", len(det) >= 1 and 62 < det[0] < 70, det)
        check("false start: ends after 6 minutes, buzzer on", len(land) >= 1 and abs(land[0] - det[0] - 360) < 2 and any(v == 1 for t, v in buzzer if land[0] <= t < 900), land)
        check("real launch after it: detected", len(det) == 2 and 900 < det[1] < 906, det)
        check("real launch: a new file", "cansat27_001.csv" in files and len(files.get("cansat27_001.csv", [])) > 300, st["files"])
        if "cansat27_001.csv" in files:
            rows = files["cansat27_001.csv"]
            top = max(rows, key=lambda r: f(r, "alt_m"))
            check("real launch: the flight is in the new file (apogee, landing)", f(top, "alt_m") > 1200 and t_of(rows[-1]) > 900 + 300, (top["alt_m"], t_of(rows[-1])))
            check("real launch: buzzer silent, packets again", not [t for t, v in buzzer if v == 1 and det[1] + 1 < t < det[1] + 300] and len([1 for t, p in packets if t > 905]) > 300)
            late = [r for r in rows if t_of(r) > 920]
            check("real launch: FFT works again after the restart", med([r for r in rows if 925 < t_of(r) < 1000], "vib_0_10_g") > 0.03)
    elif sc == "slow":
        rows, t_ap, t_land, det = flight_common(sc, st, files, packets, serial, buzzer)
        land = when(serial, "LANDING GEDETECTEERD")
        check("slow descent (2.2 m/s): the measurement goes on until the CanSat lies still", len(land) == 1 and land[0] > t_land + 5, (land, t_land))
        check("slow descent: the touchdown is logged", t_of(rows[-1]) > t_land and max(f(r, "acc_peak_g") for r in rows if t_of(r) > t_land - 1) > 15)
    elif sc in ("gpsloss", "gpsback", "gpssilent"):
        rows, t_ap, t_land, det = flight_common(sc, st, files, packets, serial, buzzer)
        before = [r for r in rows if 60 < t_of(r) < 89]
        after = [r for r in rows if 97 < t_of(r) < 125]
        check(f"{sc}: before the loss a fix with a time", all(r["time_utc"] != "00:00:00" for r in before))
        check(f"{sc}: after the loss time_utc = 00:00:00", all(r["time_utc"] == "00:00:00" for r in after), after[0]["time_utc"])
        check(f"{sc}: the SD file keeps the last known position", all(r["lat"] == before[-1]["lat"] and r["lon"] == before[-1]["lon"] for r in after), (after[0]["lat"], before[-1]["lat"]))
        pk = [p for t, p in packets if 97 < t < 125]
        check(f"{sc}: the radio sends the no-fix position", all(p[3] == "50.45730" and p[4] == "6.22138" for p in pk), pk[0][3:5])
        late = [r for r in rows if 135 < t_of(r) < 200]
        if sc == "gpsback":
            check("gpsback: the fix comes back with new positions", all(r["time_utc"] != "00:00:00" for r in late) and f(late[-1], "lon") > f(before[-1], "lon") + 0.001)
        else:
            check(f"{sc}: stays without a fix", all(r["time_utc"] == "00:00:00" for r in late))
    elif sc == "nobmp":
        rows = files["cansat27_000.csv"]
        check("no BMP390: keeps logging, no launch, no buzzer after start", len(rows) > 480 and not when(serial, "LANCERING") and not [t for t, v in buzzer if t > 15])
        check("no BMP390: vibrations still measured", max(f(r, "acc_peak_g") for r in rows) > 15)
    elif sc == "nolsm":
        rows = files["cansat27_000.csv"]
        det = when(serial, "LANCERING GEDETECTEERD")
        top = max(rows, key=lambda r: f(r, "alt_m"))
        check("no LSM6DSO: altitude and launch still work", len(det) == 1 and f(top, "alt_m") > 1200, det)
        check("no LSM6DSO: vibration columns are 0", all(f(r, "acc_peak_g") == 0 and f(r, "vib_0_10_g") == 0 for r in rows))
    elif sc == "nosd":
        det = when(serial, "LANCERING GEDETECTEERD")
        check("no SD card: packets and launch still work", not files and len(packets) > 400 and len(det) == 1, len(packets))

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
