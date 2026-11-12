"""Maakt de beelden voor de handleiding van de antennetest (niet nodig voor
de leerlingen).

  python maak_beelden.py <pad naar antennetest/> <repository>

Schrijft in antennetest/beelden/:
  overzicht.png          de opstelling: één ontvanger, drie schermen
  aansluiten_teensy.png  RFM95W op de Teensy 4.1        (zoals de ultieme test)
  aansluiten_pico.png    RFM95W op de Raspberry Pi Pico (zoals de ultieme test)
  afstandstest.png       de plaatsen voor de test op 100 m
  dashboard1_radio.png   scherm 1 met radiogegevens
  dashboard2_radio.png   scherm 2 met radiogegevens
  livestream_radio.png   het streamdashboard met radiogegevens (oefenvlucht)
"""
import importlib.util
import os
import random
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1])
REPO = os.path.abspath(sys.argv[2])
CANSAT = os.path.join(REPO, "cansat")

# de tekeningen van de ultieme test, maar nu naar antennetest/beelden
sys.argv = [sys.argv[0], ROOT, CANSAT]
_spec = importlib.util.spec_from_file_location(
    "ultieme_beelden", os.path.join(REPO, "ultieme_test_bron", "maak_beelden.py"))
U = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(U)

from matplotlib.patches import Arc, FancyBboxPatch  # noqa: E402  (na U: Agg)

plt = U.plt
INK, MUTED, LINE, BOX, ACCENT = U.INK, U.MUTED, U.LINE, U.BOX, U.ACCENT


def small(ax, x, y, w, h, title, sub, fc="white", ec=LINE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=9.5,
            fontweight="bold", color=INK)
    ax.text(x + w / 2, y + 1.3, sub, ha="center", va="bottom", fontsize=7.5,
            color=MUTED)


def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.4):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw))


# ── 1. Overzicht: één ontvanger, één bestand, drie schermen ──────────
def overview():
    fig, ax = U.canvas(11, 5.4)
    # de zender
    U.box(ax, 1.5, 6, 25, 40, "Team Breadboard", "de zender (de CanSat)")
    for i, t in enumerate(["Teensy 4.1 + sensoren", "RFM95W + antenne 8 cm",
                           "stroom: netbook", "of powerbank"]):
        ax.text(14, 32 - i * 5, t, ha="center", fontsize=9.5, color=INK)
    # de radio
    for i in range(3):
        ax.add_patch(Arc((29, 26), 4 + 4 * i, 8 + 6 * i, theta1=-50, theta2=50,
                         color=ACCENT, lw=2))
    arrow(ax, 33, 26, 41, 26, color=ACCENT, lw=2)
    ax.text(36.5, 38.5, "LoRa-radio\n868 MHz", ha="center", fontsize=9.5,
            fontweight="bold", color=ACCENT)
    ax.text(37.5, 19.5, "1 pakket\nper seconde", ha="center", va="top",
            fontsize=8, color=MUTED)
    # het grondstation: één laptop
    U.box(ax, 42, 2, 56.5, 44, "Team Grondstation", "één Windows-laptop")
    small(ax, 44, 21, 12, 10, "Pico", "ontvanger\nmain.py", fc="#eef4fc", ec=ACCENT)
    arrow(ax, 56.4, 26, 59.4, 26)
    ax.text(57.9, 27.3, "USB", ha="center", fontsize=7, color=MUTED)
    small(ax, 59.6, 21, 15, 10, "start_meting", "de logger: de enige\ndie de Pico leest")
    arrow(ax, 74.8, 26, 77.6, 26)
    small(ax, 77.8, 21, 18.5, 10, "metingen\\naam.csv", "het bestand met\nalle pakketten")
    # drie schermen lezen mee uit het bestand
    for x, title, sub in ((45.5, "scherm 1", "grafieken"),
                          (62.5, "scherm 2", "3D, kaart, radio"),
                          (79.5, "livestream", "grote cijfers")):
        small(ax, x, 5, 15, 9.5, title, sub, fc=BOX)
        arrow(ax, 87, 20.6, x + 7.5, 14.8)
    ax.text(70.3, 17.6, "de drie schermen lezen mee uit het bestand",
            ha="center", fontsize=8, color=MUTED,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    U.save(fig, "overzicht.png")


# ── 2. Het streamdashboard met radiogegevens (de oefenvlucht) ────────
def livestream():
    sys.path.insert(0, os.path.join(REPO, "livestream", "stream"))
    sys.path.insert(0, os.path.join(CANSAT, "tools"))
    import stream_dashboard as sd
    import gen_test_csv as g
    import serial_logger as sl
    rng = random.Random(7)
    rows = []
    for t, regel in g.vlucht_regels(rng):           # zoals via de radio
        rssi, snr, lost = g.vlucht_radio(t, regel, rng)
        if not lost:
            parts = g.radio_packet(regel, t, opwarmen=False) + [str(rssi), f"{snr:.1f}"]
            millis = int(regel.split(",", 1)[0]) - 5212 + 2380
            rows.append((t, sl.radio_row(parts, millis)))
    dash = sd.StreamDashboard()
    for t, row in rows:
        if t > 100:                                  # in de daling, aan de parachute
            break
        cols = {k: row.get(k, "nan") for k in sl.COLUMNS}
        dash.q.put(("row", cols, float(t)))
        dash.tick(now=t + 0.2)
    path = os.path.join(U.OUT, "livestream_radio.png")
    dash.fig.savefig(path, facecolor=sd.C["page"])
    plt.close("all")
    print("geschreven:", path)


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)                       # de dashboards schrijven niets in de repo
    overview()
    U.teensy_drawing()
    U.pico_drawing()
    U.field()
    U.dashboards()
    livestream()
