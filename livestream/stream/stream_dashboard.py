r"""
CanSat 2027 — Stream dashboard (voor een YouTube-livestream)
============================================================

Een eenvoudig dashboard met grote cijfers, gemaakt om te streamen. Het toont:
hoogte, verticale snelheid, temperatuur, luchtdruk, de fase van de vlucht, de
ontvangst en een grafiek van de hoogte. Rechtsboven staan de logo's, en er is
een vak waar je in OBS het camerabeeld op legt.

Het leest via USB, en herkent zelf wat er binnenkomt:
  - de Teensy zelf (droogtest, zonder antenne): elke seconde een meetregel
  - de extra LoRa-ontvanger (ontvanger_stream.ino): elk pakket van de CanSat

Starten (in de map CanSatLive):
  py stream\stream_dashboard.py           vraagt de poort (of demo)
  py stream\stream_dashboard.py COM7      rechtstreeks COM7
  py stream\stream_dashboard.py --demo    nagebootste vlucht, zonder hardware

Logo's: zet logo_school.png en logo_team.png in de map 'logos'.
Elke ontvangen regel wordt ook bewaard in de map 'metingen'.

De hoogte telt vanaf de plaats waar je start: de eerste 5 metingen zijn het
nulpunt. Start dit dashboard dus vóór de lancering, als de CanSat nog op de
grond staat.
"""

import argparse
import glob
import math
import os
import queue
import random
import statistics
import sys
import threading
import time
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator  # noqa: E402

# ═══════════════ PAS AAN ═══════════════
TITLE = "CanSat 2027"     # bv. "CanSat 2027 · Team Kepler"
# ═══════════════════════════════════════

WINDOW_S = 300            # grafiek: de laatste 5 minuten
ALT_AXIS_M = 1100         # hoogte-as tot 1100 m (groeit mee als het hoger gaat)
GROUND_PACKETS = 5        # nulpunt = mediaan van de eerste 5 metingen
SIGNAL_WARN_S = 3         # zolang niets ontvangen: oranje
SIGNAL_LOST_S = 10        # zolang niets ontvangen: rood
UPDATE_MS = 250           # zo vaak kijken of er iets nieuws is
WINDOW_TITLE = "CanSat 2027 — Stream"   # zo vind je het venster in OBS

# Vak voor het camerabeeld: in OBS leg je de camera precies hierop.
# Op een OBS-canvas van 1920×1080 is dat positie (1200, 150), grootte 672×378.
CAMERA_SLOT = (0.625, 0.51111, 0.35, 0.35)   # x, y (onderkant), breedte, hoogte

# Het LoRa-pakket van de vluchtcode: deze 13 waarden, in deze volgorde.
# De nieuwere vluchtcode stuurt daarna nog 6 FFT-waarden (19 in totaal);
# die toont de stream niet, maar ze worden wel bewaard.
FIELDS = ["temp_C", "press_hPa", "alt_m", "lat", "lon",
          "lacc_x", "lacc_y", "lacc_z", "heading", "roll", "pitch",
          "fft_peak_hz", "audio_rms"]
FFT_FIELDS = ["fft_peak_amp", "vib_0_10_g", "vib_10_30_g", "vib_30_60_g",
              "vib_60_120_g", "vib_120_208_g"]
RADIO_LENGTHS = (len(FIELDS), len(FIELDS) + len(FFT_FIELDS))   # 13 of 19

# Een meetregel van de Teensy via USB (sensortest_fft.ino of de vluchtcode).
# Oudere versies hebben minder kolommen; de eerste 26 zijn altijd dezelfde.
CSV_COLUMNS = ["millis", "temp_C", "press_hPa", "alt_m", "lat", "lon", "time_utc",
               "gyro_x", "gyro_y", "gyro_z", "lacc_x", "lacc_y", "lacc_z",
               "grav_x", "grav_y", "grav_z", "heading", "roll", "pitch",
               "qw", "qx", "qy", "qz", "fft_peak_hz", "fft_peak_amp", "audio_rms",
               "acc_peak_g", "gps_course_deg", "gps_speed_ms",
               "vib_0_10_g", "vib_10_30_g", "vib_30_60_g", "vib_60_120_g",
               "vib_120_208_g"]
USB_FORMATS = (26, 27, 29, 34)

MAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # CanSatLive
LOGO_DIR = os.path.join(MAP, "logos")
METINGEN = os.path.join(MAP, "metingen")
TEENSY_VID = 0x16C0                                # USB-code van PJRC (Teensy)

# Kleuren (donker thema)
C = dict(page="#0d0d0d", surface="#1a1a19", border="#2c2c2a",
         ink="#f0efec", ink2="#c3c2b7", muted="#898781",
         grid="#2c2c2a", axis="#383835", series="#3987e5",
         good="#0ca30c", warning="#fab219", critical="#d03b3b")


# ═════════════════════════════════════════════════════════════
#  DATA
# ═════════════════════════════════════════════════════════════
def parse_line(line):
    """Een ontvangen regel → (meting, bron), of (None, None) als het geen
    meting is. bron = "radio" (pakket via de LoRa-ontvanger) of "usb" (de
    Teensy rechtstreeks, bij de droogtest)."""
    parts = line.strip().split(",")
    n = len(parts)
    try:
        if any(n in (k, k + 2) for k in RADIO_LENGTHS):   # + RSSI en SNR
            vals = [float(p) for p in parts]
            row = dict(zip(FIELDS, vals))
            with_quality = n - 2 in RADIO_LENGTHS
            row["rssi"] = vals[-2] if with_quality else None
            row["snr"] = vals[-1] if with_quality else None
            row["millis"] = None
            return row, "radio"
        if n in USB_FORMATS:
            cols = dict(zip(CSV_COLUMNS, parts))
            row = {k: float(cols[k]) for k in FIELDS}
            row["millis"] = float(cols["millis"])
            row["rssi"] = row["snr"] = None
            return row, "usb"
    except (ValueError, KeyError):
        pass
    return None, None


def is_number(x):
    return x is not None and not math.isnan(x)


class Flight:
    """Houdt de vlucht bij: hoogte boven de startplaats, snelheid, fase."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.t = deque(maxlen=20000)      # tijd (s sinds de eerste meting)
        self.h = deque(maxlen=20000)      # hoogte boven de startplaats (m)
        self.first_alts = []
        self.t0 = None
        self.count = 0
        self.last = None
        self.last_t = None                # klok van de laatste meting
        self.source = None                # "radio" of "usb"
        self.v = 0.0                      # verticale snelheid (m/s, + = omhoog)
        self.max_h = 0.0
        self.launched = False
        self.landed = False
        self._calm_since = None

    def add(self, row, now, source):
        """Voeg een meting toe. Geeft True terug als het een nieuwe sessie is
        (bv. de Teensy is herstart): dan begint alles opnieuw."""
        # tijd: de klok van de Teensy (millis) als die er is, anders de pc-klok
        t_abs = row["millis"] / 1000.0 if row.get("millis") is not None else now
        restarted = False
        if self.t0 is not None and (source != self.source
                                    or (self.t and t_abs - self.t0 < self.t[-1] - 2)):
            self.reset()
            restarted = True
        if self.t0 is None:
            self.t0 = t_abs
        self.count += 1
        self.last, self.last_t, self.source = row, now, source

        alt = row["alt_m"]
        if not is_number(alt):
            return restarted
        if len(self.first_alts) < GROUND_PACKETS:
            self.first_alts.append(alt)
        h = alt - statistics.median(self.first_alts)
        self.t.append(t_abs - self.t0)
        self.h.append(h)
        self.max_h = max(self.max_h, h)
        self.v = self._slope(4.0)

        if not self.launched and h > 30:
            self.launched = True
        if self.launched and not self.landed:
            if h < 10 and abs(self.v) < 1.0:
                self._calm_since = self._calm_since or now
                if now - self._calm_since >= 5:
                    self.landed = True
            else:
                self._calm_since = None
        return restarted

    def _slope(self, span):
        """Rechte door de punten van de laatste `span` seconden (m/s)."""
        if not self.t:
            return 0.0
        pts = [(t, h) for t, h in zip(self.t, self.h) if t >= self.t[-1] - span]
        if len(pts) < 2 or pts[-1][0] - pts[0][0] < 1.0:
            return self.v
        mt = sum(p[0] for p in pts) / len(pts)
        mh = sum(p[1] for p in pts) / len(pts)
        num = sum((t - mt) * (h - mh) for t, h in pts)
        den = sum((t - mt) ** 2 for t, _ in pts)
        return num / den if den else self.v

    def phase(self):
        if self.count == 0:
            return "WAITING"
        if self.landed:
            return "LANDED"
        if not self.launched:
            return "ON THE PAD"
        return "ASCENT" if self.v > 2 else "DESCENT"

    def signal(self, now):
        """(kleur, tekst) voor de ontvangst."""
        if self.last_t is None:
            return C["muted"], "Waiting for data"
        age = now - self.last_t
        n = f"{self.count} packets"
        if age < SIGNAL_WARN_S:
            if self.source == "usb":
                return C["good"], f"Receiving via USB · {n}"
            rssi = self.last.get("rssi")
            dbm = f" · {rssi:.0f} dBm" if rssi is not None else ""
            return C["good"], f"Receiving · {n}{dbm}"
        if age < SIGNAL_LOST_S:
            return C["warning"], f"No data for {age:.0f} s · {n}"
        return C["critical"], f"No signal for {age:.0f} s · {n}"


# ═════════════════════════════════════════════════════════════
#  BRONNEN: USB-poort of demo (draaien in een aparte thread)
# ═════════════════════════════════════════════════════════════
def serial_reader(port, q, stop):
    """Leest regels van de poort. Valt de kabel even weg, dan probeert het
    elke 2 s opnieuw."""
    import serial
    while not stop.is_set():
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                q.put(("status", f"Verbonden met {port}."))
                while not stop.is_set():
                    raw = ser.readline()
                    if raw:
                        q.put(("line", raw.decode("utf-8", errors="replace").strip(),
                               time.monotonic()))
        except (serial.SerialException, OSError) as e:
            msg = str(e)
            if "PermissionError" in msg or "Access is denied" in msg \
                    or "Toegang geweigerd" in msg:
                msg = ("bezet door een ander programma. Sluit de Arduino IDE "
                       "helemaal, en andere dashboards die deze poort gebruiken")
            q.put(("status", f"{port}: {msg} — opnieuw over 2 s"))
            stop.wait(2)


def demo_packet(k):
    """Pakket nummer k (= seconde k) van een nagebootste vlucht, in hetzelfde
    formaat als de ontvanger: 20 s op de grond, 10 s stijgen tot ±1000 m,
    dalen aan de parachute (±8,5 m/s), landen."""
    if k < 20:
        h = 0.0
    elif k < 30:
        u = (k - 20) / 10
        h = 1000 * (1 - (1 - u) ** 2)
    else:
        h = max(0.0, 1000 - 8.5 * (k - 30))
    h += random.gauss(0, 0.4)
    alt = 612.0 + h                                  # startplaats 612 m
    press = 1013.25 * (1 - alt / 44330) ** 5.255
    temp = 16.0 - 0.0065 * h + random.gauss(0, 0.05)
    lat = 50.846712 + 0.000002 * max(0, k - 30)
    lon = 4.352417 + 0.000035 * max(0, k - 30)
    rssi = -62 - 0.035 * h + random.gauss(0, 1.5)
    snr = 9.5 - 0.004 * h + random.gauss(0, 0.4)
    vals = [f"{temp:.1f}", f"{press:.1f}", f"{alt:.1f}", f"{lat:.5f}",
            f"{lon:.5f}"]
    vals += [f"{random.gauss(0, 0.3):.2f}" for _ in range(3)]
    vals += [f"{random.uniform(0, 360):.1f}", f"{random.gauss(0, 5):.1f}",
             f"{random.gauss(0, 5):.1f}", f"{random.uniform(1, 200):.0f}",
             f"{0.003 + abs(random.gauss(0, 0.001)):.3f}",
             f"{rssi:.1f}", f"{snr:.1f}"]
    return ",".join(vals)


def demo_reader(q, stop):
    """1 pakket per seconde; ongeveer 5% gaat verloren, zoals bij echte radio."""
    t_start, k = time.monotonic(), 0
    while not stop.is_set():
        if random.random() > 0.05:
            q.put(("line", demo_packet(k), time.monotonic()))
        k += 1
        stop.wait(max(0.0, t_start + k - time.monotonic()))


# ═════════════════════════════════════════════════════════════
#  HET SCHERM
# ═════════════════════════════════════════════════════════════
def mmss(x, _pos=None):
    x = max(0, int(round(x)))
    return f"{x // 60}:{x % 60:02d}"


def find_logo(name):
    """logos/logo_school.png (of .jpg/.jpeg) → pad, of None."""
    for ext in ("png", "jpg", "jpeg", "PNG", "JPG", "JPEG"):
        hits = glob.glob(os.path.join(LOGO_DIR, f"{name}.{ext}"))
        if hits:
            return hits[0]
    return None


class StreamDashboard:
    def __init__(self, demo=False, log_dir=None):
        self.demo = demo
        self.flight = Flight()
        self.q = queue.Queue()
        self.stop = threading.Event()
        self._last_status = None
        self._shown = None
        self._mode_shown = None
        self.log_dir = log_dir
        self.logs = {}
        self.stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        self._build()

    # ── opbouw ──
    def _card(self, x, y, w, h):
        ax = self.fig.add_axes([x, y, w, h])
        ax.set_facecolor(C["surface"])
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(C["border"])
        return ax

    def _build(self):
        plt.rcParams["toolbar"] = "None"           # geen knoppenbalk in de stream
        plt.rcParams["font.family"] = "sans-serif"
        self.fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=C["page"])
        try:
            self.fig.canvas.manager.set_window_title(WINDOW_TITLE)
        except AttributeError:
            pass
        f = self.fig

        # ── kop: titel links, ontvangst in het midden, logo's rechts ──
        self.txt_title = f.text(0.03, 0.952, TITLE, fontsize=24,
                                fontweight="bold", color=C["ink"], va="center")
        self._fit_text(self.txt_title, 0.37)
        self.mode_dot = Line2D([0.036], [0.905], marker="o", markersize=8,
                               color=C["muted"], transform=f.transFigure)
        f.add_artist(self.mode_dot)
        self.txt_mode = f.text(0.046, 0.905, "", fontsize=12, color=C["muted"],
                               va="center")

        self.sig_dot = Line2D([0.446], [0.952], marker="o", markersize=12,
                              color=C["muted"], transform=f.transFigure)
        f.add_artist(self.sig_dot)
        self.txt_sig = f.text(0.458, 0.952, "", fontsize=14, color=C["ink"],
                              va="center")
        self.txt_sig_label = f.text(0.440, 0.905, "", fontsize=11,
                                    color=C["muted"], va="center")
        self.logos = self._place_logos()

        # ── grote cijfers (links) en het cameravak (rechts) ──
        cx, cy, cw, ch = CAMERA_SLOT
        hero = self._card(0.03, cy, 0.285, ch)
        hero.text(0.07, 0.86, "Altitude above launch site", fontsize=13,
                  color=C["muted"], transform=hero.transAxes, va="center")
        self.txt_alt = hero.text(0.07, 0.50, "—", fontsize=48, fontweight="bold",
                                 color=C["muted"], transform=hero.transAxes,
                                 va="center")
        self.txt_alt_sub = hero.text(0.07, 0.14, "", fontsize=13, color=C["ink2"],
                                     transform=hero.transAxes, va="center")
        self.txt_phase = hero.text(0.93, 0.14, "", fontsize=12, fontweight="bold",
                                   color=C["ink"], ha="right", va="center",
                                   transform=hero.transAxes,
                                   bbox=dict(boxstyle="round,pad=0.4",
                                             fc=C["page"], ec=C["border"]))

        det = self._card(0.335, cy, 0.265, ch)
        self.tiles = []
        labels = ["Vertical speed", "Temperature", "Air pressure"]
        for i, label in enumerate(labels):
            y = 1 - (i + 0.5) / 3                    # midden van de rij
            det.text(0.08, y + 0.075, label, fontsize=12, color=C["muted"],
                     transform=det.transAxes, va="center")
            val = det.text(0.08, y - 0.06, "—", fontsize=22, fontweight="bold",
                           color=C["muted"], transform=det.transAxes,
                           va="center")
            sub = det.text(0.93, y + 0.075, "", fontsize=11, color=C["ink2"],
                           transform=det.transAxes, va="center", ha="right")
            self.tiles.append((val, sub))
            if i:
                det.axhline(1 - i / 3, xmin=0.05, xmax=0.95,
                            color=C["border"], linewidth=1)

        cam = self._card(cx, cy, cw, ch)
        for y, text, size, color in (
                (0.58, "Camera", 18, C["ink2"]),
                (0.42, "Put the camera on this box in OBS", 11, C["muted"]),
                (0.30, "1920×1080 canvas: position 1200, 150 · size 672 × 378",
                 10, C["muted"])):
            cam.text(0.5, y, text, fontsize=size, color=color, ha="center",
                     va="center", transform=cam.transAxes)

        # ── grafiek: hoogte ──
        f.text(0.03, 0.455, "Altitude (m)", fontsize=13, color=C["ink2"],
               va="center")
        ax = f.add_axes([0.07, 0.085, 0.905, 0.33])
        ax.set_facecolor(C["page"])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(C["axis"])
        ax.tick_params(colors=C["muted"], labelsize=11, length=0, pad=6)
        ax.grid(axis="y", color=C["grid"], linewidth=1, linestyle="-")
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MultipleLocator(200))
        ax.xaxis.set_major_locator(MultipleLocator(60))
        ax.xaxis.set_major_formatter(FuncFormatter(mmss))
        ax.set_xlabel("Elapsed time (min:s)", color=C["muted"], fontsize=11)
        ax.set_ylim(0, ALT_AXIS_M)
        ax.set_xlim(0, WINDOW_S)
        self.ln_alt, = ax.plot([], [], color=C["series"], linewidth=2,
                               solid_capstyle="round", solid_joinstyle="round")
        self.dot_alt, = ax.plot([], [], marker="o", markersize=9,
                                color=C["series"], markeredgecolor=C["page"],
                                markeredgewidth=2, linestyle="none")
        self.txt_end = ax.annotate("", xy=(0, 0), xytext=(-12, 12),
                                   textcoords="offset points", ha="right",
                                   fontsize=13, color=C["ink"])
        self.fill = None
        self.ax = ax
        self._show_mode()
        # basisgroottes onthouden: bij een ander venster schaalt alles mee
        self._base_w = self.fig.get_figwidth()
        self._fonts = [(t, t.get_fontsize()) for t in self.fig.findobj(Text)]
        self._marks = [(m, m.get_markersize())
                       for m in (self.mode_dot, self.sig_dot, self.dot_alt)]

    def _fit_text(self, text, max_width):
        """Maak een tekst kleiner tot hij in `max_width` (deel van de breedte)
        past. Zo botst een lange titel nooit met de rest van de kop."""
        renderer = self.fig.canvas.get_renderer()
        width_px = self.fig.get_figwidth() * self.fig.dpi

        def too_wide():
            return text.get_window_extent(renderer).width > max_width * width_px

        size = text.get_fontsize()
        while size > 10 and too_wide():
            size -= 1
            text.set_fontsize(size)
        while too_wide() and len(text.get_text()) > 5:   # nog te lang: inkorten
            text.set_text(text.get_text()[:-2].rstrip() + "…")

    def _place_logos(self):
        """Zet logo_team en logo_school rechtsboven, naast elkaar. Ontbreekt een
        bestand, dan blijft die plaats gewoon leeg."""
        placed = []
        right, max_h, max_w, gap = 0.975, 0.075, 0.11, 0.015
        fig_ratio = self.fig.get_figheight() / self.fig.get_figwidth()
        for name in ("logo_school", "logo_team"):   # van rechts naar links
            path = find_logo(name)
            if path is None:
                continue
            try:
                img = mpimg.imread(path)
            except Exception as e:  # kapot of vreemd bestand: niet crashen
                print(f"Logo {os.path.basename(path)} kan niet gelezen worden: {e}")
                continue
            ih, iw = img.shape[:2]
            h = max_h
            w = (iw / ih) * h * fig_ratio
            if w > max_w:                          # heel breed logo: kleiner
                h *= max_w / w
                w = max_w
            ax = self.fig.add_axes([right - w, 0.93 - h / 2, w, h])
            ax.imshow(img, aspect="auto", interpolation="antialiased")
            ax.axis("off")
            placed.append(name)
            right -= w + gap
        return placed

    def scale_to_window(self, _event=None):
        """Tekst en punten schalen mee met de grootte van het venster. Zo
        blijft de schikking (en het cameravak) altijd hetzelfde, ook op een
        klein scherm of met Windows-schaal 125-150%."""
        f = self.fig.get_figwidth() / self._base_w
        for t, size in self._fonts:
            t.set_fontsize(size * f)
        for m, size in self._marks:
            m.set_markersize(size * f)
        self.ax.tick_params(labelsize=11 * f, pad=6 * f)

    def keep_on_screen(self):
        """Zorg dat het venster op het scherm past en 16:9 blijft (dan klopt
        het cameravak in OBS). Doet niets zonder Tk-venster (bv. bij tests)."""
        try:
            widget = self.fig.canvas.get_tk_widget()
        except AttributeError:
            return
        top = widget.winfo_toplevel()
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        w, h = widget.winfo_width(), widget.winfo_height()
        if w < 50 or h < 50:                       # nog niet op het scherm
            return
        want_w = min(w, 0.92 * sw, 0.82 * sh * 16 / 9)
        want_h = want_w * 9 / 16
        if abs(want_w - w) > 0.03 * w or abs(want_h - h) > 0.03 * h:
            dpi = self.fig.dpi
            self.fig.set_size_inches(want_w / dpi, want_h / dpi, forward=True)
            print(f"Venster aangepast aan het scherm: {int(want_w)} × {int(want_h)}.")

    # ── bijwerken ──
    def _show_mode(self):
        """Onder de titel: waar komen de gegevens vandaan? Eerlijk gemeld."""
        src = "demo" if self.demo else self.flight.source
        if src == self._mode_shown:
            return
        self._mode_shown = src
        text, color, label = {
            "demo": ("DEMO — simulated flight, not real data", C["warning"],
                     "Radio signal"),
            "usb": ("TEST — sensors connected by USB, no radio", C["warning"],
                    "USB link"),
            "radio": ("Live telemetry from the CanSat · LoRa radio, "
                      "1 update per second", C["muted"], "Radio signal"),
            None: ("Waiting for data", C["muted"], "Data link"),
        }[src]
        self.mode_dot.set_color(color)
        self.txt_mode.set_text(text)
        self.txt_mode.set_color(C["ink"] if color == C["warning"] else C["muted"])
        self.txt_sig_label.set_text(label)

    def _log(self, line, source):
        """Bewaar elke ontvangen regel (één bestand per soort bron)."""
        if not self.log_dir:
            return
        f = self.logs.get(source)
        if f is None:
            os.makedirs(self.log_dir, exist_ok=True)
            n = len(line.split(","))
            path = os.path.join(self.log_dir, f"stream_{self.stamp}_{source}.csv")
            f = open(path, "w", newline="", encoding="utf-8")
            if source == "radio":
                body = FIELDS + (FFT_FIELDS if n >= len(FIELDS) + len(FFT_FIELDS) else [])
                cols = body + (["rssi_dBm", "snr_dB"] if n == len(body) + 2 else [])
            else:
                cols = CSV_COLUMNS[:n]
            f.write("pc_time," + ",".join(cols) + "\r\n")
            self.logs[source] = f
            print(f"Metingen worden bewaard in: {path}")
        f.write(datetime.now().isoformat(timespec="milliseconds") + "," + line + "\r\n")
        f.flush()

    def _drain(self):
        changed = False
        while True:
            try:
                item = self.q.get_nowait()
            except queue.Empty:
                return changed
            if item[0] == "status":
                if item[1] != self._last_status:
                    print(item[1])
                    self._last_status = item[1]
                continue
            _, line, now = item
            row, source = parse_line(line)
            if row is None:
                if line and not line.startswith("millis,"):
                    print(f"[USB] {line}")
                continue
            if self.flight.add(row, now, source):
                print("Nieuwe sessie (de Teensy of de bron is herstart): "
                      "de grafiek begint opnieuw.")
            self._log(line, source)
            changed = True

    def tick(self, now=None):
        """Nieuwe metingen verwerken; tekenen als er iets veranderd is."""
        now = time.monotonic() if now is None else now
        if now - getattr(self, "_screen_check", 0) > 2:
            self._screen_check = now
            self.keep_on_screen()
        changed = self._drain()
        color, sig_text = self.flight.signal(now)
        if changed or sig_text != self._shown:
            self._shown = sig_text
            self._update(color, sig_text)
            self.fig.canvas.draw_idle()

    def _update(self, color, sig_text):
        fl = self.flight
        self._show_mode()
        self.sig_dot.set_color(color)
        self.txt_sig.set_text(sig_text)
        self.txt_phase.set_text(fl.phase())
        if fl.last is None:
            return
        for val, _ in self.tiles:
            val.set_color(C["ink"])
        temp, press = fl.last["temp_C"], fl.last["press_hPa"]
        (v_val, v_sub), (t_val, t_sub), (p_val, p_sub) = self.tiles
        t_val.set_text(f"{temp:.1f} °C" if is_number(temp) else "—")
        t_sub.set_text("inside the CanSat")
        p_val.set_text(f"{press:.0f} hPa" if is_number(press) else "—")
        p_sub.set_text("sea level ≈ 1013 hPa")
        if not fl.h:                     # nog geen bruikbare hoogte
            return

        h = fl.h[-1]
        self.txt_alt.set_color(C["ink"])
        self.txt_alt.set_text(f"{int(round(h)):,} m")
        self.txt_alt_sub.set_text(f"Highest so far: {int(round(fl.max_h)):,} m")
        v = fl.v
        v_val.set_text(f"{abs(v):.1f} m/s")
        v_sub.set_text("↓ falling" if v < -0.5 else "↑ rising" if v > 0.5
                       else "steady")

        # alleen het zichtbare stuk tekenen: blijft licht, ook na uren
        t_now = fl.t[-1]
        x0 = max(0.0, t_now - 0.95 * WINDOW_S)     # rechts wat ruimte voor het punt
        pts = [(t, hh) for t, hh in zip(fl.t, fl.h) if t >= x0 - 2]
        ts, hs = [p[0] for p in pts], [p[1] for p in pts]
        self.ax.set_xlim(x0, x0 + WINDOW_S)
        if fl.source == "usb":
            # droogtest: kleine hoogteverschillen (trap, tafel) → de as schaalt mee
            self.ax.yaxis.set_major_locator(MaxNLocator(5))
            self.ax.set_ylim(min(0, min(hs) - 1), max(10, max(hs) * 1.3))
        else:
            # echte vlucht: vaste as tot 1100 m (groeit mee als het hoger gaat)
            self.ax.yaxis.set_major_locator(MultipleLocator(200))
            self.ax.set_ylim(min(0, min(hs) - 10),
                             max(ALT_AXIS_M, fl.max_h * 1.1))
        self.ln_alt.set_data(ts, hs)
        self.dot_alt.set_data([t_now], [h])
        if self.fill is not None:
            self.fill.remove()
        self.fill = self.ax.fill_between(ts, 0, hs, color=C["series"],
                                         alpha=0.10, linewidth=0)
        # label naast het punt, aan de kant waar de lijn niet loopt
        if t_now - x0 < 0.85 * WINDOW_S:
            off, ha, va = (14, 0), "left", "center"
        elif fl.v < 0:
            off, ha, va = (-12, -12), "right", "top"
        else:
            off, ha, va = (-12, 12), "right", "bottom"
        self.txt_end.set_position(off)
        self.txt_end.set_ha(ha)
        self.txt_end.set_va(va)
        self.txt_end.xy = (t_now, h)
        self.txt_end.set_text(f"{int(round(h)):,} m")

    # ── starten ──
    def run(self, source):
        threading.Thread(target=source, args=(self.q, self.stop),
                         daemon=True).start()
        self.fig.canvas.mpl_connect("close_event", lambda _e: self.close())
        self.fig.canvas.mpl_connect("resize_event", self.scale_to_window)
        try:                                        # venster blijft 16:9
            self.fig.canvas.get_tk_widget().winfo_toplevel().aspect(16, 9, 16, 9)
        except Exception:
            pass
        self.timer = self.fig.canvas.new_timer(interval=UPDATE_MS)
        self.timer.add_callback(self.tick)
        self.timer.start()
        plt.show()
        self.close()

    def close(self):
        self.stop.set()
        for f in self.logs.values():
            if not f.closed:
                f.close()


# ═════════════════════════════════════════════════════════════
#  OPSTARTEN
# ═════════════════════════════════════════════════════════════
def ask_port():
    """Vraag de poort. Geeft 'demo' of de naam van een poort."""
    from serial.tools import list_ports
    while True:
        ports = sorted(list_ports.comports(), key=lambda p: p.device)
        teensys = [p.device for p in ports if p.vid == TEENSY_VID]
        print("\nOp welke poort zit de Teensy (droogtest) of de stream-ontvanger?")
        if not ports:
            print("   Geen enkele poort gevonden. Zit de USB-kabel goed?")
        for i, p in enumerate(ports, 1):
            merk = "   ← Teensy" if p.device in teensys else ""
            print(f"   {i}. {p.device:<8} {p.description}{merk}")
        print("   Typ het nummer of de naam (bv. COM7), 'r' om opnieuw te zoeken,")
        print("   of 'demo' voor een nagebootste vlucht.")
        if len(teensys) == 1:
            voorstel = teensys[0]
        elif len(ports) == 1:
            voorstel = ports[0].device
        else:
            voorstel = ""
        extra = f" [{voorstel}]" if voorstel else ""
        answer = input(f"   Poort{extra}: ").strip() or voorstel
        if not answer or answer.lower() == "r":
            continue
        if answer.lower() == "demo":
            return "demo"
        if answer.isdigit():
            nr = int(answer)
            if 1 <= nr <= len(ports):
                return ports[nr - 1].device
            print(f"   Nummer {nr} staat niet in de lijst.")
            continue
        return answer.upper() if answer.upper().startswith("COM") else answer


def main():
    p = argparse.ArgumentParser(description="CanSat 2027 stream dashboard")
    p.add_argument("port", nargs="?", help="poort van de Teensy of ontvanger, bv. COM7")
    p.add_argument("--demo", action="store_true",
                   help="nagebootste vlucht (zonder hardware)")
    args = p.parse_args()

    port = "demo" if args.demo else args.port
    if port != "demo":
        try:
            import serial  # noqa: F401
        except ImportError:
            print("FOUT: het pakket 'pyserial' ontbreekt.\n"
                  "  py -m pip install -r requirements.txt\n"
                  "  (De demo werkt wel: py stream\\stream_dashboard.py --demo)")
            return 1
    if port is None:
        try:
            port = ask_port()
        except (KeyboardInterrupt, EOFError):
            print("\nGestopt.")
            return 1

    logos = [n for n in ("logo_school", "logo_team") if find_logo(n)]
    print("Logo's gevonden: " + (", ".join(logos) if logos else
          "geen (zet logo_school.png en logo_team.png in de map 'logos')"))
    if port == "demo":
        print("DEMO: een nagebootste vlucht. Er wordt niets bewaard.")
        dash = StreamDashboard(demo=True)
        dash.run(demo_reader)
    else:
        dash = StreamDashboard(log_dir=METINGEN)
        dash.run(lambda q, stop: serial_reader(port, q, stop))
    return 0


if __name__ == "__main__":
    sys.exit(main())
