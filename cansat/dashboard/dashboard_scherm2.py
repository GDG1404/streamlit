"""
CanSat 2027 — Screen 2 · 3D Flight Path & Orientation (Python version)
=======================================================================

Python equivalent of scherm2_gps_orientatie.html, built with matplotlib.
Reuses the data sources and the phase detector of dashboard_scherm1.py
(same folder).

Panels:
  - Header: the dot is green while data come in. Live only: amber after
    3 s without new data, red after 10 s, with a warning ("NO SIGNAL").
  - KPI bar: flight time, altitude, drift over the ground (from the GPS;
    via the radio it is worked out from the GPS positions), DISTANCE from
    the start with the direction, and latitude and longitude with 5
    decimals: the two numbers to type in a maps app to find the can back.
  - 3D FLIGHT PATH: the trajectory in a slowly rotating xyz frame
    (east / north / altitude, metres), coloured by altitude, with a
    ground shadow, a drop line and an N on the north side of the floor.
    A ground test (never higher than GROUND_TEST_M) zooms in; the scene
    grows with the flight.
    Press 'M' to toggle to the 2D OSM map around the start (the first GPS
    fix; Elsenborn in the simulator) — the recovery view. The map zooms
    out automatically when the can drifts off the map.
    After the landing a green bar gives the landing position.
  - Altitude profile bar (below the map), with the apogee
  - Large 3D can (66×115 mm, closed with lid and bottom) coloured by
    the LOAD PER ZONE (model in krachten.py, from the measured g): the
    force through the can at each height, as a share of the ESA design
    load (20 g on the bottom), with a colour scale. On the pad, during the
    launch and at the landing the force comes in at the bottom; when the
    parachute pulls, at the top. Peak hold: colours stay at the highest
    value reached, so at the end of the flight you can see which zones
    carried the most. Next to it: the force of this moment and the largest
    load of the launch, under the parachute and at the landing.
  - Radio link status (RSSI / SNR / packets / lost)

Keys: M = map / 3D. Replay and simulator: SPACE = pause, R = play the
replay again, F = full screen. A replay stays on its last picture.

OSM tiles are downloaded once per location and cached in ./osm_cache
(works offline afterwards — open the dashboard once with internet near
the launch site, e.g. on a replay of a short test there).

Requirements:  pip install numpy matplotlib pillow
Run:           python dashboard_scherm2.py                  (settings in screen 1)
               python dashboard_scherm2.py --replay test_000.csv
               python dashboard_scherm2.py --live cansat27_live.csv
               python dashboard_scherm2.py --sim
"""

import math
import os
import random
import sys
import time
import urllib.request
from collections import deque

import numpy as np

# reuse the data sources + theme from screen 1 (same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashboard_scherm1 as s1  # SIM_SPEED read via s1 (CLI)
import krachten as K            # force model: load per zone of the can
from dashboard_scherm1 import (C, PhaseDetector, TelemetrySimulator,
                               WindowFit, add_unit, clock_text, from_radio,
                               has_gps_fix, is_number, make_source, mmss)

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3D projection)
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from PIL import Image

# OSM basemap settings (2D map view)
OSM_ZOOM = 16         # start zoom: ±~975 m around the launch point
OSM_MIN_ZOOM = 12     # zoom out at most to ±~15 km
OSM_RADIUS_2D = 2     # 2D map: (2·2+1)² = 25 tiles
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "osm_cache")
MAP_DIM = 0.55        # darken factor so the dark theme keeps working

# 3D flight view
VIEW3D_SPAN = 400     # flight: smallest half-width of the xy scene (m)
GROUND_SPAN = 20      # ground test: smallest half-width of the xy scene (m)
GROUND_TOP = 5        # ground test: smallest height of the scene (m)
ROTATE_DEG_S = 1.5    # slow camera rotation (°/s); 0 = static
DRIFT_SPAN_S = 10     # drift from GPS positions: over the last seconds

# Screen 2 is heavy (3D views + map). It checks for new data every
# UPDATE_MS, but only redraws when a new row came in (live/replay: about
# 1x per second). 500 = check 2x per second, 1000 = 1x per second.
UPDATE_MS = 500

# ── helpers ──────────────────────────────────────────────────
def rotation_matrix(heading_deg, roll_deg, pitch_deg):
    """Rotation matrix from euler angles (degrees)."""
    h, r, p = (math.radians(a) for a in (heading_deg, roll_deg, pitch_deg))
    ch, sh = math.cos(h), math.sin(h)
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    Rz = np.array([[ch, -sh, 0], [sh, ch, 0], [0, 0, 1]])
    Ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return Rz @ Ry @ Rx


def cylinder_mesh(radius=0.033, height=0.115, n_theta=24, n_z=12):
    """Cylinder shell (real can: Ø66 × 115 mm), centred on the origin."""
    theta = np.linspace(0, 2 * np.pi, n_theta)
    z = np.linspace(-height / 2, height / 2, n_z)
    TH, Z = np.meshgrid(theta, z)
    X = radius * np.cos(TH)
    Y = radius * np.sin(TH)
    return X, Y, Z, TH


def cap_mesh(radius=0.033, z=0.0, n_theta=24):
    """Closed end cap (lid/bottom) at height z."""
    theta = np.linspace(0, 2 * np.pi, n_theta)
    r = np.array([0.0, radius * 0.55, radius])
    TH, R = np.meshgrid(theta, r)
    X = R * np.cos(TH)
    Y = R * np.sin(TH)
    Z = np.full_like(X, z)
    return X, Y, Z


def latlon_to_xy(lat, lon, lat0, lon0):
    """Lat/lon → metres relative to the launch point (flat approximation)."""
    dy = (lat - lat0) * 111_320.0
    dx = (lon - lon0) * 111_320.0 * math.cos(math.radians(lat0))
    return dx, dy


def compass_point(deg):
    """Course in degrees (0 = north, 90 = east) → N, NE, E, ... NW."""
    names = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    return names[int((deg % 360) / 45 + 0.5) % 8]


def deg2tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def tile2deg(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


_osm_offline = False   # set after the first failed download


def fetch_tile(z, x, y):
    """OSM tile from local cache, downloading it once if needed.

    After one failed download no further downloads are tried, so an
    offline start (launch site, school network) does not wait for the
    timeout of every tile. Downloads go through a temp file, so an
    interrupted download never leaves a broken tile in the cache.
    """
    global _osm_offline
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{z}_{x}_{y}.png")
    if not os.path.exists(path):
        if _osm_offline:
            raise OSError("offline: skipped tile download")
        url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        req = urllib.request.Request(
            url, headers={"User-Agent": "CanSat2027-groundstation/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read()
        except Exception:
            _osm_offline = True
            print("OSM: no internet → map without background tiles "
                  "(cached tiles are still used)")
            raise
        tmp = path + ".part"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    return np.asarray(Image.open(path).convert("RGB")) / 255.0




def nice_up(v):
    """v rounded up to a round number (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8 ×
    a power of ten), so that the scene is not redrawn at every row."""
    if v <= 0:
        return 1.0
    p = 10.0 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * p * (1 + 1e-9):
            return m * p
    return 10 * p


def lat_text(lat):
    return f"{abs(lat):.5f}", "°N" if lat >= 0 else "°S"


def lon_text(lon):
    return f"{abs(lon):.5f}", "°E" if lon >= 0 else "°W"


# ═════════════════════════════════════════════════════════════
#  DASHBOARD SCREEN 2
# ═════════════════════════════════════════════════════════════
class Dashboard2:
    def __init__(self):
        self.sim = make_source()             # live CSV, replay CSV or simulator
        self.live = isinstance(self.sim, s1.CsvLive)
        self.replay = isinstance(self.sim, s1.CsvReplay)
        self.sim_mode = isinstance(self.sim, TelemetrySimulator)
        if self.replay:
            self.sim.loop = False            # stay on the last picture (R = again)
        self.ori_artists = []
        self.cyl = cylinder_mesh()
        self.cap_top = cap_mesh(z=+0.115 / 2)
        self.cap_bot = cap_mesh(z=-0.115 / 2)
        self.stress_cmap = LinearSegmentedColormap.from_list(
            "load", [C["green"], C["amber"], C["orange"], C["red"]])
        self.alt_cmap = LinearSegmentedColormap.from_list(
            "altitude", [C["orange"], C["amber"], C["cyan"]])
        self.alt_norm = Normalize(0, self.sim.h_max)
        # height of each ring of the mesh above the bottom (m)
        Zr = self.cyl[2][:, 0]
        self.ring_z = (Zr - Zr.min()) / (Zr.max() - Zr.min()) * K.CAN_HEIGHT_M
        self.view3d = True
        self.paused = False
        self._wall = None        # wall-clock pacing for real-time replay
        self._changed = False    # new row since the last tick → redraw
        self._rx_wall = None     # wall-clock time of the last new data
        self._t_open = time.monotonic()
        self._link_shown = None  # what the header says about the data link
        self._rssi_text, self._rssi_color = "", C["green"]
        self._map_fixed = False          # True once basemap is redrawn for real GPS
        self._basemap_artists = []       # artists to remove on basemap redraw
        self._zoom = OSM_ZOOM            # current map zoom (zooms out)
        self._map_half = float("inf")    # map coverage (m), set on draw
        self._scene = None               # (half-width, height) of the 3D scene
        self._last_pos = None            # (x, y, alt, dist) drawn last
        self.track_x, self.track_y, self.track_z = [], [], []
        self._reset_run()
        if self.live:            # an old file: say at once how old the data are
            try:
                age = max(0.0, time.time() - os.path.getmtime(self.sim.path))
                self._rx_wall = self._t_open - age
            except OSError:
                pass
        self._build_figure()
        # remember the origin used at build time so we can detect when
        # CsvLive updates it after the first real GPS fix arrives
        self._init_lat0 = self.sim.lat0
        self._init_lon0 = self.sim.lon0

    def _reset_run(self):
        """Everything that belongs to one run of the can (cleared when it
        restarts, when a replay starts again and in the demo loop)."""
        self.detector = PhaseDetector()      # phase from data, not sim
        self.track_x.clear()
        self.track_y.clear()
        self.track_z.clear()
        self.pkt_rx, self.pkt_lost = 0, 0
        self._last_t = None      # previous row time (restart + loss detection)
        self.t_first = None      # time of the first row (Teensy time, s)
        self._dts = []           # recent row intervals → nominal log rate
        self.stress_peak = np.zeros(self.cyl[2].shape)   # peak hold per patch
        self._f_now, self._where_now = 0.0, "bottom"
        # largest load so far: "largest" and, in a flight, "launch",
        # "parachute" and "landing" → (g, side, at the sensor limit)
        self.load_max = {}
        self._pad_loads = deque(maxlen=10)   # the launch peak comes just
                                             # before the launch is recognised
        self.alt_top = 0.0       # highest altitude: ground test or flight
        self.reach = 0.0         # farthest from the start (m)
        self.fixes = deque(maxlen=40)        # (t, x, y) of rows with a GPS fix
        self.last_fix = None     # (t, lat, lon, x, y) of the last GPS fix

    def _style_axes(self, ax, title=None, title_color=None, face=None):
        ax.set_facecolor(face or C["panel"])
        for s in ax.spines.values():
            s.set_color(C["border"])
            s.set_linewidth(0.8)
        ax.tick_params(colors=C["dim"], labelsize=7.5, labelcolor=C["muted"])
        if title:
            ax.set_title(title, loc="left", fontsize=9,
                         color=title_color or C["muted"],
                         fontfamily="monospace", pad=4)

    def _title_text(self):
        return ("Screen 2 — 3D Flight Path & Orientation ("
                + self.sim.label
                + s1.state_suffix(self.sim, self.live, self.paused) + ")")

    # ── OSM basemaps ──
    def _tile_block(self, radius):
        """Stitch (2r+1)² tiles into one image + extent in local metres."""
        lat0, lon0 = self.sim.lat0, self.sim.lon0
        z = self._zoom
        xt, yt = deg2tile(lat0, lon0, z)
        cx, cy = int(xt), int(yt)
        rows = []
        for ty in range(cy - radius, cy + radius + 1):
            row = []
            for tx in range(cx - radius, cx + radius + 1):
                try:
                    row.append(fetch_tile(z, tx, ty))
                except Exception:
                    row.append(np.full((256, 256, 3), 0.06))  # dark filler
            rows.append(np.hstack(row))
        img = np.vstack(rows)
        lat_n, lon_w = tile2deg(cx - radius, cy - radius, z)
        lat_s, lon_e = tile2deg(cx + radius + 1, cy + radius + 1, z)
        x_w, y_n = latlon_to_xy(lat_n, lon_w, lat0, lon0)
        x_e, y_s = latlon_to_xy(lat_s, lon_e, lat0, lon0)
        return img * MAP_DIM, (x_w, x_e, y_s, y_n)

    def _draw_basemap_2d(self):
        # remove previous basemap artists (called again when GPS origin changes)
        for art in self._basemap_artists:
            try:
                art.remove()
            except Exception:
                pass
        self._basemap_artists = []
        self._set_map_title()
        try:
            img, (x_w, x_e, y_s, y_n) = self._tile_block(OSM_RADIUS_2D)
        except Exception:
            self.ax_gps.grid(True, color="#111820", linewidth=0.7)
            return
        # half-width the map covers around the launch point (metres)
        self._map_half = min(-x_w, x_e, -y_s, y_n)
        bm = self.ax_gps.imshow(img, extent=(x_w, x_e, y_s, y_n),
                           origin="upper", zorder=0,
                           interpolation="bilinear")
        f = self.fit.f if hasattr(self, "fit") else 1.0
        cp = self.ax_gps.text(0.99, 0.01, "© OpenStreetMap contributors",
                         transform=self.ax_gps.transAxes, fontsize=6.5 * f,
                         color=C["dim"], ha="right")
        self._basemap_artists = [bm, cp]

    def _set_map_title(self):
        """Map title: the real location of the start."""
        if self.sim_mode:
            where = "ELSENBORN, BELGIUM (sim)"
        elif getattr(self.sim, "_have_fix", False):
            (lat, ns), (lon, ew) = lat_text(self.sim.lat0), lon_text(self.sim.lon0)
            where = f"START {lat}{ns} {lon}{ew}"
        else:
            where = "WAITING FOR GPS FIX"
        self.ax_gps.set_title(f"● GPS LIVE TRACK — {where}   [M] 3D view",
                              loc="left", fontsize=9, color=C["green"],
                              fontfamily="monospace", pad=4)

    # ── keys: M toggles 3D flight ↔ 2D map; pause and replay again ──
    def _on_key(self, event):
        key = (event.key or "").lower()
        if key == "m":
            self.view3d = not self.view3d
            self.ax_flight.set_visible(self.view3d)
            self.ax_gps.set_visible(not self.view3d)
            # only the visible view is kept up to date: catch up now (the
            # data may be paused, or the replay may have ended)
            if self._last_pos is not None:
                x, y, alt, dist = self._last_pos
                if self.view3d:
                    self._update_track_3d(x, y, alt)
                else:
                    self._update_track_2d(x, y, alt, dist)
        elif self.live:
            return
        elif key in (" ", "space"):
            self.paused = not self.paused
        elif key == "r" and self.replay:
            self.sim.restart()
            self.paused = False
        else:
            return
        self.txt_title.set_text(self._title_text())
        self.fig.canvas.draw_idle()

    def _build_figure(self):
        plt.rcParams.update({
            "font.family": "monospace",
            "text.color": C["text"],
            "axes.labelcolor": C["muted"],
        })
        s1.quiet_keymaps()
        self.fig = plt.figure(figsize=s1.DESIGN_SIZE, facecolor=C["bg"])
        self.fig.canvas.manager.set_window_title(
            "CanSat 2027 — Screen 2 · 3D Flight Path & Orientation")
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

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
        badge = s1.PHASE_BADGE["PRELAUNCH"]
        self.txt_phase = self.fig.text(0.887, 0.962, "PRELAUNCH", fontsize=10.5,
                                       color=badge, ha="right",
                                       bbox=dict(boxstyle="round,pad=0.3",
                                                 fc="none", ec=badge))
        self.txt_clock = self.fig.text(0.98, 0.962, "00:00", fontsize=13,
                                       color=C["cyan"], ha="right")
        self.fig.text(0.02, 0.008, "M = map / 3D" + (
            "" if self.live else " · SPACE = pause" + (
                " · R = play again" if self.replay else ""))
            + " · F = full screen", fontsize=7, color=C["dim"])

        # ── KPI bar ──
        kpis = [("FLIGHT TIME", "", C["cyan"]),
                ("ALTITUDE", "m", C["amber"]),
                ("DRIFT (GPS)", "m/s", C["green"]),
                ("DISTANCE", "m", C["green"]),
                ("LATITUDE", "°N", C["blue"]),
                ("LONGITUDE", "°E", C["blue"])]
        self.txt_kpi, self.txt_kpi_sub, self.txt_kpi_unit = [], [], []
        for i, (label, unit, col) in enumerate(kpis):
            x = 0.02 + i * 0.162
            self.fig.text(x, 0.922, label, fontsize=8, color=C["muted"])
            v = self.fig.text(x, 0.881, "—", fontsize=20,
                              fontweight="bold", color=col)
            self.txt_kpi_unit.append(
                add_unit(self.fig, v, unit, C["muted"], size=9))
            sub = self.fig.text(x, 0.858, "", fontsize=7.5, color=C["muted"])
            self.txt_kpi.append(v)
            self.txt_kpi_sub.append(sub)

        # ── grid: flight view + profile left, big can + link right ──
        gs = GridSpec(3, 5, figure=self.fig,
                      left=0.05, right=0.985, top=0.822, bottom=0.075,
                      hspace=0.50, wspace=0.40,
                      height_ratios=[40, 36, 15])

        # 3D flight path (left, rows 0–1) — default view
        self.ax_flight = self.fig.add_subplot(gs[0:2, :3], projection="3d")
        self.ax_flight.set_facecolor(C["bg"])
        self.ax_flight.set_title(
            "● 3D FLIGHT PATH — EAST / NORTH / ALTITUDE   [M] 2D map",
            loc="left", fontsize=9, color=C["green"],
            fontfamily="monospace", pad=2)
        # dark xyz frame
        pane_rgba = (0.086, 0.106, 0.133, 0.9)         # ≈ panel colour
        for axis in (self.ax_flight.xaxis, self.ax_flight.yaxis,
                     self.ax_flight.zaxis):
            axis.set_pane_color(pane_rgba)
            axis.label.set_color(C["muted"])
            axis.label.set_size(8)
            try:
                axis._axinfo["grid"].update(
                    color="#1c2128", linewidth=0.5)
            except (AttributeError, KeyError):
                pass
        self.ax_flight.tick_params(colors=C["dim"], labelsize=7,
                                   labelcolor=C["muted"])
        for axis in (self.ax_flight.xaxis, self.ax_flight.yaxis,
                     self.ax_flight.zaxis):
            axis.set_major_locator(MaxNLocator(5))     # few ticks: faster
        self.ax_flight.set_xlabel("east (m)")
        self.ax_flight.set_ylabel("north (m)")
        self.ax_flight.set_zlabel("altitude (m)")
        try:
            self.ax_flight.set_box_aspect((1, 1, 0.6), zoom=1.12)
        except (AttributeError, TypeError):            # older matplotlib
            try:
                self.ax_flight.set_box_aspect((1, 1, 0.6))
            except AttributeError:
                pass
        self._azim = -60.0
        self.ax_flight.view_init(elev=28, azim=self._azim)
        # a ring around the start on the ground plane, and north: an N just
        # outside the floor with a short line towards it (_scale_scene
        # puts them in place)
        self.ln_ring3d, = self.ax_flight.plot([], [], [], color=C["green"],
                                              lw=1, ls="--", alpha=0.5)
        self.ln_north, = self.ax_flight.plot([], [], [], color=C["muted"],
                                             lw=1.2)
        self.txt_north = self.ax_flight.text(
            0, 0, 0, "N", fontsize=10, color=C["text"], ha="center",
            va="center", fontweight="bold")
        # dummy segment: add_collection3d crashes on an empty collection
        self.trk3d = Line3DCollection(np.zeros((1, 2, 3)),
                                      cmap=self.alt_cmap,
                                      norm=self.alt_norm, linewidth=2.5)
        self.ax_flight.add_collection3d(self.trk3d)
        self.ln_shadow, = self.ax_flight.plot([], [], [], color="#3a424d",
                                              lw=1.4, alpha=0.9)
        self.ln_drop, = self.ax_flight.plot([], [], [], color=C["text"],
                                            lw=0.8, ls=":", alpha=0.7)
        self.pt_now3d, = self.ax_flight.plot([], [], [], "o",
                                             color=C["cyan"], ms=7)
        self.pt_start3d, = self.ax_flight.plot([], [], [], "o",
                                               color=C["orange"], ms=7)
        self.pt_apo3d, = self.ax_flight.plot([], [], [], "^",
                                             color=C["amber"], ms=7)
        self.ax_flight.text2D(0.0, 0.95,         # top: clear of the axis labels
                              "▲ apogee · ● start · colour = altitude · "
                              "N = north",
                              transform=self.ax_flight.transAxes,
                              fontsize=7.5, color=C["muted"],
                              family="monospace")

        # 2D map (same slot, hidden by default — toggle with M)
        self.ax_gps = self.fig.add_subplot(gs[0:2, :3])
        self._style_axes(self.ax_gps, face="#0a0f16")
        self.ax_gps.set_aspect("equal", adjustable="box")
        self.ax_gps.set_xlabel("east (m)", fontsize=7.5)
        self.ax_gps.set_ylabel("north (m)", fontsize=7.5)
        self._draw_basemap_2d()
        ang = np.linspace(0, 2 * np.pi, 80)
        self.ax_gps.plot(50 * np.cos(ang), 50 * np.sin(ang),
                         color=C["green"], lw=1, ls="--", alpha=0.6,
                         zorder=3)
        self.ax_gps.plot(0, 0, "+", color=C["green"], ms=12, alpha=0.8,
                         zorder=3)
        self.ax_gps.text(55, 0, "START · ring 50 m", fontsize=8,
                         color=C["green"], alpha=0.9, zorder=3)
        # track: white outline underneath + altitude-coloured line on top
        self.ln_outline, = self.ax_gps.plot([], [], color="white", lw=4.5,
                                            alpha=0.85, zorder=4,
                                            solid_capstyle="round")
        self.trk2d = LineCollection([], cmap=self.alt_cmap,
                                    norm=self.alt_norm, linewidth=2.4,
                                    zorder=5, capstyle="round")
        self.ax_gps.add_collection(self.trk2d)
        self.pt_start, = self.ax_gps.plot([], [], "o", color=C["orange"],
                                          ms=8, zorder=6)
        self.pt_now, = self.ax_gps.plot([], [], "o", color=C["cyan"], ms=9,
                                        zorder=6,
                                        markeredgecolor="white")
        self.txt_now = self.ax_gps.text(0, 0, "", fontsize=8.5,
                                        color="white", zorder=6,
                                        visible=False)
        self.ax_gps.set_visible(False)

        # over the flight view, 3D or map: the landing position, and the
        # warning when no data come in any more (live)
        self.txt_landed = self.fig.text(
            0.335, 0.772, "", fontsize=10.5, fontweight="bold",
            color=C["green"], ha="center", va="top", zorder=8,
            bbox=dict(boxstyle="round,pad=0.45", fc="#0f2417", ec=C["green"]))
        self.txt_landed.set_visible(False)
        self.txt_warn = self.fig.text(
            0.335, 0.69, "", fontsize=13, fontweight="bold", color=C["red"],
            ha="center", va="top", linespacing=1.5, zorder=8,
            bbox=dict(boxstyle="round,pad=0.5", fc="#2d1215", ec=C["red"]))
        self.txt_warn.set_visible(False)

        # Altitude profile bar (left, below the map)
        self.ax_prof = self.fig.add_subplot(gs[2, :3])
        self._style_axes(self.ax_prof, "● ALTITUDE PROFILE", C["blue"])
        grad = np.linspace(0, 1, 256).reshape(1, -1)
        self.im_prof = self.ax_prof.imshow(
            grad, aspect="auto", cmap=self.alt_cmap,
            extent=(0, self.sim.h_max, 0, 1))
        self.ax_prof.set_autoscale_on(False)
        self.ax_prof.set_yticks([])
        self.ax_prof.set_xlim(0, self.sim.h_max)
        self.ln_prof = self.ax_prof.axvline(0, color=C["text"], lw=2.5)
        self.txt_prof = self.ax_prof.text(
            0, 0.5, "", fontsize=8.5, color=C["text"], va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc=C["bg"], ec="none",
                      alpha=0.75))
        self.pt_prof_apo, = self.ax_prof.plot([], [], "^", color=C["bg"],
                                              ms=7, zorder=4)
        self.txt_prof_apo = self.ax_prof.set_title(
            "", loc="right", fontsize=7.5, color=C["muted"], pad=4)
        self.ax_prof.set_xlabel("altitude (m)", fontsize=7.5, labelpad=2)

        # Big 3D orientation + load heatmap (right, rows 0–1)
        self.ax_ori = self.fig.add_subplot(gs[0:2, 3:], projection="3d")
        self.ax_ori.set_facecolor(C["bg"])
        self.ax_ori.set_axis_off()
        lim = 0.068          # smaller limits → bigger can
        self.ax_ori.set_xlim(-lim, lim)
        self.ax_ori.set_ylim(-lim, lim)
        self.ax_ori.set_zlim(-lim, lim)
        try:
            self.ax_ori.set_box_aspect((1, 1, 1))
        except AttributeError:
            pass
        self.ax_ori.set_title(
            "● 3D ORIENTATION + LOAD PER ZONE (model from the measured g)",
            loc="left", fontsize=9, color=C["purple"],
            fontfamily="monospace", pad=2)
        self.txt_euler = self.ax_ori.text2D(
            0.0, 0.90, "", transform=self.ax_ori.transAxes,
            fontsize=9, color=C["amber"], family="monospace", va="top")
        # the force of this moment and the largest loads so far
        self.txt_load = self.ax_ori.text2D(
            0.0, 0.085, "", transform=self.ax_ori.transAxes,
            fontsize=8.5, color=C["text"], family="monospace", va="bottom",
            linespacing=1.35)
        # which sensor the g comes from
        self.txt_sensor = self.ax_ori.text2D(
            0.0, 0.045, "", transform=self.ax_ori.transAxes,
            fontsize=7.5, color=C["muted"], family="monospace", va="bottom")
        self.ax_ori.text2D(
            0.0, 0.01, "colour = force / force at 20 g (ESA) · peak hold",
            transform=self.ax_ori.transAxes, fontsize=7.5,
            color=C["muted"], family="monospace", va="bottom")
        # colour scale of the can: share of the ESA design force
        pos = self.ax_ori.get_position()
        self.ax_scale = self.fig.add_axes(
            [pos.x1 - 0.045, pos.y0 + 0.36 * pos.height, 0.009,
             0.36 * pos.height])
        self.ax_scale.imshow(np.linspace(0, 1, 256).reshape(-1, 1),
                             aspect="auto", origin="lower",
                             cmap=self.stress_cmap, extent=(0, 1, 0, 100))
        self.ax_scale.set_xticks([])
        self.ax_scale.yaxis.tick_right()
        self.ax_scale.set_yticks([0, 50, 100])
        self.ax_scale.set_yticklabels(["0", "50", "100 %"])
        self.ax_scale.tick_params(colors=C["dim"], labelsize=7.5,
                                  labelcolor=C["muted"], length=3)
        for s in self.ax_scale.spines.values():
            s.set_color(C["border"])
        self.ax_scale.set_title("of 20 g", fontsize=7.5, color=C["muted"],
                                pad=5)

        # Radio link status (right, bottom)
        self.ax_link = self.fig.add_subplot(gs[2, 3:])
        self._style_axes(self.ax_link, "● RADIO LINK STATUS", C["green"])
        self.ax_link.set_title("868.0 MHz · SF7 · 1 packet per second",
                               loc="right", fontsize=7.5, color=C["muted"],
                               pad=4)
        self.ax_link.set_xticks([])
        self.ax_link.set_yticks([])
        labels = ["RSSI", "SNR", "Packets", "Lost"]
        self.txt_link_val, self.txt_link_sub = [], []
        cols = [C["green"], C["cyan"], C["green"], C["amber"]]
        for i, (lab, col) in enumerate(zip(labels, cols)):
            x = 0.125 + i * 0.25
            self.ax_link.text(x, 0.78, lab, fontsize=8, color=C["muted"],
                              ha="center", transform=self.ax_link.transAxes)
            v = self.ax_link.text(x, 0.36, "—", fontsize=15,
                                  fontweight="bold", color=col, ha="center",
                                  transform=self.ax_link.transAxes)
            s = self.ax_link.text(x, 0.09, "", fontsize=7.5, color=C["muted"],
                                  ha="center",
                                  transform=self.ax_link.transAxes)
            self.txt_link_val.append(v)
            self.txt_link_sub.append(s)

        self._scale_scene()
        # text and markers scale with the window (13-inch laptop, ...)
        self.fit = WindowFit(self.fig)

    # ── the size of the 3D scene ──
    def _scale_scene(self):
        """Limits of the 3D scene, the altitude colours and the altitude
        bar. A ground test (never higher than GROUND_TEST_M) zooms in, as
        on screen 1; a flight gets the full height. Both grow with the
        data, in round steps."""
        flight = (self.sim_mode or self.alt_top > s1.GROUND_TEST_M
                  or (self.replay and self.sim.h_max > s1.GROUND_TEST_M))
        if flight:
            z_top = max(self.sim.h_max, self.alt_top) * 1.1
            known = 0 if self.live else getattr(self.sim, "xy_span", 0)
            span = max(VIEW3D_SPAN, known, self.reach * 1.15)
        else:
            z_top = max(GROUND_TOP, self.alt_top * 1.25)
            span = max(GROUND_SPAN, self.reach * 1.15)
        scene = (nice_up(span), nice_up(z_top))
        if scene == self._scene:
            return
        self._scene = scene
        span, z_top = scene
        self.ax_flight.set_xlim(-span, span)
        self.ax_flight.set_ylim(-span, span)
        self.ax_flight.set_zlim(0, z_top)
        ang = np.linspace(0, 2 * np.pi, 60)
        r = span / 8                     # flight: 50 m around the start
        self.ln_ring3d.set_data_3d(r * np.cos(ang), r * np.sin(ang),
                                   np.zeros_like(ang))
        self.ln_north.set_data_3d([0, 0], [span * 0.82, span], [0, 0])
        try:
            self.txt_north.set_position_3d((0, span * 1.1, 0))
        except AttributeError:                         # older matplotlib
            self.txt_north.set_position((0, span * 1.1))
            self.txt_north.set_3d_properties(0, None)
        self.alt_norm.vmax = z_top       # colours of the track
        self.trk3d.changed()
        self.trk2d.changed()
        self.im_prof.set_extent((0, z_top, 0, 1))
        self.ax_prof.set_xlim(0, z_top)

    # ── 3D can with peak-hold load heatmap, raster and caps ──
    def _draw_cylinder(self, row):
        for art in self.ori_artists:
            art.remove()
        self.ori_artists = []

        X, Y, Z, TH = self.cyl

        # peak hold: the map is accumulated per row in
        # _accumulate_stress(); here we only render it
        sp = self.stress_peak
        faces = 0.25 * (sp[:-1, :-1] + sp[1:, :-1] +
                        sp[:-1, 1:] + sp[1:, 1:])
        rgba_wall = self.stress_cmap(faces)

        R = rotation_matrix(row["heading"], row["roll"], row["pitch"])

        def rotate(Xm, Ym, Zm):
            pts = R @ np.vstack((Xm.ravel(), Ym.ravel(), Zm.ravel()))
            return (pts[0].reshape(Xm.shape), pts[1].reshape(Ym.shape),
                    pts[2].reshape(Zm.shape))

        # wall — thin dark raster keeps the curvature readable
        Xr, Yr, Zr = rotate(X, Y, Z)
        surf = self.ax_ori.plot_surface(Xr, Yr, Zr, facecolors=rgba_wall,
                                        shade=False, antialiased=False,
                                        edgecolor=C["bg"], linewidth=0.35)
        self.ori_artists.append(surf)

        # lid and bottom, coloured from the adjacent wall ring
        for cap, ring in ((self.cap_top, sp[-1, :]), (self.cap_bot, sp[0, :])):
            mids = 0.5 * (ring[:-1] + ring[1:])
            rgba_cap = self.stress_cmap(np.tile(mids, (2, 1)))
            Xc, Yc, Zc = rotate(*cap)
            csurf = self.ax_ori.plot_surface(Xc, Yc, Zc,
                                             facecolors=rgba_cap,
                                             shade=False, antialiased=False,
                                             edgecolor=C["bg"],
                                             linewidth=0.35)
            self.ori_artists.append(csurf)

        # slightly heavier rim top/bottom → silhouette stays clear
        theta = np.linspace(0, 2 * np.pi, 48)
        for zc in (0.115 / 2, -0.115 / 2):
            rim = np.vstack((0.033 * np.cos(theta), 0.033 * np.sin(theta),
                             np.full_like(theta, zc)))
            rim = R @ rim
            ln, = self.ax_ori.plot(rim[0], rim[1], rim[2],
                                   color=C["bg"], lw=1.3)
            self.ori_artists.append(ln)

        # body axes (X orange, Y green, Z blue)
        L = 0.075
        for vec, col in zip(np.eye(3) * L,
                            (C["orange"], C["green"], C["blue"])):
            v = R @ vec
            q = self.ax_ori.quiver(0, 0, 0, v[0], v[1], v[2],
                                   color=col, lw=1.8,
                                   arrow_length_ratio=0.18)
            self.ori_artists.append(q)

        # which end is which: the blue arrow comes out of the top, where
        # the parachute pulls
        v = R @ np.array([0.0, 0.0, 0.088])
        self.ori_artists.append(self.ax_ori.text(
            v[0], v[1], v[2], "top", fontsize=8.5 * self.fit.f,
            color=C["blue"], ha="center", va="center"))

        self.txt_load.set_text(self._load_text())
        self.txt_sensor.set_text(self._sensor_text(row))

    # ── the forces as text ──
    def _force_n(self, g, side):
        """The largest force in the can (N): at the side where it enters."""
        return float(K.axial_force_n(
            g, side, 0.0 if side == "bottom" else K.CAN_HEIGHT_M))

    def _load_text(self):
        where = {"bottom": "bottom", "top": "top (parachute)"}
        lines = [f"force now  {self._f_now:5.1f} N · "
                 f"{where[self._where_now]}"]
        names = [n for n in ("launch", "parachute", "landing")
                 if n in self.load_max] or [n for n in ("largest",)
                                            if n in self.load_max]
        for name in names:
            g, side, limit = self.load_max[name]
            more = "≥" if limit else ""
            lines.append(f"{name:<9s} {more + format(g, '.1f'):>6s} g · "
                         f"{more}{self._force_n(g, side):.0f} N · {side}")
        return "\n".join(lines)

    def _sensor_text(self, row):
        if K.finite(row.get("acc_peak_g")):
            return "g: the peak of every second (LSM6DSO, up to 16 g)"
        if from_radio(row):
            return ("radio: g from the BNO055, at most about 4 g · "
                    "the real peaks are on the SD card")
        return "g from the BNO055 (this file has no peak g)"

    # ── flight track rendering ──
    def _segments(self, xs, ys, zs=None):
        p = (np.array([xs, ys]).T if zs is None
             else np.array([xs, ys, zs]).T)
        return np.stack([p[:-1], p[1:]], axis=1)

    def _update_track_3d(self, x, y, alt):
        if len(self.track_x) > 1:
            zs = np.array(self.track_z)
            self.trk3d.set_segments(
                self._segments(self.track_x, self.track_y, self.track_z))
            self.trk3d.set_array(0.5 * (zs[:-1] + zs[1:]))
            self.ln_shadow.set_data_3d(self.track_x, self.track_y,
                                       np.zeros(len(self.track_x)))
            i_apo = int(np.argmax(zs))
            if zs[i_apo] > 10:
                self.pt_apo3d.set_data_3d([self.track_x[i_apo]],
                                          [self.track_y[i_apo]],
                                          [zs[i_apo]])
        self.ln_drop.set_data_3d([x, x], [y, y], [0, alt])
        self.pt_now3d.set_data_3d([x], [y], [alt])
        self.pt_start3d.set_data_3d([self.track_x[0]], [self.track_y[0]],
                                    [0])

    def _update_track_2d(self, x, y, alt, dist):
        if len(self.track_x) > 1:
            zs = np.array(self.track_z)
            self.trk2d.set_segments(
                self._segments(self.track_x, self.track_y))
            self.trk2d.set_array(0.5 * (zs[:-1] + zs[1:]))
            self.ln_outline.set_data(self.track_x, self.track_y)
        self.pt_start.set_data([self.track_x[0]], [self.track_y[0]])
        self.pt_now.set_data([x], [y])
        span = max(150, self.reach * 1.3, dist * 1.3)
        self.txt_now.set_position((x + 0.03 * span, y + 0.03 * span))
        self.txt_now.set_text(f"{alt:.0f} m")
        self.txt_now.set_visible(True)
        # can drifted off the map → zoom out one level (tiles are cached)
        if span > self._map_half and self._zoom > OSM_MIN_ZOOM:
            self._zoom -= 1
            self._draw_basemap_2d()
        self.ax_gps.set_xlim(-span, span)
        self.ax_gps.set_ylim(-span * 0.70, span * 0.70)

    def _clear_track(self):
        """Forget the drawn flight track (restart or new GPS origin)."""
        self.track_x.clear()
        self.track_y.clear()
        self.track_z.clear()
        self.fixes.clear()
        self.reach = 0.0
        self.pt_apo3d.set_data_3d([], [], [])
        self.trk3d.set_segments(np.empty((0, 2, 3)))
        self.trk3d.set_array(np.array([]))
        self.ln_shadow.set_data_3d([], [], [])
        self.trk2d.set_segments(np.empty((0, 2, 2)))
        self.trk2d.set_array(np.array([]))
        self.ln_outline.set_data([], [])

    # ── ingest one telemetry row ──
    def _ingest(self, row):
        t = row["millis"] / 1000.0

        # restart detection (demo/replay loop, can reboot): time jumps
        # back. The firmware's first row is at several seconds, not ~0.
        if self._last_t is not None and t < self._last_t:
            self._reset_run()
            self._clear_track()
        if self.t_first is None:
            self.t_first = t

        # packet statistics: the simulator simulates ~1% loss; for real
        # data (live/replay) loss is estimated from gaps in the stream,
        # relative to the normal row interval (1 Hz, 10 Hz, ...)
        if self.sim_mode:
            if random.random() < 0.01:
                self.pkt_lost += 1
            else:
                self.pkt_rx += 1
        else:
            if self._last_t is not None:
                gap = t - self._last_t
                if self._dts:
                    nominal = float(np.median(self._dts))
                    if nominal > 0 and gap > 1.5 * nominal:
                        self.pkt_lost += max(0, round(gap / nominal) - 1)
                self._dts = (self._dts + [gap])[-20:]
            self.pkt_rx += 1
        self._last_t = t

        # phase from the data (same detector as screen 1)
        det = self.detector.update(t, row)

        # GPS → metres relative to the launch point; without a fix the
        # firmware logs placeholder coordinates → keep the last position
        if has_gps_fix(row):
            x, y = latlon_to_xy(row["lat"], row["lon"],
                                self.sim.lat0, self.sim.lon0)
            self.fixes.append((t, x, y))
            self.last_fix = (t, row["lat"], row["lon"], x, y)
            self.reach = max(self.reach, math.hypot(x, y))
        elif self.track_x:
            x, y = self.track_x[-1], self.track_y[-1]
        else:
            x, y = 0.0, 0.0
        alt = max(0.0, row["alt_m"])
        self.alt_top = max(self.alt_top, row["alt_m"])   # nan: unchanged
        self.track_x.append(x)
        self.track_y.append(y)
        self.track_z.append(alt)

        # load model: accumulate the peak-hold map per row
        self._accumulate_stress(row, det, t)
        return det, t, x, y, alt

    def _accumulate_stress(self, row, phase, t):
        """Load per zone (krachten.py): the g of this row, the side where
        the force comes in (bottom: pad, launch, landing; top: parachute)
        and the force through each ring of the can, as a share of the
        ESA design load. Peak hold per ring. Also keeps the largest load
        of the launch, under the parachute and at the landing."""
        n = K.load_factor_g(row)
        side = K.support_for(phase, row["alt_m"], n)
        share = np.clip(K.zone_share(n, side, self.ring_z), 0.0, 1.0)
        self.stress_peak = np.maximum(self.stress_peak, share[:, None])
        # the largest force is at the side where it comes in
        self._f_now = self._force_n(n, side)
        self._where_now = side
        limit = (K.finite(row.get("acc_peak_g"))
                 and n >= K.SENSOR_MAX_G - 0.1)

        def keep(name, g=n, where=side, lim=limit):
            if name not in self.load_max or g > self.load_max[name][0]:
                self.load_max[name] = (g, where, lim)

        keep("largest")
        if phase == "PRELAUNCH":
            self._pad_loads.append((t, n, side, limit))
        elif phase == "ASCENT":
            if "launch" not in self.load_max:     # just recognised: the peak
                t0 = self.detector.t_launch       # came a moment earlier
                for tp, gp, sp, lp in self._pad_loads:
                    if t0 is not None and tp >= t0 - 0.5:
                        keep("launch", gp, sp, lp)
            keep("launch")
        elif phase in ("APOGEE", "DESCENT"):
            keep("parachute" if side == "top" else "landing")
        elif "launch" in self.load_max:           # LANDED after a flight
            keep("landing")

    # ── drift over the ground ──
    def _drift(self, row):
        """(speed m/s, course °, worked out from positions?) or None. The
        GPS gives both; they are not in the radio packet, so there they
        come from the last GPS positions."""
        spd, crs = row.get("gps_speed_ms"), row.get("gps_course_deg")
        if is_number(spd):
            return spd, crs, False
        if len(self.fixes) < 2:
            return None
        t1, x1, y1 = self.fixes[-1]
        t0, x0, y0 = next(f for f in self.fixes if t1 - f[0] <= DRIFT_SPAN_S)
        if t1 - t0 < 1.5:
            return None
        dx, dy = x1 - x0, y1 - y0
        return (math.hypot(dx, dy) / (t1 - t0),
                math.degrees(math.atan2(dx, dy)) % 360, True)

    # ── the data link (live only): are the data still coming in? ──
    def _refresh_link(self, now=None):
        """Header dot, link text and the warning over the flight view.
        Returns True when something on screen changed."""
        now = time.monotonic() if now is None else now
        since = self._rx_wall if self._rx_wall is not None else self._t_open
        t_launch = self.detector.t_launch
        t_flight = (self._last_t - t_launch
                    if self._last_t is not None and t_launch is not None
                    else None)
        level, text, warn = s1.link_status(
            self.live, self._last_t is not None, now - since, t_flight)
        dot = C[s1.LINK_COLOR[level]]
        color = dot if text is not None else self._rssi_color
        text = self._rssi_text if text is None else text
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
            dt = UPDATE_MS / 1000.0 * s1.SIM_SPEED
        else:
            dt = min(max(2.0, 3 * UPDATE_MS / 1000.0),
                     now - self._wall) * s1.SIM_SPEED
        self._wall = now
        if self.paused:
            self._changed = False
            return []

        # camera rotation runs on wall time, also when no new data
        if self.view3d and ROTATE_DEG_S:
            self._azim += ROTATE_DEG_S * dt / max(s1.SIM_SPEED, 1e-9)
            self.ax_flight.view_init(elev=28, azim=self._azim)

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
        det, t, x, y, alt = self._ingest(row)

        # ── live mode: redraw basemap once the real GPS origin is known ──
        # CsvLive sets lat0/lon0 from the first GPS row it ingests.
        # If the dashboard started before any data arrived, the map was
        # drawn at the default location. Detect the change and redraw once.
        # Replay and simulator are unaffected.
        if (not self._map_fixed and self.live
                and (self.sim.lat0 != self._init_lat0
                     or self.sim.lon0 != self._init_lon0)):
            # Discard track points computed from the old (default) origin;
            # restart the track at the current point (new origin)
            self._clear_track()
            x, y = latlon_to_xy(row["lat"], row["lon"],
                                self.sim.lat0, self.sim.lon0)
            self.track_x.append(x)
            self.track_y.append(y)
            self.track_z.append(alt)
            if has_gps_fix(row):
                self.fixes.append((t, x, y))
                self.last_fix = (t, row["lat"], row["lon"], x, y)
                self.reach = math.hypot(x, y)
            self._draw_basemap_2d()
            self._map_fixed = True

        # ── header: real RSSI/SNR when the logger records them; only
        # the simulator shows simulated values (labelled) ──
        radio = from_radio(row)
        title = self._title_text()
        if self.txt_title.get_text() != title:      # LIVE: USB or radio
            self.txt_title.set_text(title)
        rssi = row.get("rssi")
        snr = row.get("snr")
        rssi_sub = "dBm"
        if not is_number(rssi) and self.sim_mode:
            rssi = -70 - 0.045 * alt + random.gauss(0, 1.5)
            rssi_sub = "dBm (sim)"
        if not is_number(snr) and self.sim_mode:
            snr = 9.5 - 0.004 * alt + random.gauss(0, 0.4)
        self._rssi_color = C["green"]
        if is_number(rssi):
            self._rssi_text = f"RSSI {rssi:.0f} dBm" + (
                " (sim)" if self.sim_mode else
                f" · SNR {snr:+.1f} dB" if is_number(snr) else "")
            if rssi < s1.RSSI_BAD_DBM:
                self._rssi_color = C["red"]
            elif rssi < s1.RSSI_WEAK_DBM:
                self._rssi_color = C["amber"]
        else:
            self._rssi_text = ""                    # USB or SD card: no radio
        self._refresh_link(now)
        self.txt_pkt.set_text(f"packet #{self.pkt_rx}")
        self.txt_phase.set_text(det)
        badge = s1.PHASE_BADGE.get(det, C["amber"])
        self.txt_phase.set_color(badge)
        self.txt_phase.get_bbox_patch().set_edgecolor(badge)
        self.txt_clock.set_text(clock_text(self.detector, self.t_first, t))

        # ── KPIs ──
        # flight time counts from the launch and stops at the landing
        t_up, t_down = self.detector.t_launch, self.detector.t_landed
        if t_up is None:
            self.txt_kpi[0].set_text("—")
            self.txt_kpi_sub[0].set_text("waiting for launch")
        else:
            self.txt_kpi[0].set_text(mmss((t_down if t_down is not None
                                           else t) - t_up))
            self.txt_kpi_sub[0].set_text("landed" if t_down is not None
                                         else "since launch")
        # altitude in whole metres; a ground test (never higher than
        # GROUND_TEST_M) to 0.1 m, also below the start
        baro = row["alt_m"]
        if (self.sim_mode or self.alt_top > s1.GROUND_TEST_M
                or not is_number(baro)):
            alt_txt = f"{alt:.0f}"
        else:
            alt_txt = f"{round(baro, 1) or 0.0:.1f}"          # no "-0.0"
        if self.sim_mode:
            self.txt_kpi[1].set_text(f"{alt + random.gauss(0, 4):.0f}")
            self.txt_kpi_sub[1].set_text(f"baro: {alt:.0f}m (GPS sim)")
        else:
            # GPS altitude is not in the telemetry
            self.txt_kpi[1].set_text(alt_txt)
            self.txt_kpi_sub[1].set_text("barometric (AGL)")
        # drift: speed and direction over the ground
        fix = has_gps_fix(row)
        drift = self._drift(row) if fix else None
        if not fix:
            self.txt_kpi[2].set_text("—")
            self.txt_kpi_sub[2].set_text("no GPS fix")
        elif drift is None:                  # no speed, no positions yet
            self.txt_kpi[2].set_text("—")
            self.txt_kpi_sub[2].set_text("not in radio packet" if radio
                                         else "not in this file")
        else:
            spd, crs, derived = drift
            self.txt_kpi[2].set_text(f"{spd:.1f}")
            self.txt_kpi_sub[2].set_text((
                f"towards {compass_point(crs)} ({crs:.0f}°)" if spd >= 0.5
                else "standing still")
                + (" · from positions" if derived else ""))
        # where the can is: distance and direction from the start, and
        # the two numbers for a maps app (the last GPS fix)
        dist = math.hypot(x, y)
        if self.last_fix is None:
            self.txt_kpi[3].set_text("—")
            self.txt_kpi_sub[3].set_text("no GPS fix")
            lat, lon, where = row["lat"], row["lon"], ""
            fix_sub = "no GPS fix (placeholder)"
            pos_color = C["dim"]
        else:
            t_fix, lat, lon = self.last_fix[:3]
            bearing = math.degrees(math.atan2(x, y)) % 360
            where = (f"{compass_point(bearing)} ({bearing:.0f}°) of the start"
                     if dist >= 5 else "at the start")
            self.txt_kpi[3].set_text(f"{dist:.0f}")
            self.txt_kpi_sub[3].set_text(where)
            fix_sub = ("GPS fix" if fix else
                       f"no GPS fix · last {s1.duration_text(t - t_fix)} ago")
            pos_color = C["blue"] if fix else C["amber"]
        for i, (value, unit) in ((4, lat_text(lat)), (5, lon_text(lon))):
            self.txt_kpi[i].set_text(value)
            self.txt_kpi[i].set_color(pos_color)
            self.txt_kpi_unit[i].set_text(unit)
        self.txt_kpi_sub[4].set_text(fix_sub)
        self.txt_kpi_sub[5].set_text("")

        # ── after the landing: where to find the can ──
        if det == "LANDED":
            if self.last_fix is not None:
                self.txt_landed.set_text(
                    f"LANDED at  {lat:.5f}, {lon:.5f}   ·   {dist:.0f} m "
                    + (where if dist >= 5 else "from the start"))
            else:
                self.txt_landed.set_text("LANDED · no GPS position")
            self.txt_landed.set_visible(True)
        else:
            self.txt_landed.set_visible(False)

        # ── flight view (only the visible one, for speed) ──
        self._scale_scene()
        self._last_pos = (x, y, alt, dist)
        if self.view3d:
            self._update_track_3d(x, y, alt)
        else:
            self._update_track_2d(x, y, alt, dist)

        # ── 3D orientation + heatmap ──
        self._draw_cylinder(row)
        self.txt_euler.set_text(
            f"Heading {row['heading']:5.0f}°\n"
            f"Roll    {row['roll']:+5.1f}°\n"
            f"Pitch   {row['pitch']:+5.1f}°")

        # ── altitude profile ──
        z_top = self._scene[1]
        self.ln_prof.set_xdata([alt, alt])
        right = alt > 0.8 * z_top                # label stays in the bar
        self.txt_prof.set_position(
            (alt + (-0.015 if right else 0.015) * z_top, 0.5))
        self.txt_prof.set_horizontalalignment("right" if right else "left")
        self.txt_prof.set_text(f"{alt_txt} m")
        if det in ("APOGEE", "DESCENT", "LANDED") and self.alt_top > 0:
            self.pt_prof_apo.set_data([self.alt_top], [0.86])
            self.txt_prof_apo.set_text(f"▲ apogee {self.alt_top:.0f} m")
        else:
            self.pt_prof_apo.set_data([], [])
            self.txt_prof_apo.set_text("")

        # ── radio link ──
        tot = self.pkt_rx + self.pkt_lost
        if is_number(rssi):
            self.txt_link_val[0].set_text(f"{rssi:.0f}")
            self.txt_link_val[0].set_color(self._rssi_color)
            self.txt_link_sub[0].set_text(rssi_sub)
        else:
            self.txt_link_val[0].set_text("—")
            self.txt_link_sub[0].set_text("no radio")
        if is_number(snr):
            self.txt_link_val[1].set_text(f"{snr:+.1f}")
            self.txt_link_sub[1].set_text("dB" + (" (sim)" if self.sim_mode
                                                 else ""))
        else:
            self.txt_link_val[1].set_text("—")
            self.txt_link_sub[1].set_text("dB")
        self.txt_link_val[2].set_text(f"{self.pkt_rx}")
        self.txt_link_sub[2].set_text("received")
        self.txt_link_val[3].set_text(f"{self.pkt_lost}")
        self.txt_link_sub[3].set_text(
            f"{100 * self.pkt_lost / tot:.1f}%" if tot else "0%")

        return []

    def run(self):
        # A timer instead of FuncAnimation: FuncAnimation redraws the whole
        # figure on every tick, also without new data. Drawing is the slow
        # part (~0.1 s on a fast PC, more on a school laptop).
        self.fit.fit_screen()
        self.timer = self.fig.canvas.new_timer(interval=UPDATE_MS)
        self.timer.add_callback(self._tick)
        self.timer.start()
        plt.show()

    def _tick(self):
        self.update(0)
        if self._refresh_link() or self._changed:
            self.fig.canvas.draw_idle()


if __name__ == "__main__":
    s1.apply_args(s1.parse_args(__doc__.splitlines()[1]))
    Dashboard2().run()
