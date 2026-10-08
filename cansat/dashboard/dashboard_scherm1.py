"""
CanSat 2027 — Screen 1 · Flight Data & Sensors (Python version)
================================================================

Python equivalent of scherm1_sensordata.html, built with matplotlib.

Test data: as long as there is no real CSV, TelemetrySimulator generates
a realistic flight (prelaunch → ascent → apogee → parachute → landing).
The simulator produces rows in EXACTLY the same column order as the
Teensy firmware (see initSD() in Cansat2027_teensy.ino), so the real
CSV/serial parser plugs in 1-to-1 later.

Panels:
  - KPI bar with sub-values (apogee, max descent rate, mean Cd)
  - Altitude vs time with apogee marker
  - Acceleration XYZ / gyroscope (sliding window)
  - FFT vibration spectrum, axis limited to the Nyquist frequency
    (208 Hz), with the TOP-5 most frequent peak frequencies of the
    flight marked as numbered lines
  - Audio RMS with a CHUTE marker at parachute opening
  - FLIGHT PHASE TIMELINE: horizontal bar showing the phases over time
  - Cd & descent rate on a twin axis

Requirements:  pip install numpy matplotlib
Run:           python dashboard_scherm1.py                      (settings below)
               python dashboard_scherm1.py --replay test_000.csv
               python dashboard_scherm1.py --live cansat27_live.csv
               python dashboard_scherm1.py --sim
"""

import argparse
import csv
import math
import os
import random
import time
from collections import deque

import numpy as np
import matplotlib

matplotlib.use("TkAgg")  # default on Windows; change if needed
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

# ── Settings ─────────────────────────────────────────────────
SIM_SPEED = 1.0      # 1.0 = realtime, 2.0 = double speed
UPDATE_MS = 100      # GUI update interval (ms)
WINDOW_S  = 30       # time window for the small charts (s)
F_NYQUIST = 208      # LSM6DSO: 416 Hz ODR → usable spectrum 0–208 Hz

# ── Data source mode ─────────────────────────────────────────
# "live"   : follow a GROWING csv that the ground receiver appends to
#            (catch-up of existing history, then tail the newest rows)
# "replay" : play back a FINISHED csv in real time from the start
# In both modes: file missing → fall back to the simulator.
DATA_MODE = "live"

LIVE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "04_Testdata", "cansat27_live.csv")
REPLAY_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "..", "04_Testdata", "cansat27_replay.csv")

# ── Colours (same as HTML mockup) ────────────────────────────
C = {
    "bg":     "#0d1117",
    "panel":  "#161b22",
    "border": "#30363d",
    "grid":   "#1c2128",
    "text":   "#e6edf3",
    "muted":  "#8b949e",
    "dim":    "#6e7681",
    "cyan":   "#00d4ff",
    "green":  "#3fb950",
    "amber":  "#e3b341",
    "purple": "#a371f7",
    "orange": "#ff6b35",
    "blue":   "#58a6ff",
    "red":    "#f85149",
}

# simulator phases (Dutch, internal) → display names (English)
PHASE_EN = {
    "PRELAUNCH": "PRELAUNCH",
    "STIJGEND": "ASCENT",
    "APOGEE": "APOGEE",
    "DALEND": "DESCENT",
    "GELAND": "LANDED",
}
PHASE_COLORS = {
    "PRELAUNCH": "#30363d",
    "ASCENT": "#1f6feb",
    "APOGEE": "#9e6a03",
    "DESCENT": "#bc4c00",
    "LANDED": "#21262d",
}

# Column order — identical to firmware cansat27.csv
CSV_COLUMNS = [
    "millis", "temp_C", "press_hPa", "alt_m",
    "lat", "lon", "time_utc",
    "gyro_x", "gyro_y", "gyro_z",
    "lacc_x", "lacc_y", "lacc_z",
    "grav_x", "grav_y", "grav_z",
    "heading", "roll", "pitch",
    "qw", "qx", "qy", "qz",
    "fft_peak_hz", "fft_peak_amp",
    "audio_rms",
]

# Without a GPS fix the firmware logs placeholder coordinates and this
# time; such rows must not be used as the GPS reference point.
NO_FIX_TIME = "00:00:00"


def has_gps_fix(row):
    return row.get("time_utc", NO_FIX_TIME) != NO_FIX_TIME


# Sources store the descent speed valid AT each row under this key, so a
# batch of rows (live catch-up, fast replay) does not all get the speed
# of the last row. Not a CSV column.
V_KEY = "_v_desc"


def row_speed(source, row):
    """Descent speed (m/s, + = descending) belonging to this row."""
    return row.get(V_KEY, source.v)


# ═════════════════════════════════════════════════════════════
#  FLIGHT SIMULATOR
# ═════════════════════════════════════════════════════════════
class TelemetrySimulator:
    """Generates test data of a complete CanSat flight.

    Physics: 350 g can, parachute Ø45 cm → terminal velocity ±8 m/s.
    """

    MASS   = 0.350          # kg
    A_PARA = 0.159          # m² (parachute Ø 0.45 m)
    G      = 9.81
    H_MAX  = 450.0          # apogee (m)

    T_LAUNCH  = 5.0         # s — launch
    T_APOGEE  = 35.0        # s — highest point
    T_CHUTE   = 38.0        # s — parachute opens

    LAT0, LON0 = 50.4583, 6.2219    # launch site (Elsenborn)

    def __init__(self):
        self.reset()

    def reset(self):
        self.t = 0.0
        self.alt = 0.0
        self.v = 0.0            # vertical speed (+ = descending)
        self.phase = "PRELAUNCH"
        self.spin = 0.0
        self._landed_since = None
        self.x = 0.0            # horizontal drift vs start (m, east)
        self.y = 0.0            # idem (m, north)
        self.wind_dir = random.uniform(0, 2 * math.pi)
        # source interface (shared with CsvReplay)
        self.lat0, self.lon0 = self.LAT0, self.LON0
        self.h_max = self.H_MAX      # expected apogee, for axis scaling
        self.xy_span = 400.0         # half-width of the 3D scene (m)
        self.label = "SIMULATED TEST DATA"

    # ── helpers ──
    def _temperature(self, alt):
        return 15.0 - 0.0065 * alt + random.gauss(0, 0.05)

    def _pressure(self, alt):
        return 1013.25 * (1 - 2.25577e-5 * alt) ** 5.25588 + random.gauss(0, 0.15)

    def _rho(self, alt):
        return 1.225 * (1 - 2.25577e-5 * alt) ** 4.25588

    def step(self, dt):
        """Simulate dt seconds; returns one telemetry row (dict)."""
        self.t += dt
        t = self.t

        # ── flight profile ──
        if t < self.T_LAUNCH:
            self.phase, self.alt, self.v = "PRELAUNCH", 0.0, 0.0
        elif t < self.T_APOGEE:
            self.phase = "STIJGEND"
            frac = (t - self.T_LAUNCH) / (self.T_APOGEE - self.T_LAUNCH)
            new_alt = self.H_MAX * math.sin(frac * math.pi / 2)
            self.v = -(new_alt - self.alt) / dt
            self.alt = new_alt
        elif self.alt > 0.5:
            self.phase = "APOGEE" if t < self.T_CHUTE else "DALEND"
            rho = self._rho(self.alt)
            v_term = math.sqrt(2 * self.MASS * self.G /
                               (rho * 0.50 * self.A_PARA))
            if t < self.T_CHUTE:                      # free fall before chute
                self.v += self.G * dt
            else:                                     # towards terminal speed
                self.v += (v_term - self.v) * min(1.0, 2.0 * dt)
            self.alt = max(0.0, self.alt - self.v * dt)
        else:
            self.phase = "GELAND"
            self.v = 0.0
            if self._landed_since is None:
                self._landed_since = t
            elif t - self._landed_since > 8.0:        # demo loop: restart
                self.reset()

        descending = self.phase == "DALEND"

        # ── horizontal wind drift → GPS track ──
        if self.phase in ("STIJGEND", "APOGEE", "DALEND"):
            self.wind_dir += random.gauss(0, 0.02)
            wind = 3.0 + 1.0 * math.sin(0.05 * t)
            self.x += wind * math.cos(self.wind_dir) * dt
            self.y += wind * math.sin(self.wind_dir) * dt
        lat = self.LAT0 + self.y / 111_320.0
        lon = self.LON0 + self.x / (111_320.0 * math.cos(math.radians(self.LAT0)))

        # ── acceleration (linear, gravity removed) ──
        lacc_x = random.gauss(0, 0.15)
        lacc_y = random.gauss(0, 0.15)
        lacc_z = random.gauss(0, 0.20)
        if self.T_LAUNCH <= t < self.T_LAUNCH + 1.2:        # launch spike
            lacc_z += 40.0 * math.exp(-4 * (t - self.T_LAUNCH))
        if self.T_CHUTE <= t < self.T_CHUTE + 1.0:          # parachute shock
            lacc_z -= 25.0 * math.exp(-6 * (t - self.T_CHUTE))
        if descending:
            lacc_x += 1.5 * math.sin(2 * math.pi * 0.8 * t)  # swinging
            lacc_y += 1.5 * math.cos(2 * math.pi * 0.8 * t)

        # ── gyroscope: spin damping out after chute opening ──
        if descending:
            self.spin = 120 * math.exp(-0.08 * (t - self.T_CHUTE)) + 8
        elif self.phase == "STIJGEND":
            self.spin = 25
        else:
            self.spin = 0
        gyro_x = random.gauss(0, 2) + self.spin * 0.15
        gyro_y = random.gauss(0, 2) - self.spin * 0.10
        gyro_z = self.spin + random.gauss(0, 3)

        # ── orientation ──
        heading = (self.spin * t) % 360
        roll  = (8 if descending else 2) * math.sin(0.9 * t) + random.gauss(0, 0.3)
        pitch = (8 if descending else 2) * math.cos(0.7 * t) + random.gauss(0, 0.3)
        h2 = math.radians(heading) / 2
        qw, qx, qy, qz = math.cos(h2), 0.0, 0.0, math.sin(h2)

        # ── FFT peak (LSM6DSO vibration) ──
        if descending:
            fft_hz  = 23 + 4 * math.sin(0.3 * t) + random.gauss(0, 1)
            fft_amp = 0.8 + random.gauss(0, 0.1)
        elif self.phase == "STIJGEND":
            fft_hz, fft_amp = 55 + random.gauss(0, 5), 1.5 + random.gauss(0, 0.2)
        else:
            fft_hz, fft_amp = random.uniform(0, 5), 0.05

        # ── audio RMS ~ v² + shock at chute ──
        audio = 0.004 + 0.0006 * self.v ** 2 + random.gauss(0, 0.002)
        if self.T_CHUTE <= t < self.T_CHUTE + 0.8:
            audio += 0.35 * math.exp(-8 * (t - self.T_CHUTE))
        audio = max(0.0, audio)

        return {
            "millis": int(t * 1000),
            "temp_C": self._temperature(self.alt),
            "press_hPa": self._pressure(self.alt),
            "alt_m": self.alt + random.gauss(0, 0.4),
            "lat": lat + random.gauss(0, 2e-6),
            "lon": lon + random.gauss(0, 2e-6),
            "time_utc": "12:00:00",
            "gyro_x": gyro_x, "gyro_y": gyro_y, "gyro_z": gyro_z,
            "lacc_x": lacc_x, "lacc_y": lacc_y, "lacc_z": lacc_z,
            "grav_x": 0.0, "grav_y": 0.0, "grav_z": 9.81,
            "heading": heading, "roll": roll, "pitch": pitch,
            "qw": qw, "qx": qx, "qy": qy, "qz": qz,
            "fft_peak_hz": max(0.0, fft_hz),
            "fft_peak_amp": max(0.0, fft_amp),
            "audio_rms": audio,
        }

    def drag_coefficient(self, row):
        """Dynamic Cd from terminal-velocity approximation (descent only)."""
        if self.phase != "DALEND" or self.v < 2.0:
            return float("nan")
        rho = self._rho(row["alt_m"])
        cd = 2 * self.MASS * self.G / (rho * self.A_PARA * self.v ** 2)
        return min(1.5, max(0.0, cd + random.gauss(0, 0.015)))

    def fetch(self, dt):
        """Advance dt seconds; returns the new telemetry rows (list)."""
        n_sub = min(40, max(1, int(dt / 0.05)))
        row = None
        for _ in range(n_sub):
            row = self.step(dt / n_sub)
        return [row]


# ═════════════════════════════════════════════════════════════
#  CSV REPLAY SOURCE
# ═════════════════════════════════════════════════════════════
class CsvReplay:
    """Replays a flight CSV in firmware format (cansat27_replay.csv).

    Exposes the same interface as TelemetrySimulator (step, v,
    drag_coefficient, lat0/lon0, h_max, xy_span) so the dashboards
    don't care where the data comes from. Altitude is converted to
    AGL (ground level = median of the first 10 rows). Loops when the
    recording ends.
    """

    MASS = TelemetrySimulator.MASS
    A_PARA = TelemetrySimulator.A_PARA
    G = TelemetrySimulator.G

    def __init__(self, path):
        self.rows = []
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                row = {}
                for k, val in r.items():
                    if k == "time_utc":
                        row[k] = val
                    else:
                        try:
                            row[k] = float(val)
                        except (TypeError, ValueError):
                            row[k] = 0.0
                row["millis"] = int(row.get("millis", 0))
                self.rows.append(row)
        if len(self.rows) < 10:
            raise ValueError(f"replay CSV too short: {path}")

        # altitude → AGL (first 10 rows: safely before any launch)
        self.ground_asl = float(np.median(
            [r["alt_m"] for r in self.rows[:10]]))
        for r in self.rows:
            r["alt_m"] -= self.ground_asl

        # GPS reference: first row with a fix (rows before it carry
        # placeholder coordinates); no fix at all → firmware defaults
        fixed = [r for r in self.rows if has_gps_fix(r)] or self.rows
        self.lat0 = fixed[0]["lat"]
        self.lon0 = fixed[0]["lon"]
        self.h_max = max(r["alt_m"] for r in self.rows)
        xs, ys = [], []
        coslat = math.cos(math.radians(self.lat0))
        for r in fixed:
            xs.append(abs((r["lon"] - self.lon0) * 111_320.0 * coslat))
            ys.append(abs((r["lat"] - self.lat0) * 111_320.0))
        self.xy_span = max(150.0, 1.15 * max(max(xs), max(ys)))
        self.label = "REPLAY: real flight data"

        self.t = 0.0
        self.i = 0
        self.v = 0.0          # vertical speed, + = descending (sim convention)
        self.phase = None     # replay has no ground truth
        self._started = False

    def fetch(self, dt):
        """Advance the replay clock; returns the rows passed in dt."""
        self.t += dt
        target_ms = self.t * 1000.0
        out = []
        while (self.i + 1 < len(self.rows) and
               self.rows[self.i + 1]["millis"] <= target_ms):
            prev, cur = self.rows[self.i], self.rows[self.i + 1]
            dtr = (cur["millis"] - prev["millis"]) / 1000.0
            if dtr > 0:
                v_new = (prev["alt_m"] - cur["alt_m"]) / dtr
                self.v += 0.3 * (v_new - self.v)        # light smoothing
            cur[V_KEY] = self.v
            self.i += 1
            out.append(cur)
        # end of recording → loop (dashboards detect t jumping back)
        if (self.i >= len(self.rows) - 1 and
                target_ms > self.rows[-1]["millis"] + 5000):
            self.t, self.i, self.v = 0.0, 0, 0.0
            self.rows[0][V_KEY] = 0.0
            return [self.rows[0]]
        # first frame: show something immediately
        if not out and not self._started:
            self._started = True
            return [self.rows[0]]
        return out

    def drag_coefficient(self, row):
        """Cd from the real descent rate (descent only)."""
        v = row_speed(self, row)
        if v < 2.0:
            return float("nan")
        rho = 1.225 * (1 - 2.25577e-5 *
                       (row["alt_m"] + self.ground_asl)) ** 4.25588
        cd = 2 * self.MASS * self.G / (rho * self.A_PARA * v ** 2)
        return min(1.5, max(0.0, cd))


class CsvLive:
    """Tails a GROWING csv that the ground receiver appends to.

    On startup the already-written history is ingested in one
    catch-up pass (so charts and phase detection are complete), after
    which fetch() returns only the newly appended rows. A partially
    written last line is held back until its newline arrives; repeated
    header lines (can reboot) are skipped. If the dashboard crashes
    mid-flight, simply restart it: the catch-up brings it back up to
    date instantly.
    """

    MASS = TelemetrySimulator.MASS
    A_PARA = TelemetrySimulator.A_PARA
    G = TelemetrySimulator.G

    def __init__(self, path, h_max=1000.0):
        self.path = path
        self._fh = open(path, "r", encoding="utf-8", newline="")
        self._buf = ""
        self._cols = None
        self.rows = []
        self._gnd = []
        self.ground_asl = None
        # defaults until the first GPS row arrives
        self.lat0 = TelemetrySimulator.LAT0
        self.lon0 = TelemetrySimulator.LON0
        self.h_max = h_max        # start value; grows with the flight
        self.xy_span = 600.0
        self.label = "LIVE: tailing CSV"
        self.phase = None         # live data has no ground truth
        self.v = 0.0              # + = descending
        self._have_fix = False    # lat0/lon0 still the default
        # catch-up of existing history; handed to the dashboard on the
        # first fetch() so charts and phase detection start complete
        self._pending = self._read_new()
        print(f"live: caught up {len(self._pending)} existing rows, "
              f"now tailing {path}")

    def _parse_line(self, line):
        parts = line.strip().split(",")
        if self._cols is None:
            if parts and parts[0] == "millis":
                self._cols = parts
            return None
        if len(parts) != len(self._cols) or parts[0] == "millis":
            return None                  # repeated header / broken line
        row = {}
        try:
            for k, val in zip(self._cols, parts):
                row[k] = val if k == "time_utc" else float(val)
        except ValueError:
            return None
        row["millis"] = int(row["millis"])
        return row

    def _ingest_row(self, row):
        # ground reference from the first 10 rows
        if len(self._gnd) < 10:
            self._gnd.append(row["alt_m"])
            self.ground_asl = float(np.median(self._gnd))
        row["alt_m"] -= self.ground_asl
        if not self._have_fix and has_gps_fix(row):
            self.lat0, self.lon0 = row["lat"], row["lon"]
            self._have_fix = True
        if self.rows:
            prev = self.rows[-1]
            dtr = (row["millis"] - prev["millis"]) / 1000.0
            if dtr > 0:
                v_new = (prev["alt_m"] - row["alt_m"]) / dtr
                self.v += 0.3 * (v_new - self.v)
        row[V_KEY] = self.v
        self.h_max = max(self.h_max, row["alt_m"] * 1.1)
        self.rows.append(row)
        return row

    def _read_new(self):
        out = []
        data = self._fh.read()           # '' when nothing new
        if data:
            self._buf += data
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                row = self._parse_line(line)
                if row is not None:
                    out.append(self._ingest_row(row))
        return out

    def fetch(self, dt):
        """All rows appended to the file since the previous call
        (the first call also returns the catch-up history)."""
        out, self._pending = self._pending + self._read_new(), []
        return out

    def drag_coefficient(self, row):
        v = row_speed(self, row)
        if v < 2.0 or self.ground_asl is None:
            return float("nan")
        rho = 1.225 * (1 - 2.25577e-5 *
                       (row["alt_m"] + self.ground_asl)) ** 4.25588
        cd = 2 * self.MASS * self.G / (rho * self.A_PARA * v ** 2)
        return min(1.5, max(0.0, cd))


def make_source():
    """Mode 1: LIVE (tail a growing csv) · mode 2: REPLAY · else sim."""
    if DATA_MODE == "live" and LIVE_CSV:
        path = os.path.normpath(LIVE_CSV)
        if os.path.exists(path):
            try:
                src = CsvLive(path)
                print(f"data source: LIVE {path}")
                return src
            except Exception as e:
                print(f"live failed ({e}) → trying replay")
        else:
            print(f"live: {path} not found → trying replay")
    if REPLAY_CSV:
        path = os.path.normpath(REPLAY_CSV)
        if os.path.exists(path):
            try:
                src = CsvReplay(path)
                print(f"data source: REPLAY {path}\n"
                      f"  apogee {src.h_max:.0f} m AGL · "
                      f"ground {src.ground_asl:.0f} m ASL · "
                      f"{len(src.rows)} rows")
                return src
            except Exception as e:
                print(f"replay failed ({e}) → falling back to simulator")
    print("data source: SIMULATOR")
    return TelemetrySimulator()


# ═════════════════════════════════════════════════════════════
#  PHASE DETECTOR
# ═════════════════════════════════════════════════════════════
class PhaseDetector:
    """Derives the flight phase purely from the telemetry stream.

    Uses NO simulator internals: only barometric altitude, linear
    acceleration and time — exactly what the real telemetry contains,
    so this code works unchanged on real flight data later.

    Why transport to the launch site never triggers a false launch:
    the ground reference slowly follows the measured altitude while
    the phase is PRELAUNCH, so slow elevation changes (driving, being
    carried up) are absorbed. Only a *sustained fast climb* or a
    *motor boost spike* counts as a launch.

    Transitions (all thresholds in one place — tune after the first
    real test flight):
      PRELAUNCH → ASCENT : climb > CLIMB_RATE m/s for CLIMB_SUSTAIN s,
                           OR accel spike > BOOST_ACC plus altitude gain
      ASCENT    → APOGEE : climb rate ≈ 0 while high above the ground
      *         → DESCENT: sink > SINK_RATE m/s sustained for 1 s
      DESCENT   → LANDED : altitude stable near the ground reference
    """

    CLIMB_RATE      = 10.0   # m/s sustained climb = launch
    CLIMB_SUSTAIN   = 1.0    # s
    BOOST_ACC       = 30.0   # m/s² acceleration spike = motor boost
    MIN_APOGEE_AGL  = 100.0  # m above ground before apogee is possible
    SINK_RATE       = 2.0    # m/s sustained sink = descent
    LAND_RATE       = 0.5    # m/s — "standing still"
    LAND_SUSTAIN    = 3.0    # s
    LAND_AGL        = 30.0   # m above ground reference
    RATE_SPAN       = 4.0    # s window for the climb-rate fit
                             # (works at 1 Hz LoRa rate and faster)

    def __init__(self):
        self.phase = "PRELAUNCH"
        self.samples = deque(maxlen=400)     # (t, alt)
        self.ground_alt = None
        self._since = {}                     # condition name -> start time

    def _sustained(self, name, cond, t, dur):
        """True once `cond` has been continuously true for `dur` s."""
        if not cond:
            self._since.pop(name, None)
            return False
        self._since.setdefault(name, t)
        return t - self._since[name] >= dur

    def _rate(self, t):
        """Climb rate (m/s): linear fit over the last RATE_SPAN seconds."""
        pts = [(ts, a) for ts, a in self.samples if ts >= t - self.RATE_SPAN]
        if len(pts) < 3:
            return 0.0
        ts = np.array([p[0] for p in pts])
        al = np.array([p[1] for p in pts])
        denom = ((ts - ts.mean()) ** 2).sum()
        if denom <= 0:
            return 0.0
        return float(((ts - ts.mean()) * (al - al.mean())).sum() / denom)

    def update(self, t, row):
        """Feed one telemetry row; returns the current phase."""
        alt = row["alt_m"]
        self.samples.append((t, alt))

        # ground reference: slow follower while on the ground
        if self.ground_alt is None:
            self.ground_alt = alt
        if self.phase in ("PRELAUNCH", "LANDED"):
            self.ground_alt += (alt - self.ground_alt) * 0.02

        rate = self._rate(t)                 # + = climbing
        agl = alt - self.ground_alt          # height above ground ref
        a_mag = math.sqrt(row["lacc_x"] ** 2 + row["lacc_y"] ** 2 +
                          row["lacc_z"] ** 2)

        if self.phase == "PRELAUNCH":
            climb = self._sustained("climb", rate > self.CLIMB_RATE,
                                    t, self.CLIMB_SUSTAIN)
            boost = (self._sustained("boost", a_mag > self.BOOST_ACC,
                                     t, 0.2) and agl > 5)
            if climb or boost:
                self.phase = "ASCENT"
        elif self.phase == "ASCENT":
            if agl > self.MIN_APOGEE_AGL and rate < 1.0:
                self.phase = "APOGEE"
            elif self._sustained("sink", rate < -self.SINK_RATE, t, 1.0):
                self.phase = "DESCENT"       # apogee missed → straight on
        elif self.phase == "APOGEE":
            if self._sustained("sink", rate < -self.SINK_RATE, t, 1.0):
                self.phase = "DESCENT"
        elif self.phase == "DESCENT":
            if agl < self.LAND_AGL and self._sustained(
                    "still", abs(rate) < self.LAND_RATE,
                    t, self.LAND_SUSTAIN):
                self.phase = "LANDED"
        return self.phase


# ═════════════════════════════════════════════════════════════
#  DASHBOARD
# ═════════════════════════════════════════════════════════════
class Dashboard:
    N_FFT_BARS = 26
    N_TOP = 5            # number of marked dominant frequencies

    def __init__(self):
        self.sim = make_source()
        self.detector = PhaseDetector()
        self.hist = {k: deque(maxlen=4000) for k in
                     ("t", "alt", "ax", "ay", "az", "gx", "gy", "gz",
                      "audio", "cd", "v")}
        self.apogee = 0.0
        self.t_apogee = 0.0
        self.v_max = 0.0
        self.cd_sum, self.cd_n = 0.0, 0
        self.freq_hist = []          # peak frequencies seen this flight
        self.segments = []           # [phase, t_start, t_end] timeline
        self.seg_artists = []
        self.t_chute = None
        self.pkt_rx = 0
        self._wall = None        # wall-clock pacing for real-time replay
        self._build_figure()

    # ── construction ──
    def _style_axes(self, ax, title=None, title_color=None):
        ax.set_facecolor(C["panel"])
        for s in ax.spines.values():
            s.set_color(C["border"])
            s.set_linewidth(0.8)
        ax.tick_params(colors=C["dim"], labelsize=7)
        ax.grid(True, color=C["grid"], linewidth=0.5)
        if title:
            ax.set_title(title, loc="left", fontsize=8,
                         color=title_color or C["muted"],
                         fontfamily="monospace", pad=4)

    def _build_figure(self):
        plt.rcParams.update({
            "font.family": "monospace",
            "text.color": C["text"],
            "axes.labelcolor": C["muted"],
        })
        self.fig = plt.figure(figsize=(15, 8.5), facecolor=C["bg"])
        self.fig.canvas.manager.set_window_title(
            "CanSat 2027 — Screen 1 · Flight Data & Sensors")

        # ── header ──
        self.fig.text(0.02, 0.965, "CanSat 2027", fontsize=14,
                      fontweight="bold", color=C["text"])
        self.fig.text(0.115, 0.965, "● ", fontsize=10, color=C["green"])
        self.fig.text(0.13, 0.965,
                      f"Screen 1 — Flight Data & Sensors ({self.sim.label})",
                      fontsize=9, color=C["muted"])
        self.txt_rssi = self.fig.text(0.66, 0.965, "RSSI —", fontsize=9,
                                      color=C["green"], ha="right")
        self.txt_pkt = self.fig.text(0.79, 0.965, "packet #0", fontsize=8,
                                     color=C["muted"], ha="right")
        self.txt_phase = self.fig.text(0.86, 0.965, "PRELAUNCH", fontsize=10,
                                       color=C["amber"], ha="right",
                                       bbox=dict(boxstyle="round,pad=0.3",
                                                 fc="none", ec=C["amber"]))
        self.txt_clock = self.fig.text(0.97, 0.965, "00:00", fontsize=12,
                                       color=C["cyan"], ha="right")
        # detected phase vs simulator ground truth (transition latency
        # of the detector shows up here as a brief mismatch)
        self.txt_truth = self.fig.text(0.86, 0.945, "", fontsize=7,
                                       color=C["dim"], ha="right")

        # ── KPI bar (value + sub-value) ──
        kpis = [("ALTITUDE", "m", C["cyan"]),
                ("TEMPERATURE", "°C", C["amber"]),
                ("PRESSURE", "hPa", C["text"]),
                ("DESCENT RATE", "m/s", C["blue"]),
                ("CD DRAG COEFFICIENT", "—", C["green"])]
        self.txt_kpi, self.txt_kpi_sub = [], []
        for i, (label, unit, col) in enumerate(kpis):
            x = 0.02 + i * 0.196
            self.fig.text(x, 0.928, label, fontsize=7, color=C["dim"])
            v = self.fig.text(x, 0.888, "—", fontsize=18, fontweight="bold",
                              color=col)
            self.fig.text(x + 0.135, 0.888, unit, fontsize=8, color=C["muted"])
            sub = self.fig.text(x, 0.866, "", fontsize=7, color=C["dim"])
            self.txt_kpi.append(v)
            self.txt_kpi_sub.append(sub)

        # ── panel grid (extra thin row for the phase timeline) ──
        gs = GridSpec(4, 6, figure=self.fig,
                      left=0.05, right=0.985, top=0.845, bottom=0.05,
                      hspace=0.55, wspace=0.45,
                      height_ratios=[32, 24, 7, 19])

        # Row 1: altitude (wide) + acceleration
        self.ax_alt = self.fig.add_subplot(gs[0, :4])
        self._style_axes(self.ax_alt, "● ALTITUDE VS TIME  [LIVE]", C["cyan"])
        self.ln_alt, = self.ax_alt.plot([], [], color=C["cyan"], lw=2)
        self.fill_alt = None
        self.ln_apogee = self.ax_alt.axvline(np.nan, color=C["amber"], lw=1,
                                             ls="--", alpha=0.6)
        self.txt_apogee = self.ax_alt.text(0, 0, "", fontsize=7,
                                           color=C["amber"], visible=False)
        self.ax_alt.set_ylim(0, self.sim.h_max * 1.12)
        self.ax_alt.set_ylabel("m", fontsize=7)

        self.ax_acc = self.fig.add_subplot(gs[0, 4:])
        self._style_axes(self.ax_acc, "● ACCELERATION (m/s²)", C["blue"])
        self.ln_ax, = self.ax_acc.plot([], [], color=C["blue"], lw=1.2, label="X")
        self.ln_ay, = self.ax_acc.plot([], [], color=C["green"], lw=1.2, label="Y")
        self.ln_az, = self.ax_acc.plot([], [], color=C["orange"], lw=1.2, label="Z")
        self.ax_acc.set_ylim(-30, 45)
        self.ax_acc.legend(loc="upper right", fontsize=6, frameon=False,
                           labelcolor=C["muted"])

        # Row 2: gyro + FFT + audio
        self.ax_gyro = self.fig.add_subplot(gs[1, :2])
        self._style_axes(self.ax_gyro, "● GYROSCOPE (°/s)", C["purple"])
        self.ln_gx, = self.ax_gyro.plot([], [], color=C["purple"], lw=1.2, label="X")
        self.ln_gy, = self.ax_gyro.plot([], [], color=C["blue"], lw=1.2, label="Y")
        self.ln_gz, = self.ax_gyro.plot([], [], color=C["green"], lw=1.2, label="Z")
        self.ax_gyro.set_ylim(-50, 150)
        self.ax_gyro.legend(loc="upper right", fontsize=6, frameon=False,
                            labelcolor=C["muted"])

        self.ax_fft = self.fig.add_subplot(gs[1, 2:4])
        self._style_axes(self.ax_fft,
                         "● FFT VIBRATION SPECTRUM (0–208 Hz · Nyquist)",
                         C["amber"])
        freqs = np.linspace(0, F_NYQUIST, self.N_FFT_BARS)
        self.fft_bars = self.ax_fft.bar(freqs, np.zeros(self.N_FFT_BARS),
                                        width=F_NYQUIST / self.N_FFT_BARS * 0.8,
                                        color=C["amber"])
        self.ax_fft.set_xlim(0, F_NYQUIST)
        self.ax_fft.set_ylim(0, 2.2)
        self.ax_fft.set_xlabel("Hz", fontsize=7)
        self.txt_fftpeak = self.ax_fft.text(0.97, 0.9, "", fontsize=8,
                                            color=C["amber"], ha="right",
                                            transform=self.ax_fft.transAxes)
        # top-5 most frequent peak frequencies of this flight
        self.top_lines, self.top_texts = [], []
        for i in range(self.N_TOP):
            ln = self.ax_fft.axvline(np.nan, color=C["blue"], lw=1,
                                     ls=(0, (2, 2)), alpha=0.85)
            tx = self.ax_fft.text(0, 2.05, "", fontsize=6, color=C["blue"],
                                  ha="center")
            self.top_lines.append(ln)
            self.top_texts.append(tx)

        self.ax_aud = self.fig.add_subplot(gs[1, 4:])
        self._style_axes(self.ax_aud, "● AUDIO RMS", C["orange"])
        self.ln_aud, = self.ax_aud.plot([], [], color=C["orange"], lw=1.5)
        self.ax_aud.set_ylim(0, 0.5)
        self.txt_aud = self.ax_aud.text(0.5, 0.85, "", fontsize=13,
                                        fontweight="bold", color=C["orange"],
                                        ha="center",
                                        transform=self.ax_aud.transAxes)
        self.ln_chute = self.ax_aud.axvline(np.nan, color=C["amber"], lw=1,
                                            ls="--", alpha=0.8)
        self.txt_chute = self.ax_aud.text(0, 0.45, "", fontsize=6,
                                          color=C["amber"], rotation=90,
                                          va="top")

        # Row 3: flight phase timeline (the bar nobody else shows)
        self.ax_phase = self.fig.add_subplot(gs[2, :])
        self._style_axes(self.ax_phase, "● FLIGHT PHASE TIMELINE", C["amber"])
        self.ax_phase.set_ylim(0, 1)
        self.ax_phase.set_yticks([])
        self.ax_phase.grid(False)
        self.ln_phase_now = self.ax_phase.axvline(0, color=C["text"], lw=1.5)

        # Row 4: Cd & descent rate (twin y-axis)
        self.ax_cd = self.fig.add_subplot(gs[3, :])
        self._style_axes(self.ax_cd,
                         "● DRAG COEFFICIENT CD & DESCENT RATE",
                         C["green"])
        self.ln_cd, = self.ax_cd.plot([], [], color=C["green"], lw=1.8,
                                      label="Cd (−)")
        self.ax_cd.set_ylim(0, 1.5)
        self.ax_cd.tick_params(axis="y", colors=C["green"])
        self.ax_v = self.ax_cd.twinx()
        self.ax_v.set_facecolor("none")
        for s in self.ax_v.spines.values():
            s.set_color(C["border"])
        self.ax_v.tick_params(colors=C["blue"], labelsize=7)
        self.ln_v, = self.ax_v.plot([], [], color=C["blue"], lw=1.5,
                                    ls="--", label="v (m/s)")
        self.ax_v.set_ylim(0, 40)
        self.ax_cd.set_xlabel("time (s)", fontsize=7)
        lines = [self.ln_cd, self.ln_v]
        self.ax_cd.legend(lines, [l.get_label() for l in lines],
                          loc="upper right", fontsize=7, frameon=False,
                          labelcolor=C["muted"])

    # ── phase timeline ──
    def _track_phase(self, t, ph):
        if not self.segments or self.segments[-1][0] != ph:
            self.segments.append([ph, t, t])
            if ph == "DESCENT" and self.t_chute is None:
                self.t_chute = t
        else:
            self.segments[-1][2] = t

    def _draw_timeline(self, t_end):
        for art in self.seg_artists:
            art.remove()
        self.seg_artists = []
        xspan = max(60, t_end + 5)
        for ph, t0, t1 in self.segments:
            rect = Rectangle((t0, 0.18), max(t1 - t0, 0.1), 0.64,
                             facecolor=PHASE_COLORS.get(ph, C["dim"]),
                             edgecolor="none")
            self.ax_phase.add_patch(rect)
            self.seg_artists.append(rect)
            if (t1 - t0) / xspan > 0.07:        # label only if wide enough
                tx = self.ax_phase.text(0.5 * (t0 + t1), 0.5, ph,
                                        fontsize=6.5, color=C["text"],
                                        ha="center", va="center")
                self.seg_artists.append(tx)
        self.ax_phase.set_xlim(0, xspan)
        self.ln_phase_now.set_xdata([t_end, t_end])

    # ── top-5 dominant frequencies ──
    def _update_top_freqs(self):
        n_show = 0
        if len(self.freq_hist) >= 20:
            counts, edges = np.histogram(
                self.freq_hist, bins=self.N_FFT_BARS * 2,
                range=(0, F_NYQUIST))
            order = np.argsort(counts)[::-1]
            for rank, idx in enumerate(order[:self.N_TOP]):
                if counts[idx] < 3:
                    break
                fc = 0.5 * (edges[idx] + edges[idx + 1])
                self.top_lines[rank].set_xdata([fc, fc])
                self.top_lines[rank].set_visible(True)
                self.top_texts[rank].set_position((fc, 2.05))
                self.top_texts[rank].set_text(f"{rank + 1}·{fc:.0f}Hz")
                n_show += 1
        for i in range(n_show, self.N_TOP):
            self.top_lines[i].set_visible(False)
            self.top_texts[i].set_text("")

    # ── ingest one telemetry row (history, detector, statistics) ──
    def _ingest(self, row):
        cd = self.sim.drag_coefficient(row)
        t = row["millis"] / 1000.0

        # restart detection (demo loop / can reboot)
        if self.hist["t"] and t < self.hist["t"][-1]:
            for d in self.hist.values():
                d.clear()
            self.apogee = self.v_max = 0.0
            self.cd_sum, self.cd_n = 0.0, 0
            self.freq_hist.clear()
            self.segments.clear()
            self.t_chute = None
            self.pkt_rx = 0
            self.ln_chute.set_xdata([np.nan, np.nan])
            self.txt_chute.set_text("")
            self.detector = PhaseDetector()

        # phase from the DATA (not from the simulator) — this is the
        # logic that runs unchanged on real telemetry
        det = self.detector.update(t, row)

        h = self.hist
        h["t"].append(t)
        h["alt"].append(row["alt_m"])
        h["ax"].append(row["lacc_x"]); h["ay"].append(row["lacc_y"])
        h["az"].append(row["lacc_z"])
        h["gx"].append(row["gyro_x"]); h["gy"].append(row["gyro_y"])
        h["gz"].append(row["gyro_z"])
        h["audio"].append(row["audio_rms"])
        h["cd"].append(cd)
        v_now = row_speed(self.sim, row) if det == "DESCENT" else float("nan")
        h["v"].append(v_now)
        if row["alt_m"] > self.apogee:
            self.apogee = row["alt_m"]
            self.t_apogee = t
        if not math.isnan(v_now):
            self.v_max = max(self.v_max, v_now)
        if not math.isnan(cd):
            self.cd_sum += cd
            self.cd_n += 1
        if row["fft_peak_amp"] > 0.3:
            self.freq_hist.append(min(row["fft_peak_hz"], F_NYQUIST))
        self.pkt_rx += 1
        self._track_phase(t, det)
        return cd, det, t

    # ── per-frame update ──
    def update(self, _frame):
        # advance data time by the REAL elapsed wall-clock time, so the
        # replay stays real-time even when rendering takes >UPDATE_MS
        now = time.monotonic()
        if self._wall is None:
            dt = UPDATE_MS / 1000.0 * SIM_SPEED
        else:
            dt = min(2.0, now - self._wall) * SIM_SPEED
        self._wall = now

        # fetch all new rows (a live catch-up can deliver hundreds at
        # once); ingest each of them, render once from the last
        rows = self.sim.fetch(dt)
        if not rows:
            return []
        for r in rows[:-1]:
            self._ingest(r)
        row = rows[-1]
        cd, det, t = self._ingest(row)

        h = self.hist
        ts = np.array(h["t"])

        # ── header ──
        # echte RSSI als de logger die meeschrijft (kolom 27); alleen de
        # simulator toont een gesimuleerde waarde, expliciet gelabeld
        rssi = row.get("rssi")
        if rssi is not None:
            self.txt_rssi.set_text(f"RSSI {rssi:.0f} dBm")
        elif isinstance(self.sim, TelemetrySimulator):
            rssi_sim = -70 - 0.045 * row["alt_m"] + random.gauss(0, 1.5)
            self.txt_rssi.set_text(f"RSSI {rssi_sim:.0f} dBm (sim)")
        else:
            self.txt_rssi.set_text("RSSI —")
        self.txt_pkt.set_text(f"packet #{self.pkt_rx}")
        self.txt_phase.set_text(det)
        self.txt_clock.set_text(f"{int(t // 60):02d}:{int(t % 60):02d}")
        if self.sim.phase is not None:          # simulator: ground truth
            truth = PHASE_EN.get(self.sim.phase, self.sim.phase)
            ok = truth == det
            self.txt_truth.set_text(f"sim truth: {truth} "
                                    f"{'✓' if ok else '✗'}")
            self.txt_truth.set_color(C["green"] if ok else C["red"])
        else:                                   # replay: no ground truth
            self.txt_truth.set_text("phase detected from data")
            self.txt_truth.set_color(C["dim"])

        # ── KPIs ──
        vals = (f"{row['alt_m']:.0f}", f"{row['temp_C']:.1f}",
                f"{row['press_hPa']:.0f}",
                f"{row_speed(self.sim, row):.1f}" if det == "DESCENT" else "0.0",
                f"{cd:.2f}" if not math.isnan(cd) else "—")
        subs = (f"apogee: {self.apogee:.0f} m" if self.apogee > 10 else "",
                "",
                "",
                f"max: {self.v_max:.1f} m/s" if self.v_max > 0 else "",
                f"mean: {self.cd_sum / self.cd_n:.2f}" if self.cd_n else "")
        for txt, v in zip(self.txt_kpi, vals):
            txt.set_text(v)
        for txt, v in zip(self.txt_kpi_sub, subs):
            txt.set_text(v)

        # ── altitude (y-axis grows along in live mode) ──
        if self.apogee > self.sim.h_max:
            self.sim.h_max = self.apogee * 1.1
        self.ax_alt.set_ylim(0, self.sim.h_max * 1.12)
        self.ln_alt.set_data(ts, h["alt"])
        if self.fill_alt:
            self.fill_alt.remove()
        self.fill_alt = self.ax_alt.fill_between(
            ts, 0, np.array(h["alt"]), color=C["cyan"], alpha=0.12)
        self.ax_alt.set_xlim(0, max(60, t + 5))
        if self.apogee > 10:
            self.ln_apogee.set_xdata([self.t_apogee, self.t_apogee])
            self.txt_apogee.set_position((self.t_apogee + 1,
                                          self.sim.h_max * 1.03))
            self.txt_apogee.set_text(f"APOGEE {self.apogee:.0f}m")
            self.txt_apogee.set_visible(True)
        else:
            self.txt_apogee.set_visible(False)

        # ── sliding window for the small charts ──
        t0 = max(0, t - WINDOW_S)
        for ax in (self.ax_acc, self.ax_gyro, self.ax_aud):
            ax.set_xlim(t0, max(WINDOW_S, t))
        self.ln_ax.set_data(ts, h["ax"])
        self.ln_ay.set_data(ts, h["ay"])
        self.ln_az.set_data(ts, h["az"])
        self.ln_gx.set_data(ts, h["gx"])
        self.ln_gy.set_data(ts, h["gy"])
        self.ln_gz.set_data(ts, h["gz"])
        self.ln_aud.set_data(ts, h["audio"])
        self.txt_aud.set_text(f"{row['audio_rms']:.3f}")
        if self.t_chute is not None:
            self.ln_chute.set_xdata([self.t_chute, self.t_chute])
            self.txt_chute.set_position((self.t_chute + 0.4, 0.45))
            self.txt_chute.set_text("CHUTE")

        # ── FFT spectrum (synthetic around the peak) ──
        freqs = np.linspace(0, F_NYQUIST, self.N_FFT_BARS)
        peak_hz, peak_amp = row["fft_peak_hz"], row["fft_peak_amp"]
        spectrum = peak_amp * np.exp(-((freqs - peak_hz) ** 2) / (2 * 18 ** 2))
        spectrum += np.abs(np.random.normal(0, 0.03, self.N_FFT_BARS))
        for bar, amp in zip(self.fft_bars, spectrum):
            bar.set_height(amp)
        self.txt_fftpeak.set_text(f"{peak_hz:.0f} Hz ▲" if peak_amp > 0.3 else "")
        self._update_top_freqs()

        # ── flight phase timeline ──
        self._draw_timeline(t)

        # ── Cd & descent rate ──
        self.ln_cd.set_data(ts, h["cd"])
        self.ln_v.set_data(ts, h["v"])
        self.ax_cd.set_xlim(0, max(60, t + 5))

        return []

    def run(self):
        self.anim = FuncAnimation(self.fig, self.update,
                                  interval=UPDATE_MS, cache_frame_data=False)
        plt.show()


def parse_args(description=__doc__.splitlines()[1]):
    """Optional overrides of the data source settings above."""
    p = argparse.ArgumentParser(description=description)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--replay", metavar="CSV",
                   help="play back a finished csv (e.g. test_000.csv from SD)")
    g.add_argument("--live", metavar="CSV",
                   help="follow a growing csv (e.g. from serial_logger.py)")
    g.add_argument("--sim", action="store_true",
                   help="use the built-in flight simulator")
    p.add_argument("--speed", type=float, default=SIM_SPEED,
                   help="replay/simulator speed (default %(default)s)")
    return p.parse_args()


def apply_args(args):
    """Set the module settings from parse_args() (also used by screen 2)."""
    global SIM_SPEED, DATA_MODE, LIVE_CSV, REPLAY_CSV
    SIM_SPEED = args.speed
    if args.replay:
        DATA_MODE, REPLAY_CSV = "replay", args.replay
    elif args.live:
        DATA_MODE, LIVE_CSV, REPLAY_CSV = "live", args.live, None
    elif args.sim:
        DATA_MODE, LIVE_CSV, REPLAY_CSV = "sim", None, None


if __name__ == "__main__":
    apply_args(parse_args())
    Dashboard().run()
