"""Maakt de beelden voor de handleiding van de ultieme test (niet nodig voor
de leerlingen).

  python maak_beelden.py <pad naar ultieme_test/> <pad naar cansat/>

Schrijft in ultieme_test/beelden/:
  overzicht.png          de opstelling: zender, radio, ontvanger, laptop
  aansluiten_teensy.png  RFM95W op de Teensy 4.1 (breadboard)
  aansluiten_pico.png    RFM95W op de Raspberry Pi Pico (ontvanger)
  afstandstest.png       de plaatsen voor de test op 100 m
  dashboard1_radio.png   scherm 1 met radiogegevens (13 inch laptop)
  dashboard2_radio.png   scherm 2 met radiogegevens
"""
import os
import random
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
matplotlib.use = lambda *a, **k: None          # de dashboards vragen TkAgg
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

ROOT = os.path.abspath(sys.argv[1])
CANSAT = os.path.abspath(sys.argv[2])
OUT = os.path.join(ROOT, "beelden")

INK, MUTED, LINE, BOX = "#1b1b1a", "#5d5c58", "#c9c8c0", "#f3f2ee"
ACCENT = "#2a78d6"
# draadkleuren: elke draad heeft ook altijd een naam (niet enkel kleur)
WIRE = {"3.3V": "#d62728", "GND": "#1b1b1a", "SCK": "#d99a00",
        "MISO": "#1f77b4", "MOSI": "#2ca02c", "CS": "#ff7f0e",
        "RST": "#9467bd", "G0": "#8c564b"}


def canvas(w, h, units_w=100):
    """Figuur van w x h inch; tekencoördinaten 0..units_w breed."""
    fig = plt.figure(figsize=(w, h), dpi=150, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, units_w)
    ax.set_ylim(0, units_w * h / w)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, title, sub=None, fc=BOX, ec=LINE, size=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                                fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top",
            fontsize=size, fontweight="bold", color=INK)
    if sub:
        ax.text(x + w / 2, y + h - 5.0, sub, ha="center", va="top",
                fontsize=size - 3, color=MUTED)


def label(ax, x, y, text, color=INK, size=8, ha="center", weight="normal"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=color,
            fontweight=weight,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("geschreven:", path)


# ── RFM95W-bordje (rechts op de aansluitschema's) ─────────────────────
RFM_PINS = [("3.3V", "VIN  of  3.3V"), ("GND", "GND"), ("SCK", "SCK"),
            ("MISO", "MISO"), ("MOSI", "MOSI"), ("CS", "CS  of  NSS"),
            ("RST", "RST  of  RESET"), ("G0", "G0  of  DIO0")]


def rfm_board(ax, x, y0, dy, with_g0=True):
    """Tekent het radiobordje; geeft de y van elke pin terug."""
    n = len(RFM_PINS)
    top = y0 + (n - 1) * dy
    box(ax, x, y0 - 4, 26, top - y0 + 12, "RFM95W", "radiomodule, 868 MHz",
        fc="#eef4fc", ec=ACCENT)
    ys = {}
    for i, (key, text) in enumerate(RFM_PINS):
        y = top - i * dy
        ys[key] = y
        faded = key == "G0" and not with_g0
        ax.plot([x], [y], "o", ms=7, color=LINE if faded else WIRE[key],
                mec=INK, mew=0.6, zorder=5)
        ax.text(x + 2, y, text, va="center", fontsize=9,
                color=MUTED if faded else INK)
    # antenne: draadje van 8 cm aan ANT, recht omhoog
    ant_x, pad_y = x + 24, top + 6.5
    ax.plot([ant_x, ant_x], [pad_y, pad_y + 11], color="#b08d57", lw=2.5)
    ax.plot([ant_x], [pad_y], "s", ms=6, color="#b08d57", mec=INK, mew=0.6,
            zorder=6)
    ax.text(ant_x - 1.2, pad_y - 1.8, "ANT", ha="right", va="center",
            fontsize=8, color=INK)
    label(ax, ant_x - 1.5, pad_y + 8, "antenne: draadje van 8 cm,\nrecht omhoog",
          size=8, ha="right")
    return ys


def wire(ax, x1, y1, x2, y2, key, xmid=None, name_at=None):
    """Draad in drie rechte stukken (zoals op een breadboard)."""
    xm = (x1 + x2) / 2 if xmid is None else xmid
    ax.plot([x1, xm, xm, x2], [y1, y1, y2, y2], color=WIRE[key], lw=2.4,
            solid_capstyle="round", zorder=3)
    ax.plot([x1], [y1], "o", ms=7, color=WIRE[key], mec=INK, mew=0.6, zorder=5)
    if name_at is not None:
        label(ax, name_at, y1, key, color=WIRE[key], size=7.5, weight="bold")


# ── 1. Teensy 4.1 + RFM95W ───────────────────────────────────────────
def teensy_drawing():
    fig, ax = canvas(10, 7.0)
    teensy = [("3.3V", "3.3V"), ("GND", "GND"), ("SCK", "pin 13"),
              ("MISO", "pin 12"), ("MOSI", "pin 11"), ("CS", "pin 10"),
              ("RST", "pin 9"), ("G0", "pin 2")]
    dy, y0 = 5.0, 10.0
    top = y0 + (len(teensy) - 1) * dy
    box(ax, 6, y0 - 4, 24, top - y0 + 12, "Teensy 4.1",
        "op het breadboard")
    ys_rfm = rfm_board(ax, 66, y0, dy)
    for i, (key, text) in enumerate(teensy):
        y = top - i * dy
        ax.text(28, y, text, ha="right", va="center", fontsize=9.5,
                fontweight="bold", color=INK)
        wire(ax, 30, y, 66, ys_rfm[key], key, xmid=48, name_at=39)
    ax.text(50, 66, "De radio op de Teensy 4.1 (zoals in de vluchtcode)",
            ha="center", fontsize=13, fontweight="bold", color=INK)
    notes = ("Alles op 3,3 V.  Pin 13 is ook het lampje van de Teensy: dat flikkert tijdens het zenden (normaal).\n"
             "Nooit zenden zonder antenne: dat kan de radio beschadigen.  "
             "De pinnen 0, 1, 8, 18-21 (sensoren) blijven zoals ze zijn.")
    ax.text(50, 2.2, notes, ha="center", va="bottom", fontsize=8, color=MUTED)
    save(fig, "aansluiten_teensy.png")


# ── 2. Raspberry Pi Pico + RFM95W ────────────────────────────────────
PICO_LEFT = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6",
             "GP7", "GP8", "GP9", "GND", "GP10", "GP11", "GP12", "GP13", "GND",
             "GP14", "GP15"]                               # pootjes 1..20
PICO_RIGHT = ["GP16", "GP17", "GND", "GP18", "GP19", "GP20", "GP21", "GND",
              "GP22", "RUN", "GP26", "GP27", "GND", "GP28", "ADC_VREF",
              "3V3(OUT)", "3V3_EN", "GND", "VSYS", "VBUS"]  # pootjes 21..40
PICO_USED = {36: "3.3V", 38: "GND", 24: "SCK", 21: "MISO", 25: "MOSI",
             22: "CS", 26: "RST"}


def pico_drawing():
    fig, ax = canvas(10, 7.8)
    x0, x1, ytop, ybot = 14, 34, 64, 8
    pitch = (ytop - ybot) / 20.5
    ax.add_patch(Rectangle((x0, ybot - 1), x1 - x0, ytop - ybot + 3,
                           fc="#2f6b3a", ec=INK, lw=1.2))
    ax.add_patch(Rectangle(((x0 + x1) / 2 - 3, ytop + 1.2), 6, 2.6,
                           fc="#c0c0c0", ec=INK, lw=1))          # USB
    ax.text((x0 + x1) / 2, ytop + 5, "USB", ha="center", fontsize=8, color=MUTED)
    ax.text((x0 + x1) / 2, (ytop + ybot) / 2, "Raspberry\nPi Pico", ha="center",
            va="center", fontsize=11, fontweight="bold", color="white",
            rotation=90)

    def ypin(n):            # pootje 1 linksboven, 20 linksonder, 21 rechtsonder
        i = n - 1 if n <= 20 else 40 - n
        return ytop - 0.5 - i * pitch

    for n in range(1, 41):
        left = n <= 20
        name = PICO_LEFT[n - 1] if left else PICO_RIGHT[n - 21]
        x = x0 if left else x1
        used = n in PICO_USED
        col = WIRE[PICO_USED[n]] if used else "#d8d8d8"
        ax.plot([x], [ypin(n)], "o", ms=5.5 if used else 4, color=col,
                mec=INK, mew=0.5, zorder=5)
        # gebruikte pootjes: naam en nummer binnen op het bordje (buiten
        # loopt de draad)
        ax.text(x + (1.2 if left else -1.2), ypin(n),
                f"{name} · {n}" if used else name,
                ha="left" if left else "right", va="center",
                fontsize=6.4 if used else 5.6,
                color="white" if used else "#cfe3d2",
                fontweight="bold" if used else "normal")
        if not used:
            ax.text(x - 1.4 if left else x + 1.4, ypin(n), str(n),
                    ha="right" if left else "left", va="center", fontsize=6,
                    color=MUTED)

    dy, y0 = 5.0, 16.0
    ys_rfm = rfm_board(ax, 68, y0, dy, with_g0=False)
    lanes = {"3.3V": 52, "GND": 55, "SCK": 46, "MISO": 40, "MOSI": 49,
             "CS": 43, "RST": 58}
    for n, key in PICO_USED.items():
        wire(ax, x1, ypin(n), 68, ys_rfm[key], key, xmid=lanes[key])
    ax.text(68 + 2, ys_rfm["G0"] - 3.2, "(G0 / DIO0: niet nodig)", fontsize=8,
            color=MUTED)
    ax.text(50, 75, "De radio op de Raspberry Pi Pico (standaardpinnen van main.py)",
            ha="center", fontsize=13, fontweight="bold", color=INK)
    ax.text(50, 1.0, "Zit jullie radio al op andere pinnen? Laat de draden zitten en "
            "pas bovenaan main.py de pinnummers aan (zie de handleiding).",
            ha="center", va="bottom", fontsize=8, color=MUTED)
    save(fig, "aansluiten_pico.png")


# ── 3. Overzicht van de opstelling ───────────────────────────────────
def overview():
    fig, ax = canvas(11, 4.6)
    box(ax, 2, 6, 30, 33, "Team Breadboard", "de zender (CanSat)")
    for i, t in enumerate(["Teensy 4.1 + sensoren", "RFM95W + antenne 8 cm",
                           "stroom via USB: netbook", "of powerbank"]):
        ax.text(17, 26 - i * 4.4, t, ha="center", fontsize=9.5, color=INK)
    box(ax, 66, 6, 32, 33, "Team Ontvanger", "het grondstation")
    for i, t in enumerate(["RFM95W + Pico (main.py)", "USB → Windows-laptop",
                           "start_meting.py", "dashboard 1 en 2"]):
        ax.text(82, 26 - i * 4.4, t, ha="center", fontsize=9.5, color=INK)
    for i in range(3):                         # radiogolven
        ax.add_patch(matplotlib.patches.Arc((35, 22.5), 4 + 4 * i, 8 + 6 * i,
                                            theta1=-50, theta2=50, color=ACCENT,
                                            lw=2))
    ax.annotate("", xy=(64, 22.5), xytext=(40, 22.5),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=2))
    ax.text(51, 33, "LoRa-radio, 868 MHz", ha="center", fontsize=10,
            fontweight="bold", color=ACCENT)
    ax.text(51, 17.5, "1 pakket per seconde\n(19 meetwaarden, met de FFT)",
            ha="center", va="top", fontsize=8.5, color=MUTED)
    ax.annotate("", xy=(64, 3.5), xytext=(34, 3.5),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.2))
    ax.text(49, 1.0, "10 m → 50 m → 100 m", ha="center", fontsize=9, color=MUTED)
    save(fig, "overzicht.png")


# ── 4. De afstandstest ────────────────────────────────────────────────
def field():
    fig, ax = canvas(11, 3.3)
    y = 17
    ax.plot([8, 92], [y, y], color=LINE, lw=6, solid_capstyle="round")
    ax.text(50, y + 8.5, "rechte lijn met vrij zicht (bv. een speelplaats of sportveld)",
            ha="center", fontsize=9, color=MUTED)
    ax.plot([8], [y], "s", ms=14, color=ACCENT)
    ax.text(8, y - 6, "0 m\nTeam Ontvanger\n(tafel, laptop, Pico)", ha="center",
            va="top", fontsize=8.5, color=INK)
    for d in (10, 50, 100):
        x = 8 + 0.84 * d
        ax.plot([x], [y], "v", ms=12, color="#d62728")
        ax.text(x, y + 4, f"{d} m", ha="center", fontsize=10, fontweight="bold",
                color=INK)
        ax.text(x, y - 5, "1 minuut\nblijven staan", ha="center", va="top",
                fontsize=8, color=MUTED)
    ax.add_patch(Rectangle((60, 2), 12, 7, fc="#e3e2dc", ec=MUTED))
    ax.text(66, 5.5, "gebouw", ha="center", va="center", fontsize=8, color=MUTED)
    ax.text(74, 5.5, "← extra: ook eens achter\n   een gebouw testen", va="center",
            fontsize=8, color=MUTED)
    ax.text(50, 29.5, "Team Breadboard stapt van punt naar punt, Team Ontvanger blijft bij 0 m",
            ha="center", fontsize=10.5, fontweight="bold", color=INK)
    save(fig, "afstandstest.png")


# ── 5. Schermafbeeldingen van de dashboards met radiogegevens ─────────
def dashboards():
    sys.path.insert(0, os.path.join(CANSAT, "dashboard"))
    sys.path.insert(0, os.path.join(CANSAT, "tools"))
    import gen_test_csv as g
    import dashboard_scherm1 as d1
    import dashboard_scherm2 as d2
    import serial_logger as sl
    random.seed(4)
    tmp = os.path.join(tempfile.mkdtemp(), "radio.csv")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:   # zoals de logger
        fh.write(sl.HEADER + "\r\n")
        t_ms = 5212
        for t in range(g.DURATION_S):
            row = g.make_row(t, t_ms)
            rssi, snr, lost = g.radio_quality(t)
            if not lost:
                parts = g.radio_packet(row, t) + [str(rssi), f"{snr:.1f}"]
                fh.write(sl.csv_line(sl.radio_row(parts, t_ms - 2832), sl.COLUMNS)
                         + "\r\n")
            t_ms += 1000
    d1.DATA_MODE, d1.LIVE_CSV, d1.REPLAY_CSV = "live", tmp, None
    for name, cls in (("dashboard1_radio.png", d1.Dashboard),
                      ("dashboard2_radio.png", d2.Dashboard2)):
        dash = cls()
        dash._wall = None
        dash.update(0)
        dash.fig.set_size_inches(13.66, 6.9)    # 13-inch laptop, venster
        dash.fit.rescale()
        dash.update(0)
        path = os.path.join(OUT, name)
        dash.fig.savefig(path, dpi=100, facecolor=dash.fig.get_facecolor())
        plt.close("all")
        print("geschreven:", path)


if __name__ == "__main__":
    overview()
    teensy_drawing()
    pico_drawing()
    field()
    dashboards()
