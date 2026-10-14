r"""
CanSat 2027 — Stream dashboard (voor een YouTube-livestream)
============================================================

Een eenvoudig dashboard met grote cijfers, gemaakt om te streamen. Het leest
de pakketten van een extra LoRa-ontvanger (ontvanger_stream.ino) via USB en
toont: hoogte, verticale snelheid, temperatuur, luchtdruk, de fase van de
vlucht, de radio-ontvangst en een grafiek van de hoogte.

Gebruik:
  py dashboard\stream_dashboard.py           vraagt de poort (of demo)
  py dashboard\stream_dashboard.py COM7      ontvanger op COM7
  py dashboard\stream_dashboard.py --demo    nagebootste vlucht, zonder hardware

In OBS Studio zet je dit venster in je stream (bron: Window Capture).
Druk op F voor volledig scherm. Zie LIVESTREAM.md.

De hoogte telt vanaf de startplaats: de eerste 5 pakketten zijn het nulpunt.
Start dit dashboard dus vóór de lancering, als de CanSat nog op de grond staat.

Elk ontvangen pakket wordt ook bewaard in metingen\stream_<datum>_<uur>.csv.
"""

import argparse
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
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

# ═══════════════ PAS AAN ═══════════════
TITLE = "CanSat 2027"     # bv. "CanSat 2027 · Team Kepler"
# ═══════════════════════════════════════

WINDOW_S = 300            # grafiek: de laatste 5 minuten
ALT_AXIS_M = 1100         # hoogte-as tot 1100 m (groeit mee als het hoger gaat)
GROUND_PACKETS = 5        # nulpunt = mediaan van de eerste 5 pakketten
SIGNAL_WARN_S = 3         # zolang geen pakket: oranje
SIGNAL_LOST_S = 10        # zolang geen pakket: rood
UPDATE_MS = 250           # zo vaak kijken of er iets nieuws is

# Het LoRa-pakket van de vluchtcode (13 waarden, in deze volgorde)
FIELDS = ["temp_C", "press_hPa", "alt_m", "lat", "lon",
          "lacc_x", "lacc_y", "lacc_z", "heading", "roll", "pitch",
          "fft_peak_hz", "audio_rms"]

MAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # C:\CanSat

# Kleuren (donker thema)
C = dict(page="#0d0d0d", surface="#1a1a19", border="#2c2c2a",
         ink="#f0efec", ink2="#c3c2b7", muted="#898781",
         grid="#2c2c2a", axis="#383835", series="#3987e5",
         good="#0ca30c", warning="#fab219", critical="#d03b3b")


# ═════════════════════════════════════════════════════════════
#  DATA
# ═════════════════════════════════════════════════════════════
def parse_packet(line):
    """'13 waarden[,rssi,snr]' → dict, of None als het geen pakket is."""
    parts = line.strip().split(",")
    if len(parts) not in (len(FIELDS), len(FIELDS) + 2):
        return None
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        return None
    row = dict(zip(FIELDS, vals))
    extra = vals[len(FIELDS):]
    row["rssi"] = extra[0] if extra else None
    row["snr"] = extra[1] if extra else None
    return row


class Flight:
    """Houdt de vlucht bij: hoogte boven de startplaats, snelheid, fase."""

    def __init__(self):
        self.t = deque(maxlen=20000)      # aankomsttijd (s sinds 1e pakket)
        self.h = deque(maxlen=20000)      # hoogte boven de startplaats (m)
        self.first_alts = []
        self.t0 = None
        self.count = 0
        self.last = None
        self.last_t = None                # klok van het laatste pakket
        self.v = 0.0                      # verticale snelheid (m/s, + = omhoog)
        self.max_h = 0.0
        self.launched = False
        self.landed = False
        self._calm_since = None

    def add(self, row, now):
        if self.t0 is None:
            self.t0 = now
        if len(self.first_alts) < GROUND_PACKETS:
            self.first_alts.append(row["alt_m"])
        ground = statistics.median(self.first_alts)
        t = now - self.t0
        h = row["alt_m"] - ground
        self.t.append(t)
        self.h.append(h)
        self.count += 1
        self.last, self.last_t = row, now
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
        """(kleur, tekst) voor de radio-ontvangst."""
        if self.last_t is None:
            return C["muted"], "Waiting for data"
        age = now - self.last_t
        n = f"{self.count} packets"
        if age < SIGNAL_WARN_S:
            rssi = self.last.get("rssi")
            dbm = f" · {rssi:.0f} dBm" if rssi is not None else ""
            return C["good"], f"Receiving · {n}{dbm}"
        if age < SIGNAL_LOST_S:
            return C["warning"], f"No packet for {age:.0f} s · {n}"
        return C["critical"], f"No signal for {age:.0f} s · {n}"


# ═════════════════════════════════════════════════════════════
#  BRONNEN: seriële poort of demo (draaien in een aparte thread)
# ═════════════════════════════════════════════════════════════
def serial_reader(port, q, stop):
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
                msg = "bezet door een ander programma (Arduino IDE of logger?)"
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


class StreamDashboard:
    def __init__(self, demo=False, log_path=None):
        self.demo = demo
        self.flight = Flight()
        self.q = queue.Queue()
        self.stop = threading.Event()
        self._last_status = None
        self._shown = None
        self.log = None
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self.log = open(log_path, "w", newline="", encoding="utf-8")
            self.log.write("pc_time," + ",".join(FIELDS) + ",rssi_dBm,snr_dB\r\n")
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
            self.fig.canvas.manager.set_window_title("CanSat 2027 — Stream")
        except AttributeError:
            pass
        f = self.fig

        # ── kop ──
        f.text(0.03, 0.952, TITLE, fontsize=24, fontweight="bold",
               color=C["ink"], va="center")
        sub_color = C["warning"] if self.demo else C["muted"]
        f.add_artist(Line2D([0.036], [0.905], marker="o", markersize=8,
                            color=sub_color, transform=f.transFigure))
        f.text(0.046, 0.905,
               "DEMO — simulated flight, not real data" if self.demo
               else "Live telemetry from the CanSat · LoRa radio, 1 update per second",
               fontsize=12, color=C["ink"] if self.demo else C["muted"],
               va="center")

        self.sig_dot = Line2D([0.536], [0.952], marker="o", markersize=12,
                              color=C["muted"], transform=f.transFigure)
        f.add_artist(self.sig_dot)
        self.txt_sig = f.text(0.548, 0.952, "", fontsize=14, color=C["ink"],
                              va="center")
        f.text(0.530, 0.905, "Radio signal", fontsize=11, color=C["muted"],
               va="center")

        self.txt_phase = f.text(0.97, 0.952, "", fontsize=15, fontweight="bold",
                                color=C["ink"], ha="right", va="center",
                                bbox=dict(boxstyle="round,pad=0.45",
                                          fc=C["surface"], ec=C["border"]))
        f.text(0.97, 0.905, "Flight phase", fontsize=11, color=C["muted"],
               ha="right", va="center")

        # ── grote cijfers ──
        top, height = 0.60, 0.25
        hero = self._card(0.03, top, 0.33, height)
        hero.text(0.06, 0.80, "Altitude above launch site", fontsize=13,
                  color=C["muted"], transform=hero.transAxes, va="center")
        self.txt_alt = hero.text(0.06, 0.45, "—", fontsize=54, fontweight="bold",
                                 color=C["muted"], transform=hero.transAxes,
                                 va="center")
        self.txt_alt_sub = hero.text(0.06, 0.13, "", fontsize=13, color=C["ink2"],
                                     transform=hero.transAxes, va="center")

        self.tiles = []
        labels = ["Vertical speed", "Temperature", "Air pressure"]
        w, gap, x = 0.1833, 0.02, 0.38
        for i, label in enumerate(labels):
            ax = self._card(x + i * (w + gap), top, w, height)
            ax.text(0.09, 0.80, label, fontsize=13, color=C["muted"],
                    transform=ax.transAxes, va="center")
            val = ax.text(0.09, 0.45, "—", fontsize=30, fontweight="bold",
                          color=C["muted"], transform=ax.transAxes, va="center")
            sub = ax.text(0.09, 0.13, "", fontsize=12, color=C["ink2"],
                          transform=ax.transAxes, va="center")
            self.tiles.append((val, sub))

        # ── grafiek: hoogte ──
        f.text(0.03, 0.535, "Altitude (m)", fontsize=13, color=C["ink2"],
               va="center")
        ax = f.add_axes([0.07, 0.09, 0.90, 0.40])
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

    # ── bijwerken ──
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
            row = parse_packet(line)
            if row is None:
                if line:
                    print(f"[ontvanger] {line}")
                continue
            self.flight.add(row, now)
            if self.log:
                self.log.write(datetime.now().isoformat(timespec="milliseconds")
                               + "," + line + "\r\n")
                self.log.flush()
            changed = True

    def tick(self, now=None):
        """Nieuwe pakketten verwerken; tekenen als er iets veranderd is."""
        now = time.monotonic() if now is None else now
        changed = self._drain()
        color, sig_text = self.flight.signal(now)
        if changed or sig_text != self._shown:
            self._shown = sig_text
            self._update(now, color, sig_text)
            self.fig.canvas.draw_idle()

    def _update(self, now, color, sig_text):
        fl = self.flight
        self.sig_dot.set_color(color)
        self.txt_sig.set_text(sig_text)
        self.txt_phase.set_text(fl.phase())
        if fl.last is None:
            return
        h = fl.h[-1]
        self.txt_alt.set_color(C["ink"])
        for val, _ in self.tiles:
            val.set_color(C["ink"])
        self.txt_alt.set_text(f"{int(round(h)):,} m")
        self.txt_alt_sub.set_text(f"Highest so far: {int(round(fl.max_h)):,} m")

        v = fl.v
        (v_val, v_sub), (t_val, t_sub), (p_val, p_sub) = self.tiles
        v_val.set_text(f"{abs(v):.1f} m/s")
        v_sub.set_text("↓ falling" if v < -0.5 else "↑ rising" if v > 0.5
                       else "steady")
        t_val.set_text(f"{fl.last['temp_C']:.1f} °C")
        t_sub.set_text("measured in the CanSat")
        p_val.set_text(f"{fl.last['press_hPa']:.0f} hPa")
        p_sub.set_text("sea level ≈ 1013 hPa")

        # alleen het zichtbare stuk tekenen: blijft licht, ook na uren
        t_now = fl.t[-1]
        x0 = max(0.0, t_now - 0.95 * WINDOW_S)     # rechts wat ruimte voor het punt
        pts = [(t, h) for t, h in zip(fl.t, fl.h) if t >= x0 - 2]
        ts, hs = [p[0] for p in pts], [p[1] for p in pts]
        self.ax.set_xlim(x0, x0 + WINDOW_S)
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
        self.timer = self.fig.canvas.new_timer(interval=UPDATE_MS)
        self.timer.add_callback(self.tick)
        self.timer.start()
        plt.show()
        self.close()

    def close(self):
        self.stop.set()
        if self.log and not self.log.closed:
            self.log.close()


# ═════════════════════════════════════════════════════════════
#  OPSTARTEN
# ═════════════════════════════════════════════════════════════
def ask_port():
    """Vraag de poort van de stream-ontvanger. Geeft 'demo' of een poort."""
    from serial.tools import list_ports
    while True:
        ports = sorted(list_ports.comports(), key=lambda p: p.device)
        print("\nOp welke poort zit de stream-ontvanger?")
        if not ports:
            print("   Geen enkele poort gevonden. Zit de USB-kabel goed?")
        for i, p in enumerate(ports, 1):
            print(f"   {i}. {p.device:<8} {p.description}")
        print("   Typ het nummer of de naam (bv. COM7), 'r' om opnieuw te zoeken,")
        print("   of 'demo' voor een nagebootste vlucht.")
        voorstel = ports[0].device if len(ports) == 1 else ""
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
    p.add_argument("port", nargs="?", help="poort van de ontvanger, bv. COM7")
    p.add_argument("--demo", action="store_true",
                   help="nagebootste vlucht (zonder hardware)")
    args = p.parse_args()

    port = "demo" if args.demo else args.port
    if port is None or port != "demo":
        try:
            import serial  # noqa: F401
        except ImportError:
            print("FOUT: het pakket 'pyserial' ontbreekt.\n"
                  "  py -m pip install pyserial\n"
                  "  (Of probeer eerst: py dashboard\\stream_dashboard.py --demo)")
            return 1
    if port is None:
        try:
            port = ask_port()
        except (KeyboardInterrupt, EOFError):
            print("\nGestopt.")
            return 1

    if port == "demo":
        print("DEMO: een nagebootste vlucht. Er wordt niets bewaard.")
        dash = StreamDashboard(demo=True)
        dash.run(demo_reader)
    else:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        log = os.path.join(MAP, "metingen", f"stream_{stamp}.csv")
        print(f"Pakketten worden ook bewaard in: {log}")
        dash = StreamDashboard(log_path=log)
        dash.run(lambda q, stop: serial_reader(port, q, stop))
    return 0


if __name__ == "__main__":
    sys.exit(main())
