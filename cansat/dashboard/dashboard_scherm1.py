"""
CanSat 2027 — Screen 1 · Flight Data & Sensors (Python version)
================================================================

Python equivalent of scherm1_sensordata.html, built with matplotlib.

Test data: as long as there is no real CSV, TelemetrySimulator generates
a realistic flight (prelaunch → ascent → apogee → parachute → landing).
The simulator produces rows in EXACTLY the same column order as the
Teensy firmware (see initSD() in Cansat2027_teensy.ino), so the real
CSV/serial parser plugs in 1-to-1 later.

Layout: on the left the flight over time (altitude, flight phases and
vibration history on one time axis), on the right the forces of this
moment, below the parachute, the gyroscope or the radio signal, and sound.

Panels:
  - Header: the dot is green while data come in. Live only: after
    LINK_WARN_S without new data it turns amber ("No data for 4 s"), after
    LINK_LOST_S red, with a warning in the altitude chart ("NO SIGNAL")
  - KPI bar with sub-values: altitude (apogee), vertical speed (up in the
    climb, down under the parachute, with the descent rate ESA asks for),
    temperature, pressure, vibration (all bands together and the pattern of
    this moment: quiet, slow, medium, fast or a shock, the same rules as in
    tools/flight_report.py) and Cd (median)
  - Altitude vs time with an apogee marker (once the climb is over) and a
    landing marker with the flight time. A ground test (never higher than
    GROUND_TEST_M above the start) zooms in, so a staircase shows; in
    flight the axis is 0–1100 m
  - Flight phases & vibration history: the phases as a bar, and under it
    one row per frequency band with one cell per measurement, brighter =
    stronger (log scale). A lost radio packet leaves a hole.
  - Acceleration XYZ plus the PEAK acceleration per log interval
    (LSM6DSO, ±16 g), so short shocks (ejection, parachute) are not
    missed between two log lines; the largest shock is marked
  - Vibration bands: the MEASURED RMS vibration (g) in 5 frequency bands
    up to the Nyquist frequency (208 Hz), computed on the Teensy from the
    same FFT (Parseval, window-corrected), with the highest value of the
    flight per band, the strongest frequency and the TOP-5 most frequent
    strong frequencies. Only measured values are shown.
  - Cd & descent rate on a twin axis. Cd only in the steady descent (speed
    within STEADY_BAND of the usual descent rate): the formula says
    drag = weight, which is not so while the parachute opens or the can lands
  - Gyroscope (sliding window). For radio data: the signal strength (RSSI)
    of every packet over the flight, the lost packets and how many arrived
    in the last minute
  - Audio RMS with a CHUTE marker at parachute opening

Radio data (Pico receiver, see pico/main.py): the radio packet has 19
values (13 measurements + the FFT: peak strength and the 5 vibration
bands), plus RSSI and SNR. The gyroscope and the peak g are not in the
packet: the radio signal panel takes the place of the gyroscope, and the
acceleration panel says "peak g: not in radio packet".
Text and markers scale with the window, so the layout stays the same on a
small laptop screen.

Keys (replay and simulator): SPACE = pause, R = play the replay again,
F = full screen. A replay stays on its last picture at the end.

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
import sys
import time
from collections import deque

import numpy as np
import matplotlib

matplotlib.use("TkAgg")  # default on Windows; change if needed
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation, Text
from matplotlib.ticker import FuncFormatter, Locator

try:
    import krachten as K   # our CanSat (mass, parachute) + the force model
except ImportError:
    sys.exit("krachten.py is missing. Put it in the same folder as "
             "dashboard_scherm1.py and dashboard_scherm2.py: the dashboards "
             "need it.")

# ── Settings ─────────────────────────────────────────────────
SIM_SPEED = 1.0      # 1.0 = realtime, 2.0 = double speed
UPDATE_MS = 100      # check for new data every UPDATE_MS (ms); the screen
                     # is only redrawn when a new row came in
DESIGN_SIZE = (15.0, 8.5)   # window size (inches) the layout was drawn for
AUDIO_MIN_TOP = 0.01  # audio chart: smallest top of the y-axis
WINDOW_S  = 30       # time window for the small charts (s)
F_NYQUIST = 208      # LSM6DSO: 416 Hz ODR → usable spectrum 0–208 Hz
LINK_WARN_S = 3      # live: no new data for this long → amber "last data ... ago"
LINK_LOST_S = 10     # live: no new data for this long → red "NO DATA"

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
    "LANDED": "#238636",
}
# the phase in the header: text and border in the colour of the phase
PHASE_BADGE = {
    "PRELAUNCH": "#8b949e",
    "ASCENT": "#58a6ff",
    "APOGEE": "#e3b341",
    "DESCENT": "#ff6b35",
    "LANDED": "#3fb950",
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
    "acc_peak_g",
    "gps_course_deg", "gps_speed_ms",
    "vib_0_10_g", "vib_10_30_g", "vib_30_60_g", "vib_60_120_g", "vib_120_208_g",
]
# vibration bands (same edges as BAND_EDGE_HZ in the firmware)
BAND_COLUMNS = CSV_COLUMNS[-5:]
BAND_EDGES_HZ = (0, 10, 30, 60, 120, 208)
BAND_LABELS = [f"{a}–{b}" for a, b in zip(BAND_EDGES_HZ, BAND_EDGES_HZ[1:])]
# Older files (26, 27 or 29 columns, before acc_peak_g / the GPS drift /
# the vibration band columns) still load: the dashboards read columns by name and treat a
# missing one as "no data".

FFT_STRONG_G = 0.05  # fft_peak_amp (g) above which a vibration counts as
                     # "strong": a phone vibrating against the can is enough
# The vibration pattern of one row, from the five bands only: the same
# rules and names as in the flight report (tools/flight_report.py) and in
# our FFT lab tests.
QUIET_G = 0.01       # all bands together below this: quiet
ALL_BANDS_G = 0.02   # every band at least this, at the same time: a shock
PATTERNS = ("quiet", "slow · 0–10 Hz", "medium · 10–60 Hz", "fast · 60–208 Hz",
            "all bands at once: a shock")
# vibration history (the strip under the altitude chart): colour scale
VIB_MIN_G, VIB_MAX_G = 0.001, 1.0    # darkest and brightest (log scale)
STRIP_MAX_BINS = 600                 # at most this many time steps in the strip
SHOCK_MIN_G = 1.5    # a peak below this is no shock: at rest the sensor reads 1 g
STEADY_BAND = 0.20   # Cd only in the steady descent: speed within 20 % of the
                     # usual descent rate (as tools/krachten_analyse.py)
RSSI_WEAK_DBM, RSSI_BAD_DBM, RSSI_LIMIT_DBM = -100, -110, -120
ACC_PEAK_MAX_G = 16  # LSM6DSO range in the firmware (±16 g)
GROUND_TEST_M = 50   # never higher than this above the start: a ground
                     # test. The altitude chart then zooms in, so a
                     # staircase (~3 m per floor) shows. Higher: 0–1100 m
SEA_LEVEL_HPA = 1013.0   # sea-level pressure of the day (hPa). start_meting
                         # asks it on launch day (--sea-level); the altitude
                         # is converted to it. See SeaLevelFix.
FIRMWARE_SEA_LEVEL_HPA = 1014.0   # SEA_LEVEL_PRESSURE in the sketches

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


def is_number(v):
    return v is not None and v == v          # nan != nan


def fmt(v, spec):
    """Value for a label; nan (not measured, not in the radio packet) → —."""
    return format(v, spec) if is_number(v) else "—"


def ground_ylim(alts, min_span=5.0):
    """Altitude range for a ground test: every height and 0 in view, at
    least min_span metres tall, so sensor noise (±0.2 m) stays small."""
    vals = [a for a in alts if is_number(a)]
    lo, hi = min(vals + [0.0]), max(vals + [0.0])
    pad = max(0.5, 0.1 * (hi - lo), (min_span - (hi - lo)) / 2)
    return lo - pad, hi + pad


# Time on screen: the Teensy counts from the moment it is switched on, and
# on launch day it can stand on the pad for an hour. So the time charts
# start at the first data, and after a launch just before it; the clock
# counts from the first data and from the launch on as T+.
LAUNCH_LEAD_S = 30     # after a launch: the time charts start this long before it
AFTER_LANDING_S = 60   # ... and stop growing this long after the landing


def mmss(seconds):
    """Seconds → 'mm:ss' (the minutes may go past 59)."""
    s = int(max(0.0, seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def clock_text(detector, t_first, t):
    """Header clock: time since the first data; from the launch: T+."""
    if detector.t_launch is None:
        return mmss(t - (t_first if t_first is not None else t))
    dt = t - detector.t_launch
    if dt > -1.0:                    # the liftoff second itself counts as T+00:00
        return "T+" + mmss(dt)
    return "T−" + mmss(-dt)


class FromRefLocator(Locator):
    """Ticks on round seconds counted from a reference time (the first
    data, or the launch once it is detected)."""
    STEPS = (5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600)

    def __init__(self, ref):
        self.ref = ref                       # function → reference time (s)

    def __call__(self):
        return self.tick_values(*self.axis.get_view_interval())

    def tick_values(self, vmin, vmax):
        ref = self.ref()
        step = next((s for s in self.STEPS if (vmax - vmin) / s <= 8), 7200)
        k0, k1 = math.ceil((vmin - ref) / step), math.floor((vmax - ref) / step)
        return [ref + k * step for k in range(k0, k1 + 1)]


def time_axis(ax, ref):
    """Time axis in seconds from ref() (the data stay in Teensy time)."""
    ax.xaxis.set_major_locator(FromRefLocator(ref))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda v, _pos: f"{int(round(v - ref()))}"))


def duration_text(seconds):
    """'12 s', and from one minute on '3 min 05 s'."""
    s = int(max(0.0, seconds))
    return f"{s} s" if s < 60 else f"{s // 60} min {s % 60:02d} s"


def vibration_pattern(bands):
    """The vibration pattern of one row, from the five bands only: an index
    in PATTERNS, or None when a band is missing."""
    if len(bands) == 0 or any(not is_number(b) for b in bands):
        return None
    if math.sqrt(sum(b * b for b in bands)) < QUIET_G:
        return 0                                   # quiet
    if min(bands) >= ALL_BANDS_G:
        return 4                                   # all bands at once: a shock
    j = max(range(len(bands)), key=lambda i: bands[i])
    return 1 if j == 0 else (2 if j <= 2 else 3)   # slow, medium or fast


def from_radio(row):
    """Row that came in via the radio (Pico receiver): serial_logger then
    records the RSSI. Columns that are not in the radio packet are nan."""
    return is_number(row.get("rssi"))


def add_unit(fig, value_text, unit, color, size=8):
    """Unit right after the value, however wide the value is ('6' or
    '1013'). A fixed position put °C next to the pressure instead."""
    if not unit:
        return None
    ann = Annotation(unit, xy=(1, 0), xycoords=value_text, xytext=(4, 0),
                     textcoords="offset points", fontsize=size, color=color,
                     va="bottom")
    fig.add_artist(ann)
    return ann


class WindowFit:
    """Keeps the designed layout at every window size.

    Font sizes are in points, so in a smaller window (a 13-inch laptop,
    Windows scaling 125-150 %, a maximised window) the text used to be
    relatively bigger and ran into other text. Here every text, tick label
    and marker scales with the window instead, and the window starts
    inside the screen."""

    def __init__(self, fig):
        self.fig = fig
        self.f = 1.0
        ticks = {}
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis, getattr(ax, "zaxis", None)):
                if axis is None:
                    continue
                labels = axis.get_ticklabels()
                ticks[axis] = labels[0].get_fontsize() if labels else 7
        tick_ids = {id(t) for axis in ticks for t in
                    axis.get_ticklabels() + axis.get_ticklabels(minor=True)}
        self.ticks = ticks
        self.fonts = [(t, t.get_fontsize()) for t in fig.findobj(Text)
                      if id(t) not in tick_ids]
        self.marks = [(m, m.get_markersize()) for m in fig.findobj(Line2D)
                      if m.get_marker() not in (None, "None", "", " ")]
        fig.canvas.mpl_connect("resize_event", self.rescale)

    def rescale(self, _event=None):
        w, h = self.fig.get_size_inches()
        f = max(0.4, min(2.0, w / DESIGN_SIZE[0], h / DESIGN_SIZE[1]))
        if abs(f - self.f) < 0.005:
            return
        self.f = f
        for t, size in self.fonts:
            t.set_fontsize(size * f)
        for axis, size in self.ticks.items():
            axis.set_tick_params(labelsize=size * f)
        for m, size in self.marks:
            m.set_markersize(size * f)

    def fit_screen(self):
        """Make the window fit on the screen (Tk only). Runs a moment after
        the window appears: only then does Tk know the real size (with
        Windows scaling 125-150 % the window grows when it is shown)."""
        try:
            top = self.fig.canvas.get_tk_widget().winfo_toplevel()
        except AttributeError:
            return

        def fit():
            top.update_idletasks()
            w, h = top.winfo_width(), top.winfo_height()   # incl. toolbar
            if w < 50 or h < 50:                           # not shown yet
                return
            # width and height each as much as the screen allows; the
            # text scales with the smaller of the two (rescale)
            new_w = int(min(w, 0.95 * top.winfo_screenwidth()))
            new_h = int(min(h, 0.88 * top.winfo_screenheight()))
            if new_w < w - 2 or new_h < h - 2:   # the figure follows the window
                top.geometry("%dx%d+0+0" % (new_w, new_h))

        for ms in (300, 1500):
            top.after(ms, fit)


# ═════════════════════════════════════════════════════════════
#  FLIGHT SIMULATOR
# ═════════════════════════════════════════════════════════════
class TelemetrySimulator:
    """Generates test data of a complete CanSat flight.

    Physics: mass and parachute from krachten.py (330 g, Ø 45 cm)
    → terminal velocity ±8 m/s.
    """

    MASS   = K.MASS_KG                 # kg, whole CanSat with parachute
    A_PARA = K.parachute_area_m2()     # m²
    G      = K.G
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
        gps_speed = 0.0
        if self.phase in ("STIJGEND", "APOGEE", "DALEND"):
            self.wind_dir += random.gauss(0, 0.02)
            wind = 3.0 + 1.0 * math.sin(0.05 * t)
            self.x += wind * math.cos(self.wind_dir) * dt
            self.y += wind * math.sin(self.wind_dir) * dt
            gps_speed = wind
        # GPS course over ground: 0° = north, 90° = east (x = east, y = north)
        gps_course = math.degrees(math.atan2(math.cos(self.wind_dir),
                                             math.sin(self.wind_dir))) % 360
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

        # ── vibration bands (g RMS): sensor noise floor (~1 mg over the
        #    full 208 Hz, spread by bandwidth) + the vibration in its band ──
        bands = []
        for lo, hi in zip(BAND_EDGES_HZ, BAND_EDGES_HZ[1:]):
            v = 0.001 * math.sqrt((hi - lo) / 208) * (1 + random.gauss(0, 0.1))
            if lo <= fft_hz < hi:
                v = math.hypot(v, fft_amp / math.sqrt(2))   # sine: RMS = A/√2
            bands.append(abs(v))

        # ── audio RMS ~ v² + shock at chute ──
        audio = 0.004 + 0.0006 * self.v ** 2 + random.gauss(0, 0.002)
        if self.T_CHUTE <= t < self.T_CHUTE + 0.8:
            audio += 0.35 * math.exp(-8 * (t - self.T_CHUTE))
        audio = max(0.0, audio)

        # total acceleration incl. gravity, as the LSM6DSO measures it (g)
        acc_g = math.sqrt(lacc_x ** 2 + lacc_y ** 2 +
                          (lacc_z + self.G) ** 2) / self.G

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
            "acc_peak_g": acc_g,
            "gps_course_deg": gps_course,
            "gps_speed_ms": max(0.0, gps_speed + random.gauss(0, 0.1)),
            **dict(zip(BAND_COLUMNS, bands)),
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
        row, peak = None, 0.0
        for _ in range(n_sub):
            row = self.step(dt / n_sub)
            peak = max(peak, row["acc_peak_g"])
        row["acc_peak_g"] = peak          # like the firmware: max per interval
        return [row]


# ═════════════════════════════════════════════════════════════
#  ALTITUDE WITH THE SEA-LEVEL PRESSURE OF THE DAY
# ═════════════════════════════════════════════════════════════
class SeaLevelFix:
    """Altitude above sea level with the sea-level pressure of the day.

    The Teensy computes alt_m = 44330 · (1 − (p / P0)^0.1903) with its own
    fixed P0 (SEA_LEVEL_PRESSURE in the sketch, 1014 hPa). With P0, alt_m
    becomes 44330 − (44330 − alt_m) · (P0 / sea level)^0.1903: the altitude
    for the sea-level pressure of the day, without losing the decimals of
    alt_m (the radio sends the pressure with only 1 decimal, ±0.4 m).
    P0 stays 1014 hPa unless the rows clearly show the sketch was given
    another value (their pressure and altitude give P0 back)."""

    def __init__(self):
        self._p0 = []                  # P0 according to the first rows

    def __call__(self, row):
        p, alt = row.get("press_hPa"), row.get("alt_m")
        ok_p = is_number(p) and p > 100
        if not is_number(alt):
            return (44330.0 * (1.0 - (p / SEA_LEVEL_HPA) ** 0.1903) if ok_p
                    else float("nan"))
        if ok_p and len(self._p0) < 20 and abs(alt) < 20000:
            self._p0.append(p / (1.0 - alt / 44330.0) ** (1 / 0.1903))
        p0 = FIRMWARE_SEA_LEVEL_HPA
        if self._p0:
            m = float(np.median(self._p0))
            if abs(m - FIRMWARE_SEA_LEVEL_HPA) > 0.3:     # sketch changed
                p0 = round(m, 1)
        return 44330.0 - (44330.0 - alt) * (p0 / SEA_LEVEL_HPA) ** 0.1903


def saved_sea_level(csv_path):
    """The sea-level pressure start_meting saved next to a measurement
    (test_01.csv → test_01_luchtdruk.txt), or None."""
    if not csv_path:
        return None
    try:
        with open(csv_path[:-4] + "_luchtdruk.txt", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.lstrip().startswith("#"):
                    return float(line.split("=", 1)[1].strip().replace(",", "."))
    except (OSError, ValueError):
        pass
    return None


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
    loop = True       # at the end: start again. False: stay on the last row
                      # (finished becomes True) until restart() is called.

    def __init__(self, path):
        self.rows = []
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("millis") == "millis":      # header again: the can
                    continue                         # restarted, not a row
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

        # altitude for the sea-level pressure of the day, then → AGL
        # (first 10 rows: safely before any launch)
        to_asl = SeaLevelFix()
        for r in self.rows:
            r["alt_m"] = to_asl(r)
        self.ground_asl = float(np.median(
            [r["alt_m"] for r in self.rows[:10]]))
        for r in self.rows:
            r["alt_m"] -= self.ground_asl

        # GPS reference: first row with a fix (rows before it carry
        # placeholder coordinates); no fix at all → firmware defaults
        fixed = [r for r in self.rows if has_gps_fix(r)]
        self._have_fix = bool(fixed)
        fixed = fixed or self.rows
        self.lat0 = fixed[0]["lat"]
        self.lon0 = fixed[0]["lon"]
        self.h_max = max(r["alt_m"] for r in self.rows)
        xs, ys = [], []
        coslat = math.cos(math.radians(self.lat0))
        for r in fixed:
            xs.append(abs((r["lon"] - self.lon0) * 111_320.0 * coslat))
            ys.append(abs((r["lat"] - self.lat0) * 111_320.0))
        self.xy_span = max(150.0, 1.15 * max(max(xs), max(ys)))
        self.label = ("REPLAY: radio data (LoRa)" if from_radio(self.rows[0])
                      else "REPLAY: real flight data")

        # The replay clock starts at the first row: the Teensy may have
        # been on for a long time before the logger started (millis counts
        # from power-on), and the replay must not wait that long.
        self.t = self.rows[0]["millis"] / 1000.0
        self.i = 0
        self.v = 0.0          # vertical speed, + = descending (sim convention)
        self.phase = None     # replay has no ground truth
        self._started = False
        self.finished = False

    def restart(self):
        """Play the recording again from its first row."""
        self.t, self.i, self.v = self.rows[0]["millis"] / 1000.0, 0, 0.0
        self._started = self.finished = False

    def fetch(self, dt):
        """Advance the replay clock; returns the rows passed in dt."""
        if self.finished:
            return []
        self.t += dt
        target_ms = self.t * 1000.0
        out = []
        while self.i + 1 < len(self.rows):
            if self.rows[self.i + 1]["millis"] < self.rows[self.i]["millis"]:
                # the can restarted in this file: millis starts again, so
                # the replay clock continues from the new start
                self.t = self.rows[self.i + 1]["millis"] / 1000.0
                target_ms, self.v = self.t * 1000.0, 0.0
            if self.rows[self.i + 1]["millis"] > target_ms:
                break
            prev, cur = self.rows[self.i], self.rows[self.i + 1]
            dtr = (cur["millis"] - prev["millis"]) / 1000.0
            if dtr > 0:
                v_new = (prev["alt_m"] - cur["alt_m"]) / dtr
                self.v += 0.3 * (v_new - self.v)        # light smoothing
            cur[V_KEY] = self.v
            self.i += 1
            out.append(cur)
        # end of recording → loop (dashboards detect t jumping back), or
        # stay on the last row
        if self.i >= len(self.rows) - 1 and not self.loop:
            self.finished = True
            return out
        if (self.i >= len(self.rows) - 1 and
                target_ms > self.rows[-1]["millis"] + 5000):
            self.t, self.i, self.v = self.rows[0]["millis"] / 1000.0, 0, 0.0
            self.rows[0][V_KEY] = 0.0
            return out + [self.rows[0]]
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
        # air density from our own pressure and temperature
        rho = K.row_air_density(row, row["alt_m"] + self.ground_asl)
        cd = float(K.drag_coefficient(v, rho, self.MASS, self.A_PARA))
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
        self._to_asl = SeaLevelFix()
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
        if not self.rows:            # now we know where the data comes from
            self.label = ("LIVE: radio (LoRa via Pico)" if from_radio(row)
                          else "LIVE: USB (Teensy)")
        row["alt_m"] = self._to_asl(row)   # sea-level pressure of the day
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
        # air density from our own pressure and temperature
        rho = K.row_air_density(row, row["alt_m"] + self.ground_asl)
        cd = float(K.drag_coefficient(v, rho, self.MASS, self.A_PARA))
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
        self.peaks = deque(maxlen=400)       # (t, peak g): the landing shock
        self.ground_alt = None
        self._since = {}                     # condition name -> start time
        self.t_launch = None                 # liftoff (s, Teensy time)
        self.t_landed = None                 # touchdown (s, Teensy time)

    def _liftoff(self, t):
        """Last moment on the ground before the climb: the liftoff."""
        for ts, a in reversed(self.samples):
            if a - self.ground_alt < 2.0:
                return ts
        return t

    def _touchdown(self, t):
        """The landing: the first moment on the ground after the fall, or
        the landing shock right there when the peak acceleration is known
        (the same moment as in the flight report). The can is only called
        LANDED after it has been still for a while."""
        alt_now = self.samples[-1][1]
        down, later = None, t
        for ts, a in reversed(self.samples):
            if a - alt_now > 2.0:          # here it was still in the air
                down = later
                break
            later = ts
        if down is None:
            return self._since.get("still", t)
        near = [(g, ts) for ts, g in self.peaks
                if down - 3.0 <= ts <= down + 1.5 and g > K.IMPACT_G]
        return max(near)[1] if near else down

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
        peak = row.get("acc_peak_g")
        if is_number(peak):
            self.peaks.append((t, peak))

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
                self.t_launch = self._liftoff(t)
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
                self.t_landed = self._touchdown(t)
        return self.phase


# ═════════════════════════════════════════════════════════════
#  DASHBOARD
# ═════════════════════════════════════════════════════════════
N_BANDS = len(BAND_COLUMNS)
# vibration history: from the panel colour (quiet) to bright (strong)
VIB_CMAP = LinearSegmentedColormap.from_list(
    "vib", ["#222b37", "#4a3a10", "#a37a17", "#e3b341", "#fff1b8"])
VIB_CMAP.set_bad(C["bg"])              # no data: a lost packet, an old file


class Dashboard:
    N_FREQ_BINS = 52     # histogram bins for the top-5 frequencies
    N_TOP = 5            # number of marked dominant frequencies
    MIN_FREQ_ROWS = 5    # rows above FFT_STRONG_G before the list shows (~5 s)
    MIN_FREQ_COUNT = 2   # a frequency must come back at least this often

    def __init__(self):
        self.sim = make_source()
        self.live = isinstance(self.sim, CsvLive)
        self.replay = isinstance(self.sim, CsvReplay)
        if self.replay:
            self.sim.loop = False       # stay on the last picture (R = again)
        self.hist = {k: deque(maxlen=4000) for k in
                     ("t", "alt", "ax", "ay", "az", "gx", "gy", "gz",
                      "audio", "cd", "v", "apk", "rssi", "bands")}
        self.seg_artists = []
        self.paused = False
        self._wall = None        # wall-clock pacing for real-time replay
        self._changed = False    # new data since the last frame?
        self._rx_wall = None     # wall-clock time of the last new data
        self._t_open = time.monotonic()
        self._link_shown = None  # what the header says about the data link
        self._rssi_text, self._rssi_color = "", C["green"]
        self._radio_panel = False
        self._reset_run()
        if self.live:            # an old file: say at once how old the data are
            try:
                age = max(0.0, time.time() - os.path.getmtime(self.sim.path))
                self._rx_wall = self._t_open - age
            except OSError:
                pass
        self._build_figure()
        for ax in (self.ax_alt, self.ax_acc, self.ax_gyro, self.ax_radio,
                   self.ax_aud, self.ax_phase, self.ax_cd):
            time_axis(ax, self.time_ref)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _reset_run(self):
        """Everything that belongs to one run of the can (cleared when it
        restarts, when a replay starts again and in the demo loop)."""
        for d in self.hist.values():
            d.clear()
        self.detector = PhaseDetector()
        self.band_max = np.zeros(N_BANDS)       # highest per band
        self.shock_g, self.t_shock = 0.0, 0.0   # largest peak this flight
        self.apogee = 0.0
        self.t_apogee = 0.0
        self.v_max = 0.0             # fastest descent (m/s)
        self.climb_max = 0.0         # fastest climb (m/s)
        self.v_desc = []             # descent rate of every DESCENT row
        self.v_steady = []           # ... of the rows in the steady descent
        self.cd_vals = []            # Cd of each steady descent row (median)
        self.freq_hist = []          # (t, peak frequency) of strong rows
        self.segments = []           # [phase, t_start, t_end] timeline
        self.t_chute = None
        self.pkt_rx = 0
        self.pkt_lost = 0            # estimated from gaps in the stream
        self.lost_t = deque(maxlen=2000)   # when (for the radio chart)
        self._dts = []               # the last row intervals
        self.t_first = None          # time of the first row (Teensy time, s)

    # ── time on screen ──
    def time_ref(self):
        """Zero of the time axes: the launch, before that the first data."""
        if self.detector.t_launch is not None:
            return self.detector.t_launch
        return self.t_first if self.t_first is not None else 0.0

    def flight_window(self, t):
        """x-range of the altitude, phase and Cd charts: from the first data
        (still in memory); after a launch from just before it until shortly
        after the landing, so the flight fills the chart."""
        first = self.hist["t"][0] if self.hist["t"] else t
        end = t + 5
        det = self.detector
        if det.t_launch is None:
            x0 = first
        else:
            x0 = max(first, det.t_launch - LAUNCH_LEAD_S)
            if det.t_landed is not None:
                end = min(end, det.t_landed + AFTER_LANDING_S)
        return x0, max(x0 + 60, end)

    # ── construction ──
    def _style_axes(self, ax, title=None, title_color=None):
        ax.set_facecolor(C["panel"])
        for s in ax.spines.values():
            s.set_color(C["border"])
            s.set_linewidth(0.8)
        ax.tick_params(colors=C["dim"], labelsize=7.5, labelcolor=C["muted"])
        ax.grid(True, color=C["grid"], linewidth=0.5)
        if title:
            ax.set_title(title, loc="left", fontsize=9,
                         color=title_color or C["muted"],
                         fontfamily="monospace", pad=4)

    def _note(self, ax, x, y, **kw):
        """Text inside a panel on a dark plate, so no line runs through it."""
        kw.setdefault("fontsize", 7.5)
        kw.setdefault("color", C["text"])
        return ax.text(x, y, "", transform=ax.transAxes, zorder=6,
                       bbox=dict(boxstyle="round,pad=0.25", fc=C["panel"],
                                 ec="none", alpha=0.9), **kw)

    def _title_text(self):
        s = self.sim.label
        if not self.live:
            if self.paused:
                s += " · paused"
            elif getattr(self.sim, "finished", False):
                s += " · ended"
            elif SIM_SPEED != 1:
                s += f" · ×{SIM_SPEED:g}"
        return f"Screen 1 — Flight Data & Sensors ({s})"

    def _build_figure(self):
        plt.rcParams.update({
            "font.family": "monospace",
            "text.color": C["text"],
            "axes.labelcolor": C["muted"],
        })
        # matplotlib's own shortcuts would change a chart by accident (L:
        # log scale, G: grid) or close the window (Q). F (full screen) and
        # S (save a picture) stay.
        for key in plt.rcParams:
            if key.startswith("keymap.") and key not in (
                    "keymap.fullscreen", "keymap.save", "keymap.copy"):
                plt.rcParams[key] = []
        self.fig = plt.figure(figsize=DESIGN_SIZE, facecolor=C["bg"])
        self.fig.canvas.manager.set_window_title(
            "CanSat 2027 — Screen 1 · Flight Data & Sensors")

        # ── header ──
        self.fig.text(0.02, 0.962, "CanSat 2027", fontsize=14,
                      fontweight="bold", color=C["text"])
        # the dot: green = data come in, amber/red = not any more
        self.txt_dot = self.fig.text(0.117, 0.962, "●", fontsize=11,
                                     color=C["dim"])
        self.txt_title = self.fig.text(0.132, 0.962, self._title_text(),
                                       fontsize=9.5, color=C["muted"])
        self.txt_rssi = self.fig.text(0.705, 0.962, "", fontsize=9.5,
                                      color=C["green"], ha="right")
        self.txt_pkt = self.fig.text(0.80, 0.962, "packet #0", fontsize=8.5,
                                     color=C["muted"], ha="right")
        self.txt_phase = self.fig.text(0.887, 0.962, "PRELAUNCH", fontsize=10.5,
                                       color=PHASE_BADGE["PRELAUNCH"], ha="right",
                                       bbox=dict(boxstyle="round,pad=0.3",
                                                 fc="none",
                                                 ec=PHASE_BADGE["PRELAUNCH"]))
        self.txt_clock = self.fig.text(0.98, 0.962, "00:00", fontsize=13,
                                       color=C["cyan"], ha="right")
        # detected phase vs simulator ground truth (transition latency
        # of the detector shows up here as a brief mismatch)
        self.txt_truth = self.fig.text(0.887, 0.938, "", fontsize=7,
                                       color=C["dim"], ha="right")
        if not self.live:
            self.fig.text(0.02, 0.008, "SPACE = pause" + (
                " · R = play again" if self.replay else "")
                + " · F = full screen", fontsize=7, color=C["dim"])

        # ── KPI bar (value + sub-value) ──
        kpis = [("ALTITUDE", "m", C["cyan"]),
                ("VERTICAL SPEED", "m/s", C["blue"]),
                ("TEMPERATURE", "°C", C["text"]),
                ("PRESSURE", "hPa", C["text"]),
                ("VIBRATION", "g", C["amber"]),
                ("CD DRAG COEFFICIENT", "", C["green"])]     # no unit
        self.txt_kpi, self.txt_kpi_sub = [], []
        for i, (label, unit, col) in enumerate(kpis):
            x = 0.02 + i * 0.162
            self.fig.text(x, 0.922, label, fontsize=8, color=C["muted"])
            v = self.fig.text(x, 0.881, "—", fontsize=20, fontweight="bold",
                              color=col)
            add_unit(self.fig, v, unit, C["muted"], size=9)
            sub = self.fig.text(x, 0.858, "", fontsize=7.5, color=C["muted"])
            self.txt_kpi.append(v)
            self.txt_kpi_sub.append(sub)

        # ── panels: on the left the flight over time (altitude, phases and
        #    vibration history on one time axis), on the right the forces
        #    of this moment, below the parachute, the gyroscope or the
        #    radio signal, and the sound ──
        gs = GridSpec(3, 6, figure=self.fig,
                      left=0.055, right=0.962, top=0.822, bottom=0.07,
                      hspace=0.36, wspace=0.62,
                      height_ratios=[36, 25, 23])

        # Row 1: altitude (wide) + acceleration
        self.ax_alt = self.fig.add_subplot(gs[0, :4])
        self._style_axes(self.ax_alt, "● ALTITUDE VS TIME (m above the start)",
                         C["cyan"])
        self.ln_alt, = self.ax_alt.plot([], [], color=C["cyan"], lw=2)
        self.fill_alt = None
        self.ln_apogee = self.ax_alt.axvline(np.nan, color=C["amber"], lw=1,
                                             ls="--", alpha=0.6)
        self.txt_apogee = self.ax_alt.text(0, 0, "", fontsize=8,
                                           color=C["amber"], visible=False)
        self.ln_landed = self.ax_alt.axvline(np.nan, color=C["green"], lw=1,
                                             ls="--", alpha=0.7)
        self.txt_landed = self.ax_alt.text(
            0, 0.92, "", fontsize=8, color=C["green"], ha="right",
            transform=self.ax_alt.get_xaxis_transform())
        self.ax_alt.set_ylim(0, self.sim.h_max * 1.12)
        # says why the axis is small during a ground test
        self.txt_alt_zoom = self.ax_alt.set_title(
            "", loc="right", fontsize=7.5, color=C["muted"], pad=4)
        # live: the data stopped coming in
        self.txt_warn = self.ax_alt.text(
            0.5, 0.86, "", fontsize=13, fontweight="bold", color=C["red"],
            ha="center", va="top", linespacing=1.5, zorder=7,
            transform=self.ax_alt.transAxes,
            bbox=dict(boxstyle="round,pad=0.5", fc="#2d1215", ec=C["red"]))
        self.txt_warn.set_visible(False)

        self.ax_acc = self.fig.add_subplot(gs[0, 4:])
        self._style_axes(self.ax_acc, "● ACCELERATION (m/s²)", C["blue"])
        self.ln_ax, = self.ax_acc.plot([], [], color=C["blue"], lw=1.2, label="X")
        self.ln_ay, = self.ax_acc.plot([], [], color=C["green"], lw=1.2, label="Y")
        self.ln_az, = self.ax_acc.plot([], [], color=C["orange"], lw=1.2, label="Z")
        self.ax_acc.set_ylim(-30, 45)
        # peak |a| per log interval (LSM6DSO, incl. gravity: rest = 1 g)
        self.ax_pk = self.ax_acc.twinx()
        self.ax_pk.set_ylim(0, ACC_PEAK_MAX_G)
        self.ax_pk.tick_params(colors=C["text"], labelsize=7.5)
        for sp in self.ax_pk.spines.values():
            sp.set_color(C["border"])
        self.ax_pk.set_ylabel("peak g", fontsize=7.5, color=C["text"],
                              labelpad=2)
        self.ln_pk, = self.ax_pk.plot([], [], color=C["text"], lw=1.2,
                                      ls="--", label="peak (g)")
        self.txt_shock = self._note(self.ax_pk, 0.02, 0.89)
        lines = [self.ln_ax, self.ln_ay, self.ln_az, self.ln_pk]
        leg = self.ax_pk.legend(lines, [l.get_label() for l in lines],
                                loc="upper right", fontsize=7, ncol=2,
                                labelcolor=C["muted"], facecolor=C["panel"],
                                edgecolor="none", framealpha=0.85,
                                borderpad=0.3, columnspacing=1.0)
        leg.set_zorder(6)

        # Row 2: flight phases + vibration history (the same time axis as
        # the altitude chart above it) + the vibration of this moment
        self.ax_phase = self.fig.add_subplot(gs[1, :4])
        self._style_axes(
            self.ax_phase,
            "● FLIGHT PHASES & VIBRATION HISTORY  "
            "(g RMS per band · brighter = stronger)", C["amber"])
        self.mesh_vib = None         # drawn in _draw_strip
        self.vib_norm = LogNorm(VIB_MIN_G, VIB_MAX_G, clip=True)
        self.ax_phase.set_autoscale_on(False)
        self.ax_phase.grid(False)
        self.ax_phase.set_ylim(0, N_BANDS + 1.3)
        self.ax_phase.set_yticks([i + 0.5 for i in range(N_BANDS)]
                                 + [N_BANDS + 0.72])
        self.ax_phase.set_yticklabels(BAND_LABELS + ["phase"], fontsize=7)
        self.ax_phase.tick_params(axis="y", length=0)
        self.ax_phase.set_ylabel("band (Hz)", fontsize=7.5, labelpad=2)
        for i in range(1, N_BANDS + 1):          # a thin line between the rows
            self.ax_phase.axhline(i, color=C["bg"], lw=1, zorder=2)
        self.ln_phase_now = self.ax_phase.axvline(0, color=C["text"], lw=1.2,
                                                  zorder=5)
        # shown when the bands are missing (old radio packet, old file)
        self.txt_strip_note = self.ax_phase.text(
            0.5, 0.5 * N_BANDS / (N_BANDS + 1.3), "", fontsize=8,
            color=C["muted"], ha="center", va="center",
            transform=self.ax_phase.transAxes, zorder=6)

        self.ax_fft = self.fig.add_subplot(gs[1, 4:])
        self._style_axes(self.ax_fft, "● VIBRATION PER BAND (g RMS)",
                         C["amber"])
        # one bar per frequency band = latest measurement; the grey tick
        # is the highest value of this flight. Log scale: from sensor
        # noise (~0.001 g) up to strong vibration (several g). The top of
        # the axis is kept free for the text.
        xb = np.arange(N_BANDS)
        self.band_bars = self.ax_fft.bar(xb, np.full(len(xb), 1e-5),
                                         width=0.65, color=C["amber"],
                                         zorder=3)
        self.band_max_marks, = self.ax_fft.plot(
            xb, np.full(len(xb), np.nan), "_", color=C["muted"], ms=20, mew=2,
            zorder=4)
        self.band_texts = [self.ax_fft.text(x, 1e-4, "", fontsize=7,
                                            color=C["text"], ha="center",
                                            va="bottom", zorder=5) for x in xb]
        self.ax_fft.set_yscale("log")
        self.ax_fft.set_ylim(1e-4, 30)
        self.ax_fft.set_yticks([0.001, 0.01, 0.1, 1, 10])
        self.ax_fft.set_yticklabels(["0.001", "0.01", "0.1", "1", "10"])
        self.ax_fft.minorticks_off()
        self.ax_fft.grid(axis="x", visible=False)
        self.ax_fft.set_xticks(xb)
        self.ax_fft.set_xticklabels(BAND_LABELS, fontsize=7.5)
        self.ax_fft.set_xlabel("frequency band (Hz)", fontsize=7.5, labelpad=2)
        # top right: the strongest vibration of this moment
        self.txt_fftpeak = self.ax_fft.set_title(
            "", loc="right", fontsize=8, color=C["amber"], pad=4)
        # top-5 most frequent strong frequencies of this flight
        self.txt_top = self.ax_fft.text(0.985, 0.90, "", fontsize=7,
                                        color=C["blue"], ha="right",
                                        transform=self.ax_fft.transAxes,
                                        zorder=6)
        # shown when the bands are missing (old radio packet, old file)
        self.txt_band_note = self.ax_fft.text(
            0.5, 0.5, "", fontsize=8, color=C["muted"], ha="center",
            va="center", transform=self.ax_fft.transAxes)

        # Row 3: Cd & descent rate + gyroscope / radio signal + audio
        self.ax_cd = self.fig.add_subplot(gs[2, :2])
        self._style_axes(self.ax_cd,
                         "● DRAG COEFFICIENT CD & DESCENT RATE",
                         C["green"])
        self.ln_cd, = self.ax_cd.plot([], [], color=C["green"], lw=1.8,
                                      label="Cd (−)")
        self.ax_cd.set_ylim(0, 1.5)
        self.ax_cd.tick_params(axis="y", colors=C["green"],
                               labelcolor=C["green"])
        self.ax_v = self.ax_cd.twinx()
        self.ax_v.set_facecolor("none")
        for s in self.ax_v.spines.values():
            s.set_color(C["border"])
        self.ax_v.tick_params(colors=C["blue"], labelsize=7.5)
        self.ln_v, = self.ax_v.plot([], [], color=C["blue"], lw=1.5,
                                    ls="--", label="v (m/s)")
        self.ax_v.set_ylim(0, 40)
        # the descent rate ESA asks for
        lo, hi = K.DESCENT_RATE_MS
        self.ax_v.axhspan(lo, hi, color=C["blue"], alpha=0.10, lw=0)
        self.ax_v.text(0.015, (lo + hi) / 2, f"ESA {lo:g}–{hi:g} m/s",
                       fontsize=7, color=C["blue"], va="center",
                       transform=self.ax_v.get_yaxis_transform())
        self.txt_cd_note = self.ax_cd.text(
            0.5, 0.56, "", fontsize=8, color=C["muted"], ha="center",
            va="center", linespacing=1.5, transform=self.ax_cd.transAxes)
        lines = [self.ln_cd, self.ln_v]
        self.ax_v.legend(lines, [l.get_label() for l in lines],
                         loc="upper right", fontsize=7, frameon=False,
                         labelcolor=C["muted"])

        self.ax_gyro = self.fig.add_subplot(gs[2, 2:4])
        self._style_axes(self.ax_gyro, "● GYROSCOPE (°/s)", C["purple"])
        self.ln_gx, = self.ax_gyro.plot([], [], color=C["purple"], lw=1.2, label="X")
        self.ln_gy, = self.ax_gyro.plot([], [], color=C["blue"], lw=1.2, label="Y")
        self.ln_gz, = self.ax_gyro.plot([], [], color=C["green"], lw=1.2, label="Z")
        self.ax_gyro.set_ylim(-50, 150)
        self.ax_gyro.legend(loc="upper right", fontsize=7, frameon=False,
                            labelcolor=C["muted"], ncol=3, columnspacing=1.0)
        # shown when there is nothing to draw
        self.txt_gyro_note = self.ax_gyro.text(
            0.5, 0.5, "", fontsize=8, color=C["muted"], ha="center",
            va="center", transform=self.ax_gyro.transAxes)

        # The same place, for radio data: the gyroscope is not in the radio
        # packet, the signal strength is. One dot per packet.
        self.ax_radio = self.fig.add_subplot(gs[2, 2:4])
        self._style_axes(self.ax_radio, "● RADIO SIGNAL (RSSI, dBm)",
                         C["green"])
        self.ln_rssi, = self.ax_radio.plot([], [], color=C["green"], lw=1.2,
                                           marker="o", ms=2.5)
        self.ln_lost, = self.ax_radio.plot([], [], "|", color=C["red"],
                                           ms=7, mew=1.2)
        self.ax_radio.set_ylim(-132, -20)
        self.ax_radio.set_yticks([-120, -100, -80, -60, -40])
        self.ax_radio.axhline(RSSI_LIMIT_DBM, color=C["red"], lw=1,
                              ls="--", alpha=0.7)
        self.ax_radio.text(0.985, RSSI_LIMIT_DBM + 2, "limit of the radio",
                           fontsize=7, color=C["red"], ha="right", va="bottom",
                           transform=self.ax_radio.get_yaxis_transform())
        self.txt_link = self._note(self.ax_radio, 0.02, 0.89)
        self.ax_radio.set_visible(False)

        self.ax_aud = self.fig.add_subplot(gs[2, 4:])
        self._style_axes(self.ax_aud, "● AUDIO RMS", C["orange"])
        self.ln_aud, = self.ax_aud.plot([], [], color=C["orange"], lw=1.5)
        # y-axis scales with the sound (real values are small: ~0.003
        # in a quiet room, a clap averaged over 1 s maybe 0.02)
        self.ax_aud.set_ylim(0, AUDIO_MIN_TOP)
        self.txt_aud = self.ax_aud.text(0.5, 0.84, "", fontsize=13,
                                        fontweight="bold", color=C["orange"],
                                        ha="center",
                                        transform=self.ax_aud.transAxes)
        self.ln_chute = self.ax_aud.axvline(np.nan, color=C["amber"], lw=1,
                                            ls="--", alpha=0.8)
        # clip_on: outside the time window the label must not show up on
        # top of another panel
        self.txt_chute = self.ax_aud.text(0, 0.9, "", fontsize=7,
                                          color=C["amber"], rotation=90,
                                          va="top", clip_on=True,
                                          transform=self.ax_aud.get_xaxis_transform())
        self.time_labels = [ax.xaxis.label for ax in
                            (self.ax_cd, self.ax_gyro, self.ax_radio,
                             self.ax_aud)]
        for lab in self.time_labels:
            lab.set_fontsize(7.5)
            lab.set_text("time since start (s)")
        for ax in (self.ax_cd, self.ax_gyro, self.ax_radio, self.ax_aud):
            ax.xaxis.labelpad = 2

        # text and markers scale with the window (13-inch laptop, ...)
        self.fit = WindowFit(self.fig)

    # ── keys: pause a replay, play it again ──
    def _on_key(self, event):
        key = (event.key or "").lower()
        if self.live:
            return
        if key in (" ", "space"):
            self.paused = not self.paused
        elif key == "r" and self.replay:
            self.sim.restart()
            self.paused = False
        else:
            return
        self.txt_title.set_text(self._title_text())
        self.fig.canvas.draw_idle()

    # ── phase timeline ──
    def _track_phase(self, t, ph):
        if not self.segments or self.segments[-1][0] != ph:
            self.segments.append([ph, t, t])
            if ph == "DESCENT" and self.t_chute is None:
                self.t_chute = t
        else:
            self.segments[-1][2] = t

    def _draw_timeline(self, t_end, x0, x1):
        for art in self.seg_artists:
            art.remove()
        self.seg_artists = []
        y0, height = N_BANDS + 0.22, 1.0
        for k, (ph, t0, t1) in enumerate(self.segments):
            # up to the start of the next phase: no holes in the bar
            if k + 1 < len(self.segments):
                t1 = self.segments[k + 1][1]
            rect = Rectangle((t0, y0), max(t1 - t0, 0.1), height,
                             facecolor=PHASE_COLORS.get(ph, C["dim"]),
                             edgecolor="none", zorder=3)
            self.ax_phase.add_patch(rect)
            self.seg_artists.append(rect)
            a, b = max(t0, x0), min(t1, x1)      # the part that is in view
            # the label only where it fits (~1 % of the width per letter)
            if b > a and (b - a) / (x1 - x0) > 0.0105 * (len(ph) + 2):
                tx = self.ax_phase.text(0.5 * (a + b), y0 + height / 2, ph,
                                        fontsize=7.5 * self.fit.f,
                                        color=C["text"], ha="center",
                                        va="center", zorder=4)
                self.seg_artists.append(tx)
        self.ax_phase.set_xlim(x0, x1)
        self.ln_phase_now.set_xdata([t_end, t_end])

    def _draw_strip(self, x0, x1):
        """Vibration history: one row per band, one cell per measurement.
        A lost packet leaves a hole. A long recording gets wider cells,
        each with the highest value in it, so a short shock stays visible."""
        if self.mesh_vib is not None:
            self.mesh_vib.remove()
            self.mesh_vib = None
        ts = np.array(self.hist["t"])
        if len(ts) == 0:
            return
        vals = np.array(self.hist["bands"], dtype=float)       # rows × bands
        nominal = float(np.median(self._dts)) if self._dts else 1.0
        nominal = nominal if nominal > 0 else 1.0
        keep = (ts >= x0 - nominal) & (ts <= x1 + nominal)
        ts, vals = ts[keep], vals[keep]
        if len(ts) == 0 or not np.isfinite(vals).any():
            self.txt_strip_note.set_text(
                "" if len(ts) == 0 else "no band data: " + (
                    "not in this radio packet" if is_number(self.hist["rssi"][-1])
                    else "not in this file"))
            return
        self.txt_strip_note.set_text("")
        k = int(math.ceil(len(ts) / STRIP_MAX_BINS))            # rows per cell
        if k > 1:
            pad = -len(ts) % k
            ts = np.concatenate([ts, np.full(pad, ts[-1])])
            vals = np.concatenate([vals, np.full((pad, N_BANDS), np.nan)])
            first, last = ts[::k], ts[k - 1::k]
            vals = np.fmax.reduce(vals.reshape(-1, k, N_BANDS), axis=1)
        else:
            first = last = ts
        half = nominal / 2
        edges, cols = [first[0] - half], []
        hole = np.full(N_BANDS, np.nan)
        for i in range(len(first)):
            cols.append(vals[i])
            if i + 1 == len(first):
                edges.append(last[i] + half)
            elif first[i + 1] - last[i] <= 1.5 * nominal:      # the next row
                edges.append((last[i] + first[i + 1]) / 2)
            else:                                              # rows are missing
                edges += [last[i] + half, first[i + 1] - half]
                cols.append(hole)
        grid = np.ma.masked_invalid(np.array(cols).T)          # bands × cells
        self.mesh_vib = self.ax_phase.pcolormesh(
            np.array(edges), np.arange(N_BANDS + 1), grid, cmap=VIB_CMAP,
            norm=self.vib_norm, shading="flat", zorder=1)

    # ── top-5 dominant frequencies ──
    def _update_top_freqs(self):
        found = []
        # after liftoff only the flight counts: above FFT_STRONG_G, carrying
        # the can to the launch pad would fill the list too
        t_launch = self.detector.t_launch
        freqs = np.array([f for t, f in self.freq_hist
                          if t_launch is None or t >= t_launch])
        if len(freqs) >= self.MIN_FREQ_ROWS:
            edges = np.linspace(0, F_NYQUIST, self.N_FREQ_BINS + 1)
            bin_of = np.clip(np.digitize(freqs, edges) - 1,
                             0, self.N_FREQ_BINS - 1)
            counts = np.bincount(bin_of, minlength=self.N_FREQ_BINS)
            for idx in np.argsort(counts)[::-1]:
                if (counts[idx] < self.MIN_FREQ_COUNT
                        or len(found) == self.N_TOP):
                    break
                # the measured frequencies in this bin, not the bin centre
                # (bins are 4 Hz wide): 37 Hz shows as 37, like "strongest".
                # A frequency on a bin edge fills two bins: show it once.
                hz = f"{np.median(freqs[bin_of == idx]):.0f}Hz"
                if hz not in found:
                    found.append(hz)
        self.txt_top.set_text(
            "most frequent: " + "  ".join(
                f"{rank}·{hz}" for rank, hz in enumerate(found, 1))
            if found else "")

    # ── ingest one telemetry row (history, detector, statistics) ──
    def _ingest(self, row):
        cd = self.sim.drag_coefficient(row)
        t = row["millis"] / 1000.0

        # restart detection (demo loop / can reboot / replay again)
        if self.hist["t"] and t < self.hist["t"][-1]:
            self._reset_run()
            self.ln_chute.set_xdata([np.nan, np.nan])
            self.txt_chute.set_text("")
        if self.t_first is None:
            self.t_first = t

        # lost rows, estimated from gaps in the stream relative to the
        # normal row interval (as screen 2 does)
        if self.hist["t"]:
            gap = t - self.hist["t"][-1]
            if self._dts:
                nominal = float(np.median(self._dts))
                if nominal > 0 and gap > 1.5 * nominal:
                    n_lost = max(0, round(gap / nominal) - 1)
                    self.pkt_lost += n_lost
                    for k in range(1, min(n_lost, 300) + 1):
                        self.lost_t.append(self.hist["t"][-1] + k * nominal)
            self._dts = (self._dts + [gap])[-20:]

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
        h["rssi"].append(row.get("rssi", float("nan")))
        v_row = row_speed(self.sim, row)             # + = descending
        v_now = v_row if det == "DESCENT" else float("nan")
        h["v"].append(v_now)
        if row["alt_m"] > self.apogee:
            self.apogee = row["alt_m"]
            self.t_apogee = t
        if det == "ASCENT" and is_number(v_row):
            self.climb_max = max(self.climb_max, -v_row)
        # Cd only in the steady descent: the formula says drag = weight, and
        # that is not so while the parachute opens or the can lands. Steady
        # = within STEADY_BAND of the usual descent rate (the median).
        steady = False
        if not math.isnan(v_now):
            self.v_max = max(self.v_max, v_now)
            self.v_desc.append(v_now)
            usual = float(np.median(self.v_desc))
            steady = (len(self.v_desc) >= 5 and
                      abs(v_now - usual) <= STEADY_BAND * usual)
        if steady:
            self.v_steady.append(v_now)
        if not (steady and is_number(cd)):
            cd = float("nan")
        else:
            self.cd_vals.append(cd)
        h["cd"].append(cd)
        bands = tuple(row.get(c, float("nan")) for c in BAND_COLUMNS)
        h["bands"].append(bands)
        if all(is_number(b) for b in bands):
            self.band_max = np.maximum(self.band_max, bands)
        apk = row.get("acc_peak_g", float("nan"))    # nan: older file
        h["apk"].append(apk)
        if apk > self.shock_g:
            self.shock_g, self.t_shock = apk, t
        if row["fft_peak_amp"] > FFT_STRONG_G:
            self.freq_hist.append((t, min(row["fft_peak_hz"], F_NYQUIST)))
        self.pkt_rx += 1
        self._track_phase(t, det)
        return cd, det, t

    # ── the data link (live only): are the data still coming in? ──
    def _refresh_link(self, now=None):
        """Header dot, link text and the warning in the altitude chart.
        Returns True when something on screen changed."""
        now = time.monotonic() if now is None else now
        dot, text, color, warn = C["green"], self._rssi_text, self._rssi_color, ""
        if self.live:
            since = self._rx_wall if self._rx_wall is not None else self._t_open
            age = now - since
            if not self.hist["t"] and age < LINK_LOST_S:   # no row yet
                dot, text, color = C["amber"], "waiting for data…", C["amber"]
            elif age >= LINK_LOST_S:
                dot = color = C["red"]
                text = f"No signal for {duration_text(age)}"
                warn = (f"NO SIGNAL for {duration_text(age)}\n"
                        "check the receiver and the logger window")
            elif age >= LINK_WARN_S:
                dot = color = C["amber"]
                text = f"No data for {age:.0f} s"
        shown = (dot, text, color, warn)
        if shown == self._link_shown:
            return False
        self._link_shown = shown
        self.txt_dot.set_color(dot)
        self.txt_rssi.set_text(text)
        self.txt_rssi.set_color(color)
        self.txt_warn.set_text(warn)
        self.txt_warn.set_visible(bool(warn))
        return True

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
        if self.paused:
            self._changed = False
            return []

        # fetch all new rows (a live catch-up can deliver hundreds at
        # once); ingest each of them, render once from the last
        rows = self.sim.fetch(dt)
        self._changed = bool(rows)
        if not rows:
            title = self._title_text()              # a replay that ended
            if self.txt_title.get_text() != title:
                self.txt_title.set_text(title)
                self._changed = True
            return []
        self._rx_wall = now
        for r in rows[:-1]:
            self._ingest(r)
        row = rows[-1]
        cd, det, t = self._ingest(row)
        radio = from_radio(row)

        h = self.hist
        ts = np.array(h["t"])

        # ── header ──
        title = self._title_text()
        if self.txt_title.get_text() != title:      # LIVE: USB or radio
            self.txt_title.set_text(title)
        # real RSSI/SNR when the data came in via the radio; only the
        # simulator shows a simulated value, explicitly labelled
        rssi, snr = row.get("rssi"), row.get("snr")
        self._rssi_color = C["green"]
        if is_number(rssi):
            self._rssi_text = f"RSSI {rssi:.0f} dBm" + (
                f" · SNR {snr:+.1f} dB" if is_number(snr) else "")
            if rssi < RSSI_BAD_DBM:
                self._rssi_color = C["red"]
            elif rssi < RSSI_WEAK_DBM:
                self._rssi_color = C["amber"]
        elif isinstance(self.sim, TelemetrySimulator):
            rssi_sim = -70 - 0.045 * row["alt_m"] + random.gauss(0, 1.5)
            self._rssi_text = f"RSSI {rssi_sim:.0f} dBm (sim)"
        else:
            self._rssi_text = ""                    # USB or SD card: no radio
        self._refresh_link(now)
        self.txt_pkt.set_text(f"packet #{self.pkt_rx}")
        self.txt_phase.set_text(det)
        badge = PHASE_BADGE.get(det, C["amber"])
        self.txt_phase.set_color(badge)
        self.txt_phase.get_bbox_patch().set_edgecolor(badge)
        self.txt_clock.set_text(clock_text(self.detector, self.t_first, t))
        if self.sim.phase is not None:          # simulator: ground truth
            truth = PHASE_EN.get(self.sim.phase, self.sim.phase)
            ok = truth == det
            self.txt_truth.set_text(f"sim truth: {truth} "
                                    f"{'✓' if ok else '✗'}")
            self.txt_truth.set_color(C["green"] if ok else C["red"])
        else:                                   # real data: no ground truth
            self.txt_truth.set_text("")

        # ── KPIs ──
        alt = row["alt_m"]
        flight = self.apogee > GROUND_TEST_M      # else: a ground test
        # the highest point so far is the apogee once the climb is over
        topped = det in ("APOGEE", "DESCENT", "LANDED")
        if not is_number(alt):
            alt_txt = "—"
        elif flight:
            alt_txt = f"{int(round(alt))}"                # no "-0"
        else:                       # ground test: decimetres count here
            alt_txt = f"{round(alt, 1) or 0.0:.1f}"       # no "-0.0"
        if flight:
            alt_sub = (f"apogee: {self.apogee:.0f} m" if topped
                       else f"highest: {self.apogee:.0f} m")
        else:
            alt_sub = (f"highest: {self.apogee:.1f} m"
                       if self.apogee >= 1.0 else "")
        # vertical speed: up in the climb, down under the parachute
        v_row = row_speed(self.sim, row)
        if det in ("ASCENT", "APOGEE", "DESCENT") and is_number(v_row):
            arrow = "↓" if v_row > 0.05 else ("↑" if v_row < -0.05 else "")
            v_txt = arrow + (f"{abs(v_row):.0f}" if abs(v_row) >= 20
                             else f"{abs(v_row):.1f}")
        else:
            v_txt = "0.0"
        v_sub, v_sub_color = "", C["muted"]
        if self.v_steady:            # the usual descent rate, once it is steady
            usual = float(np.median(self.v_steady))
            lo, hi = K.DESCENT_RATE_MS
            v_sub = f"descent: {usual:.1f} m/s · ESA {lo:g}–{hi:g}"
            v_sub_color = C["green"] if lo <= usual <= hi else C["amber"]
        elif self.v_desc and det == "LANDED":
            v_sub = f"descent: {np.median(self.v_desc):.1f} m/s (never steady)"
        elif self.climb_max > 0:
            v_sub = f"fastest climb: {self.climb_max:.0f} m/s"
        # vibration: all bands together, and the pattern of this moment
        bands = h["bands"][-1]
        pattern = vibration_pattern(bands)
        if pattern is None:
            vib_txt = "—"
            vib_sub = ("not in radio packet" if radio else "no band data")
        else:
            total = math.sqrt(sum(b * b for b in bands))
            vib_txt = f"{total:.3f}" if total < 0.1 else f"{total:.2f}"
            vib_sub = PATTERNS[pattern]
        vals = (alt_txt,
                v_txt,
                fmt(row["temp_C"], ".1f"),
                # 0.01 hPa ≈ 8 cm: on a ground test every step shows. The
                # radio sends the pressure with 1 decimal only.
                fmt(row["press_hPa"], ".1f" if radio else ".2f"),
                vib_txt,
                fmt(cd, ".2f"))
        # real data: where the start lies, and the sea-level pressure used
        asl = getattr(self.sim, "ground_asl", None)
        real = not isinstance(self.sim, TelemetrySimulator)
        if real and is_number(asl):
            alt_sub = (alt_sub + " · " if alt_sub else "") + f"start {asl:.0f} m ASL"
        if self.cd_vals:
            cd_sub = f"median: {np.median(self.cd_vals):.2f}"
        else:
            cd_sub = "descent not steady yet" if det == "DESCENT" else ""
        subs = (alt_sub,
                v_sub,
                "",
                (f"sea level {SEA_LEVEL_HPA:g} hPa" +
                 (" · radio: 0.1 hPa" if radio else "")) if real else "",
                vib_sub,
                cd_sub)
        for txt, v in zip(self.txt_kpi, vals):
            txt.set_text(v)
        for txt, v in zip(self.txt_kpi_sub, subs):
            txt.set_text(v)
        self.txt_kpi_sub[1].set_color(v_sub_color)

        # ── altitude: in flight 0–1100 m (grows along with a higher
        #    apogee); a ground test zooms in (GROUND_TEST_M) ──
        if flight:
            if self.apogee > self.sim.h_max:
                self.sim.h_max = self.apogee * 1.1
            self.ax_alt.set_ylim(0, self.sim.h_max * 1.12)
            self.txt_alt_zoom.set_text("")
        else:
            self.ax_alt.set_ylim(*ground_ylim(h["alt"]))
            self.txt_alt_zoom.set_text(
                f"below {GROUND_TEST_M} m: zoomed in · flight: 0–1100 m")
        self.ln_alt.set_data(ts, h["alt"])
        if self.fill_alt:
            self.fill_alt.remove()
        self.fill_alt = self.ax_alt.fill_between(
            ts, 0, np.array(h["alt"]), color=C["cyan"], alpha=0.12)
        x0, x1 = self.flight_window(t)
        self.ax_alt.set_xlim(x0, x1)
        if flight and topped:
            self.ln_apogee.set_xdata([self.t_apogee, self.t_apogee])
            self.txt_apogee.set_position((self.t_apogee + 0.008 * (x1 - x0),
                                          self.sim.h_max * 1.03))
            self.txt_apogee.set_text(f"APOGEE {self.apogee:.0f} m")
            self.txt_apogee.set_visible(True)
        else:
            self.ln_apogee.set_xdata([np.nan, np.nan])
            self.txt_apogee.set_visible(False)
        t_landed, t_launch = self.detector.t_landed, self.detector.t_launch
        if t_landed is not None and t_launch is not None:
            self.ln_landed.set_xdata([t_landed, t_landed])
            self.txt_landed.set_position((t_landed - 0.008 * (x1 - x0), 0.92))
            self.txt_landed.set_text(
                f"LANDED · flight time {mmss(t_landed - t_launch)}")
        else:
            self.ln_landed.set_xdata([np.nan, np.nan])
            self.txt_landed.set_text("")

        # ── sliding window for the small charts ──
        t0 = max(0, t - WINDOW_S)
        for ax in (self.ax_acc, self.ax_gyro, self.ax_aud):
            ax.set_xlim(t0, max(WINDOW_S, t))
        self.ln_ax.set_data(ts, h["ax"])
        self.ln_ay.set_data(ts, h["ay"])
        self.ln_az.set_data(ts, h["az"])
        self.ln_pk.set_data(ts, h["apk"])
        if self.shock_g >= SHOCK_MIN_G:
            more = "≥" if self.shock_g >= K.SENSOR_MAX_G - 0.1 else ""
            self.txt_shock.set_text(
                f"largest shock {more}{self.shock_g:.1f} g at "
                f"{clock_text(self.detector, self.t_first, self.t_shock)}")
        elif self.shock_g > 0:
            self.txt_shock.set_text("largest shock: none yet (at rest: 1 g)")
        elif radio:
            self.txt_shock.set_text("peak g: not in radio packet")
        else:
            self.txt_shock.set_text("")

        # ── gyroscope, or for radio data the signal strength ──
        if radio != self._radio_panel:
            self._radio_panel = radio
            self.ax_radio.set_visible(radio)
            self.ax_gyro.set_visible(not radio)
        if radio:
            self._draw_radio(ts, t, x0, x1)
        else:
            self.ln_gx.set_data(ts, h["gx"])
            self.ln_gy.set_data(ts, h["gy"])
            self.ln_gz.set_data(ts, h["gz"])
            seen = [g for tt, g3 in zip(ts, zip(h["gx"], h["gy"], h["gz"]))
                    if tt >= t0 for g in g3 if is_number(g)]
            if seen:
                self.txt_gyro_note.set_text("")
                # the usual range, wider when the can spins faster
                self.ax_gyro.set_ylim(min(-50, 1.15 * min(seen)),
                                      max(150, 1.15 * max(seen)))
            else:
                self.txt_gyro_note.set_text("no gyroscope data")

        self.ln_aud.set_data(ts, h["audio"])
        vis = [a for tt, a in zip(ts, h["audio"]) if tt >= t0 and a == a]
        self.ax_aud.set_ylim(0, max([AUDIO_MIN_TOP] + vis) * 1.25)
        self.txt_aud.set_text(fmt(row["audio_rms"], ".4f"))
        if self.t_chute is not None:
            self.ln_chute.set_xdata([self.t_chute, self.t_chute])
            self.txt_chute.set_position((self.t_chute + 0.4, 0.9))
            self.txt_chute.set_text("CHUTE")

        # ── vibration bands: measured values only ──
        bands = np.array(bands, dtype=float)
        if np.isnan(bands).any():               # old radio packet or older file
            for bar, tx in zip(self.band_bars, self.band_texts):
                bar.set_height(1e-5)
                tx.set_text("")
            self.band_max_marks.set_ydata(np.full(len(bands), np.nan))
            self.txt_band_note.set_text("bands not in radio packet" if radio
                                        else "no band data in this file")
        else:
            for bar, tx, v, top in zip(self.band_bars, self.band_texts,
                                       bands, self.band_max):
                bar.set_height(max(v, 1e-5))
                # the value above the bar, or above the grey tick (the
                # highest so far) when that sits just above the bar
                y = max(v, 1.2e-4) * 1.22
                if v <= top < 6 * v:
                    y = top * 1.5
                tx.set_position((bar.get_x() + bar.get_width() / 2, y))
                tx.set_text(f"{v:.2g}")
            self.band_max_marks.set_ydata(
                np.where(self.band_max > 0, self.band_max, np.nan))
            self.txt_band_note.set_text("")
        peak_hz, peak_amp = row["fft_peak_hz"], row["fft_peak_amp"]
        if not is_number(peak_amp):     # radio: frequency yes, strength no
            peak = (f"strongest {peak_hz:.0f} Hz" if is_number(peak_hz)
                    else "no vibration data")
        elif peak_amp > FFT_STRONG_G:
            peak = f"strongest {peak_hz:.0f} Hz · {peak_amp:.2f} g"
        else:
            peak = "no strong vibration"
        self.txt_fftpeak.set_text(peak)
        self._update_top_freqs()

        # ── flight phases + vibration history ──
        self._draw_strip(x0, x1)
        self._draw_timeline(t, x0, x1)

        # ── Cd & descent rate ──
        self.ln_cd.set_data(ts, h["cd"])
        self.ln_v.set_data(ts, h["v"])
        self.ax_cd.set_xlim(x0, x1)
        self.ax_v.set_ylim(0, max(40.0, 1.15 * self.v_max))
        if self.v_desc:
            self.txt_cd_note.set_text("")
        else:
            self.txt_cd_note.set_text("starts in the descent,\nunder the parachute")
        label = ("time since launch (s)" if self.detector.t_launch is not None
                 else "time since start (s)")
        if self.time_labels[0].get_text() != label:
            for lab in self.time_labels:
                lab.set_text(label)

        return []

    def _draw_radio(self, ts, t, x0, x1):
        """Signal strength of every packet over the flight, the packets
        that did not arrive, and how many arrived in the last minute."""
        rssi = np.array(self.hist["rssi"], dtype=float)
        nominal = float(np.median(self._dts)) if self._dts else 1.0
        if len(ts) > 1 and nominal > 0:          # no line across lost packets
            cut = np.where(np.diff(ts) > 1.5 * nominal)[0] + 1
            ts_l, rssi_l = np.insert(ts, cut, np.nan), np.insert(rssi, cut, np.nan)
        else:
            ts_l, rssi_l = ts, rssi
        self.ln_rssi.set_data(ts_l, rssi_l)
        lost = np.array(self.lost_t, dtype=float)
        self.ln_lost.set_data(lost, np.full(len(lost), -127.0))
        self.ax_radio.set_xlim(x0, x1)
        got = int(np.sum(ts > t - 60.0))
        span = min(60.0, t - (self.t_first if self.t_first is not None else t))
        expected = max(int(round(span / nominal)) + 1 if nominal > 0 else got, got)
        text = f"last minute {got}/{expected} ({100 * got / expected:.0f} %)"
        if self.pkt_lost:
            text += f" · lost {self.pkt_lost} (red marks)"
        self.txt_link.set_text(text)

    def run(self):
        # A timer instead of FuncAnimation: FuncAnimation redraws the whole
        # figure on every tick, also without new data (heavy on a laptop
        # that also runs screen 2). Now: redraw only when a row came in, or
        # when the header must say that no data come in any more.
        self.fit.fit_screen()
        self.timer = self.fig.canvas.new_timer(interval=UPDATE_MS)
        self.timer.add_callback(self._tick)
        self.timer.start()
        plt.show()

    def _tick(self):
        self.update(0)
        if self._refresh_link() or self._changed:
            self.fig.canvas.draw_idle()


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
    p.add_argument("--sea-level", type=float, metavar="HPA",
                   help="sea-level pressure of the day; default: the value "
                        "start_meting saved next to the csv, else "
                        f"{SEA_LEVEL_HPA:g}")
    return p.parse_args()


def apply_args(args):
    """Set the module settings from parse_args() (also used by screen 2)."""
    global SIM_SPEED, DATA_MODE, LIVE_CSV, REPLAY_CSV, SEA_LEVEL_HPA
    SIM_SPEED = args.speed
    if args.replay:
        DATA_MODE, REPLAY_CSV = "replay", args.replay
    elif args.live:
        DATA_MODE, LIVE_CSV, REPLAY_CSV = "live", args.live, None
    elif args.sim:
        DATA_MODE, LIVE_CSV, REPLAY_CSV = "sim", None, None
    saved = saved_sea_level(args.replay or args.live)
    if args.sea_level is not None:
        SEA_LEVEL_HPA = args.sea_level
    elif saved is not None:
        SEA_LEVEL_HPA = saved
    print(f"sea-level pressure: {SEA_LEVEL_HPA:g} hPa")


if __name__ == "__main__":
    apply_args(parse_args())
    Dashboard().run()
