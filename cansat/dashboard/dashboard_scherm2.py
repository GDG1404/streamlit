"""
CanSat 2027 — Screen 2 · 3D Flight Path & Orientation (Python version)
=======================================================================

Python equivalent of scherm2_gps_orientatie.html, built with matplotlib.
Reuses the flight simulator from dashboard_scherm1.py (same folder).

Panels:
  - 3D FLIGHT PATH: the trajectory in a slowly rotating xyz frame
    (east / north / altitude, metres), coloured by altitude, with a
    ground shadow and a drop line for depth perception.
    Press 'M' to toggle to the 2D OSM map around the launch point (the
    first GPS fix; Elsenborn in the simulator) — the recovery view. The
    map zooms out automatically when the can drifts off the map.
  - Altitude profile bar (below the map)
  - Large 3D can (66×115 mm, closed with lid and bottom) with an
    ESTIMATED load heatmap (a simple model from the accelerations, not
    a measurement). Peak hold: colours stay at the highest value reached,
    so at the end of the flight you can see where the load was largest.
    A thin dark raster keeps the shape readable when everything colours.
  - Radio link status (RSSI / packets / SNR)

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

import numpy as np

# reuse simulator + theme from screen 1 (same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashboard_scherm1 as s1  # SIM_SPEED/UPDATE_MS read via s1 (CLI)
from dashboard_scherm1 import (C, PhaseDetector, TelemetrySimulator,
                               has_gps_fix, make_source)

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.gridspec import GridSpec
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
VIEW3D_SPAN = 400     # half-width of the xy scene (m)
ROTATE_DEG_S = 1.5    # slow camera rotation (°/s); 0 = static

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


# ═════════════════════════════════════════════════════════════
#  DASHBOARD SCREEN 2
# ═════════════════════════════════════════════════════════════
class Dashboard2:
    def __init__(self):
        self.sim = make_source()             # replay CSV or simulator
        self.detector = PhaseDetector()      # phase from data, not sim
        self.track_x, self.track_y, self.track_z = [], [], []
        self.pkt_rx, self.pkt_lost = 0, 0
        self._last_t = None      # previous row time (restart + loss detection)
        self._dts = []           # recent row intervals → nominal log rate
        self.ori_artists = []
        self.cyl = cylinder_mesh()
        self.cap_top = cap_mesh(z=+0.115 / 2)
        self.cap_bot = cap_mesh(z=-0.115 / 2)
        self.stress_cmap = LinearSegmentedColormap.from_list(
            "load", [C["green"], C["amber"], C["orange"], C["red"]])
        self.alt_cmap = LinearSegmentedColormap.from_list(
            "altitude", [C["orange"], C["amber"], C["cyan"]])
        self.alt_norm = Normalize(0, self.sim.h_max)
        self.stress_peak = np.zeros(self.cyl[2].shape)   # peak hold per patch
        self.peak_load_n = 0.0
        self._f_now = 0.0
        self.view3d = True
        self._wall = None        # wall-clock pacing for real-time replay
        self._map_fixed = False          # True once basemap is redrawn for real GPS
        self._basemap_artists = []       # artists to remove on basemap redraw
        self._zoom = OSM_ZOOM            # current map zoom (zooms out)
        self._map_half = float("inf")    # map coverage (m), set on draw
        self._build_figure()
        # remember the origin used at build time so we can detect when
        # CsvLive updates it after the first real GPS fix arrives
        self._init_lat0 = self.sim.lat0
        self._init_lon0 = self.sim.lon0

    def _style_axes(self, ax, title=None, title_color=None, face=None):
        ax.set_facecolor(face or C["panel"])
        for s in ax.spines.values():
            s.set_color(C["border"])
            s.set_linewidth(0.8)
        ax.tick_params(colors=C["dim"], labelsize=7)
        if title:
            ax.set_title(title, loc="left", fontsize=8,
                         color=title_color or C["muted"],
                         fontfamily="monospace", pad=4)

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
        cp = self.ax_gps.text(0.99, 0.01, "© OpenStreetMap contributors",
                         transform=self.ax_gps.transAxes, fontsize=6,
                         color=C["dim"], ha="right")
        self._basemap_artists = [bm, cp]

    def _set_map_title(self):
        """Map title: the real location of the launch point."""
        if isinstance(self.sim, TelemetrySimulator):
            where = "ELSENBORN, BELGIUM (sim)"
        elif getattr(self.sim, "_have_fix", False):
            lat, lon = self.sim.lat0, self.sim.lon0
            where = (f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'} "
                     f"{abs(lon):.4f}°{'E' if lon >= 0 else 'W'}")
        else:
            where = "WAITING FOR GPS FIX"
        self.ax_gps.set_title(f"● GPS LIVE TRACK — {where}   [M] 3D view",
                              loc="left", fontsize=8, color=C["green"],
                              fontfamily="monospace", pad=4)

    # ── key handler: M toggles 3D flight ↔ 2D map ──
    def _on_key(self, event):
        if event.key and event.key.lower() == "m":
            self.view3d = not self.view3d
            self.ax_flight.set_visible(self.view3d)
            self.ax_gps.set_visible(not self.view3d)
            self.fig.canvas.draw_idle()

    def _build_figure(self):
        plt.rcParams.update({
            "font.family": "monospace",
            "text.color": C["text"],
            "axes.labelcolor": C["muted"],
        })
        self.fig = plt.figure(figsize=(15, 8.5), facecolor=C["bg"])
        self.fig.canvas.manager.set_window_title(
            "CanSat 2027 — Screen 2 · 3D Flight Path & Orientation")
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        # ── header ──
        self.fig.text(0.02, 0.965, "CanSat 2027", fontsize=14,
                      fontweight="bold", color=C["text"])
        self.fig.text(0.115, 0.965, "● ", fontsize=10, color=C["cyan"])
        self.fig.text(0.13, 0.965,
                      "Screen 2 — 3D Flight Path & Orientation "
                      f"({self.sim.label})",
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

        # ── KPI bar ──
        kpis = [("GPS FIX", "sat", C["green"]),
                ("FLIGHT TIME", "", C["cyan"]),
                ("ALTITUDE (GPS)", "m", C["amber"]),
                ("LATITUDE", "", C["blue"]),
                ("LONGITUDE", "", C["blue"])]
        self.txt_kpi, self.txt_kpi_sub = [], []
        for i, (label, unit, col) in enumerate(kpis):
            x = 0.02 + i * 0.196
            self.fig.text(x, 0.925, label, fontsize=7, color=C["dim"])
            size = 18 if i < 3 else 13
            v = self.fig.text(x, 0.885, "—", fontsize=size,
                              fontweight="bold", color=col)
            if unit:
                self.fig.text(x + 0.135, 0.885, unit, fontsize=8,
                              color=C["muted"])
            sub = self.fig.text(x, 0.862, "", fontsize=7, color=C["dim"])
            self.txt_kpi.append(v)
            self.txt_kpi_sub.append(sub)

        # ── grid: flight view + profile left, big can + link right ──
        gs = GridSpec(3, 5, figure=self.fig,
                      left=0.05, right=0.985, top=0.83, bottom=0.05,
                      hspace=0.50, wspace=0.40,
                      height_ratios=[40, 34, 18])

        # 3D flight path (left, rows 0–1) — default view
        self.ax_flight = self.fig.add_subplot(gs[0:2, :3], projection="3d")
        self.ax_flight.set_facecolor(C["bg"])
        self.ax_flight.set_title(
            "● 3D FLIGHT PATH — EAST / NORTH / ALTITUDE   [M] 2D map",
            loc="left", fontsize=8, color=C["green"],
            fontfamily="monospace", pad=2)
        # dark xyz frame
        pane_rgba = (0.086, 0.106, 0.133, 0.9)         # ≈ panel colour
        for axis in (self.ax_flight.xaxis, self.ax_flight.yaxis,
                     self.ax_flight.zaxis):
            axis.set_pane_color(pane_rgba)
            axis.label.set_color(C["muted"])
            axis.label.set_size(7)
            try:
                axis._axinfo["grid"].update(
                    color="#1c2128", linewidth=0.5)
            except (AttributeError, KeyError):
                pass
        self.ax_flight.tick_params(colors=C["dim"], labelsize=6)
        self.ax_flight.set_xlabel("east (m)")
        self.ax_flight.set_ylabel("north (m)")
        self.ax_flight.set_zlabel("altitude (m)")
        span = max(VIEW3D_SPAN, getattr(self.sim, "xy_span", VIEW3D_SPAN))
        self._span3d = span
        self.ax_flight.set_xlim(-span, span)
        self.ax_flight.set_ylim(-span, span)
        self.ax_flight.set_zlim(0, self.sim.h_max * 1.1)
        try:
            self.ax_flight.set_box_aspect((1, 1, 0.6))
        except AttributeError:
            pass
        self._azim = -60.0
        self.ax_flight.view_init(elev=28, azim=self._azim)
        # target zone on the ground plane
        ang = np.linspace(0, 2 * np.pi, 60)
        self.ax_flight.plot(50 * np.cos(ang), 50 * np.sin(ang),
                            np.zeros_like(ang), color=C["green"],
                            lw=1, ls="--", alpha=0.5)
        # dummy segment: add_collection3d crashes on an empty collection
        self.trk3d = Line3DCollection(np.zeros((1, 2, 3)),
                                      cmap=self.alt_cmap,
                                      norm=self.alt_norm, linewidth=2.5)
        self.ax_flight.add_collection3d(self.trk3d)
        self.ln_shadow, = self.ax_flight.plot([], [], [], color="#2a3038",
                                              lw=1.4, alpha=0.9)
        self.ln_drop, = self.ax_flight.plot([], [], [], color=C["text"],
                                            lw=0.8, ls=":", alpha=0.7)
        self.pt_now3d, = self.ax_flight.plot([], [], [], "o",
                                             color=C["cyan"], ms=7)
        self.pt_start3d, = self.ax_flight.plot([], [], [], "o",
                                               color=C["orange"], ms=7)
        self.pt_apo3d, = self.ax_flight.plot([], [], [], "^",
                                             color=C["amber"], ms=7)
        # set the limits again: autoscale from add_collection3d/plot
        # must not shift the scene
        self.ax_flight.set_xlim(-self._span3d, self._span3d)
        self.ax_flight.set_ylim(-self._span3d, self._span3d)
        self.ax_flight.set_zlim(0, self.sim.h_max * 1.1)
        self.ax_flight.text2D(0.0, 0.02,
                              "▲ apogee · ● start · colour = altitude",
                              transform=self.ax_flight.transAxes,
                              fontsize=7, color=C["dim"],
                              family="monospace")

        # 2D map (same slot, hidden by default — toggle with M)
        self.ax_gps = self.fig.add_subplot(gs[0:2, :3])
        self._style_axes(self.ax_gps, face="#0a0f16")
        self.ax_gps.set_aspect("equal", adjustable="box")
        self.ax_gps.set_xlabel("east (m)", fontsize=7)
        self.ax_gps.set_ylabel("north (m)", fontsize=7)
        self._draw_basemap_2d()
        ang = np.linspace(0, 2 * np.pi, 80)
        self.ax_gps.plot(50 * np.cos(ang), 50 * np.sin(ang),
                         color=C["green"], lw=1, ls="--", alpha=0.6,
                         zorder=3)
        self.ax_gps.plot(0, 0, "+", color=C["green"], ms=12, alpha=0.8,
                         zorder=3)
        self.ax_gps.text(55, 0, "TARGET", fontsize=8, color=C["green"],
                         alpha=0.9, zorder=3)
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
        self.txt_now = self.ax_gps.text(0, 0, "", fontsize=8,
                                        color="white", zorder=6,
                                        visible=False)
        self.ax_gps.set_visible(False)

        # Altitude profile bar (left, below the map)
        self.ax_prof = self.fig.add_subplot(gs[2, :3])
        self._style_axes(self.ax_prof, "● ALTITUDE PROFILE", C["blue"])
        grad = np.linspace(0, 1, 256).reshape(1, -1)
        self.ax_prof.imshow(grad, aspect="auto", cmap=self.alt_cmap,
                            extent=(0, self.sim.h_max, 0, 1))
        self.ax_prof.set_yticks([])
        self.ax_prof.set_xlim(0, self.sim.h_max)
        self.ln_prof = self.ax_prof.axvline(0, color=C["text"], lw=2.5)
        self.txt_prof = self.ax_prof.text(0, 1.15, "", fontsize=8,
                                          color=C["cyan"], ha="center")
        self.ax_prof.set_xlabel("altitude (m)", fontsize=7)

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
            "● 3D ORIENTATION + ESTIMATED LOAD (model, not measured)",
            loc="left", fontsize=8, color=C["purple"],
            fontfamily="monospace", pad=2)
        self.txt_quat = self.ax_ori.text2D(
            0.0, 0.85, "", transform=self.ax_ori.transAxes,
            fontsize=8, color=C["purple"], family="monospace", va="top")
        self.txt_euler = self.ax_ori.text2D(
            1.0, 0.85, "", transform=self.ax_ori.transAxes,
            fontsize=9, color=C["amber"], family="monospace",
            va="top", ha="right")
        self.txt_load = self.ax_ori.text2D(
            0.0, 0.02, "", transform=self.ax_ori.transAxes,
            fontsize=8, color=C["red"], family="monospace", va="bottom")
        self.ax_ori.text2D(
            1.0, 0.02, "estimate · green = low · red = high (peak hold)",
            transform=self.ax_ori.transAxes, fontsize=7,
            color=C["dim"], family="monospace", va="bottom", ha="right")

        # Radio link status (right, bottom)
        self.ax_link = self.fig.add_subplot(gs[2, 3:])
        self._style_axes(self.ax_link, "● RADIO LINK STATUS", C["green"])
        self.ax_link.set_xticks([])
        self.ax_link.set_yticks([])
        labels = ["Packets", "Lost", "SNR", "Frequency"]
        self.txt_link_val, self.txt_link_sub = [], []
        cols = [C["green"], C["amber"], C["cyan"], C["muted"]]
        for i, (lab, col) in enumerate(zip(labels, cols)):
            x = 0.125 + i * 0.25
            self.ax_link.text(x, 0.80, lab, fontsize=7, color=C["dim"],
                              ha="center", transform=self.ax_link.transAxes)
            v = self.ax_link.text(x, 0.42, "—", fontsize=14,
                                  fontweight="bold", color=col, ha="center",
                                  transform=self.ax_link.transAxes)
            s = self.ax_link.text(x, 0.10, "", fontsize=7, color=C["dim"],
                                  ha="center",
                                  transform=self.ax_link.transAxes)
            self.txt_link_val.append(v)
            self.txt_link_sub.append(s)
        self.txt_link_val[3].set_text("868.0")
        self.txt_link_sub[3].set_text("MHz · SF7")

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

        # peak force at the attachment point (accumulated in _ingest)
        self.txt_load.set_text(
            f"est. attachment {self._f_now:5.1f} N · "
            f"peak {self.peak_load_n:.1f} N "
            f"({self.peak_load_n / (TelemetrySimulator.MASS * 9.81):.1f} g)")

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
        self.txt_now.set_position((x + 8, y + 8))
        self.txt_now.set_text(f"{alt:.0f}m")
        self.txt_now.set_visible(True)
        span = max(150, dist * 1.3)
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
            self._clear_track()
            self.pkt_rx = self.pkt_lost = 0
            self._last_t = None
            self._dts.clear()
            self.peak_load_n = 0.0
            self.stress_peak[:] = 0.0
            self.detector = PhaseDetector()

        # packet statistics: the simulator simulates ~1% loss; for real
        # data (live/replay) loss is estimated from gaps in the stream,
        # relative to the normal row interval (1 Hz, 10 Hz, ...)
        if isinstance(self.sim, TelemetrySimulator):
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
        elif self.track_x:
            x, y = self.track_x[-1], self.track_y[-1]
        else:
            x, y = 0.0, 0.0
        alt = max(0.0, row["alt_m"])
        self.track_x.append(x)
        self.track_y.append(y)
        self.track_z.append(alt)

        # load model: accumulate the peak-hold stress map per row
        self._accumulate_stress(row)
        return det, t, x, y, alt

    def _accumulate_stress(self, row):
        X, Y, Z, TH = self.cyl
        a_ax = 9.81 + max(0.0, -row["lacc_z"])
        # the per-interval peak (LSM6DSO) also catches shocks that fall
        # between two log lines; older files without it: nan → ignored
        apk = row.get("acc_peak_g", float("nan"))
        if apk == apk:
            a_ax = max(a_ax, apk * 9.81)
        a_lat = math.hypot(row["lacc_x"], row["lacc_y"])
        th_f = math.atan2(row["lacc_y"], row["lacc_x"])
        frac = (Z - Z.min()) / (Z.max() - Z.min())
        sigma = a_ax * frac + 0.8 * a_lat * frac * (
            0.5 + 0.5 * np.cos(TH - th_f))
        self.stress_peak = np.maximum(self.stress_peak,
                                      np.clip(sigma / 45.0, 0.0, 1.0))
        self._f_now = TelemetrySimulator.MASS * (a_ax + 0.8 * a_lat)
        self.peak_load_n = max(self.peak_load_n, self._f_now)

    # ── per-frame update ──
    def update(self, _frame):
        # advance data time by the REAL elapsed wall-clock time, so the
        # replay stays real-time even when rendering takes >UPDATE_MS
        now = time.monotonic()
        if self._wall is None:
            dt = s1.UPDATE_MS / 1000.0 * s1.SIM_SPEED
        else:
            dt = min(2.0, now - self._wall) * s1.SIM_SPEED
        self._wall = now

        # camera rotation runs on wall time, also when no new data
        if self.view3d and ROTATE_DEG_S:
            self._azim += ROTATE_DEG_S * dt / max(s1.SIM_SPEED, 1e-9)
            self.ax_flight.view_init(elev=28, azim=self._azim)

        rows = self.sim.fetch(dt)
        if not rows:
            return []
        for r in rows[:-1]:
            self._ingest(r)
        row = rows[-1]
        det, t, x, y, alt = self._ingest(row)

        # ── live mode: redraw basemap once the real GPS origin is known ──
        # CsvLive sets lat0/lon0 from the first GPS row it ingests.
        # If the dashboard started before any data arrived, the map was
        # drawn at the default location. Detect the change and redraw once.
        # Replay and simulator are unaffected (their label doesn't start with "LIVE").
        if (not self._map_fixed
                and getattr(self.sim, "label", "").startswith("LIVE")
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
            self._draw_basemap_2d()
            self._map_fixed = True

        # ── header: real RSSI/SNR when the logger records them; only
        # the simulator shows simulated values (labelled) ──
        sim_mode = isinstance(self.sim, TelemetrySimulator)
        rssi = row.get("rssi")
        snr = row.get("snr")
        if rssi is not None:
            self.txt_rssi.set_text(f"RSSI {rssi:.0f} dBm")
        elif sim_mode:
            rssi_sim = -70 - 0.045 * alt + random.gauss(0, 1.5)
            self.txt_rssi.set_text(f"RSSI {rssi_sim:.0f} dBm (sim)")
        else:
            self.txt_rssi.set_text("RSSI —")
        if snr is None and sim_mode:
            snr = 9.5 - 0.004 * alt + random.gauss(0, 0.4)
        self.txt_pkt.set_text(f"packet #{self.pkt_rx}")
        self.txt_phase.set_text(det)
        self.txt_clock.set_text(f"{int(t // 60):02d}:{int(t % 60):02d}")

        # ── KPIs ──
        dist = math.hypot(x, y)
        if sim_mode:
            fix = det != "PRELAUNCH" or t > 2
            sats = random.randint(6, 9) if fix else 0
            self.txt_kpi[0].set_text(f"{sats}")
            self.txt_kpi_sub[0].set_text("3D fix · HDOP 1.2 (sim)" if fix
                                         else "searching…")
            self.txt_kpi[2].set_text(f"{alt + random.gauss(0, 4):.0f}")
            self.txt_kpi_sub[2].set_text(f"baro: {alt:.0f}m (GPS sim)")
        else:
            # satellite count and GPS altitude are not in the telemetry
            self.txt_kpi[0].set_text("—")
            self.txt_kpi_sub[0].set_text("not in telemetry")
            self.txt_kpi[2].set_text(f"{alt:.0f}")
            self.txt_kpi_sub[2].set_text("barometric (AGL)")
        self.txt_kpi[1].set_text(f"{int(t // 60):02d}:{int(t % 60):02d}")
        self.txt_kpi[3].set_text(f"{row['lat']:.4f}°N")
        self.txt_kpi_sub[3].set_text("GPS fix" if has_gps_fix(row)
                                     else "no GPS fix (placeholder)")
        self.txt_kpi[4].set_text(f"{row['lon']:.4f}°E")
        self.txt_kpi_sub[4].set_text(f"distance from start: {dist:.0f} m")

        # ── flight view (only the visible one, for speed) ──
        if self.view3d:
            self._update_track_3d(x, y, alt)
        else:
            self._update_track_2d(x, y, alt, dist)

        # ── 3D orientation + heatmap ──
        self._draw_cylinder(row)
        self.txt_quat.set_text(
            f"qw {row['qw']:+.4f}\nqx {row['qx']:+.4f}\n"
            f"qy {row['qy']:+.4f}\nqz {row['qz']:+.4f}")
        self.txt_euler.set_text(
            f"Heading {row['heading']:5.0f}°\n"
            f"Roll    {row['roll']:+5.1f}°\n"
            f"Pitch   {row['pitch']:+5.1f}°")

        # ── altitude profile ──
        self.ln_prof.set_xdata([alt, alt])
        self.txt_prof.set_position((alt, 1.15))
        self.txt_prof.set_text(f"{alt:.0f}m ▲")

        # ── radio link ──
        tot = self.pkt_rx + self.pkt_lost
        self.txt_link_val[0].set_text(f"{self.pkt_rx}")
        self.txt_link_sub[0].set_text("received")
        self.txt_link_val[1].set_text(f"{self.pkt_lost}")
        self.txt_link_sub[1].set_text(
            f"{100 * self.pkt_lost / tot:.1f}%" if tot else "0%")
        if snr is not None:
            self.txt_link_val[2].set_text(f"{snr:+.1f}")
            self.txt_link_sub[2].set_text("dB" + (" (sim)" if sim_mode else ""))
        else:
            self.txt_link_val[2].set_text("—")
            self.txt_link_sub[2].set_text("dB")

        return []

    def run(self):
        self.anim = FuncAnimation(self.fig, self.update,
                                  interval=s1.UPDATE_MS, cache_frame_data=False)
        plt.show()


if __name__ == "__main__":
    s1.apply_args(s1.parse_args(__doc__.splitlines()[1]))
    Dashboard2().run()
