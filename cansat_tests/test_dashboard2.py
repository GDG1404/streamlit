"""
Tests for dashboard 2 (cansat/dashboard/dashboard_scherm2.py)
==============================================================

Uses the test data and the helpers of test_dashboard1.py (same folder):
a practice flight from the SD card and via the radio, a bench test, and
variants (no GPS, GPS lost on the way down).

Run (Linux, without a screen):   xvfb-run -a python cansat_tests/test_dashboard2.py
Run (Windows):                   py cansat_tests\\test_dashboard2.py
One test only:                   ... test_dashboard2.py radio keys
"""

import argparse
import os
import random
import re
import sys

import numpy as np

import test_dashboard1 as T        # the data, the fake clock and the helpers
from test_dashboard1 import CLOCK, D, check, key, read, write

import dashboard_scherm2 as D2  # noqa: E402


def dash_for(replay=None, live=None, sim=False, speed=1.0):
    D.plt.close("all")
    D.SEA_LEVEL_HPA = 1013.0
    D.apply_args(argparse.Namespace(replay=replay, live=live, sim=sim, speed=speed,
                                    sea_level=None))
    return D2.Dashboard2()


def run(dash, seconds, step=0.5):
    for _ in range(int(round(seconds / step))):
        CLOCK[0] += step
        dash.update(0)


def run_to(dash, t_data, step=0.5):
    """Play until t_data seconds after the first row."""
    for _ in range(200000):
        if dash._last_t is not None and dash._last_t - dash.t_first >= t_data:
            return
        CLOCK[0] += step
        dash.update(0)
    raise RuntimeError(f"the data never reached {t_data} s")


def kpi(dash):
    return ([t.get_text() for t in dash.txt_kpi], [t.get_text() for t in dash.txt_kpi_sub])


def make_data():
    d = T.make_data()
    head, body = read(d["sd"])
    i_utc, i_lat, i_lon = head.index("time_utc"), head.index("lat"), head.index("lon")

    def no_fix(r):
        r = list(r)
        r[i_utc], r[i_lat], r[i_lon] = "00:00:00", "50.457303", "6.221376"
        return r

    d["nogps"] = write("geengps.csv", [head], [no_fix(r) for r in body])
    # the GPS loses its fix 100 s after the first row (on the way down)
    t0 = int(body[0][0])
    d["gpslost"] = write("gpsweg.csv", [head], [
        (no_fix(r) if int(r[0]) - t0 > 100000 else r) for r in body])
    return d


# ═════════════════════════════════════════════════════════════
#  THE TESTS
# ═════════════════════════════════════════════════════════════
def test_flight(d):
    """The practice flight from the SD card."""
    dash = dash_for(replay=d["sd"])
    run_to(dash, 10)
    vals, subs = kpi(dash)
    check("pad: waiting for launch", vals[0] == "—" and subs[0] == "waiting for launch")
    check("pad: no GPS fix yet", vals[3] == "—" and subs[3] == "no GPS fix"
          and subs[4] == "no GPS fix (placeholder)" and vals[2] == "—" and subs[2] == "no GPS fix", str(subs))
    check("pad: placeholder position is dimmed", dash.txt_kpi[4].get_color() == D.C["dim"])
    check("pad: flight scale for a flight file", dash._scene == (600.0, 1200.0), str(dash._scene))
    run_to(dash, 30)
    vals, subs = kpi(dash)
    check("pad: GPS fix", subs[4] == "GPS fix" and dash.txt_kpi[4].get_color() == D.C["blue"]
          and re.match(r"^50\.458\d\d$", vals[4]) is not None, f"{vals[4]} {subs[4]}")
    check("pad: at the start", subs[3] == "at the start" and float(vals[3]) < 5, f"{vals[3]} {subs[3]}")
    check("pad: largest load is 1 g", dash._load_text().splitlines()[1].startswith("largest")
          and " 1.0 g" in dash._load_text(), dash._load_text())
    run_to(dash, 130)
    vals, subs = kpi(dash)
    check("descent: flight time since launch", vals[0] == "01:15" and subs[0] == "since launch", vals[0])
    check("descent: altitude", vals[1] == "428" and subs[1] == "barometric (AGL)", vals[1])
    check("descent: drift from the GPS", vals[2] == "4.6" and subs[2] == "towards NE (65°)", f"{vals[2]} {subs[2]}")
    check("descent: distance and direction", vals[3] == "259" and subs[3] == "NE (65°) of the start", f"{vals[3]} {subs[3]}")
    check("descent: latitude and longitude with 5 decimals",
          vals[4] == "50.45928" and vals[5] == "6.22524"
          and dash.txt_kpi_unit[4].get_text() == "°N" and dash.txt_kpi_unit[5].get_text() == "°E", f"{vals[4]} {vals[5]}")
    check("descent: no landing bar yet", not dash.txt_landed.get_visible())
    check("descent: phase in its colour", dash.txt_phase.get_text() == "DESCENT"
          and dash.txt_phase.get_color() == D.PHASE_BADGE["DESCENT"])
    check("descent: apogee on the altitude bar", dash.txt_prof_apo.get_text() == "▲ apogee 955 m")
    run_to(dash, 200)
    vals, subs = kpi(dash)
    check("landed: flight time as in the flight report", vals[0] == "02:07" and subs[0] == "landed", vals[0])
    check("landed: the landing bar with the two numbers for a maps app",
          dash.txt_landed.get_visible()
          and dash.txt_landed.get_text().startswith("LANDED at  50.46017, 6.22820")
          and "491 m NE (65°) of the start" in dash.txt_landed.get_text(), dash.txt_landed.get_text())
    loads = {k: (round(v[0], 1), v[1], v[2]) for k, v in dash.load_max.items()}
    check("landed: largest loads as in the flight report",
          loads.get("launch") == (11.2, "bottom", False) and loads.get("parachute") == (4.1, "top", False)
          and loads.get("landing") == (16.2, "bottom", True), str(loads))
    text = dash._load_text()
    check("landed: the loads as text", "launch" in text and "36 N · bottom" in text and "13 N · top" in text
          and "≥16.2 g · ≥52 N · bottom" in text, text)
    check("landed: sensor note", dash.txt_sensor.get_text().startswith("g: the peak of every second"))
    peak = dash.stress_peak[:, 0]
    check("landed: the bottom carried the most, the top the least", peak[0] > 0.75 and peak[0] > peak[-1] > 0.1,
          f"bottom {peak[0]:.2f} top {peak[-1]:.2f}")
    check("landed: the scene did not rescale during the flight", dash._scene == (600.0, 1200.0), str(dash._scene))
    check("no radio: no RSSI", dash.txt_rssi.get_text() == "" and dash.txt_link_val[0].get_text() == "—"
          and dash.txt_link_sub[0].get_text() == "no radio" and dash.pkt_lost == 0)


def test_radio(d):
    """The same flight via the radio."""
    dash = dash_for(replay=d["radio"])
    run_to(dash, 130)
    vals, subs = kpi(dash)
    check("radio: drift worked out from the positions",
          3.5 < float(vals[2]) < 5.6 and re.match(r"towards (NE|E) \(\d+°\) · from positions", subs[2]) is not None,
          f"{vals[2]} {subs[2]}")
    check("radio: distance", abs(float(vals[3]) - 259) < 8 and "of the start" in subs[3], f"{vals[3]} {subs[3]}")
    check("radio: RSSI and SNR in the header and in the panel",
          re.match(r"RSSI -\d+ dBm · SNR [+-]\d+\.\d dB", dash.txt_rssi.get_text()) is not None
          and re.match(r"^-\d+$", dash.txt_link_val[0].get_text()) is not None
          and dash.txt_link_sub[0].get_text() == "dBm"
          and re.match(r"^[+-]\d+\.\d$", dash.txt_link_val[1].get_text()) is not None, dash.txt_rssi.get_text())
    check("radio: says where the g comes from", dash.txt_sensor.get_text().startswith("radio: g from the BNO055"))
    run_to(dash, 190)
    lost = 206 - len(read(d["radio"])[1])
    check("radio: packets and lost", dash.txt_link_val[2].get_text() == str(dash.pkt_rx)
          and 1 <= dash.pkt_lost <= lost and dash.txt_link_val[3].get_text() == str(dash.pkt_lost),
          f"rx {dash.pkt_rx} lost {dash.pkt_lost}")
    check("radio: landing bar", dash.txt_landed.get_visible() and "LANDED at  50.460" in dash.txt_landed.get_text(),
          dash.txt_landed.get_text())
    for n in (26, 27, 29):
        dash = dash_for(replay=d[f"old{n}"])
        run_to(dash, 190)
        check(f"older file with {n} columns plays to the landing", dash.detector.phase == "LANDED"
              and dash.txt_landed.get_visible())


def test_gps(d):
    """No GPS at all; the GPS loses its fix on the way down."""
    dash = dash_for(replay=d["nogps"])
    run_to(dash, 200)
    vals, subs = kpi(dash)
    check("no GPS: notes instead of numbers", vals[2] == "—" and subs[2] == "no GPS fix" and vals[3] == "—"
          and subs[4] == "no GPS fix (placeholder)" and dash.txt_kpi[4].get_color() == D.C["dim"], str(subs))
    check("no GPS: landing bar says so", dash.txt_landed.get_text() == "LANDED · no GPS position")
    check("no GPS: the flight is still drawn, straight up", dash.detector.phase == "LANDED" and max(dash.track_z) > 900
          and max(np.abs(dash.track_x)) == 0)
    dash = dash_for(replay=d["gpslost"])
    run_to(dash, 95)
    lat_before = kpi(dash)[0][4]
    run_to(dash, 130)
    vals, subs = kpi(dash)
    check("GPS lost: the last position stays, with its age", vals[4] != "50.45730" and subs[4].startswith("no GPS fix · last ")
          and subs[4].endswith(" s ago") and dash.txt_kpi[4].get_color() == D.C["amber"], f"{vals[4]} {subs[4]}")
    check("GPS lost: drift says no fix", vals[2] == "—" and subs[2] == "no GPS fix")
    run_to(dash, 200)
    check("GPS lost: landing bar gives the last known position",
          dash.txt_landed.get_visible() and "LANDED at  50.45" in dash.txt_landed.get_text(), dash.txt_landed.get_text())
    check("the position before the loss was a real one", lat_before.startswith("50.45") and lat_before != "50.45730", lat_before)


def test_scale(d):
    """The size of the 3D scene: ground test, live, flight."""
    dash = dash_for(replay=d["bench"])
    run_to(dash, 110)
    span, top = dash._scene
    check("bench: the scene zooms in", span <= 50 and top <= 10, str(dash._scene))
    check("bench: the altitude bar follows", dash.ax_prof.get_xlim()[1] == top and dash.alt_norm.vmax == top)
    check("bench: the shock as largest load", "largest" in dash._load_text() and "7.7 g" in dash._load_text(),
          dash._load_text())
    check("bench: altitude with a decimal", re.match(r"^\d\.\d$", kpi(dash)[0][1]) is not None, kpi(dash)[0][1])
    lines = open(d["sd"], encoding="utf-8").read().splitlines(keepends=True)
    live = os.path.join(T.TMP, "live2.csv")
    with open(live, "w", encoding="utf-8", newline="") as fh:
        fh.writelines(lines[:41])
    dash = dash_for(live=live)
    run(dash, 1)
    check("live on the pad: zoomed in", dash._scene[1] <= 10 and dash._scene[0] <= 50, str(dash._scene))
    with open(live, "a", encoding="utf-8", newline="") as fh:
        fh.writelines(lines[41:])
    run(dash, 1)
    check("live after the flight: the full height", dash._scene[1] >= 1100 and dash._scene[0] >= 400, str(dash._scene))
    check("live: flight recognised, loads kept", dash.detector.phase == "LANDED"
          and round(dash.load_max["landing"][0], 1) == 16.2 and round(dash.load_max["launch"][0], 1) == 11.2,
          str(dash.load_max))
    check("round steps", [D2.nice_up(v) for v in (0.5, 5, 6.2, 26, 565, 1050, 1201)] == [0.5, 5, 8, 30, 600, 1200, 1500],
          str([D2.nice_up(v) for v in (0.5, 5, 6.2, 26, 565, 1050, 1201)]))
    check("south and west", D2.lat_text(-33.86882) == ("33.86882", "°S") and D2.lon_text(-70.5) == ("70.50000", "°W"))


def test_keys(d):
    """M for the map, pause, the end of the replay, play again."""
    dash = dash_for(replay=d["sd"], speed=4.0)
    run(dash, 20)
    n0 = dash.pkt_rx
    check("replay at speed 4", 70 <= n0 <= 90 and "×4" in dash.txt_title.get_text(), f"rows={n0}")
    key(dash, " ")
    azim = dash._azim
    run(dash, 10)
    check("SPACE pauses, also the camera", dash.paused and dash.pkt_rx == n0 and dash._azim == azim
          and "paused" in dash.txt_title.get_text())
    key(dash, "m")
    check("M while paused: the map shows the track so far",
          dash.ax_gps.get_visible() and not dash.ax_flight.get_visible()
          and len(dash.trk2d.get_segments()) == len(dash.track_x) - 1, str(len(dash.trk2d.get_segments())))
    key(dash, " ")
    run(dash, 60)
    total = len(dash.sim.rows)
    check("the last picture stays at the end", dash.pkt_rx == total and dash.sim.finished
          and "ended" in dash.txt_title.get_text() and dash.txt_landed.get_visible())
    x0, x1 = dash.ax_gps.get_xlim()
    y0, y1 = dash.ax_gps.get_ylim()
    check("the map holds the whole track", x0 < min(dash.track_x) and max(dash.track_x) < x1
          and y0 < min(dash.track_y) and max(dash.track_y) < y1, f"{x0:.0f}..{x1:.0f}")
    key(dash, "m")
    check("M after the end: back to 3D, with the track", dash.ax_flight.get_visible()
          and len(dash.trk3d._segments3d) == len(dash.track_x) - 1)
    key(dash, "r")
    run(dash, 3)
    check("R plays it again", 8 <= dash.pkt_rx <= 16 and dash.detector.phase == "PRELAUNCH"
          and not dash.txt_landed.get_visible() and not dash.load_max.get("launch"), f"rows={dash.pkt_rx}")
    for k in ("q", "l", "g", None):
        key(dash, k)
    check("other keys do nothing", not dash.paused)


def test_live(d):
    """Live: the data stop coming in and come back; the simulator."""
    lines = open(d["radio"], encoding="utf-8").read().splitlines(keepends=True)
    live = os.path.join(T.TMP, "live3.csv")
    with open(live, "w", encoding="utf-8", newline="") as fh:
        fh.write(lines[0])
    real_time = D.time.time
    D.time.time = lambda: CLOCK[0] + 5e8
    os.utime(live, (CLOCK[0] + 5e8, CLOCK[0] + 5e8))
    try:
        dash = dash_for(live=live)

        def tick(seconds=0.5):
            CLOCK[0] += seconds
            dash.update(0)
            return dash._refresh_link() or dash._changed

        tick()
        check("live: waiting for the first row", dash.txt_rssi.get_text() == "waiting for data…")
        for i in range(100):
            with open(live, "a", encoding="utf-8", newline="") as fh:
                fh.write(lines[1 + i])
            tick(1.0)
        check("live: data come in", dash.txt_dot.get_color() == D.C["green"] and dash.txt_rssi.get_text().startswith("RSSI")
              and not dash.txt_warn.get_visible() and "LIVE: radio" in dash.txt_title.get_text())
        redraws = sum(bool(tick(0.5)) for _ in range(8))
        check("live: amber after 3 s", dash.txt_dot.get_color() == D.C["amber"]
              and dash.txt_rssi.get_text().startswith("No data for"), dash.txt_rssi.get_text())
        check("live: few redraws while waiting", redraws <= 3, str(redraws))
        for _ in range(22):
            tick(0.5)
        check("live: red after 10 s, with the warning", dash.txt_dot.get_color() == D.C["red"]
              and dash.txt_warn.get_visible() and "check the receiver" in dash.txt_warn.get_text(), dash.txt_warn.get_text())
        check("live: the last position stays on screen", kpi(dash)[0][4].startswith("50.45") and len(dash.track_x) > 50,
              f"{kpi(dash)[0][4]} {len(dash.track_x)} points")
        with open(live, "a", encoding="utf-8", newline="") as fh:
            fh.write(lines[101])
        tick(1.0)
        check("live: back to green", dash.txt_dot.get_color() == D.C["green"] and not dash.txt_warn.get_visible())
        key(dash, " ")
        check("live: no pause, M still works", not dash.paused)
        key(dash, "m")
        check("live: M shows the map", dash.ax_gps.get_visible())
    finally:
        D.time.time = real_time
    level, text, warn = D.link_status(True, True, 45, 350)
    check("after the flight the silence is explained", level == "lost" and "stops sending 6 minutes" in warn, warn)
    random.seed(5)
    dash = dash_for(sim=True)
    run(dash, 70)
    check("simulator flies", dash.detector.phase in ("DESCENT", "LANDED") and dash.alt_top > 400
          and "(sim)" in dash.txt_rssi.get_text(), dash.txt_rssi.get_text())


TESTS = {"flight": test_flight, "radio": test_radio, "gps": test_gps, "scale": test_scale,
         "keys": test_keys, "live": test_live}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(TESTS)
    data = make_data()
    for name in wanted:
        print(f"── {name}: {TESTS[name].__doc__.strip().splitlines()[0]}")
        TESTS[name](data)
    print(f"\n{'FAILED: ' + ', '.join(T.FAILS) if T.FAILS else 'all tests passed'}")
    sys.exit(1 if T.FAILS else 0)
