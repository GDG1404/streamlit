"""
Tests for dashboard 3, the stream dashboard (livestream/stream/stream_dashboard.py)
====================================================================================

Feeds the dashboard the packets of its own simulated flight (and variants:
a weather change on the pad, a walk up a hill, the stairs, lost packets,
silence) with a fake clock and checks what is on screen.

Run (Linux, without a screen):   xvfb-run -a python cansat_tests/test_dashboard3.py
Run (Windows):                   py cansat_tests\\test_dashboard3.py
One test only:                   ... test_dashboard3.py drift hill
"""

import csv
import os
import random
import sys

import test_dashboard1 as T        # the test data and check()
from test_dashboard1 import check

sys.path.insert(0, os.path.join(T.HERE, "..", "livestream", "stream"))
import stream_dashboard as sd  # noqa: E402

sd.LOGO_DIR = os.path.join(T.TMP, "no_logos")


# ═════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════
def packet(k, dh=0.0):
    """Packet k of the simulated flight, the altitude shifted by dh metres."""
    parts = sd.demo_packet(k).split(",")
    alt = float(parts[2]) + dh
    parts[2] = f"{alt:.1f}"
    parts[1] = f"{1013.25 * (1 - alt / 44330) ** 5.255:.1f}"
    return ",".join(parts)


def usb_line(millis, alt):
    """A line of the Teensy over USB (34 columns) at this altitude."""
    vals = {c: "0" for c in sd.CSV_COLUMNS}
    vals.update(millis=str(int(millis)), temp_C="21.4", press_hPa="942.5",
                alt_m=f"{alt:.2f}", lat="50.846712", lon="4.352417", time_utc="00:00:00")
    return ",".join(vals[c] for c in sd.CSV_COLUMNS)


class Run:
    """A dashboard that is fed one item per second."""

    def __init__(self, demo=False):
        sd.plt.close("all")
        self.d = sd.StreamDashboard(demo=demo)
        self.k = 0

    def feed(self, items):
        """items: packets (text), rows (dict) or None (nothing arrives)."""
        for item in items:
            now = 100.0 + self.k
            if isinstance(item, dict):
                self.d.q.put(("row", item, now))
            elif item is not None:
                self.d.q.put(("line", item, now))
            self.d.tick(now=now + 0.05)
            self.k += 1
        return self

    @property
    def fl(self):
        return self.d.flight


def flight(dh=0.0, start=0, stop=200, lost=()):
    return [None if k in lost else packet(k, dh) for k in range(start, stop)]


# ═════════════════════════════════════════════════════════════
#  THE TESTS
# ═════════════════════════════════════════════════════════════
def test_demo(_d):
    """The simulated flight: phases, clock, chart."""
    random.seed(11)
    r = Run(demo=True).feed(flight(stop=11, lost=(41, 63)))
    d = r.d
    check("pad: ON THE PAD, about 0 m", r.fl.phase() == "ON THE PAD" and d.txt_alt.get_text() == "0 m", d.txt_alt.get_text())
    check("pad: waiting for launch", d.txt_clock.get_text() == "" and d.txt_clock_label.get_text() == "Waiting for launch")
    check("pad: time axis since the start", d.ax.get_xlabel() == "Elapsed time (min:s)")
    check("demo is labelled", d.txt_mode.get_text().startswith("DEMO"))
    r.feed(flight(start=11, stop=27, lost=(41, 63)))
    check("climb: ASCENT", r.fl.phase() == "ASCENT" and r.fl.launched and 18.5 <= r.fl.t_launch <= 20.5, f"t_launch {r.fl.t_launch}")
    check("climb: mission clock", d.txt_clock.get_text() in ("T+ 0:06", "T+ 0:07") and d.txt_clock_label.get_text() == "",
          d.txt_clock.get_text())
    check("climb: no apogee marker yet", d.txt_top.get_text() == "")
    check("climb: time axis since the launch", d.ax.get_xlabel() == "Time since launch (min:s)"
          and d.ax.xaxis.get_major_formatter()(r.fl.t_launch + 60, 0) == "T+1:00"
          and d.ax.xaxis.get_major_formatter()(r.fl.t_launch - 30, 0) == "T−0:30")
    r.feed(flight(start=27, stop=96, lost=(41, 63)))
    check("descent: DESCENT", r.fl.phase() == "DESCENT" and d.txt_phase.get_text() == "DESCENT")
    check("descent: apogee about 1000 m, marked", 990 < r.fl.max_h < 1010 and d.txt_top.get_text().startswith("Apogee 1,00"),
          d.txt_top.get_text())
    check("descent: highest so far", d.txt_alt_sub.get_text().startswith("Highest so far: 1,00"), d.txt_alt_sub.get_text())
    check("descent: falling at about 8.5 m/s", d.tiles[0][0].get_text() in ("8.4 m/s", "8.5 m/s", "8.6 m/s")
          and d.tiles[0][1].get_text() == "↓ falling", d.tiles[0][0].get_text())
    r.feed(flight(start=96, stop=161))
    check("landed: LANDED", r.fl.phase() == "LANDED" and d.txt_phase.get_text() == "LANDED")
    ft = r.fl.flight_time()
    check("landed: flight time about 2:08", 126 <= ft <= 130 and d.txt_clock.get_text() == f"Flight time {sd.mmss(ft)}",
          d.txt_clock.get_text())
    check("landed: apogee and landing marked", d.txt_alt_sub.get_text().startswith("Apogee: 1,00")
          and d.txt_landed.get_text() == "Landed" and d.txt_launch.get_text() == "Launch")
    r.feed(flight(start=161, stop=700))
    x0, x1 = d.ax.get_xlim()
    check("9 minutes later: the whole flight is still in the chart",
          x0 <= r.fl.t_launch and r.fl.t_landed < x1 and x1 - x0 <= sd.WINDOW_S + 1, f"{x0:.0f}..{x1:.0f}")
    check("... and the clock still shows the flight time", d.txt_clock.get_text() == f"Flight time {sd.mmss(ft)}")
    check("... and the altitude is still live", d.txt_alt.get_text() in ("0 m", "-1 m", "1 m") and r.fl.count > 690)
    cam = [ax for ax in d.fig.axes if any(t.get_text() == "Camera" for t in ax.texts)][0]
    pos = cam.get_position()
    check("the camera box did not move (OBS)", all(abs(a - b) < 1e-4 for a, b in
                                                 zip((pos.x0, pos.y0, pos.width, pos.height), sd.CAMERA_SLOT)),
          str((pos.x0, pos.y0, pos.width, pos.height)))
    check("Q no longer closes the window", sd.plt.rcParams["keymap.quit"] == [] and sd.plt.rcParams["keymap.yscale"] == []
          and sd.plt.rcParams["keymap.fullscreen"] != [])


def test_drift(_d):
    """40 minutes on the pad while the air pressure changes (28 m)."""
    random.seed(12)
    r = Run().feed([packet(0, 28.0 * k / 2400) for k in range(2400)])
    check("pad after 40 minutes: still about 0 m", abs(r.fl.height()) < 3 and r.fl.phase() == "ON THE PAD",
          f"{r.fl.height():.1f} m")
    r.feed(flight(dh=28.0))
    check("flight: the apogee counts from the pad", 992 < r.fl.max_h < 1008, f"{r.fl.max_h:.1f}")
    check("flight: landed, at about 0 m", r.fl.phase() == "LANDED" and abs(r.fl.height()) < 3, f"{r.fl.height():.1f}")
    check("flight: flight time", 126 <= r.fl.flight_time() <= 130, str(r.fl.flight_time()))


def test_hill(_d):
    """Carried 40 m up a hill, then the launch; the stairs; a lift."""
    random.seed(13)
    r = Run().feed([packet(0, 40.0 * k / 120) for k in range(120)])
    check("walking up: no launch", not r.fl.launched and r.fl.phase() == "ON THE PAD" and r.fl.height() > 30,
          f"{r.fl.height():.1f} m")
    r.feed([packet(0, 40.0)] * 300)
    check("5 minutes on the pad: this is the new zero", abs(r.fl.height()) < 2 and not r.fl.launched, f"{r.fl.height():.1f} m")
    r.feed(flight(dh=40.0))
    check("flight from the hill", r.fl.phase() == "LANDED" and 992 < r.fl.max_h < 1008 and abs(r.fl.height()) < 3,
          f"apogee {r.fl.max_h:.1f} end {r.fl.height():.1f}")
    # launch right after the walk, before the zero could follow
    r = Run().feed([packet(0, 40.0 * k / 60) for k in range(60)]).feed([packet(0, 40.0)] * 20).feed(flight(dh=40.0, start=15))
    check("launch right after the walk: the zero is the pad", r.fl.phase() == "LANDED" and 990 < r.fl.max_h < 1010,
          f"apogee {r.fl.max_h:.1f}")
    # the stairs over USB: 6 m in 12 s, then standing still
    up = [usb_line(5000 + 1000 * k, 600.0 + min(6.0, 0.5 * max(0, k - 20))) for k in range(140)]
    r = Run().feed(up)
    check("stairs: the 6 m stay during a test of 2 minutes", 5.5 < r.fl.height() < 6.5 and not r.fl.launched
          and r.d.txt_alt.get_text() == "6 m", r.d.txt_alt.get_text())
    check("stairs: USB test is labelled", r.d.txt_mode.get_text().startswith("TEST") and "via USB" in r.d.txt_sig.get_text())
    r.feed([usb_line(5000 + 1000 * k, 606.0) for k in range(140, 400)])
    check("standing upstairs for minutes: the new zero", abs(r.fl.height()) < 1, f"{r.fl.height():.1f}")
    # a lift: 3 m/s for 8 s
    r = Run().feed([usb_line(5000 + 1000 * k, 600.0 + min(24.0, 3.0 * max(0, k - 20))) for k in range(60)])
    check("a lift is no launch", not r.fl.launched and 23 < r.fl.height() < 25, f"{r.fl.height():.1f}")
    r.feed([usb_line(3000 + 1000 * k, 600.0) for k in range(20)])
    check("Teensy restarted: everything starts again", r.fl.count == 20 and abs(r.fl.height()) < 1)


def test_radio(d):
    """Lost packets, silence, the end of the transmission, a logger file."""
    random.seed(14)
    r = Run().feed(flight(lost=(21, 22, 23, 24)))
    check("4 packets lost in the climb: still a flight", r.fl.phase() == "LANDED" and 990 < r.fl.max_h < 1010
          and 19 <= r.fl.t_launch <= 21, f"apogee {r.fl.max_h:.0f} launch {r.fl.t_launch}")
    r = Run().feed(flight(lost=range(20, 34)))
    check("the whole climb lost: still a flight", r.fl.phase() == "LANDED" and r.fl.max_h > 900,
          f"{r.fl.phase()} apogee {r.fl.max_h:.0f}")
    r = Run().feed(flight(stop=100)).feed([None] * 5)
    check("silence: No data, the clock runs on", r.d.txt_sig.get_text().startswith("No data for 5 s")
          and r.d.txt_clock.get_text() == "T+ 1:24", f"{r.d.txt_sig.get_text()} | {r.d.txt_clock.get_text()}")
    r.feed([None] * 11)
    check("silence: No signal", r.d.txt_sig.get_text().startswith("No signal for 16 s")
          and r.d.sig_dot.get_color() == sd.C["critical"], r.d.txt_sig.get_text())
    r.feed(flight(start=116, stop=118))
    check("packets again: Receiving", r.d.txt_sig.get_text().startswith("Receiving ·"), r.d.txt_sig.get_text())
    r = Run().feed(flight(stop=20 + 345)).feed([None] * 30)
    check("6 minutes after the launch the silence is no alarm", r.d.txt_sig.get_text().startswith("End of transmission")
          and r.d.sig_dot.get_color() == sd.C["muted"], r.d.txt_sig.get_text())
    with open(d["radio"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    r = Run().feed(rows)
    check("the logger file (--live): the practice flight", r.fl.phase() == "LANDED" and 945 < r.fl.max_h < 965
          and 124 <= r.fl.flight_time() <= 129 and r.fl.source == "radio",
          f"{r.fl.phase()} apogee {r.fl.max_h:.0f} time {r.fl.flight_time()}")
    check("... radio is labelled", r.d.txt_mode.get_text().startswith("Live telemetry"))


TESTS = {"demo": test_demo, "drift": test_drift, "hill": test_hill, "radio": test_radio}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(TESTS)
    data = {"radio": T.gen("radio3.csv", "--vlucht", "--radio")}
    for name in wanted:
        print(f"── {name}: {TESTS[name].__doc__.strip().splitlines()[0]}")
        TESTS[name](data)
    print(f"\n{'FAILED: ' + ', '.join(T.FAILS) if T.FAILS else 'all tests passed'}")
    sys.exit(1 if T.FAILS else 0)
