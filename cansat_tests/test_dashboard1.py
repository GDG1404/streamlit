"""
Tests for dashboard 1 (cansat/dashboard/dashboard_scherm1.py)
==============================================================

Makes its own test data with tools/gen_test_csv.py (a practice flight from
the SD card and via the radio, a bench test) plus variants of them, plays
them through the dashboard with a fake clock and checks what is on screen.

Run (Linux, without a screen):   xvfb-run -a python cansat_tests/test_dashboard1.py
Run (Windows, in C:\\CanSat):     the dashboards there have no tests folder;
                                 run it from a copy of the repository:
                                 py cansat_tests\\test_dashboard1.py
One test only:                   ... test_dashboard1.py radio keys

The windows are never shown: the tests call the update function themselves.
"""

import argparse
import csv
import os
import random
import re
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
CANSAT = os.path.join(HERE, "..", "cansat")
sys.path.insert(0, os.path.join(CANSAT, "dashboard"))

import numpy as np  # noqa: E402
import dashboard_scherm1 as D  # noqa: E402

CLOCK = [0.0]
D.time.monotonic = lambda: CLOCK[0]          # the dashboard's wall clock
FAILS = []
TMP = tempfile.mkdtemp(prefix="cansat_test_")


# ═════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════
def check(name, cond, info=""):
    print(("  ok    " if cond else "  FAIL  ") + name, info if not cond or info else "")
    if not cond:
        FAILS.append(name)


def gen(name, *flags):
    path = os.path.join(TMP, name)
    subprocess.run([sys.executable, os.path.join(CANSAT, "tools", "gen_test_csv.py"),
                    path, *flags], check=True, stdout=subprocess.DEVNULL)
    return path


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def write(name, *parts):
    """parts: lists of rows (a header is a row too)."""
    path = os.path.join(TMP, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for part in parts:
            w.writerows(part)
    return path


def dash_for(replay=None, live=None, sim=False, speed=1.0):
    D.plt.close("all")
    D.SEA_LEVEL_HPA = 1013.0
    D.apply_args(argparse.Namespace(replay=replay, live=live, sim=sim, speed=speed,
                                    sea_level=None))
    return D.Dashboard()


def run(dash, seconds, step=0.5):
    for _ in range(int(round(seconds / step))):
        CLOCK[0] += step
        dash.update(0)


def run_to(dash, t_data, step=0.5):
    """Play until t_data seconds after the first row."""
    for _ in range(200000):
        if dash.hist["t"] and dash.hist["t"][-1] - dash.t_first >= t_data:
            return
        CLOCK[0] += step
        dash.update(0)
    raise RuntimeError(f"the data never reached {t_data} s")


def key(dash, k):
    dash._on_key(types.SimpleNamespace(key=k))


def kpi(dash):
    return [t.get_text() for t in dash.txt_kpi], [t.get_text() for t in dash.txt_kpi_sub]


# ═════════════════════════════════════════════════════════════
#  THE TEST DATA
# ═════════════════════════════════════════════════════════════
def make_data():
    d = {"sd": gen("vlucht.csv", "--vlucht"),
         "radio": gen("radio.csv", "--vlucht", "--radio"),
         "bench": gen("bank.csv")}
    head, body = read(d["sd"])
    rhead, rbody = read(d["radio"])
    bhead, bbody = read(d["bench"])
    # older files: before acc_peak_g, the GPS drift and the vibration bands
    for n in (26, 27, 29):
        d[f"old{n}"] = write(f"oud_{n}.csv", [head[:n]], [r[:n] for r in body])
    # the old radio packet with 13 values: no bands, no peak strength
    drop = [rhead.index(c) for c in ["fft_peak_amp"] + D.BAND_COLUMNS]
    d["radio13"] = write("radio13.csv", [rhead], [
        [("nan" if i in drop else v) for i, v in enumerate(r)] for r in rbody])
    # the Teensy restarts on the pad: the header again, millis starts again
    d["restart"] = write("herstart.csv", [head], body[:40], [head], body)
    # the Teensy was on for 10 minutes before the logger started
    d["late"] = write("laat.csv", [bhead], [[str(int(r[0]) + 600000)] + r[1:] for r in bbody])
    # 55 minutes on the pad before the launch
    pad, rows, t = body[:50], [], int(body[0][0])
    for i in range(3300):
        rows.append([str(t)] + pad[i % len(pad)][1:])
        t += 1000
    shift = t - int(body[0][0])
    d["long"] = write("lang.csv", [head], rows, [[str(int(r[0]) + shift)] + r[1:] for r in body])
    return d


# ═════════════════════════════════════════════════════════════
#  THE TESTS
# ═════════════════════════════════════════════════════════════
def test_flight(d):
    """The practice flight from the SD card, from the pad to the landing."""
    dash = dash_for(replay=d["sd"])
    run_to(dash, 30)
    vals, subs = kpi(dash)
    check("pad: phase PRELAUNCH, altitude about 0", dash.detector.phase == "PRELAUNCH"
          and abs(float(vals[0])) < 1.0, vals[0])
    check("pad: vibration quiet", subs[4] == "quiet" and float(vals[4]) < 0.01, f"{vals[4]} {subs[4]}")
    check("pad: at rest is no shock", "none yet" in dash.txt_shock.get_text(), dash.txt_shock.get_text())
    check("pad: ground test zoom", "zoomed in" in dash.txt_alt_zoom.get_text())
    check("pad: Cd panel says when it starts", "descent" in dash.txt_cd_note.get_text())
    run_to(dash, 62)
    vals, subs = kpi(dash)
    check("climb: phase ASCENT", dash.detector.phase == "ASCENT")
    check("climb: vertical speed up", vals[1].startswith("↑") and float(vals[1][1:]) > 50, vals[1])
    check("climb: no APOGEE yet", not dash.txt_apogee.get_visible() and subs[0].startswith("highest:"), subs[0])
    check("climb: fastest climb in the sub-value", subs[1].startswith("fastest climb:"), subs[1])
    check("climb: vibration fast", subs[4].startswith("fast"), subs[4])
    check("climb: launch shock found", dash.txt_shock.get_text().startswith("largest shock 11."),
          dash.txt_shock.get_text())
    run_to(dash, 76)
    check("parachute opening: Cd and the descent rate wait for the steady descent",
          kpi(dash)[0][5] == "—" and kpi(dash)[1][5] == "descent not steady yet"
          and kpi(dash)[1][1].startswith("fastest climb:"), str(kpi(dash)))
    run_to(dash, 130)
    vals, subs = kpi(dash)
    check("descent: phase DESCENT", dash.detector.phase == "DESCENT")
    check("descent: APOGEE label", dash.txt_apogee.get_visible() and dash.txt_apogee.get_text() == "APOGEE 955 m",
          dash.txt_apogee.get_text())
    check("descent: vertical speed down, about 8.5 m/s", vals[1].startswith("↓") and 8.0 < float(vals[1][1:]) < 9.0, vals[1])
    check("descent: descent rate with the ESA range, green",
          re.match(r"descent: 8\.[3-6] m/s · ESA 8–11", subs[1]) is not None
          and dash.txt_kpi_sub[1].get_color() == D.C["green"], subs[1])
    check("descent: Cd about 0.50", abs(float(vals[5]) - 0.50) < 0.03 and subs[5] == "median: 0.50", f"{vals[5]} {subs[5]}")
    check("descent: vibration slow", subs[4].startswith("slow"), subs[4])
    check("descent: most frequent frequencies listed", dash.txt_top.get_text().startswith("most frequent: 1·140Hz"),
          dash.txt_top.get_text())
    run_to(dash, 200)
    vals, subs = kpi(dash)
    check("landed: phase LANDED, altitude 0", dash.detector.phase == "LANDED" and vals[0] == "0", vals[0])
    check("landed: flight time as in the flight report", dash.txt_landed.get_text() == "LANDED · flight time 02:07",
          dash.txt_landed.get_text())
    check("landed: shock at the sensor limit gets ≥", "≥16.2 g at T+02:07" in dash.txt_shock.get_text(),
          dash.txt_shock.get_text())
    cd = np.array(dash.ln_cd.get_ydata(), dtype=float)
    check("landed: no Cd jump at the landing", np.nanmax(cd) < 0.65 and np.nanmin(cd) > 0.40,
          f"{np.nanmin(cd):.2f}..{np.nanmax(cd):.2f}")
    phases = [s[0] for s in dash.segments]
    check("all five phases, in order", phases == ["PRELAUNCH", "ASCENT", "APOGEE", "DESCENT", "LANDED"], str(phases))
    rects = [a for a in dash.seg_artists if isinstance(a, D.Rectangle)]
    ends = [r.get_x() + r.get_width() for r in rects[:-1]]
    starts = [r.get_x() for r in rects[1:]]
    check("phase bar without holes", np.allclose(ends, starts), f"{ends} {starts}")
    grid = np.ma.filled(dash.mesh_vib.get_array(), np.nan)
    check("vibration history: 5 bands, the launch in every band",
          grid.shape[0] == 5 and bool((np.nanmax(grid, axis=1) > 0.1).all()), str(grid.shape))
    check("the CHUTE label cannot leave its panel", dash.txt_chute.get_clip_on())
    check("no lost rows in an SD file", dash.pkt_lost == 0, str(dash.pkt_lost))
    check("gyroscope panel for SD data", dash.ax_gyro.get_visible() and not dash.ax_radio.get_visible())


def test_radio(d):
    """The same flight via the radio: 19 values, RSSI, lost packets."""
    dash = dash_for(replay=d["radio"])
    run_to(dash, 130)
    vals, subs = kpi(dash)
    n_file = len(read(d["radio"])[1])
    check("radio: the radio signal panel takes the place of the gyroscope",
          dash.ax_radio.get_visible() and not dash.ax_gyro.get_visible())
    check("radio: RSSI and SNR in the header", re.match(r"RSSI -\d+ dBm · SNR [+-]\d+\.\d dB", dash.txt_rssi.get_text())
          is not None, dash.txt_rssi.get_text())
    check("radio: pressure with one decimal", re.match(r"^\d+\.\d$", vals[3]) is not None
          and subs[3].endswith("radio: 0.1 hPa"), f"{vals[3]} {subs[3]}")
    check("radio: peak g note", dash.txt_shock.get_text() == "peak g: not in radio packet")
    check("radio: last minute", re.match(r"last minute \d+/\d+ \(\d+ %\)", dash.txt_link.get_text()) is not None,
          dash.txt_link.get_text())
    check("radio: vibration bands arrive", subs[4].startswith("slow") and dash.mesh_vib is not None, subs[4])
    run_to(dash, 190)
    lost_in_file = 206 - n_file
    check("radio: lost packets counted", 1 <= dash.pkt_lost <= lost_in_file and len(dash.lost_t) == dash.pkt_lost,
          f"{dash.pkt_lost} of {lost_in_file}")
    check("radio: flight time without peak g", dash.txt_landed.get_text() == "LANDED · flight time 02:06",
          dash.txt_landed.get_text())
    dash = dash_for(replay=d["radio13"])
    run_to(dash, 130)
    check("old radio packet: notes instead of bands",
          dash.txt_band_note.get_text() == "bands not in radio packet"
          and dash.txt_strip_note.get_text().startswith("no band data") and kpi(dash)[0][4] == "—")


def test_bench(d):
    """A test on the table: shaking, a shock, the stairs."""
    dash = dash_for(replay=d["bench"])
    run_to(dash, 34)
    check("bench: no shock yet", "none yet" in dash.txt_shock.get_text())
    run_to(dash, 37)
    check("bench: the shock is found", re.match(r"largest shock \d\.\d g at 00:3\d", dash.txt_shock.get_text())
          is not None, dash.txt_shock.get_text())
    run_to(dash, 110)
    vals, subs = kpi(dash)
    check("bench: stays a ground test", dash.detector.phase == "PRELAUNCH" and "zoomed in" in dash.txt_alt_zoom.get_text())
    check("bench: the stairs show", 5.0 < float(vals[0]) < 7.0 and subs[0].startswith("highest: 6."), f"{vals[0]} {subs[0]}")
    check("bench: every band saw the shock", bool((dash.band_max > 0.05).all()), str(dash.band_max))
    for n in (26, 27, 29):
        dash = dash_for(replay=d[f"old{n}"])
        run_to(dash, 190)
        check(f"older file with {n} columns plays to the landing", dash.detector.phase == "LANDED"
              and dash.txt_band_note.get_text() == "no band data in this file")


def test_keys(d):
    """Replay: pause, the end of the file, play again; the late start."""
    dash = dash_for(replay=d["sd"], speed=4.0)
    run(dash, 10)
    n0 = dash.pkt_rx
    check("replay at speed 4", 35 <= n0 <= 45 and "×4" in dash.txt_title.get_text(), f"rows={n0}")
    key(dash, " ")
    run(dash, 10)
    check("SPACE pauses", dash.paused and dash.pkt_rx == n0 and "paused" in dash.txt_title.get_text())
    key(dash, " ")
    run(dash, 5)
    check("SPACE again: on without a jump", n0 + 15 <= dash.pkt_rx <= n0 + 25, f"rows={dash.pkt_rx}")
    run(dash, 60)
    total = len(dash.sim.rows)
    check("the last picture stays at the end", dash.pkt_rx == total and dash.sim.finished
          and "ended" in dash.txt_title.get_text() and dash.detector.phase == "LANDED")
    run(dash, 30)
    check("... also 30 s later", len(dash.hist["t"]) == total)
    key(dash, "r")
    run(dash, 5)
    check("R plays it again", 15 <= dash.pkt_rx <= 25 and dash.detector.phase == "PRELAUNCH"
          and len(dash.hist["t"]) == dash.pkt_rx, f"rows={dash.pkt_rx}")
    for k in ("q", "l", "g", None):
        key(dash, k)
    check("other keys do nothing", not dash.paused)
    dash = dash_for(replay=d["late"])
    run(dash, 20)
    check("Teensy already on for 10 minutes: the replay starts at once", 18 <= dash.pkt_rx <= 23, f"rows={dash.pkt_rx}")


def test_restart(d):
    """The Teensy restarts in the file; a long wait on the pad."""
    dash = dash_for(replay=d["restart"])
    check("no header among the rows", all(r["millis"] > 0 for r in dash.sim.rows))
    run(dash, 30)
    check("first run plays", 28 <= dash.pkt_rx <= 33)
    run(dash, 20)
    check("after the restart a new run, in real time, without a jump in the altitude",
          8 <= dash.pkt_rx <= 12 and len(dash.hist["t"]) == dash.pkt_rx
          and -2 < min(dash.hist["alt"]) and max(dash.hist["alt"]) < 2, f"rows={dash.pkt_rx}")
    run(dash, 230)
    check("the flight after the restart", dash.detector.phase == "LANDED" and 940 < dash.apogee < 970
          and dash.txt_landed.get_text().endswith("02:07"), dash.txt_landed.get_text())
    lines = open(d["restart"], encoding="utf-8").read().splitlines(keepends=True)
    live = os.path.join(TMP, "live_restart.csv")
    with open(live, "w", encoding="utf-8", newline="") as fh:
        fh.writelines(lines[:31])
    dash = dash_for(live=live)
    run(dash, 1)
    check("live: catch-up", dash.pkt_rx == 30, f"rows={dash.pkt_rx}")
    with open(live, "a", encoding="utf-8", newline="") as fh:
        fh.writelines(lines[31:])
    run(dash, 1)
    check("live: restart and flight", dash.detector.phase == "LANDED" and dash.pkt_rx == len(lines) - 42
          and dash.pkt_lost == 0, f"rows={dash.pkt_rx} lost={dash.pkt_lost}")
    dash = dash_for(replay=d["long"])
    run(dash, 3000, step=2.0)
    cells = dash.mesh_vib.get_array().shape
    check("55 minutes on the pad: wider cells in the strip", cells[1] <= D.STRIP_MAX_BINS, str(cells))
    run(dash, 520, step=1.0)
    x0, x1 = dash.ax_alt.get_xlim()
    check("... and the charts show the flight", dash.detector.phase == "LANDED"
          and abs(dash.detector.t_launch - x0 - D.LAUNCH_LEAD_S) < 1.5 and x1 - x0 < 260, f"window {x1 - x0:.0f} s")


def test_live(d):
    """Live: the data stop coming in and come back."""
    lines = open(d["radio"], encoding="utf-8").read().splitlines(keepends=True)
    live = os.path.join(TMP, "live.csv")
    with open(live, "w", encoding="utf-8", newline="") as fh:
        fh.write(lines[0])
    real_time = D.time.time
    D.time.time = lambda: CLOCK[0] + 5e8
    os.utime(live, (CLOCK[0] + 5e8, CLOCK[0] + 5e8))
    try:
        dash = dash_for(live=live)

        def tick(seconds=0.1):
            CLOCK[0] += seconds
            dash.update(0)
            return dash._refresh_link() or dash._changed

        tick()
        check("live: waiting for the first row", dash.txt_rssi.get_text() == "waiting for data…")
        tick(12)
        check("live: no row for 12 s", dash.txt_rssi.get_text() == "No signal for 12 s" and dash.txt_warn.get_visible())
        for i in range(100):
            with open(live, "a", encoding="utf-8", newline="") as fh:
                fh.write(lines[1 + i])
            tick(1.0)
        check("live: data come in", dash.txt_dot.get_color() == D.C["green"] and dash.txt_rssi.get_text().startswith("RSSI")
              and not dash.txt_warn.get_visible() and "LIVE: radio" in dash.txt_title.get_text(), dash.txt_title.get_text())
        redraws = sum(bool(tick(0.1)) for _ in range(40))
        check("live: amber after 3 s", dash.txt_dot.get_color() == D.C["amber"]
              and dash.txt_rssi.get_text().startswith("No data for"), dash.txt_rssi.get_text())
        check("live: few redraws while waiting", redraws <= 3, str(redraws))
        redraws = sum(bool(tick(0.1)) for _ in range(110))
        check("live: red after 10 s, with the warning", dash.txt_dot.get_color() == D.C["red"]
              and dash.txt_rssi.get_text().startswith("No signal for") and dash.txt_warn.get_visible()
              and "NO SIGNAL" in dash.txt_warn.get_text(), dash.txt_rssi.get_text())
        check("live: one redraw per second while the signal is lost", redraws <= 12, str(redraws))
        tick(100)
        check("live: minutes in the warning", "1 min" in dash.txt_rssi.get_text(), dash.txt_rssi.get_text())
        with open(live, "a", encoding="utf-8", newline="") as fh:
            fh.write(lines[101])
        tick(1.0)
        check("live: back to green", dash.txt_dot.get_color() == D.C["green"] and not dash.txt_warn.get_visible())
        key(dash, " ")
        check("live: no pause", not dash.paused)
    finally:
        D.time.time = real_time


def test_sim_and_screen2(d):
    """The simulator, and screen 2 with the code it shares with screen 1."""
    random.seed(5)
    dash = dash_for(sim=True)
    run(dash, 70)
    check("simulator: flies and is recognised", dash.detector.phase in ("DESCENT", "LANDED")
          and dash.txt_truth.get_text().startswith("sim truth:") and dash.apogee > 400, dash.txt_truth.get_text())
    check("patterns", [D.vibration_pattern(b) for b in ((0.001,) * 5, (0.05, 0, 0, 0, 0), (0, 0.05, 0, 0, 0),
                                                         (0, 0, 0, 0.3, 0.1), (0.1,) * 5, (float("nan"),) * 5)]
          == [0, 1, 2, 3, 4, None])
    import dashboard_scherm2 as D2
    D.plt.close("all")
    D.apply_args(argparse.Namespace(replay=d["sd"], live=None, sim=False, speed=1.0, sea_level=None))
    dash2 = D2.Dashboard2()
    for _ in range(410):
        CLOCK[0] += 0.5
        dash2.update(0)
    check("screen 2: the same flight time", dash2.txt_kpi[1].get_text() == "02:07" and dash2.detector.phase == "LANDED",
          dash2.txt_kpi[1].get_text())


TESTS = {"flight": test_flight, "radio": test_radio, "bench": test_bench, "keys": test_keys,
         "restart": test_restart, "live": test_live, "sim": test_sim_and_screen2}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(TESTS)
    data = make_data()
    for name in wanted:
        print(f"── {name}: {TESTS[name].__doc__.strip().splitlines()[0]}")
        TESTS[name](data)
    print(f"\n{'FAILED: ' + ', '.join(FAILS) if FAILS else 'all tests passed'}")
    sys.exit(1 if FAILS else 0)
