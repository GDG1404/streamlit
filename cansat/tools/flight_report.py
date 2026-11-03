"""
CanSat 2027 — Flight report (after the flight)
==============================================

Reads the CSV file from the SD card and writes a complete flight report in
English: one web page with every chart, the key numbers and a short
explanation, built around our research question. Every chart is also saved
as a PNG (16:9, 1600 × 900 pixels) for the presentation.

Usage (in the folder C:\\CanSat):
  py tools\\flight_report.py metingen\\vlucht.csv
  py tools\\flight_report.py metingen\\vlucht.csv --team "Team Kepler"
  py tools\\flight_report.py metingen\\vlucht.csv --radio metingen\\wedstrijd_1.csv metingen\\wedstrijd_2.csv
Or drag the CSV file onto FLIGHT_REPORT.bat.

  --radio      the files of the ground stations: adds the radio link
  --team       the name on the report (or fill in TEAM_NAME below)
  --sea-level  the sea-level pressure of the day in hPa, for the height of
               the launch site above sea level (default 1013.25)
  --no-open    do not open the report in the browser

Output, next to the CSV file (e.g. metingen\\vlucht_report\\):
  flight_report.html   the report: open it in a browser, print it to PDF
  figures\\*.png        every chart, for the slides
  key_numbers.csv      every number of the report, for the slides and the paper

The CanSat data (mass, parachute) come from dashboard\\krachten.py, the
calculations from tools\\krachten_analyse.py: the numbers are the same as
on the dashboards.

Practice without a flight:
  py tools\\gen_test_csv.py metingen\\oefenvlucht.csv --vlucht
  py tools\\flight_report.py metingen\\oefenvlucht.csv
"""

import argparse
import base64
import csv
import datetime
import html
import math
import os
import pathlib
import sys
import webbrowser

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import krachten_analyse as KA  # noqa: E402  (also loads dashboard/krachten.py)

import matplotlib.pyplot as plt  # noqa: E402  (Agg: set by krachten_analyse)
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import (BoundaryNorm, LinearSegmentedColormap,  # noqa: E402
                               ListedColormap, LogNorm, Normalize)
from matplotlib.patches import Patch  # noqa: E402

K = KA.K

# ── fill in: shown on the report ─────────────────────────────
TEAM_NAME = ""                 # e.g. "Team Kepler · Sint-Jozefcollege"
BAROMETER = "BMP388"           # the pressure sensor (the flight code calls it BMP390)

RESEARCH_QUESTION = ("What forces and vibrations does a CanSat feel during "
                     "its flight, and which zones of the can carry the most load?")
PRIMARY_MISSION = ("Measure the air temperature and the air pressure, and send "
                   "them to the ground station at least once per second.")

# ── look: the same light style as tools/krachten_analyse.py ──
STYLE, FIG, DPI = KA.STIJL, KA.FIG, KA.DPI
PAPER, INK, INK2, MUTED, AXIS = KA.OPP, KA.INKT, KA.INKT2, KA.GRIJS, KA.AS
BLUE, ORANGE, AQUA, RED = KA.BLAUW, KA.ORANJE, KA.AQUA, KA.ROOD
SERIES = [BLUE, ORANGE, AQUA]                  # receivers 1, 2, 3
SHADE = "#f3f2ee"
SEQ = LinearSegmentedColormap.from_list(       # one hue, light → dark
    "seq_blue", ["#eef4fc", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                 "#2a78d6", "#1c5cab", "#104281", "#0d366b"])
SEQ_MARK = LinearSegmentedColormap.from_list(  # for lines: never too light
    "seq_blue_mark", ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"])

BANDS = [("vib_0_10_g", "0–10 Hz"), ("vib_10_30_g", "10–30 Hz"),
         ("vib_30_60_g", "30–60 Hz"), ("vib_60_120_g", "60–120 Hz"),
         ("vib_120_208_g", "120–208 Hz")]
STRONG_G = 0.05                # a vibration counts as strong (as on screen 1)
F_NYQUIST = 208.0              # half of 416 samples per second
FS_LSM, N_FFT = 416.0, 512     # samples per second, samples in one FFT (as the Teensy)
QUIET_G = 0.01                 # all bands together below this: quiet
ALL_BANDS_G = 0.02             # every band at least this, at the same time: a shock
NO_FIX = "00:00:00"            # time_utc before the first GPS fix
PHASE_NAMES = [("pad", "on the pad"), ("ascent", "ascent"),
               ("chute opening", "chute opening"), ("descent", "descent"),
               ("landing", "landing"), ("landed", "after landing")]
# the vibration pattern of one second, from the five bands only, with the
# rules of our six FFT lab tests in class: key, label, colour
PATTERNS = [("quiet", "quiet", "#dcdad3"),
            ("slow", "slow: 0–10 Hz", "#9ec5f4"),
            ("medium", "medium: 10–60 Hz", "#3987e5"),
            ("fast", "fast: 60–208 Hz", "#104281"),
            ("all", "all bands at once: a shock", ORANGE)]
EXPECTED = {   # what the lab tests predicted for each phase of the flight
    "pad": ("quiet", "quiet: all bands low, about 0.001\u00a0g"),
    "ascent": ("fast", "fast: a strong peak in a high band (lab test 4: the motor)"),
    "chute opening": ("all", "all bands at once, for about 1\u00a0s (lab test 3: a shock)"),
    "descent": ("slow", "slow: only 0–10\u00a0Hz, about 1.5–3\u00a0Hz (lab test 1: the swing)"),
    "landing": ("all", "all bands at once (lab test 3: a shock)"),
    "landed": ("quiet", "quiet again"),
}
COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west",
           "west", "north-west"]


# ═════════════════════════════════════════════════════════════
#  READING
# ═════════════════════════════════════════════════════════════
def load(path):
    """The CSV file → dict column → numpy array (nan where a value is
    missing). time_utc stays text. Same rows as krachten_analyse.lees."""
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        lines = list(csv.reader(fh))
    head, rows = None, []
    for line in lines:
        if not line:
            continue
        if line[0].strip() == "millis":          # header (also after a restart)
            head = [k.strip() for k in line]
            continue
        if head and len(line) == len(head):
            rows.append(line)
    if head is None:
        raise ValueError("no header line found (a line that starts with millis,...)")
    d = {}
    for j, key in enumerate(head):
        if key == "time_utc":
            d[key] = np.array([r[j].strip() for r in rows], dtype=object)
            continue
        col = np.full(len(rows), np.nan)
        for i, r in enumerate(rows):
            try:
                col[i] = float(r[j])
            except ValueError:
                pass
        d[key] = col
    for key in ("millis", "press_hPa", "temp_C", "alt_m"):
        if key not in d:
            raise ValueError(f"the column {key} is missing")
    ok = np.isfinite(d["millis"]) & np.isfinite(d["alt_m"])
    return {k: v[ok] for k, v in d.items()}, len(rows)


def col(d, key):
    return d[key] if key in d else np.full(len(d["millis"]), np.nan)


def finite_share(a):
    a = np.asarray(a, dtype=float)
    return float(np.isfinite(a).mean()) if len(a) else 0.0


def nanmax0(a):
    """Largest finite value, or 0 when there is none."""
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.max()) if len(a) else 0.0


# ═════════════════════════════════════════════════════════════
#  FORMATTING
# ═════════════════════════════════════════════════════════════
def num(x, nd=1, unit=""):
    if x is None or not np.isfinite(x):
        return "—"
    s = f"{x:,.{nd}f}"
    return f"{s}\u00a0{unit}" if unit else s          # no line break before the unit


def duration(s):
    if not np.isfinite(s):
        return "—"
    m, sec = divmod(int(round(s)), 60)
    if m >= 60:
        return f"{m // 60} h {m % 60} min"
    return f"{m} min {sec} s" if m else f"{sec} s"


def compass(deg):
    return COMPASS[int(((deg % 360) + 22.5) // 45) % 8]


def signed(x, nd=1):
    """A number with a real minus sign: −6.5 instead of -6.5."""
    return f"{x:.{nd}f}".replace("-", "−")


# the moments of krachten_analyse, for sentences ("at the parachute opening")
MOMENT = {"launch": "the launch", "chute opens": "the parachute opening",
          "descent": "the steady descent", "landing": "the landing"}


def at_moment(name):
    """'at the launch', 'during the steady descent', ... for sentences."""
    m = MOMENT.get(name, name)
    return ("during " if name == "descent" else "at ") + m


def at_least(r, name):
    """'≥ ' when the sensor reached its 16 g limit at this moment."""
    return "≥\u00a0" if r["afgeknipt"].get(name) else ""


def window(r):
    t, f = r["t"], r["f"]
    return t[f["lancering"]] - 30.0, t[f["klap"]] + 30.0


# ═════════════════════════════════════════════════════════════
#  ANALYSIS
# ═════════════════════════════════════════════════════════════
def time_axis(d, r):
    if r is not None:
        return r["t"]
    return (d["millis"] - d["millis"][0]) / 1000.0


def phases(d, r):
    if r is not None:
        return np.array(r["fase"], dtype=object)
    return np.array(["pad"] * len(d["millis"]), dtype=object)


def flight_numbers(d, r):
    """The flight: events, heights, speeds. None without a flight."""
    if r is None:
        return None
    t, f = r["t"], r["f"]
    h, daal = f["hoogte"], f["daal"]
    i0, it, ik = f["lancering"], f["top"], f["klap"]
    pad = slice(max(0, i0 - 30), i0 + 1)
    out = {
        "apogee": float(h[it]), "t_top": float(t[it]), "t_open": float(r["t_open"]),
        "t_land": float(t[ik]), "landed": bool(f["geland"]),
        "climb_max": float(np.nanmax(-daal[i0:it + 1])) if it > i0 else float("nan"),
        "v_mean": float(h[it] / (t[ik] - t[it])) if t[ik] > t[it] else float("nan"),
        "p_pad": float(np.nanmedian(d["press_hPa"][pad])),
        "T_pad": float(np.nanmedian(d["temp_C"][pad])),
        "p_top": float(d["press_hPa"][it]), "T_top": float(d["temp_C"][it]),
        "pad_seconds": float(t[i0] - t[0]),
    }
    for key in ("v_rustig", "v_p10", "v_p90", "cd", "cd_p10", "cd_p90",
                "cd_per_100m", "v_grond", "v_open", "open_model", "open_sensor"):
        out[key] = float(r.get(key, float("nan")))
    return out


def site_altitude(p_hpa, p0):
    """Height above sea level from the pressure (barometric formula)."""
    return 44330.0 * (1.0 - (p_hpa / p0) ** (1.0 / 5.255))


def line_fit(h, T):
    """Least-squares straight line T = a·h + b: (a, b, standard error of a, R²)."""
    a, b = np.polyfit(h, T, 1)
    res = T - (a * h + b)
    se = math.sqrt(float(np.sum(res ** 2)) / (len(h) - 2) / float(np.sum((h - h.mean()) ** 2)))
    ss = float(np.sum((T - T.mean()) ** 2))
    return float(a), float(b), se, (1.0 - float(np.sum(res ** 2)) / ss) if ss > 0 else 0.0


def lapse_rate(d, r):
    """Temperature against height in the descent: a straight line.
    The sensor inside the can follows the air slowly (time constant τ):
    T_air ≈ T_sensor + τ · dT/dt. We take the τ that makes the profile the
    straightest. Returns the slope (°C per km), its standard error, R², τ
    and the points."""
    if r is None:
        return None
    t, f = r["t"], r["f"]
    sel = (t >= r["t_open"] + 3) & (t < t[f["klap"]] - 1)
    ts, h, T = t[sel], f["hoogte"][sel], d["temp_C"][sel]
    ok = np.isfinite(h) & np.isfinite(T)
    ts, h, T = ts[ok], h[ok], T[ok]
    if len(h) < 8 or np.ptp(h) < 50:
        return None
    dTdt = np.gradient(T, ts)
    dTdt = np.convolve(np.pad(dTdt, 2, mode="edge"), np.ones(5) / 5, mode="valid")
    raw = line_fit(h, T)
    best = (raw[3], 0.0)
    for tau in np.arange(1.0, 61.0):
        r2 = line_fit(h, T + tau * dTdt)[3]
        if r2 > best[0]:
            best = (r2, float(tau))
    tau = best[1] if best[0] - raw[3] > 0.02 else 0.0     # only a clear gain
    Tc = T + tau * dTdt
    a, b, se, r2 = line_fit(h, Tc)
    return {"slope": a * 1000.0, "se": se * 1000.0, "r2": r2, "b": b, "tau": tau,
            "slope_raw": raw[0] * 1000.0, "r2_raw": raw[3], "h": h, "T": T, "Tc": Tc}


def vibration_numbers(d, r):
    """Vibration bands per phase, the strongest band and the most frequent
    strong frequencies during the flight."""
    bands = np.vstack([col(d, k) for k, _ in BANDS]).T          # rows × 5
    if not np.isfinite(bands).any():
        return None
    t, fase = time_axis(d, r), phases(d, r)
    out = {"bands": bands, "matrix": [], "phases": []}
    for key, label in PHASE_NAMES:
        sel = fase == key
        if key == "pad" and r is not None:
            sel &= t >= -60.0                                    # the last minute
        if key == "landed" and r is not None:
            sel &= t <= r["t"][r["f"]["klap"]] + 60.0
        rows = bands[sel]
        rows = rows[np.isfinite(rows).all(axis=1)]
        if len(rows):
            out["phases"].append(label)
            out["matrix"].append(np.median(rows, axis=0))
    out["matrix"] = np.array(out["matrix"])
    # the strongest band in the whole flight
    fl = (t >= -1) & (t <= (r["t"][r["f"]["klap"]] + 2 if r is not None else t[-1]))
    sub = np.where(fl[:, None], bands, np.nan)
    if np.isfinite(sub).any():
        i, j = np.unravel_index(int(np.nanargmax(sub)), sub.shape)
        out["max_g"], out["max_band"], out["max_t"] = float(sub[i, j]), BANDS[j][1], float(t[i])
        out["max_phase"] = dict(PHASE_NAMES).get(fase[i], fase[i])
    # how much stronger in the ascent than on the pad, per band
    labels = out["phases"]
    if "ascent" in labels and "on the pad" in labels:
        a = out["matrix"][labels.index("ascent")]
        p = out["matrix"][labels.index("on the pad")]
        out["ratio"] = a / np.maximum(p, 1e-4)
    # dominant frequencies of the strong rows in the flight (4 Hz bins)
    hz, amp = col(d, "fft_peak_hz"), col(d, "fft_peak_amp")
    strong = fl & np.isfinite(hz) & np.isfinite(amp) & (amp > STRONG_G)
    freqs = np.minimum(hz[strong], F_NYQUIST)
    out["n_strong"] = int(strong.sum())
    out["top"], out["top_phase"] = [], []
    if len(freqs) >= 3:
        edges = np.linspace(0, F_NYQUIST, 53)
        idx = np.clip(np.digitize(freqs, edges) - 1, 0, 51)
        counts = np.bincount(idx, minlength=52)
        names = dict(PHASE_NAMES)
        where = fase[strong]
        for k in np.argsort(counts)[::-1][:5]:
            if counts[k] >= 2:
                out["top"].append((float(np.median(freqs[idx == k])), int(counts[k])))
                ph, n = np.unique(where[idx == k], return_counts=True)
                out["top_phase"].append(names.get(ph[int(np.argmax(n))], ""))
    out["strong_t"], out["strong_hz"], out["strong_amp"] = t[strong], hz[strong], amp[strong]
    return out


def pattern_of(b):
    """The vibration pattern of one second (an index in PATTERNS), from the
    five bands only. -1 when a band is missing."""
    if not np.isfinite(b).all():
        return -1
    if math.sqrt(float(np.sum(b ** 2))) < QUIET_G:
        return 0                                       # quiet
    if b.min() >= ALL_BANDS_G:
        return 4                                       # all bands at once: a shock
    j = int(np.argmax(b))
    return 1 if j == 0 else (2 if j <= 2 else 3)       # slow, medium or fast


def vibration_patterns(d, r):
    """Every second gets a pattern from the five bands only: no height, no
    GPS. Per phase of the flight: the pattern seen most, against the one our
    lab tests predicted. Also the envelope: the highest value in each band."""
    bands = np.vstack([col(d, k) for k, _ in BANDS]).T
    if not np.isfinite(bands).any():
        return None
    pat = np.array([pattern_of(b) for b in bands], dtype=int)
    total = np.sqrt(np.sum(bands ** 2, axis=1))         # nan when a band is missing
    out = {"pattern": pat, "total": total, "rows": [], "n_ok": 0}
    if r is None:
        return out
    t, fase = r["t"], phases(d, r)
    hz, amp = col(d, "fft_peak_hz"), col(d, "fft_peak_amp")
    t_land = float(t[r["f"]["klap"]])
    keys = [k for k, _, _ in PATTERNS]
    for key, label in PHASE_NAMES:
        sel = (fase == key) & (pat >= 0)
        if key == "pad":
            sel &= t >= -60.0                            # the last minute
        if key == "landed":
            sel &= t <= t_land + 60.0
        if not sel.any():
            continue
        exp, exp_text = EXPECTED[key]
        e = keys.index(exp)
        counts = np.bincount(pat[sel], minlength=len(PATTERNS))
        mode = int(np.argmax(counts))
        if exp == "all":                 # a shock lasts about 1 s: seen at least once
            ts = t[sel]                  # (the FFT comes up to 1.2 s later)
            seen = int(((t >= ts.min() - 1.0) & (t <= ts.max() + 2.0) & (pat == e)).sum())
            match = seen > 0
        else:
            seen = int(counts[e])
            match = mode == e
        tone = sel & np.isfinite(hz) & np.isfinite(amp) & (amp >= QUIET_G)
        med = np.median(bands[sel], axis=0)
        out["rows"].append({
            "key": key, "label": label, "expected": exp, "expected_text": exp_text,
            "mode": mode, "share": float(counts[mode]) / float(sel.sum()), "seen": seen,
            "n": int(sel.sum()), "match": bool(match),
            "f_typ": float(np.median(hz[tone])) if tone.any() else float("nan"),
            "band": BANDS[int(np.argmax(med))][1],
            "level": float(np.median(total[sel])), "level_max": float(np.max(total[sel]))})
    out["n_ok"] = sum(1 for x in out["rows"] if x["match"])
    fl = (t >= -1.0) & (t <= t_land + 2.0) & np.isfinite(total)
    if fl.any():
        names = dict(PHASE_NAMES)
        env = []
        for j, (_, lab) in enumerate(BANDS):
            i = int(np.argmax(np.where(fl, bands[:, j], -1.0)))
            env.append((lab, float(bands[i, j]), names.get(fase[i], fase[i])))
        out["envelope"] = env
        i = int(np.argmax(np.where(fl, total, -1.0)))
        out["total_max"] = (float(total[i]), names.get(fase[i], fase[i]))
    return out


def g_text(v):
    """A vibration in g, with sensible decimals."""
    if not np.isfinite(v):
        return "—"
    if v < 0.001:
        return "<\u00a00.001\u00a0g"
    return f"{v:.3f}\u00a0g" if v < 0.1 else f"{v:.2f}\u00a0g"


def gps_numbers(d, r):
    """GPS: fix, the track in metres, landing site, drift."""
    lat, lon = col(d, "lat"), col(d, "lon")
    utc = d.get("time_utc", np.array([NO_FIX] * len(lat), dtype=object))
    fix = np.array([u != NO_FIX and u != "" for u in utc]) & np.isfinite(lat) & np.isfinite(lon)
    fix &= (np.abs(lat) > 0.01) | (np.abs(lon) > 0.01)
    t_all = time_axis(d, r)
    if r is not None:
        x0, x1 = window(r)
        span = (t_all >= x0) & (t_all <= x1)
    else:
        span = np.ones(len(fix), dtype=bool)
    out = {"share": float(fix[span].mean()) if span.any() else 0.0, "fix": fix}
    if fix.sum() < 3:
        return out
    t, fase = time_axis(d, r), phases(d, r)
    i_launch = r["f"]["lancering"] if r is not None else 0
    before = np.where(fix[:i_launch + 1])[0]
    i_ref = int(before[-1]) if len(before) else int(np.where(fix)[0][0])
    lat0, lon0 = lat[i_ref], lon[i_ref]
    x = (lon - lon0) * 111_320.0 * math.cos(math.radians(lat0))
    y = (lat - lat0) * 111_320.0
    out.update({"x": x, "y": y, "lat0": float(lat0), "lon0": float(lon0),
                "t_first": float(t[np.where(fix)[0][0]]),
                "utc_launch": str(utc[i_launch]) if fix[i_launch] else ""})
    after = fix & np.isin(fase, ["landing", "landed"])
    if after.any():
        xl, yl = float(np.median(x[after])), float(np.median(y[after]))
        out["lat_land"], out["lon_land"] = float(np.median(lat[after])), float(np.median(lon[after]))
    else:
        last = int(np.where(fix)[0][-1])
        xl, yl = float(x[last]), float(y[last])
        out["lat_land"], out["lon_land"] = float(lat[last]), float(lon[last])
    out["x_land"], out["y_land"] = xl, yl
    out["distance"] = math.hypot(xl, yl)
    out["bearing"] = math.degrees(math.atan2(xl, yl)) % 360
    desc = fix & (fase == "descent")
    spd, crs = col(d, "gps_speed_ms"), col(d, "gps_course_deg")
    ok = desc & np.isfinite(spd) & np.isfinite(crs)
    if ok.sum() >= 5:
        out["drift_speed"] = float(np.median(spd[ok]))
        c = np.radians(crs[ok])
        out["drift_course"] = math.degrees(math.atan2(np.sin(c).mean(), np.cos(c).mean())) % 360
    return out


def quality_numbers(d, rows_in_file, restarted):
    t = (d["millis"] - d["millis"][0]) / 1000.0
    dt = np.diff(t)
    span = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    peak = col(d, "acc_peak_g")
    bands = np.vstack([col(d, k) for k, _ in BANDS]).T
    lacc = col(d, "lacc_z")
    return {
        "rows": len(t), "rows_file": rows_in_file, "restarted": restarted,
        "span": span, "rate": float(1.0 / np.median(dt)) if len(dt) else float("nan"),
        "complete": min(1.0, len(t) / (span + 1.0)) if span > 0 else 1.0,
        "gaps": int(np.sum(dt > 1.6)), "longest_gap": float(dt.max()) if len(dt) else 0.0,
        "bmp": float(np.mean(np.isfinite(d["press_hPa"]) & (d["press_hPa"] > 100))),
        "bno": finite_share(lacc) if nanmax0(np.abs(lacc)) > 0 else 0.0,
        "lsm": (float(np.isfinite(bands).all(axis=1).mean())
                if nanmax0(bands) > 0 else 0.0),
        "peak": finite_share(peak),
        "audio": finite_share(col(d, "audio_rms")),
        "clipped": int(np.sum(peak >= K.SENSOR_MAX_G - 0.1)),
    }


def radio_numbers(path, r):
    """One ground-station file: packets, signal, and the share of packets
    received during the flight (aligned with the SD card at the apogee)."""
    d, _ = load(path)
    t = (d["millis"] - d["millis"][0]) / 1000.0
    out = {"name": os.path.basename(path), "packets": len(t),
           "rssi": col(d, "rssi"), "snr": col(d, "snr")}
    alt = d["alt_m"]
    out["aligned"] = False
    if r is not None and len(t) > 10 and np.ptp(alt) > 30:
        f = r["f"]
        i_top = int(np.nanargmax(alt))
        ta = t - t[i_top] + r["t"][f["top"]]               # time since the launch
        x0, x1 = window(r)
        sel = (ta >= x0) & (ta <= x1)
        out.update({"aligned": True, "t": ta, "window": x1 - x0,
                    "received": int(sel.sum()),
                    "share": min(1.0, sel.sum() / (x1 - x0 + 1.0))})
        rs, sn = out["rssi"][sel], out["snr"][sel]
    else:
        out["t"] = t
        rs, sn = out["rssi"], out["snr"]
    out["rssi_med"] = float(np.nanmedian(rs)) if np.isfinite(rs).any() else float("nan")
    out["rssi_min"] = float(np.nanmin(rs)) if np.isfinite(rs).any() else float("nan")
    out["snr_med"] = float(np.nanmedian(sn)) if np.isfinite(sn).any() else float("nan")
    out["snr_min"] = float(np.nanmin(sn)) if np.isfinite(sn).any() else float("nan")
    return out


# ═════════════════════════════════════════════════════════════
#  CHARTS (each one a PNG for the slides)
# ═════════════════════════════════════════════════════════════
def shade_phases(ax, r, label=True):
    """Light bands for the ascent, the chute opening and the descent."""
    if r is None:
        return
    t, f = r["t"], r["f"]
    spans = [(t[f["lancering"]], t[f["top"]], "ascent"),
             (t[f["top"]], r["t_open"], ""),
             (r["t_open"], t[f["klap"]], "descent under the parachute")]
    for k, (a, b, name) in enumerate(spans):
        if b > a:
            ax.axvspan(a, b, color=SHADE if k != 1 else "#e9e7e0", lw=0, zorder=0)
            if label and name:
                ax.text((a + b) / 2, 0.98, name, transform=ax.get_xaxis_transform(),
                        ha="center", va="top", fontsize=9, color=MUTED)


def events(ax, r):
    if r is None:
        return
    for te, _ in KA.gebeurtenissen(r):
        ax.axvline(te, color=AXIS, lw=1, zorder=1)


def save(fig, path):
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def colorbar_g(fig, mappable, cax, vmax):
    """Colour scale in g RMS with plain numbers (0.001 … 1) instead of 10ⁿ."""
    cb = fig.colorbar(mappable, cax=cax)
    ticks = [v for v in (0.001, 0.01, 0.1, 1, 10) if v <= vmax * 1.001]
    cb.set_ticks(ticks)
    cb.set_ticklabels([f"{v:g}" for v in ticks])
    cb.minorticks_off()
    cb.outline.set_visible(False)
    cax.set_title("g RMS", fontsize=10, color=INK2, pad=12)
    return cb


def fig_atmosphere(d, r, fl, sub, path):
    t = time_axis(d, r)
    x0, x1 = window(r) if r is not None else (t[0], t[-1])
    sel = (t >= x0 - 30) & (t <= x1 + 30)
    title = ("Primary mission: temperature and pressure" if fl is None else
             f"Pressure fell from {fl['p_pad']:.1f} to {fl['p_top']:.1f} hPa at the highest point")
    with plt.rc_context(STYLE):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=FIG, sharex=True)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.09, hspace=0.32)
        KA.titel(fig, title, sub)
        for a in (a1, a2):
            shade_phases(a, r, label=a is a1)
            events(a, r)
        a1.plot(t[sel], d["temp_C"][sel], color=ORANGE)
        a1.set_title(f"Air temperature ({BAROMETER}, inside the can)")
        a1.set_ylabel("temperature (°C)")
        a2.plot(t[sel], d["press_hPa"][sel], color=BLUE)
        a2.set_title(f"Air pressure ({BAROMETER})")
        a2.set_ylabel("pressure (hPa)")
        a2.set_xlabel("time since the launch (s)" if r is not None else "time (s)")
        a1.set_xlim(x0, x1)
        save(fig, path)


def fig_lapse(lr, fl, sub, path):
    corrected = lr["tau"] > 0
    with plt.rc_context(STYLE):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.10)
        KA.titel(fig, f"The air got {-lr['slope']:.1f} °C colder per km of height",
                 sub + " · under the parachute · standard atmosphere: 6.5 °C per km")
        a.scatter(lr["T"], lr["h"], s=18, color=ORANGE, edgecolor=PAPER, linewidth=0.8,
                  zorder=3, label="measured by the sensor in the can")
        if corrected:
            a.scatter(lr["Tc"], lr["h"], s=24, color=BLUE, edgecolor=PAPER, linewidth=1,
                      zorder=4, label=f"corrected for the slow sensor (τ = {lr['tau']:.0f} s)")
        hh = np.linspace(0, max(lr["h"].max(), fl["apogee"]), 50)
        a.plot(lr["slope"] / 1000 * hh + lr["b"], hh, color=INK, zorder=5,
               label=f"straight line: {lr['slope']:.1f} ± {lr['se']:.1f} °C per km "
                     f"(R² = {lr['r2']:.2f})")
        a.plot(lr["b"] - 0.0065 * hh, hh, color=MUTED, ls=(0, (4, 3)), zorder=2,
               label="standard atmosphere: −6.5 °C per km")
        a.set_xlabel("temperature (°C)")
        a.set_ylabel("height above the launch site (m)")
        a.set_title("Temperature against height")
        a.legend(loc="upper right")
        save(fig, path)


def fig_loads(r, sub, path):
    rows = [(name, g, support) for name, g, support in r["momenten"] if np.isfinite(g)]
    if not rows:
        return False
    gmax_name, gmax, _ = max(rows, key=lambda x: x[1])
    gpre = at_least(r, gmax_name)
    with plt.rc_context(STYLE):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.82, bottom=0.11)
        KA.titel(fig, f"Highest load: {gpre}{gmax:.1f} g {at_moment(gmax_name)}",
                 sub + f" · F = m · n · g with m = {K.MASS_KG * 1000:.0f} g")
        y = np.arange(len(rows))[::-1]
        for yi, (name, g, support) in zip(y, rows):
            a.barh(yi, g, height=0.55, color=BLUE, zorder=3)
            pre = "≥ " if r["afgeknipt"].get(name) else ""
            F = g * K.G * K.MASS_KG
            where = "bottom: pressed" if support == "bottom" else "top: pulled"
            label = f"{pre}{g:.1f} g  ·  {pre}{F:.0f} N  ·  {where}"
            if g > 9:                                  # long bar: label inside
                a.text(g - 0.3, yi, label, va="center", ha="right", fontsize=11,
                       color="white", fontweight="bold", zorder=4)
            else:
                a.text(g + 0.25, yi, label, va="center", fontsize=11, color=INK)
        a.set_yticks(y)
        a.set_yticklabels([n for n, _, _ in rows], fontsize=12)
        a.grid(axis="y", visible=False)
        a.axvline(K.SENSOR_MAX_G, color=MUTED, lw=1.2, ls=(0, (4, 3)))
        a.axvline(K.DESIGN_LOAD_G, color=RED, lw=1.2, ls=(0, (4, 3)))
        a.text(K.SENSOR_MAX_G, 1.01, "sensor limit 16 g", transform=a.get_xaxis_transform(),
               ha="center", va="bottom", fontsize=10, color=INK2)
        a.text(K.DESIGN_LOAD_G, 1.01, "ESA design load 20 g",
               transform=a.get_xaxis_transform(), ha="center", va="bottom",
               fontsize=10, color=INK2)
        a.set_xlim(0, K.DESIGN_LOAD_G + 4)
        a.set_xlabel("load (g)  ·  1 g = standing still")
        a.set_title("The load at each moment of the flight")
        save(fig, path)
    return True


def fig_vibration_timeline(d, r, vb, sub, path):
    t = time_axis(d, r)
    x0, x1 = window(r) if r is not None else (t[0], t[-1])
    sel = (t >= x0) & (t <= x1)
    tt, B = t[sel], vb["bands"][sel]
    if len(tt) < 3:
        return False
    edges = np.concatenate([[tt[0] - 0.5], (tt[1:] + tt[:-1]) / 2, [tt[-1] + 0.5]])
    vmax = max(1.0, float(np.nanmax(B)) if np.isfinite(B).any() else 1.0)
    with plt.rc_context(STYLE):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=FIG, sharex=True,
                                     gridspec_kw={"height_ratios": [1, 1]})
        fig.subplots_adjust(left=0.09, right=0.90, top=0.84, bottom=0.09, hspace=0.30)
        KA.titel(fig, "Vibrations during the flight, second by second",
                 sub + " · FFT of 512 samples at 416 per second (LSM6DSO, z-axis)")
        m = a1.pcolormesh(edges, np.arange(6), np.ma.masked_invalid(B.T), cmap=SEQ,
                          norm=LogNorm(vmin=1e-3, vmax=vmax), shading="flat")
        a1.set_yticks(np.arange(5) + 0.5)
        a1.set_yticklabels([lab for _, lab in BANDS])
        a1.grid(False)
        a1.set_title("Vibration in each frequency band (g RMS)")
        events(a1, r)
        cax = fig.add_axes([0.915, 0.53, 0.015, 0.27])
        colorbar_g(fig, m, cax, vmax)
        shade_phases(a2, r)
        events(a2, r)
        s = vb["strong_amp"]
        if len(s):
            sizes = 10 + 60 * np.clip(s / max(float(s.max()), 1e-6), 0, 1)
            a2.scatter(vb["strong_t"], vb["strong_hz"], s=sizes, color=BLUE,
                       edgecolor=PAPER, linewidth=0.8, zorder=3)
        else:
            a2.text(0.5, 0.5, "no strong vibration (above 0.05 g) in the flight",
                    transform=a2.transAxes, ha="center", fontsize=11, color=INK2)
        a2.set_ylim(0, F_NYQUIST + 4)
        a2.set_yticks([0, 10, 30, 60, 120, 208])
        a2.set_ylabel("frequency (Hz)")
        a2.set_title("The strongest frequency, when stronger than 0.05 g (dot size = strength)")
        a2.set_xlabel("time since the launch (s)" if r is not None else "time (s)")
        a1.set_xlim(x0, x1)
        save(fig, path)
    return True


def fig_fingerprint(vb, sub, path):
    M, labels = vb["matrix"], vb["phases"]
    if len(M) < 2:
        return False
    vmax = max(1.0, float(M.max()))
    norm = LogNorm(vmin=1e-3, vmax=vmax)
    with plt.rc_context(STYLE):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.10, right=0.90, top=0.80, bottom=0.12)
        KA.titel(fig, "Every flight phase has its own vibration fingerprint",
                 sub + " · median vibration per band in each phase (g RMS)")
        m = a.imshow(M.T, cmap=SEQ, norm=norm, aspect="auto", origin="lower")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M[i, j]
                dark = norm(max(v, 1e-3)) > 0.55
                a.text(i, j, f"{v:.2g}" if v >= 0.001 else "< 0.001", ha="center",
                       va="center", fontsize=12, color="white" if dark else INK2,
                       fontweight="bold" if v >= 0.001 else "normal")
        a.set_xticks(range(len(labels)))
        a.set_xticklabels(labels, fontsize=12)
        a.set_yticks(range(len(BANDS)))
        a.set_yticklabels([lab for _, lab in BANDS], fontsize=12)
        a.grid(False)
        for s in a.spines.values():
            s.set_visible(False)
        a.tick_params(length=0)
        cax = fig.add_axes([0.915, 0.2, 0.015, 0.5])
        colorbar_g(fig, m, cax, vmax)
        save(fig, path)
    return True


def fig_top_frequencies(vb, sub, path):
    top = vb["top"]
    if not top:
        return False
    with plt.rc_context(STYLE):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.13, right=0.95, top=0.80, bottom=0.12)
        KA.titel(fig, f"Most frequent strong vibration in the flight: {top[0][0]:.0f} Hz",
                 sub + f" · {vb['n_strong']} seconds with a vibration above 0.05 g")
        y = np.arange(len(top))[::-1]
        phase = vb.get("top_phase", [""] * len(top))
        for yi, (hz, n), ph in zip(y, top, phase):
            a.barh(yi, n, height=0.55, color=BLUE, zorder=3)
            a.text(n + 0.15, yi, f"{n} s" + (f"  ·  mostly in the {ph}" if ph else ""),
                   va="center", fontsize=12, color=INK)
        a.set_yticks(y)
        a.set_yticklabels([f"{hz:.0f} Hz" for hz, _ in top], fontsize=13)
        a.grid(axis="y", visible=False)
        a.set_xlabel("number of seconds in which this was the strongest frequency")
        a.set_xlim(0, max(n for _, n in top) * 1.18 + 1)
        a.set_title("The five most frequent strong frequencies (4 Hz wide groups)")
        save(fig, path)
    return True


def fig_fft_explained(path):
    """How the FFT works, with a made-up signal and the same steps as the
    flight computer: 512 samples at 416 per second, the steady part removed,
    a Hamming window, the amplitude of each frequency and the five bands."""
    n = np.arange(N_FFT)
    t = n / FS_LSM
    df = FS_LSM / N_FFT                                    # 0.8125 Hz between two frequencies
    f1, f2 = 4 * df, 105 * df                              # 3.25 Hz and 85.3 Hz
    rng = np.random.default_rng(7)
    z = (1.0 + 0.30 * np.sin(2 * np.pi * f1 * t) + 0.15 * np.sin(2 * np.pi * f2 * t + 0.6)
         + rng.normal(0.0, 0.01, N_FFT))                   # 1 g: gravity
    w = 0.54 - 0.46 * np.cos(2 * np.pi * n / (N_FFT - 1))  # Hamming window
    X = np.fft.rfft((z - z.mean()) * w)[: N_FFT // 2]
    f = np.arange(len(X)) * df
    amp = 2.0 * np.abs(X) / w.sum()                        # the amplitude of a sine, in g
    power = np.abs(X) ** 2
    edges = [0.0, 10.0, 30.0, 60.0, 120.0, F_NYQUIST + 1.0]
    k = np.arange(len(f))
    rms = [math.sqrt(2.0 * float(power[(f >= lo) & (f < hi) & (k > 0)].sum())
                     / (N_FFT ** 2 * float(np.mean(w ** 2))))
           for lo, hi in zip(edges, edges[1:])]
    with plt.rc_context(STYLE):
        fig = plt.figure(figsize=FIG)
        gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.3, 0.95], wspace=0.30,
                              left=0.06, right=0.985, top=0.78, bottom=0.13)
        a1, a2, a3 = (fig.add_subplot(gs[0, i]) for i in range(3))
        KA.titel(fig, "How our FFT works: from a vibration to five numbers",
                 "Illustration with a made-up signal, not flight data · the same steps as the "
                 "flight computer: 512 samples at 416 per second, Hamming window")
        a1.plot(t, z, color=BLUE, lw=1.3)
        a1.set_xlim(0, N_FFT / FS_LSM)
        a1.set_ylim(0.45, 1.62)
        a1.set_title("1 · The sensor: 512 values in 1.23 s")
        a1.set_xlabel("time (s)")
        a1.set_ylabel("acceleration (g)")
        a1.text(0.04, 0.96, "a slow swing (3.3 Hz)\nwith a fast vibration on top (85 Hz)",
                transform=a1.transAxes, fontsize=10, color=INK2, va="top")
        for i, (lo, hi) in enumerate(zip(edges, edges[1:])):      # the five bands
            if i % 2:
                a2.axvspan(lo, min(hi, F_NYQUIST), color=SHADE, lw=0, zorder=0)
        a2.plot(f, amp, color=BLUE, lw=1.3, zorder=3)
        a2.annotate("3.3 Hz: the slow swing", (f1, 0.30), xytext=(30, 0.30), va="center",
                    fontsize=10, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
        a2.annotate("85 Hz: the fast vibration", (f2, 0.15), xytext=(98, 0.215), va="center",
                    fontsize=10, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
        a2.set_xlim(0, F_NYQUIST)
        a2.set_ylim(0, 0.37)
        a2.set_xticks([0, 10, 30, 60, 120, 208])
        a2.grid(axis="x", visible=False)
        a2.set_title("2 · The FFT: how strong each frequency is")
        a2.set_xlabel("frequency (Hz) · shaded: the five bands")
        a2.set_ylabel("amplitude (g)")
        x = np.arange(len(rms))
        a3.bar(x, rms, width=0.62, color=BLUE, zorder=3)
        a3.set_yscale("log")
        a3.set_ylim(0.001, 1.0)
        a3.set_yticks([0.001, 0.01, 0.1, 1.0])
        a3.set_yticklabels(["0.001", "0.01", "0.1", "1"])
        a3.minorticks_off()
        for xi, v in zip(x, rms):
            a3.text(xi, v * 1.18, f"{v:.2f}" if v >= 0.1 else f"{v:.3f}", ha="center",
                    va="bottom", fontsize=10, color=INK)
        a3.set_xticks(x)
        a3.set_xticklabels([lab.replace(" Hz", "") for _, lab in BANDS], fontsize=9.5)
        a3.grid(axis="x", visible=False)
        a3.set_xlabel("band (Hz)")
        a3.set_ylabel("vibration (g RMS)")
        a3.set_title("3 · Five numbers: one per band")
        save(fig, path)
    return True


def fig_phase_recognition(d, r, pt, sub, path):
    """The flight phases from the barometer, next to the pattern of every
    second from the five bands only, and how strong it vibrated."""
    t = r["t"]
    x0, x1 = window(r)
    sel = (t >= x0) & (t <= x1)
    tt, pat, tot = t[sel], pt["pattern"][sel], pt["total"][sel]
    fase = phases(d, r)[sel]
    if len(tt) < 3:
        return False
    edges = np.concatenate([[tt[0] - 0.5], (tt[1:] + tt[:-1]) / 2, [tt[-1] + 0.5]])
    colors = [c for _, _, c in PATTERNS]
    names = dict(PHASE_NAMES)
    with plt.rc_context(STYLE):
        fig = plt.figure(figsize=FIG)
        gs = fig.add_gridspec(3, 1, height_ratios=[0.36, 0.36, 1.5], hspace=0.55,
                              left=0.115, right=0.975, top=0.79, bottom=0.17)
        a1 = fig.add_subplot(gs[0])
        a2 = fig.add_subplot(gs[1], sharex=a1)
        a3 = fig.add_subplot(gs[2], sharex=a1)
        KA.titel(fig, f"From the vibrations alone: {pt['n_ok']} of the {len(pt['rows'])} "
                      f"flight phases as the lab tests predicted",
                 sub + " · every second gets a pattern from the five bands only: "
                       "no height, no GPS")
        px_s = FIG[0] * DPI * a1.get_position().width / (x1 - x0)   # pixels per second
        char = DPI / 72 * 0.56                                       # pixels per character, per pt
        right = [-1e9, -1e9]                                         # labels above: two rows
        start, k = 0, 0
        for i in range(1, len(fase) + 1):                # 1 · the phases (barometer)
            if i < len(fase) and fase[i] == fase[start]:
                continue
            lo, hi = edges[start], edges[i]
            a1.axvspan(lo, hi, color="#e9e7e0" if k % 2 else "#f3f2ee", lw=0)
            label = names.get(fase[start], fase[start])
            mid = (lo + hi) / 2
            if (hi - lo) * px_s >= len(label) * 10.5 * char + 14:     # fits inside
                a1.text(mid, 0.5, label, ha="center", va="center", fontsize=10.5, color=INK)
            else:
                cx, half = (mid - x0) * px_s, len(label) * 9.5 * char / 2
                row = 0 if cx - half > right[0] + 10 else 1
                right[row] = cx + half
                a1.text(mid, 1.12 if row == 0 else 1.75, label, ha="center", va="bottom",
                        fontsize=9.5, color=INK2, transform=a1.get_xaxis_transform())
            start, k = i, k + 1
        cmap = ListedColormap(colors)                     # 2 · the pattern (FFT only)
        norm = BoundaryNorm(np.arange(-0.5, len(PATTERNS) + 0.5), cmap.N)
        a2.pcolormesh(edges, [0, 1], np.ma.masked_less(pat, 0).astype(float)[None, :],
                      cmap=cmap, norm=norm, shading="flat")
        for a, text in ((a1, "flight phase\n(barometer)"), (a2, "pattern\n(FFT only)")):
            a.set_ylim(0, 1)
            a.set_yticks([])
            a.grid(False)
            a.tick_params(labelbottom=False, length=0)
            for spine in a.spines.values():
                spine.set_visible(False)
            a.text(-0.012, 0.5, text, transform=a.transAxes, ha="right", va="center",
                   fontsize=10.5, color=INK2)
        ok = np.isfinite(tot) & (pat >= 0)               # 3 · how strong
        if ok.any():
            a3.plot(tt[ok], tot[ok], color=AXIS, lw=1.0, zorder=2)
            a3.scatter(tt[ok], tot[ok], c=[colors[p] for p in pat[ok]], s=22, zorder=3,
                       edgecolor=PAPER, linewidth=0.5)
            lo = max(3e-4, float(np.min(tot[ok])) * 0.6)
            hi = max(float(np.max(tot[ok])) * 1.8, QUIET_G * 3)
            a3.set_yscale("log")
            a3.set_ylim(lo, hi)
            ticks = [v for v in (0.001, 0.01, 0.1, 1.0, 10.0) if lo <= v <= hi]
            a3.set_yticks(ticks)
            a3.set_yticklabels([f"{v:g}" for v in ticks])
            a3.minorticks_off()
        a3.axhline(QUIET_G, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
        a3.text(x1, QUIET_G, f"quiet below {QUIET_G:g} g ", ha="right", va="bottom",
                fontsize=9.5, color=INK2)
        events(a3, r)
        a3.set_ylabel("vibration (g RMS)")
        a3.set_xlabel("time since the launch (s)")
        a3.set_title("How strong it vibrated: all five bands together")
        a1.set_xlim(x0, x1)
        handles = [Patch(facecolor=c, edgecolor="none", label=lab) for _, lab, c in PATTERNS]
        fig.legend(handles=handles, loc="lower center", ncol=len(PATTERNS), frameon=False,
                   bbox_to_anchor=(0.54, 0.012), fontsize=10.5, handlelength=1.4,
                   columnspacing=1.8)
        save(fig, path)
    return True


def fig_track(gps, r, sub, path):
    x, y, fix = gps["x"], gps["y"], gps["fix"]
    h = r["f"]["hoogte"] if r is not None else np.zeros(len(x))
    pts = np.column_stack([x[fix], y[fix]])
    hh = h[fix]
    title = (f"The CanSat landed {gps['distance']:.0f} m {compass(gps['bearing'])} "
             f"of the launch site")
    with plt.rc_context(STYLE):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.08, right=0.88, top=0.82, bottom=0.10)
        KA.titel(fig, title, sub + " · GPS PA1616D, 1 position per second")
        if len(pts) >= 2:
            segs = np.stack([pts[:-1], pts[1:]], axis=1)
            norm = Normalize(0, max(1.0, float(np.nanmax(hh))))
            lc = LineCollection(segs, cmap=SEQ_MARK, norm=norm, linewidths=2.5, zorder=3)
            lc.set_array((hh[:-1] + hh[1:]) / 2)
            a.add_collection(lc)
            cax = fig.add_axes([0.90, 0.2, 0.015, 0.5])
            cb = fig.colorbar(lc, cax=cax)
            cb.outline.set_visible(False)
            cax.set_title("height (m)", fontsize=10, color=INK2, pad=6)
        a.plot(0, 0, "o", ms=11, color=INK, markeredgecolor=PAPER, markeredgewidth=2, zorder=5)
        a.annotate("launch site", (0, 0), xytext=(10, -14), textcoords="offset points",
                   fontsize=11, color=INK)
        a.plot(gps["x_land"], gps["y_land"], "X", ms=13, color=ORANGE,
               markeredgecolor=PAPER, markeredgewidth=1.5, zorder=5)
        a.annotate(f"landing\n{gps['lat_land']:.5f}, {gps['lon_land']:.5f}",
                   (gps["x_land"], gps["y_land"]), xytext=(12, 6),
                   textcoords="offset points", fontsize=11, color=INK)
        xs = np.concatenate([[0.0, gps["x_land"]], pts[:, 0]]) if len(pts) else np.array([0.0])
        ys = np.concatenate([[0.0, gps["y_land"]], pts[:, 1]]) if len(pts) else np.array([0.0])
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        half = max(60.0, 0.62 * max(np.ptp(xs), np.ptp(ys)))
        a.set_xlim(cx - half * 1.6, cx + half * 1.6)      # 16:9: wider than high
        a.set_ylim(cy - half, cy + half)
        a.set_aspect("equal", adjustable="box")
        a.set_xlabel("east of the launch site (m)")
        a.set_ylabel("north of the launch site (m)")
        a.set_title("Ground track, coloured by height")
        save(fig, path)


def fig_radio(radios, r, sub, path):
    aligned = [x for x in radios if x["aligned"]]
    with plt.rc_context(STYLE):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=FIG,
                                     gridspec_kw={"width_ratios": [2.2, 1]})
        fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.12, wspace=0.25)
        best = max((x.get("share", 0) for x in radios), default=0)
        KA.titel(fig, f"Radio link: up to {best * 100:.0f}% of the packets arrived "
                      "during the flight" if aligned else "Radio link",
                 sub + " · LoRa 868 MHz, 1 packet per second")
        shade_phases(a1, r)
        events(a1, r)
        for k, x in enumerate(radios):
            c = SERIES[k % 3]
            a1.plot(x["t"], x["rssi"], lw=0, marker="o", ms=3.5, color=c,
                    label=f"{x['name']}")
        if r is not None and aligned:
            a1.set_xlim(*window(r))
        a1.set_ylabel("signal strength RSSI (dBm)")
        a1.set_xlabel("time since the launch (s)")
        a1.set_title("Signal strength (higher = stronger)")
        a1.legend(loc="upper right")
        names = [x["name"] for x in radios]
        vals = [x.get("share", float("nan")) * 100 for x in radios]
        yy = np.arange(len(radios))[::-1]
        for k, (yi, v) in enumerate(zip(yy, vals)):
            if np.isfinite(v):
                a2.barh(yi, v, height=0.55, color=SERIES[k % 3], zorder=3)
                inside = v >= 20
                a2.text(v - 2 if inside else v + 2, yi, f"{v:.0f}%", va="center",
                        ha="right" if inside else "left", fontsize=12,
                        color="white" if inside else INK, fontweight="bold")
        a2.set_yticks(yy)
        a2.set_yticklabels(names, fontsize=10)
        a2.set_xlim(0, 100)
        a2.grid(axis="y", visible=False)
        a2.set_xlabel("packets received during the flight (%)")
        a2.set_title("Received")
        save(fig, path)


# ═════════════════════════════════════════════════════════════
#  THE REPORT (HTML)
# ═════════════════════════════════════════════════════════════
CSS = """
:root { --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --line:#e1e0d9;
        --paper:#fcfcfb; --page:#f1f0ec; --blue:#2a78d6; --blue-soft:#eef4fc;
        --good:#0c7a0c; --good-soft:#e6f4e6; --warn:#a35200; --warn-soft:#fbeee2; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font: 16px/1.55 "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif; }
.page { max-width: 1120px; margin: 0 auto; padding: 32px 20px 64px; }
.sheet { background: var(--paper); border: 1px solid var(--line); border-radius: 14px;
         padding: 40px 48px; margin-bottom: 22px; }
.eyebrow { font-size: 13px; letter-spacing: .14em; text-transform: uppercase;
           color: var(--blue); font-weight: 700; margin: 0 0 6px; }
h1 { font-size: 40px; line-height: 1.15; margin: 0 0 8px; letter-spacing: -.01em; }
.meta { color: var(--ink2); margin: 0 0 26px; }
.question { border-left: 4px solid var(--blue); background: var(--blue-soft);
            padding: 16px 20px; border-radius: 0 10px 10px 0; margin: 0 0 12px; }
.question b { display: block; font-size: 12px; letter-spacing: .12em; text-transform: uppercase;
              color: var(--blue); margin-bottom: 4px; }
.question p { margin: 0; font-size: 19px; font-weight: 600; }
.mission { color: var(--ink2); margin: 10px 0 0; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 28px; }
.kpi { border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; background: #fff; }
.kpi .label { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.kpi .value { font-size: 28px; font-weight: 700; margin: 2px 0; font-variant-numeric: tabular-nums; }
.kpi .note { font-size: 13px; color: var(--ink2); }
.badge { display: inline-block; font-size: 12px; font-weight: 700; padding: 1px 8px; white-space: nowrap;
         border-radius: 99px; margin-left: 6px; vertical-align: 2px; }
.badge.ok { color: var(--good); background: var(--good-soft); }
.badge.check { color: var(--warn); background: var(--warn-soft); }
nav ol { columns: 2; column-gap: 48px; margin: 6px 0 0; padding-left: 26px; color: var(--ink2); }
nav li { margin: 0; padding: 3px 0; break-inside: avoid; }
nav a { color: var(--ink); text-decoration: none; }
nav a:hover { color: var(--blue); }
.sec-head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 6px; }
.sec-head .n { font-size: 15px; font-weight: 700; color: var(--blue); min-width: 28px; }
h2 { font-size: 26px; margin: 0; letter-spacing: -.005em; }
.lead { font-size: 18px; color: var(--ink); margin: 6px 0 22px 42px; }
figure { margin: 0 0 22px; }
figure img { width: 100%; height: auto; border: 1px solid var(--line); border-radius: 10px;
             display: block; background: var(--paper); }
figcaption { font-size: 13px; color: var(--ink2); margin-top: 6px; }
.cols { display: grid; grid-template-columns: 1.15fr 1fr; gap: 28px; }
h3 { font-size: 13px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted);
     margin: 0 0 8px; }
ul { margin: 0; padding-left: 20px; }
li { margin: 4px 0; }
table { width: 100%; border-collapse: collapse; font-size: 15px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
th.r { text-align: right; }
td.v { text-align: right; white-space: nowrap; font-weight: 600; }
table.plain td.v { text-align: left; white-space: normal; font-weight: 400; }
table.plain th.r { text-align: left; }
.tbl { overflow-x: auto; }
.kpi .value.long { font-size: 22px; line-height: 1.6; }
.note-box { background: #f7f6f2; border-radius: 10px; padding: 12px 16px; color: var(--ink2);
            font-size: 14px; margin-top: 16px; }
.formula { white-space: nowrap; font-family: Consolas, "Cascadia Mono", Menlo, monospace; font-size: 14px;
           background: #f4f3ef; padding: 1px 6px; border-radius: 5px; }
footer { color: var(--muted); font-size: 13px; text-align: center; margin-top: 10px; }
.small { font-size: 13px; color: var(--ink2); margin: 8px 0 0; }
table.wide { font-size: 14px; margin-bottom: 22px; }
table.wide th, table.wide td { padding: 7px 8px; }
@media (max-width: 820px) {
  .sheet { padding: 24px 18px; } h1 { font-size: 30px; }
  .kpis { grid-template-columns: repeat(2, 1fr); } .cols { grid-template-columns: 1fr; }
  nav ol { columns: 1; } .lead { margin-left: 0; }
  .kpi .value, .kpi .value.long { font-size: 20px; line-height: 1.4; }
  td.v { white-space: normal; }
}
@page { size: A4; margin: 14mm 12mm; }
@media print {
  html, body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { background: #fff; font-size: 14px; }
  .page { max-width: none; padding: 0; }
  .sheet { background: #fff; border: none; border-radius: 0; padding: 0; margin: 0;
           break-after: page; page-break-after: always; }
  .sheet.cover { break-after: auto; page-break-after: auto; margin-bottom: 30px; }
  section.sheet:last-of-type { break-after: auto; page-break-after: auto; }
  h1 { font-size: 32px; } h2 { font-size: 22px; }
  .lead { font-size: 16px; margin-left: 42px; }
  .kpis { grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 22px; }
  .kpi { padding: 10px 12px; } .kpi .label { font-size: 10px; letter-spacing: .06em; }
  .kpi .value { font-size: 21px; } .kpi .value.long { font-size: 16px; line-height: 1.65; }
  .kpi .note { font-size: 11.5px; }
  .cols { grid-template-columns: 1fr 1fr; gap: 22px; }
  nav ol { columns: 2; }
  table { font-size: 13px; } td.v { white-space: nowrap; } .tbl { overflow: visible; }
  table.wide { font-size: 11.5px; } table.wide th, table.wide td { padding: 5px 5px; }
  table.wide td.v { white-space: normal; } .small { font-size: 12px; }
  figcaption { font-size: 12px; } .note-box { font-size: 13px; }
  figure, table, .kpi, .cols, .question, .note-box { break-inside: avoid; page-break-inside: avoid; }
  h3 { break-after: avoid; page-break-after: avoid; }
  footer { margin-top: 18px; }
}
"""


def esc(s):
    return html.escape(str(s))


def img(path):
    with open(path, "rb") as fh:
        data = base64.b64encode(fh.read()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="">'


def table(rows, head=("", ""), plain=False):
    """Two columns: name and value. plain: the value as ordinary text."""
    cls = " class='plain'" if plain else ""
    out = [f"<div class='tbl'><table{cls}><thead><tr><th>{esc(head[0])}</th>"
           f"<th class='r'>{esc(head[1])}</th></tr></thead><tbody>"]
    for name, value in rows:
        out.append(f"<tr><td>{esc(name)}</td><td class='v'>{esc(value)}</td></tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def table_n(rows, head):
    out = ["<div class='tbl'><table><thead><tr>" + "".join(
        f"<th class='r'>{esc(h)}</th>" if i else f"<th>{esc(h)}</th>"
        for i, h in enumerate(head)) + "</tr></thead><tbody>"]
    for row in rows:
        out.append("<tr>" + "".join(
            f"<td class='v'>{esc(c)}</td>" if i else f"<td>{esc(c)}</td>"
            for i, c in enumerate(row)) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def table_k(rows, head, kinds):
    """A table with a kind per column: t = text (left, wraps), v = value
    (right), h = raw HTML (right), e.g. a badge."""
    def th(h, k):
        return f"<th>{esc(h)}</th>" if k == "t" else f"<th class='r'>{esc(h)}</th>"

    def td(c, k):
        if k == "t":
            return f"<td>{esc(c)}</td>"
        return f"<td class='v'>{c if k == 'h' else esc(c)}</td>"
    out = ["<div class='tbl'><table class='wide'><thead><tr>"
           + "".join(th(h, k) for h, k in zip(head, kinds)) + "</tr></thead><tbody>"]
    for row in rows:
        out.append("<tr>" + "".join(td(c, k) for c, k in zip(row, kinds)) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def bullets(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def badge(ok, good="OK", bad="check"):
    return (f"<span class='badge ok'>{good}</span>" if ok
            else f"<span class='badge check'>{bad}</span>")


class Report:
    def __init__(self, folder):
        self.folder = folder
        self.sections = []
        self.numbers = []           # (section, name, value)
        self.n_fig = 0

    def figure(self, path, caption):
        self.n_fig += 1
        return (f"<figure>{img(path)}<figcaption><b>Figure {self.n_fig}.</b> "
                f"{caption} · <i>{esc(os.path.relpath(path, self.folder))}</i>"
                f"</figcaption></figure>")

    def add(self, sid, title, lead, body):
        self.sections.append((sid, title, lead, body))

    def keep(self, section, rows):
        for name, value in rows:
            self.numbers.append((section, name, value))


def build(args, src):
    d, rows_in_file = load(src)
    if len(d["millis"]) < 5:
        raise ValueError("too few measurements in this file")
    d, restarted = KA.kies_vlucht(d)
    r = KA.analyse(d)
    base = os.path.splitext(src)[0]
    folder = base + "_report"
    figs = os.path.join(folder, "figures")
    os.makedirs(figs, exist_ok=True)
    for old in os.listdir(figs):                   # only the charts of this report
        if old.lower().endswith(".png"):
            os.remove(os.path.join(figs, old))
    team = args.team or TEAM_NAME
    src_name = os.path.basename(src)
    sub = f"{team} · {src_name}" if team else src_name
    is_radio = "rssi" in d                        # a ground-station file
    rep = Report(folder)

    fl = flight_numbers(d, r)
    lr = lapse_rate(d, r)
    vb = vibration_numbers(d, r)
    pt = vibration_patterns(d, r) if vb is not None else None
    gps = gps_numbers(d, r)
    q = quality_numbers(d, rows_in_file, restarted)
    q["radio"] = is_radio
    radios = []
    for p in args.radio or []:
        try:
            radios.append(radio_numbers(p, r))
        except (OSError, ValueError) as e:
            print(f"  radio file skipped: {p} ({e})")

    def fp(name):
        return os.path.join(figs, name)

    # ── 1. the flight ─────────────────────────────────────────
    if r is not None:
        KA.fig_vlucht(r, sub, fp("01_flight_overview.png"))
        ev = [("Launch", 0.0, 0.0), ("Highest point (apogee)", fl["t_top"], fl["apogee"]),
              ("Parachute opens", fl["t_open"], float(np.interp(fl["t_open"], r["t"],
                                                                 r["f"]["hoogte"]))),
              ("Landing" if fl["landed"] else "End of the descent data", fl["t_land"], 0.0)]
        rows = [("Highest point above the launch site", num(fl["apogee"], 0, "m")),
                ("Time to the highest point", num(fl["t_top"], 0, "s")),
                ("Flight time, launch to landing", duration(fl["t_land"])),
                ("Time under the parachute", duration(fl["t_land"] - fl["t_open"])),
                ("Fastest climb (barometer)", num(fl["climb_max"], 0, "m/s")),
                ("Mean descent rate, apogee to landing", num(fl["v_mean"], 1, "m/s")),
                ("Waiting on the pad before the launch", duration(fl["pad_seconds"]))]
        rep.keep("Flight", rows)
        body = ("<p class='note-box'>This file comes from a ground station (radio): 19 values "
                "per second. The SD card holds more: 34 values per second, including the "
                "largest acceleration of every second. Use the SD card file for the full "
                "analysis.</p>" if is_radio else "")
        body += rep.figure(fp("01_flight_overview.png"),
                          "Height from the barometer (top) and the largest acceleration in "
                          "each second (bottom), with the four moments of the flight.")
        body += "<div class='cols'><div><h3>The moments</h3>" + table_n(
            [(n, f"{tt:.0f} s", f"{hh:.0f} m") for n, tt, hh in ev],
            ("moment", "time since launch", "height")) + "</div><div><h3>Key numbers</h3>" + \
            table(rows) + "</div></div>"
        rep.add("flight", "The flight at a glance",
                f"The CanSat climbed to <b>{fl['apogee']:.0f} m</b> in {fl['t_top']:.0f} s, "
                f"opened its parachute and landed after <b>{duration(fl['t_land'])}</b>.", body)
    else:
        rep.add("flight", "The flight at a glance",
                "No flight was found in this file: the height never rose 30 m above the "
                "start. The report shows the sensors and the data quality only.",
                "<p class='note-box'>Is this the file of the flight? Take the newest file "
                "from the SD card (the highest number), e.g. cansat27_004.csv.</p>")

    # ── 2. primary mission ────────────────────────────────────
    fig_atmosphere(d, r, fl, sub, fp("02_temperature_pressure.png"))
    body = rep.figure(fp("02_temperature_pressure.png"),
                      f"Temperature and pressure, one value per second, measured by the {BAROMETER}.")
    rows = []
    if fl is not None:
        p0 = args.sea_level
        rows = [("Pressure on the pad", num(fl["p_pad"], 1, "hPa")),
                ("Pressure at the highest point", num(fl["p_top"], 1, "hPa")),
                ("Temperature on the pad", num(fl["T_pad"], 1, "°C")),
                ("Temperature at the highest point", num(fl["T_top"], 1, "°C")),
                (f"Launch site above sea level (p₀ = {p0:.2f} hPa)",
                 num(site_altitude(fl["p_pad"], p0), 0, "m"))]
    if lr is not None:
        fig_lapse(lr, fl, sub, fp("03_temperature_height.png"))
        body += rep.figure(fp("03_temperature_height.png"),
                           "Every dot is one second under the parachute. The straight line is "
                           "a least-squares fit; the dashed line is the standard atmosphere.")
        rows += [("Temperature change with height", f"{signed(lr['slope'])} ± {lr['se']:.1f} °C/km"),
                 ("Standard atmosphere", "−6.5 °C/km"),
                 ("Fit quality R²", num(lr["r2"], 2))]
        if lr["tau"] > 0:
            rows += [("Response time of the sensor τ (estimate)", f"{lr['tau']:.0f} s"),
                     ("Without that correction", f"{signed(lr['slope_raw'])} °C/km "
                                                 f"(R² = {lr['r2_raw']:.2f})")]
    rep.keep("Primary mission", rows)
    explain = [
        f"The {BAROMETER} measures the air pressure and the temperature once per second. "
        "The CanSat sends both to the ground station every second.",
        "The pressure gives the height: <span class='formula'>h = 44330 · (1 − (p / p₀)^(1/5.255))</span>. "
        "The height zero is the pressure on the pad.",
        "The temperature sensor sits inside the can and follows the air with a delay τ. We "
        "correct for it: <span class='formula'>T<sub>air</sub> ≈ T<sub>sensor</sub> + τ · dT/dt</span>, "
        "with the τ that makes the profile the straightest."]
    body += f"<div class='cols'><div><h3>How we measured</h3>{bullets(explain)}</div>" \
            f"<div><h3>Key numbers</h3>{table(rows) if rows else '—'}</div></div>"
    lead = ("The main mission: air temperature and air pressure, every second." if lr is None
            else f"Temperature and pressure were measured every second. On the way down the "
                 f"temperature changed <b>{signed(lr['slope'])} °C per km</b>; the standard "
                 f"atmosphere says −6.5 °C per km.")
    rep.add("primary", "Primary mission: temperature and pressure", lead, body)

    # ── 3. research question: forces ──────────────────────────
    if r is not None and fig_loads(r, sub, fp("04_loads.png")):
        valid = [(n, g, s) for n, g, s in r["momenten"] if np.isfinite(g)]
        gname, gmax, _ = max(valid, key=lambda x: x[1])
        rows = [(f"Load {at_moment(n)}", f"{at_least(r, n)}{g:.1f} g  ·  "
                 f"{at_least(r, n)}{g * K.G * K.MASS_KG:.0f} N") for n, g, s in valid]
        gpre = at_least(r, gname)
        rows.append(("ESA design load", f"{K.DESIGN_LOAD_G:.0f} g  ·  {K.design_force_n():.0f} N"))
        rep.keep("Forces", rows)
        clipped = [n for n, _, _ in valid if r["afgeknipt"].get(n)]
        explain = [
            "The accelerometer (LSM6DSO) measures 416 times per second how many g the CanSat "
            "feels. The flight computer keeps the largest value of every second.",
            "The load factor n is 1 g when the CanSat stands still. Every part then pushes or "
            "pulls with n times its own weight: <span class='formula'>F = m · n · g</span>.",
            "At the launch and the landing the force comes in at the bottom (the can is pressed). "
            "When the parachute opens, it comes in at the top (the can is pulled)."]
        if not r["heeft_piek"]:
            explain.append("<b>Estimate:</b> this file has no peak acceleration, so the loads "
                           "come from the BNO055 and the parachute model. Use the SD card file.")
        if clipped:
            explain.append(f"<b>Sensor limit:</b> at {' and '.join(MOMENT.get(n, n) for n in clipped)} "
                           "the sensor reached 16 g. The real load was at least that large.")
        body = rep.figure(fp("04_loads.png"), "The largest load at each moment, with the sensor "
                          "limit (16 g) and the ESA design load (20 g).")
        body += f"<div class='cols'><div><h3>How we measured</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        rep.add("forces", "Research question 1: the forces on the CanSat",
                f"The largest load was <b>{gpre}{gmax:.1f} g {at_moment(gname)}</b>: "
                f"{gpre}{gmax * K.G * K.MASS_KG:.0f} N on a {K.MASS_KG * 1000:.0f} g CanSat. "
                f"{'That is below' if gmax < K.DESIGN_LOAD_G else 'That reaches'} the ESA "
                f"design load of 20 g.", body)

    # ── 4. research question: vibrations ──────────────────────
    if vb is not None:
        fig_fft_explained(fp("05_fft_explained.png"))
        body = rep.figure(fp("05_fft_explained.png"),
                          "How the flight computer turns 1.23 s of vibration into five numbers. "
                          "A made-up signal: a slow swing of 3.3 Hz with a fast vibration of 85 Hz.")
        if fig_vibration_timeline(d, r, vb, sub, fp("06_vibration_timeline.png")):
            body += rep.figure(fp("06_vibration_timeline.png"),
                               "Top: the vibration in each of the five frequency bands, every "
                               "second (darker = stronger, log scale). Bottom: the strongest "
                               "frequency in each second.")
        if fig_fingerprint(vb, sub, fp("07_vibration_fingerprint.png")):
            body += rep.figure(fp("07_vibration_fingerprint.png"),
                               "The median vibration per band in each phase of the flight.")
        if fig_top_frequencies(vb, sub, fp("08_frequent_frequencies.png")):
            body += rep.figure(fp("08_frequent_frequencies.png"),
                               "How often each frequency was the strongest one, during the flight.")
        rows = []
        if "max_g" in vb:
            rows.append(("Strongest vibration", f"{vb['max_g']:.2f} g RMS  ·  {vb['max_band']}"))
            rows.append(("…in the phase", vb["max_phase"]))
        if "ratio" in vb:
            j = int(np.argmax(vb["ratio"]))
            rows.append(("Ascent against the pad", f"{vb['ratio'][j]:.0f} × stronger ({BANDS[j][1]})"))
        for k, (hz, n) in enumerate(vb["top"][:3], 1):
            rows.append((f"Most frequent strong frequency #{k}", f"{hz:.0f} Hz  ·  {n} s"))
        rows.append(("Seconds with a strong vibration (> 0.05 g)", str(vb["n_strong"])))
        rep.keep("Vibrations", rows)
        explain = [
            "The LSM6DSO measures the acceleration along its Z-axis 416 times per second. "
            "Every 512 samples (1.23 s) the flight computer removes the steady part (gravity), "
            "applies a Hamming window and makes an FFT: it splits the vibration into "
            "frequencies.",
            "It keeps the strongest frequency (<i>fft_peak_hz</i>) with its amplitude "
            "(<i>fft_peak_amp</i>, in g), and the vibration in five bands, from slow "
            "(0–10 Hz) to fast (120–208 Hz).",
            "A band value is an RMS: a kind of average strength. For one sine: "
            "<span class='formula'>RMS = amplitude / √2</span>.",
            "Faster than 208 Hz cannot be measured: that is half of the sample rate "
            "(the Nyquist limit)."]
        body += f"<div class='cols'><div><h3>How we measured</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        lead = "Every phase of the flight shakes the CanSat in its own way."
        if "max_g" in vb:
            lead = (f"The strongest vibration was <b>{vb['max_g']:.2f} g RMS</b> in the "
                    f"{vb['max_band']} band, during the {vb['max_phase']}. Every phase has its own "
                    f"vibration fingerprint.")
        rep.add("vibrations", "Research question 2: the vibrations", lead, body)

    # ── 4b. research question 2: the phases in the vibrations ──
    if pt is not None and pt["rows"]:
        body = ""
        if fig_phase_recognition(d, r, pt, sub, fp("09_phase_recognition.png")):
            body += rep.figure(fp("09_phase_recognition.png"),
                               "Top: the flight phases from the barometer. Middle: the vibration "
                               "pattern of every second, from the five bands only. Bottom: how "
                               "strong the vibration was, all bands together.")
        pname = [lab for _, lab, _ in PATTERNS]
        rowsn, keep = [], []
        for x in pt["rows"]:
            seen = f"{pname[x['mode']]} ({x['share'] * 100:.0f}\u00a0%)"
            if x["expected"] == "all" and x["mode"] != len(PATTERNS) - 1:
                seen += f"; a shock in {x['seen']} s" if x["seen"] else "; no shock"
            if x["mode"] == 0:                           # quiet: no band stands out
                band = "—"
            else:
                f = x["f_typ"]
                band = x["band"] + (f" · {num(f, 1 if f < 10 else 0, 'Hz')}"
                                    if np.isfinite(f) else "")
            rowsn.append((x["label"], x["expected_text"], seen, band, g_text(x["level"]),
                          badge(x["match"], "as expected", "different")))
            keep += [(f"{x['label']}: expected", x["expected_text"]),
                     (f"{x['label']}: seen most", seen),
                     (f"{x['label']}: strongest band and frequency", band),
                     (f"{x['label']}: vibration level (median)", g_text(x["level"])),
                     (f"{x['label']}: as the lab tests predicted", "yes" if x["match"] else "no")]
        body += table_k(rowsn, ("phase", "expected from the lab tests", "seen most",
                                "strongest band · frequency", "level", "result"),
                        "tttvvh")
        limits = [
            "<b>Slowest:</b> about 0.8 Hz. One FFT looks at 1.23 s; a slower movement does "
            "not fit in it.",
            "<b>Finest step:</b> 0.81 Hz between two frequencies (416 / 512). The flight "
            "computer refines the strongest peak.",
            "<b>Fastest:</b> 208 Hz, half of 416. A faster vibration is filtered out, or shows "
            "up at a mirrored frequency (lab test 4: 230 Hz looks like 186 Hz).",
            "<b>One direction:</b> only the Z-axis of the LSM6DSO. Sideways vibrations are "
            "not in the FFT.",
            "<b>A new FFT every 1.23 s.</b> A short shock is spread over that time. Its size "
            "is better in the largest acceleration of each second (research question 1).",
            "<b>Sensor noise:</b> about 0.001 g per band. A weaker vibration cannot be seen."]
        env = [(lab, f"{g_text(v)} · {ph}") for lab, v, ph in pt.get("envelope", [])]
        if "total_max" in pt:
            env.append(("all bands together", f"{g_text(pt['total_max'][0])} · "
                                              f"{pt['total_max'][1]}"))
        keep += [(f"Envelope {lab}", v) for lab, v in env]
        rep.keep("Vibration patterns", keep)
        body += (f"<div class='cols'><div><h3>What our FFT can and cannot see</h3>"
                 f"{bullets(limits)}</div><div><h3>The vibration envelope</h3>"
                 f"{table(env, ('band', 'highest in the flight'))}<p class='small'>The highest "
                 f"value in each band during the flight: what a shaker table must reach to "
                 f"repeat our flight in the lab.</p></div></div>")
        differ = [x["label"] for x in pt["rows"] if not x["match"]]
        lead = (f"From the five bands alone, without height or GPS, <b>{pt['n_ok']} of the "
                f"{len(pt['rows'])} flight phases</b> looked the way our lab tests predicted.")
        if differ:
            lead += f" Different: {esc(', '.join(differ))}."
        rep.add("phases", "Research question 2: the flight phases in the vibrations", lead, body)

    # ── 5. research question: zones ───────────────────────────
    if r is not None and r["krachten"]:
        KA.fig_kracht_hoogte(r, sub, fp("10_force_height.png"))
        KA.fig_zones(r, sub, fp("11_zones.png"))
        bottom = max(((n, F[0]) for n, F in r["krachten"].items()), key=lambda x: x[1])
        top = max(((n, F[-1]) for n, F in r["krachten"].items()), key=lambda x: x[1])
        bpre, tpre = at_least(r, bottom[0]), at_least(r, top[0])
        rows = [("Most force at the bottom",
                 f"{bpre}{bottom[1]:.0f} N  ·  {MOMENT.get(bottom[0], bottom[0])}"),
                ("Most force at the top", f"{tpre}{top[1]:.0f} N  ·  {MOMENT.get(top[0], top[0])}")]
        lead = (f"The <b>bottom</b> carried the most: {bpre}{bottom[1]:.0f} N at "
                f"{MOMENT.get(bottom[0], bottom[0])}. The top carried {tpre}{top[1]:.0f} N at "
                f"{MOMENT.get(top[0], top[0])}.")
        if r["volledig"]:
            om, z = r["omhulsel"], r["z"]
            jmin = int(np.argmin(om[1:-1])) + 1
            rows.append(("Least loaded height in the can",
                         f"{z[jmin] * 1000:.0f} mm  ·  {om[jmin]:.0f} N"))
            lead += f" The least loaded zone is around {z[jmin] * 1000:.0f} mm from the bottom."
        rows.append(("ESA design force (20 g on the bottom)", f"{K.design_force_n():.0f} N"))
        rep.keep("Zones", rows)
        explain = [
            "A horizontal slice of the can carries all the mass on the far side of it, seen from "
            "where the force comes in: <span class='formula'>N(z) = n · g · m<sub>far</sub>(z)</span>.",
            "So the closer to where the force comes in, the larger the force.",
            f"The mass ({K.MASS_KG * 1000:.0f} g) and the heavy parts are filled in in "
            "dashboard/krachten.py. Only forces along the axis of the can are modelled."]
        body = rep.figure(fp("10_force_height.png"), "The force through the can at each height, "
                          "for each moment of the flight.")
        body += rep.figure(fp("11_zones.png"), "The same forces as colours on the can: green is "
                           "little, red is close to the ESA design load.")
        body += f"<div class='cols'><div><h3>How we calculated</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        rep.add("zones", "Research question 3: which zones carry the most load?", lead, body)

    # ── 6. the parachute ──────────────────────────────────────
    if r is not None and np.isfinite(fl["cd"]):
        KA.fig_cd(r, sub, fp("12_parachute_cd.png"))
        KA.fig_controle(r, sub, fp("13_parachute_check.png"))
        lo, hi = K.DESCENT_RATE_MS
        in_range = lo <= fl["v_rustig"] <= hi
        rows = [("Steady descent rate", f"{fl['v_rustig']:.1f} m/s ({fl['v_p10']:.1f}–{fl['v_p90']:.1f})"),
                ("ESA requirement", f"{lo:.0f}–{hi:.0f} m/s"),
                ("Drag coefficient Cd", f"{fl['cd']:.2f} ({fl['cd_p10']:.2f}–{fl['cd_p90']:.2f})"),
                ("Change of Cd per 100 m", num(fl["cd_per_100m"], 3)),
                ("Predicted descent rate at the ground", num(fl["v_grond"], 1, "m/s")),
                ("Load when the parachute opened (model)", num(fl["open_model"], 1, "g")),
                ("Parachute: diameter, area",
                 f"{K.PARACHUTE_DIAMETER_M * 100:.0f} cm, {K.parachute_area_m2():.3f} m²")]
        rep.keep("Parachute", rows)
        explain = [
            "In the steady descent the drag equals the weight. Then "
            "<span class='formula'>Cd = 2 · m · g / (ρ · v² · A)</span>.",
            "The air density comes from our own pressure and temperature: "
            "<span class='formula'>ρ = p / (287 · T)</span>. So the main mission helps our own "
            "research.",
            "High up the air is thinner, so the CanSat falls faster there, but Cd stays the same."]
        body = rep.figure(fp("12_parachute_cd.png"), "Left: the descent rate against height, with "
                          "the parachute model. Right: Cd in each second of the steady descent.")
        body += rep.figure(fp("13_parachute_check.png"), "Check: the load the parachute model "
                           "predicts, next to what the sensors measured.")
        body += f"<div class='cols'><div><h3>How we calculated</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        rep.add("parachute", "The parachute",
                f"The CanSat came down at <b>{fl['v_rustig']:.1f} m/s</b> "
                f"{badge(in_range, 'within ESA 8–11 m/s', 'outside ESA 8–11 m/s')}. "
                f"Our parachute has <b>Cd = {fl['cd']:.2f}</b>.", body)

    # ── 7. energy ─────────────────────────────────────────────
    if r is not None and "p_mgv" in r:
        KA.fig_energie(r, sub, fp("14_energy.png"))
        rows = [("Height energy at the apogee", num(r["e_top"] / 1000, 2, "kJ")),
                ("Energy the parachute turned into heat", num(r["e_omgezet"] / 1000, 2, "kJ")),
                ("Power of the parachute (steady descent)", num(r["p_mgv"], 0, "W")),
                ("Motion energy just before the landing", num(r.get("e_kin_land", float("nan")), 1, "J"))]
        rep.keep("Energy", rows)
        explain = ["Height energy <span class='formula'>m · g · h</span>, motion energy "
                   "<span class='formula'>½ · m · v²</span> (vertical).",
                   "Under the parachute the CanSat loses <span class='formula'>m · g · v</span> "
                   "every second: the parachute turns it into heat and swirls of air."]
        body = rep.figure(fp("14_energy.png"), "The energy of the CanSat, and the power of the "
                          "parachute.")
        body += f"<div class='cols'><div><h3>How we calculated</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        rep.add("energy", "Energy",
                f"At the apogee the CanSat had {r['e_top'] / 1000:.2f} kJ of height energy. "
                f"The parachute turned about {r['p_mgv']:.0f} W into heat on the way down.", body)

    # ── 8. GPS ────────────────────────────────────────────────
    if "x" in gps:
        fig_track(gps, r, sub, fp("15_ground_track.png"))
        rows = [("Distance launch site → landing", num(gps["distance"], 0, "m")),
                ("Direction", f"{compass(gps['bearing'])} ({gps['bearing']:.0f}°)"),
                ("Landing position", f"{gps['lat_land']:.5f}, {gps['lon_land']:.5f}"),
                ("GPS fix during the flight", f"{gps['share'] * 100:.0f} %")]
        if "drift_speed" in gps:
            rows.insert(2, ("Drift under the parachute",
                            f"{gps['drift_speed']:.1f} m/s towards the {compass(gps['drift_course'])}"))
        if gps.get("utc_launch"):
            rows.append(("GPS time of the launch (UTC)", gps["utc_launch"]))
        rep.keep("GPS", rows)
        explain = ["Under the parachute the CanSat drifts with the wind. Its speed over the "
                   "ground and its direction come from the GPS.",
                   "The wind blows from the opposite direction of the drift."]
        body = rep.figure(fp("15_ground_track.png"), "The path over the ground, in metres from "
                          "the launch site.")
        body += f"<div class='cols'><div><h3>How we measured</h3>{bullets(explain)}</div>" \
                f"<div><h3>Key numbers</h3>{table(rows)}</div></div>"
        rep.add("gps", "Drift and landing site",
                f"The CanSat landed <b>{gps['distance']:.0f} m {compass(gps['bearing'])}</b> "
                f"of the launch site.", body)

    # ── 9. radio ──────────────────────────────────────────────
    if radios:
        fig_radio(radios, r, sub, fp("16_radio_link.png"))
        rowsn = [(x["name"], str(x["packets"]),
                  f"{x['share'] * 100:.0f} %" if x["aligned"] else "—",
                  num(x["rssi_med"], 0, "dBm"), num(x["rssi_min"], 0, "dBm"),
                  num(x["snr_med"], 1, "dB")) for x in radios]
        rep.keep("Radio", [(f"{x['name']}: received in the flight",
                            f"{x['share'] * 100:.0f} %" if x["aligned"] else "—") for x in radios])
        body = rep.figure(fp("16_radio_link.png"), "Signal strength of every packet, and the "
                          "share of the packets that arrived during the flight.")
        body += table_n(rowsn, ("ground station", "packets", "in the flight", "RSSI median",
                                "RSSI weakest", "SNR median"))
        body += ("<p class='note-box'>RSSI: how strong the signal arrives (−50 dBm is strong, "
                 "−120 dBm is the limit). SNR: how far the signal is above the noise; LoRa still "
                 "works down to about −7 dB. Each receiver is aligned with the SD card at the "
                 "highest point.</p>")
        rep.add("radio", "The radio link",
                "Every second the CanSat sent one packet with 19 values to the ground stations.",
                body)

    # ── 10. data quality ──────────────────────────────────────
    checks = [
        ("Measurements used", f"{q['rows']} rows", True),
        ("Log rate", f"{q['rate']:.2f} per second", 0.9 <= q["rate"] <= 1.1),
        ("Seconds received" if is_radio else "Seconds on the SD card",
         f"{q['complete'] * 100:.1f} %", q["complete"] > 0.97),
        ("Gaps longer than 1.6 s", f"{q['gaps']} (longest {q['longest_gap']:.1f} s)", q["gaps"] == 0),
        (f"Barometer {BAROMETER}", f"{q['bmp'] * 100:.0f} % valid", q["bmp"] > 0.99),
        ("Orientation BNO055", f"{q['bno'] * 100:.0f} % valid", q["bno"] > 0.99),
        ("Vibrations LSM6DSO (FFT)", f"{q['lsm'] * 100:.0f} % valid", q["lsm"] > 0.99),
    ] + ([] if is_radio else [
        ("Peak acceleration", f"{q['peak'] * 100:.0f} % valid", q["peak"] > 0.99)]) + [
        ("Microphone", f"{q['audio'] * 100:.0f} % valid", q["audio"] > 0.99),
        ("GPS fix", f"{gps['share'] * 100:.0f} % of the seconds"
         + (" in the flight" if r is not None else ""), gps["share"] > 0.5),
    ] + ([] if is_radio else [
        ("Sensor limit 16 g reached", f"{q['clipped']} s", q["clipped"] == 0)]) + [
        ("Teensy restarted during the file", "yes" if q["restarted"] else "no", not q["restarted"]),
    ]
    body = ("<div class='tbl'><table><thead><tr><th>check</th><th class='r'>result</th>"
            "<th class='r'>status</th></tr></thead><tbody>" +
            "".join(f"<tr><td>{esc(a)}</td><td class='v'>{esc(b)}</td><td class='v'>"
                    f"{badge(c)}</td></tr>" for a, b, c in checks) + "</tbody></table></div>")
    body += ("<p class='note-box'>Every scientific result needs this: how reliable are the "
             "measurements? Explain each “check” in the presentation.</p>")
    rep.keep("Data quality", [(a, b) for a, b, _ in checks])
    n_ok = sum(1 for _, _, c in checks if c)
    rep.add("quality", "Data quality",
            f"{n_ok} of the {len(checks)} checks are OK. The "
            f"{'ground station received' if is_radio else 'SD card holds'} "
            f"{q['complete'] * 100:.1f} % of all seconds.", body)

    # ── 11. findings and questions ────────────────────────────
    find = []
    if fl is not None:
        find.append(f"The CanSat reached {fl['apogee']:.0f} m above the launch site and landed "
                    f"after {duration(fl['t_land'])}.")
        if np.isfinite(fl["v_rustig"]):
            find.append(f"Under the parachute it fell at {fl['v_rustig']:.1f} m/s; ESA asks "
                        f"8–11 m/s. The parachute has Cd = {fl['cd']:.2f}.")
    if r is not None:
        valid = [(n, g) for n, g, _ in r["momenten"] if np.isfinite(g)]
        if valid:
            n, g = max(valid, key=lambda x: x[1])
            pre = at_least(r, n)
            find.append(f"The largest load was {pre}{g:.1f} g ({pre}{g * K.G * K.MASS_KG:.0f} N) "
                        f"{at_moment(n)}; the ESA design load is 20 g.")
    if vb is not None and "max_g" in vb:
        find.append(f"The strongest vibration was {vb['max_g']:.2f} g RMS in the {vb['max_band']} "
                    f"band, during the {vb['max_phase']}.")
    if pt is not None and pt["rows"]:
        differ = [x["label"] for x in pt["rows"] if not x["match"]]
        find.append(f"From the vibrations alone, {pt['n_ok']} of the {len(pt['rows'])} flight "
                    f"phases looked as our lab tests predicted"
                    + (f" (different: {', '.join(differ)})." if differ else "."))
        desc = next((x for x in pt["rows"] if x["key"] == "descent"), None)
        if desc is not None and np.isfinite(desc["f_typ"]):
            find.append(f"Under the parachute the strongest frequency was about "
                        f"{desc['f_typ']:.1f} Hz, in the {desc['band']} band.")
    if r is not None and r["krachten"]:
        find.append(f"The bottom of the can carried the most force ({bpre}{bottom[1]:.0f} N at "
                    f"{MOMENT.get(bottom[0], bottom[0])}); the top {tpre}{top[1]:.0f} N at "
                    f"{MOMENT.get(top[0], top[0])}.")
    if lr is not None:
        find.append(f"The temperature changed {signed(lr['slope'])} °C per km on the way down "
                    f"(standard atmosphere: −6.5 °C per km).")
    if "distance" in gps:
        find.append(f"The CanSat landed {gps['distance']:.0f} m {compass(gps['bearing'])} of the "
                    f"launch site.")
    questions = [
        "Which phase loaded the CanSat the most, and why?",
        "Which zone of the can could be lighter? Which zone must be stronger?",
        "Which phase had the strongest vibrations, and what caused them?",
        "Which lab test predicted the flight best? Which phase looked different, and why?",
        "What can our FFT not see: faster than 208 Hz, sideways, shorter than 1.2 s?",
        "Do the descent rate and the Cd match the design of the parachute?",
        "How reliable are these numbers: sensor limits, sample rate, model assumptions?",
        "What would you change in the next CanSat?"]
    body = (f"<div class='cols'><div><h3>What the data show</h3>{bullets(find) if find else '—'}"
            f"</div><div><h3>Questions for the presentation</h3>{bullets(questions)}</div></div>"
            "<p class='note-box'>The computer fills in the measurements. The interpretation "
            "and the conclusion are yours.</p>")
    rep.add("findings", "Answer to the research question",
            esc(RESEARCH_QUESTION), body)

    # ── 12. methods ───────────────────────────────────────────
    meth = [
        ("Flight computer", "Teensy 4.1, one log line per second on the SD card (34 values)"),
        ("Pressure, temperature", f"{BAROMETER}, 1 per second"),
        ("Acceleration, vibrations", "LSM6DSO, 416 per second, ±16 g; FFT of 512 samples"),
        ("FFT", "512 samples (1.23 s) on the Z-axis, steady part removed, Hamming window; "
                "frequency step 0.81 Hz, up to 208 Hz"),
        ("Vibration pattern of a second", f"quiet: all bands together below {QUIET_G:g} g · "
                                          f"shock: every band at least {ALL_BANDS_G:g} g · "
                                          "otherwise the strongest band: slow 0–10 Hz, "
                                          "medium 10–60 Hz, fast 60–208 Hz"),
        ("Expected patterns", "from our six FFT lab tests in class"),
        ("Orientation", "BNO055"),
        ("Position", "GPS PA1616D, 1 per second"),
        ("Mass of the CanSat", f"{K.MASS_KG * 1000:.0f} g (dashboard/krachten.py)"),
        ("Parachute", f"diameter {K.PARACHUTE_DIAMETER_M * 100:.0f} cm, area "
                      f"{K.parachute_area_m2():.3f} m²"),
        ("Launch", "the start of the climb"),
        ("Parachute opens", "the fastest fall in the first 20 s after the highest point"),
        ("Steady descent", "speed within 20 % of the median, no acceleration"),
        ("Landing", "the descent rate falls below 1 m/s"),
    ]
    rep.add("methods", "Methods and settings",
            "How the numbers in this report were made.", table(meth, ("item", "value"), plain=True))

    # ── write ─────────────────────────────────────────────────
    out = write_html(rep, team, src_name, fl, vb, q, gps, r, d, folder)
    # for Excel in Belgium: ";" between the columns, and a BOM so that ° ≥ − show well
    with open(os.path.join(folder, "key_numbers.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["section", "number", "value"])
        w.writerows(rep.numbers)
    return out, folder, fl, rep


def kpis(fl, vb, q, r):
    tiles = []
    if fl is not None:
        tiles.append(("Apogee", num(fl["apogee"], 0, "m"), "above the launch site"))
        tiles.append(("Flight time", duration(fl["t_land"]), "launch to landing"))
        if np.isfinite(fl["v_rustig"]):
            lo, hi = K.DESCENT_RATE_MS
            ok = lo <= fl["v_rustig"] <= hi
            tiles.append(("Descent rate", num(fl["v_rustig"], 1, "m/s"),
                          f"steady descent {badge(ok, 'ESA OK', 'ESA 8–11')}"))
            tiles.append(("Drag coefficient", f"Cd {fl['cd']:.2f}",
                          f"range {fl['cd_p10']:.2f}–{fl['cd_p90']:.2f}"))
    if r is not None:
        valid = [(n, g) for n, g, _ in r["momenten"] if np.isfinite(g)]
        if valid:
            n, g = max(valid, key=lambda x: x[1])
            pre = at_least(r, n)
            tiles.append(("Highest load", pre + num(g, 1, "g"),
                          f"{pre}{g * K.G * K.MASS_KG:.0f} N {at_moment(n)}"))
    if vb is not None and "max_g" in vb:
        tiles.append(("Strongest vibration", f"{vb['max_g']:.2f} g",
                      f"{vb['max_band']}, {vb['max_phase']}"))
    if fl is not None:
        tiles.append(("Temperature", f"{fl['T_pad']:.1f} → {fl['T_top']:.1f} °C",
                      "pad → apogee"))
    tiles.append(("Data received" if q.get("radio") else "Data on the SD card",
                  f"{q['complete'] * 100:.1f} %", "of all seconds"))
    return tiles[:8]


def write_html(rep, team, src_name, fl, vb, q, gps, r, d, folder):
    now = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    title = f"{team} — Flight report" if team else "CanSat 2027 — Flight report"
    kp = "".join(f"<div class='kpi'><div class='label'>{esc(a)}</div><div class='value"
                 f"{' long' if len(b) > 9 else ''}'>{esc(b)}</div><div class='note'>{c}</div>"
                 f"</div>" for a, b, c in kpis(fl, vb, q, r))
    toc = "".join(f"<li><a href='#{sid}'>{esc(t)}</a></li>" for sid, t, _, _ in rep.sections)
    when = f" · launch at {gps['utc_launch']} UTC" if gps.get("utc_launch") else ""
    head = (f"<section class='sheet cover'><p class='eyebrow'>CanSat 2027 · Flight report</p>"
            f"<h1>{esc(team) if team else 'The flight of our CanSat'}</h1>"
            f"<p class='meta'>Data: {esc(src_name)} "
            f"({'ground station, radio' if q.get('radio') else 'SD card'}) · {q['rows']} measurements"
            f"{esc(when)} · report made {esc(now)}</p>"
            f"<div class='question'><b>Research question</b><p>{esc(RESEARCH_QUESTION)}</p></div>"
            f"<p class='mission'><b>Primary mission:</b> {esc(PRIMARY_MISSION)}</p>"
            f"<div class='kpis'>{kp}</div></section>"
            f"<section class='sheet'><nav><h3>Contents</h3><ol>{toc}</ol></nav></section>")
    body = []
    for k, (sid, t, lead, content) in enumerate(rep.sections, 1):
        body.append(f"<section class='sheet' id='{sid}'><div class='sec-head'><span class='n'>"
                    f"{k:02d}</span><h2>{esc(t)}</h2></div><p class='lead'>{lead}</p>"
                    f"{content}</section>")
    page = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{esc(title)}</title><style>{CSS}</style></head><body><div class='page'>"
            f"{head}{''.join(body)}<footer>Made with tools/flight_report.py · CanSat 2027 · "
            f"{esc(src_name)}</footer></div></body></html>")
    out = os.path.join(folder, "flight_report.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    return out


def main():
    p = argparse.ArgumentParser(description="CanSat 2027 flight report (English)")
    p.add_argument("csv", nargs="?", help="the CSV file from the SD card")
    p.add_argument("--radio", nargs="*", default=[], help="CSV files of the ground stations")
    p.add_argument("--team", default="", help="name on the report")
    p.add_argument("--sea-level", type=float, default=1013.25,
                   help="sea-level pressure of the day (hPa)")
    p.add_argument("--no-open", action="store_true", help="do not open the browser")
    args = p.parse_args()
    src = args.csv
    if not src:
        print("CanSat 2027 — flight report")
        src = input("Drag the CSV file from the SD card into this window, then press Enter:\n").strip()
    src = src.strip().strip('"').strip("'")
    if not os.path.isfile(src):
        print(f"ERROR: file not found: {src}")
        return 1
    print(f"Reading {src} ...")
    try:
        out, folder, fl, rep = build(args, src)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    print(f"Report : {out}")
    print(f"Figures: {os.path.join(folder, 'figures')} ({rep.n_fig} PNG files)")
    print(f"Numbers: {os.path.join(folder, 'key_numbers.csv')}")
    if fl is not None:
        print(f"Apogee {fl['apogee']:.0f} m · flight time {duration(fl['t_land'])} · "
              f"descent {num(fl['v_rustig'], 1, 'm/s')} · Cd {num(fl['cd'], 2)}")
    if not args.no_open:
        webbrowser.open(pathlib.Path(out).resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
