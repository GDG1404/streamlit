"""Draws the flowcharts of the flight code (for the report, in English).

  python maak_flowchart.py [output folder]

Writes, as PNG (300 dpi) and as PDF:
  flight_code_flowchart   start-up and main loop of Cansat2027_teensy.ino
  flight_code_states      the three states of the flight
The text that goes with them is in FLOWCHART.md.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

INK, MUTED, LINE = "#1b1b1a", "#5d5c58", "#8b8a84"
GREY_F, GREY_E = "#f3f2ee", "#b9b8b0"           # start-up, radio, SD card
BLUE_F, BLUE_E = "#e9f1fc", "#2a78d6"           # measuring
GREEN_F, GREEN_E = "#e8f5ea", "#2e8b46"         # once per second: store and send
ORANGE_F, ORANGE_E = "#fdeee6", "#d9571c"       # after the flight


def canvas(w, h, units_w=100):
    fig = plt.figure(figsize=(w, h), dpi=300, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, units_w)
    ax.set_ylim(0, units_w * h / w)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, title, lines=(), fc=GREY_F, ec=GREY_E, size=8.6, title_size=None,
        align="center", round_=0.6):
    """A process box: a bold title and lines of text under it."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}",
                                fc=fc, ec=ec, lw=1.3, zorder=2))
    step = size * 0.24                       # line distance in drawing units
    n = len(lines)
    top = y + h / 2 + (n * step) / 2         # the block of text is centred
    tx = x + w / 2 if align == "center" else x + 1.6
    ax.text(tx, top, title, ha=align, va="center", fontsize=title_size or size,
            fontweight="bold", color=INK, zorder=3)
    for i, line in enumerate(lines, 1):
        ax.text(tx, top - i * step, line, ha=align, va="center", fontsize=size - 0.6,
                color=INK, zorder=3)


def diamond(ax, cx, cy, hw, hh, text, size=8.6):
    ax.add_patch(Polygon([(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx, cy - hh)],
                         closed=True, fc="white", ec=INK, lw=1.3, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=size, fontweight="bold",
            color=INK, zorder=3)


def arrow(ax, points, color=INK, lw=1.3):
    """A line through the points with an arrow head at the end."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    if len(points) > 2:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, solid_capstyle="round",
                solid_joinstyle="round", zorder=1)
    ax.annotate("", xy=points[-1], xytext=points[-2],
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=11,
                                shrinkA=0, shrinkB=0), zorder=1)


def tag(ax, x, y, text, color=INK):
    ax.text(x, y, text, ha="center", va="center", fontsize=7.8, fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), zorder=4)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        path = os.path.join(OUT, f"{name}.{ext}")
        fig.savefig(path, facecolor="white")
        print("written:", path)
    plt.close(fig)


# ── 1. Start-up and main loop ────────────────────────────────────────
def flowchart():
    fig, ax = canvas(8.27, 11.2)                      # fits on A4; 100 x 135.4 units
    T = -5.8                                          # everything this much lower than first drawn
    cx = 33                                           # the main column
    x0, w = 8, 50                                     # its boxes
    rx, rw = 66, 29                                   # the boxes on the right
    rc = rx + rw / 2
    GAP, HH, HW = 2.7, 4.8, 16                        # between two shapes; half a diamond

    ax.text(4, 136.4 + T, "Flight software of the CanSat", fontsize=16, fontweight="bold",
            color=INK, va="center")
    ax.text(4, 132.6 + T, "Teensy 4.1 · Cansat2027_teensy.ino · version 2026-11-12",
            fontsize=9, color=MUTED, va="center")

    # legend
    for i, (fc, ec, text) in enumerate(((BLUE_F, BLUE_E, "measuring"),
                                        (GREEN_F, GREEN_E, "storing and sending"),
                                        (ORANGE_F, ORANGE_E, "after the flight"))):
        y = 125.6 + T - i * 3.6
        ax.add_patch(FancyBboxPatch((rx + 1, y - 1.1), 3.6, 2.2, boxstyle="round,pad=0,rounding_size=0.4",
                                    fc=fc, ec=ec, lw=1.2))
        ax.text(rx + 6.2, y, text, fontsize=8.4, color=INK, va="center")
    ax.add_patch(Polygon([(rx + 1, 114.8 + T), (rx + 2.8, 116.1 + T), (rx + 4.6, 114.8 + T), (rx + 2.8, 113.5 + T)],
                         closed=True, fc="white", ec=INK, lw=1.2))
    ax.text(rx + 6.2, 114.8 + T, "question: yes or no", fontsize=8.4, color=INK, va="center")

    y = 128.4 + T                                     # the cursor: top of the next shape

    def step_box(h, title, lines, fc=GREY_F, ec=GREY_E, **kw):
        nonlocal y
        box(ax, x0, y - h, w, h, title, lines, fc=fc, ec=ec, size=8.4, **kw)
        y -= h
        return y + h / 2                              # the middle of the box

    def down(gap=GAP):
        nonlocal y
        arrow(ax, [(cx, y), (cx, y - gap)])
        y -= gap

    def question(text):
        nonlocal y
        cy = y - HH
        diamond(ax, cx, cy, HW, HH, text)
        arrow(ax, [(cx + HW, cy), (rx, cy)])
        tag(ax, cx + HW + 8.5, cy, "yes")
        y -= 2 * HH
        return cy

    # power on and start-up
    box(ax, cx - 11, y - 4.4, 22, 4.4, "Power on", round_=2.2, size=9.2)
    y -= 4.4
    down()
    step_box(14.6, "START-UP · once", [
        "Start the sensors, the GPS, the radio and the SD card (new file).",
        "Set the sensor bus (I2C) to 400 kHz and check the sensors answer.",
        "Switch on the memory (FIFO) of the LSM6DSO and check it.",
        "3 short beeps: ready.  3 long beeps: one part failed,",
        "the others keep working.",
    ], title_size=9.2)
    frame_top = y - 2.2
    down(7.6)
    y_entry = y + 1.6                                 # where arrows come back into the loop

    # the frame of the main loop
    frame = FancyBboxPatch((2.2, 0), 95.6, frame_top, boxstyle="round,pad=0,rounding_size=1.5",
                           fc="none", ec=LINE, lw=1.1, ls=(0, (5, 4)), zorder=0)
    ax.add_patch(frame)
    ax.text(cx + 1.4, frame_top - 2.0, "MAIN LOOP · thousands of times per second, it never waits",
            fontsize=8.6, fontweight="bold", color=MUTED, va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"), zorder=4)

    y_radio = step_box(6.4, "Radio", ["Is the last packet sent? Then free the radio."])
    down()
    step_box(6.4, "GPS", ["Read the characters that came in."], fc=BLUE_F, ec=BLUE_E)
    down()

    # is the flight over?
    cy = question("Is the flight over?")
    box(ax, rx, cy - 6.6, rw, 13.2, "AFTER THE FLIGHT", [
        "Buzzer: 3 s on, 7 s off.",
        "The BMP390 keeps measuring:",
        "a launch after all? Then a",
        "new measurement starts.",
    ], fc=ORANGE_F, ec=ORANGE_E, size=8.4)
    arrow(ax, [(rc, cy + 6.6), (rc, y_entry), (cx, y_entry)], color=ORANGE_E)
    tag(ax, cx + 2.8, y - 1.3, "no")
    down()

    # vibrations
    step_box(8.6, "Vibrations · every 5 ms", [
        "Fetch the new samples from the LSM6DSO (X, Y and Z,",
        "about 417 per second). Keep the largest acceleration (g).",
    ], fc=BLUE_F, ec=BLUE_E)
    down()
    cy = question("512 samples?")
    box(ax, rx, cy - 5.6, rw, 11.2, "FFT of X, Y and Z", [
        "The strongest frequency",
        "and its strength, and the",
        "vibration in 5 bands.",
    ], fc=BLUE_F, ec=BLUE_E, size=8.4)
    tag(ax, cx + 2.8, y - 1.1, "no")
    arrow(ax, [(rc, cy - 5.6), (rc, y - 2.5), (cx, y - 2.5)], color=BLUE_E)
    down(4.0)

    # the other sensors
    step_box(10.6, "The other sensors", [
        "Every 50 ms: BMP390 → pressure, temperature, altitude.",
        "Every 100 ms: BNO055 → orientation.",
        "Always: microphone → sound level.",
    ], fc=BLUE_F, ec=BLUE_E)
    down()

    # once per second
    cy = question("1 second passed?")
    box(ax, rx, cy - 6.9, rw, 13.8, "ONCE PER SECOND", [
        "GPS: position (fresh fix?).",
        "Flight state: launch?",
        "landed? (see figure 2)",
        "SD card: 1 line, 34 values.",
        "Radio: 1 packet, 19 values.",
    ], fc=GREEN_F, ec=GREEN_E, size=8.4)
    tag(ax, cx + 2.8, y - 1.1, "no")
    arrow(ax, [(rc, cy - 6.9), (rc, y - 3.4), (cx, y - 3.4)], color=GREEN_E)
    down(5.0)

    # save the file, and back to the start
    y_sd = step_box(6.4, "SD card · every 0.5 s", ["Save the file, so nothing is lost."],
                    fc=GREEN_F, ec=GREEN_E)
    arrow(ax, [(x0, y_sd), (4.8, y_sd), (4.8, y_radio), (x0, y_radio)])
    ax.text(3.5, (y_sd + y_radio) / 2, "again", rotation=90, fontsize=8.2, color=MUTED,
            ha="center", va="center")
    frame.set_bounds(2.2, y - 2.4, 95.6, frame_top - (y - 2.4))
    assert y - 2.4 > 0.8, "the chart does not fit on the page"
    save(fig, "flight_code_flowchart")


# ── 2. The states of the flight ──────────────────────────────────────
def states():
    fig, ax = canvas(11.0, 4.9)                       # 100 x 44.5 units
    ax.text(3, 41.4, "The three states of the flight", fontsize=15, fontweight="bold", color=INK,
            va="center")
    ax.text(3, 38.2, "Checked once per second, with the altitude of the BMP390",
            fontsize=9, color=MUTED, va="center")
    y, h, w = 9.5, 15.5, 26
    xs = (3, 37, 71)
    box(ax, xs[0], y, w, h, "1 · WAITING", [
        "on the ground and in the rocket",
        "",
        "Measures everything.",
        "Writes to the SD card.",
        "Sends by radio.",
        "Buzzer silent.",
    ], fc=GREY_F, ec=GREY_E, size=8.8, title_size=10.5)
    box(ax, xs[1], y, w, h, "2 · FLIGHT", [
        "from the launch to the landing",
        "",
        "Measures everything.",
        "Writes to the SD card.",
        "Sends by radio.",
        "Buzzer silent: the microphone measures.",
    ], fc=BLUE_F, ec=BLUE_E, size=8.8, title_size=10.5)
    box(ax, xs[2], y, w, h, "3 · AFTER THE FLIGHT", [
        "the CanSat lies on the ground",
        "",
        "The file on the SD card is closed.",
        "The radio is off.",
        "Buzzer: 3 s on, 7 s off.",
        "The BMP390 keeps measuring.",
    ], fc=ORANGE_F, ec=ORANGE_E, size=8.8, title_size=10.5)
    mid = y + h / 2
    arrow(ax, [(xs[0] + w, mid), (xs[1], mid)], lw=1.6)
    arrow(ax, [(xs[1] + w, mid), (xs[2], mid)], lw=1.6)
    # the conditions, above the arrows
    for x, title, lines in (
            (xs[0] + w + 4, "LAUNCH", ["50 m higher than", "5 seconds earlier,", "3 seconds in a row"]),
            (xs[1] + w + 4, "END", ["6 minutes after the", "launch AND the altitude", "steady for 10 s",
                                    "(at the latest: 30 min)"])):
        ax.text(x, 34.6, title, ha="center", va="center", fontsize=9, fontweight="bold", color=INK)
        for i, line in enumerate(lines):
            ax.text(x, 32.3 - i * 2.05, line, ha="center", va="center", fontsize=8, color=INK)
        ax.plot([x, x], [mid + 0.9, 32.3 - len(lines) * 2.05 + 0.9], color=LINE, lw=0.9, ls=(0, (2, 2)))
    # back from 3 to 2
    arrow(ax, [(xs[2] + w / 2, y), (xs[2] + w / 2, 4.6), (xs[1] + w / 2, 4.6), (xs[1] + w / 2, y)],
          color=ORANGE_E, lw=1.4)
    ax.text((xs[1] + xs[2] + w) / 2, 2.4,
            "a launch after all (the first one was false)?  →  a new file, everything on again",
            ha="center", va="center", fontsize=8.4, color=INK)
    save(fig, "flight_code_states")


if __name__ == "__main__":
    flowchart()
    states()
