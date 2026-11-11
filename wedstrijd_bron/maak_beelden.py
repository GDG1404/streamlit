"""Maakt de beelden voor de handleiding van de wedstrijd (niet nodig voor de
leerlingen).

  python maak_beelden.py <pad naar wedstrijd/> <repository>

Schrijft in wedstrijd/beelden/:
  overzicht.png          de opstelling: drie ontvangers, drie laptops
  vluchtverloop.png      de hoogte tijdens de vlucht, en wanneer de buzzer piept
  aansluiten_pico.png    RFM95W op de Raspberry Pi Pico    (zoals de antennetest)
  dashboard1_radio.png   scherm 1, de oefenvlucht tijdens de daling
  dashboard2_radio.png   scherm 2, de oefenvlucht tijdens de daling
  dashboard2_geland.png  scherm 2 na de landing: waar ligt de CanSat?
  dashboard1_replay.png  scherm 1 aan het einde van een replay (de SD-kaart)
  livestream_radio.png   het streamdashboard, de oefenvlucht tijdens de daling

De schermen tonen de oefenvlucht via de radio: dezelfde vlucht als wanneer je
'oefen' typt bij START_METING. De replay toont dezelfde vlucht zoals ze op
de SD-kaart staat.
"""
import importlib.util
import os
import random
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1])
REPO = os.path.abspath(sys.argv[2])

# de tekeningen van de antennetest (en de ultieme test), nu naar wedstrijd/beelden
sys.argv = [sys.argv[0], ROOT, REPO]
_spec = importlib.util.spec_from_file_location(
    "antenne_beelden", os.path.join(REPO, "antennetest_bron", "maak_beelden.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
U = A.U

from matplotlib.patches import Arc  # noqa: E402  (na U: Agg)

plt = U.plt
INK, MUTED, LINE, BOX, ACCENT = U.INK, U.MUTED, U.LINE, U.BOX, U.ACCENT
BUZZER = "#eb6834"        # oranje, de tweede kleur naast het blauw


# ── 1. Overzicht: één CanSat, drie ontvangers, drie laptops ─────────
def overview():
    fig, ax = U.canvas(11, 6.2)
    # de zender
    U.box(ax, 1.5, 12, 25, 32, "Team CanSat", "de CanSat in de lucht")
    for i, t in enumerate(["Teensy 4.1 + sensoren", "RFM95W + antenne 8,2 cm",
                           "batterij, schakelaar, buzzer", "SD-kaart: bewaart alles"]):
        ax.text(14, 33 - i * 5, t, ha="center", fontsize=9.5, color=INK)
    for i in range(3):
        ax.add_patch(Arc((29.2, 28), 4 + 4 * i, 8 + 6 * i, theta1=-50, theta2=50,
                         color=ACCENT, lw=2))
    ax.text(33.5, 47.5, "LoRa-radio\n868 MHz", ha="center", fontsize=9.5,
            fontweight="bold", color=ACCENT)
    ax.text(33.5, 10.5, "1 pakket\nper seconde", ha="center", va="top", fontsize=8,
            color=MUTED)
    # drie laptops, elk met een eigen ontvanger
    rows = ((39.5, "Laptop 1 · Grondstation", "keuze 3",
             "scherm 1 + scherm 2", "grafieken, 3D-baan, kaart"),
            (21.5, "Laptop 2 · Livestream", "keuze 5",
             "livestream", "OBS → YouTube"),
            (3.5, "Laptop 3 · Reserve", "keuze 1, 2 of 0",
             "reservekopie", "neemt over als het moet"))
    for n, (y, title, keuze, wat, sub) in enumerate(rows, 1):
        U.box(ax, 40, y, 58.5, 15, title)
        A.small(ax, 42.5, y + 1.6, 10.5, 8.6, f"Pico {n}", "ontvanger",
                fc="#eef4fc", ec=ACCENT)
        A.arrow(ax, 53.3, y + 5.9, 55.8, y + 5.9)
        ax.text(54.55, y + 7.2, "USB", ha="center", fontsize=7, color=MUTED)
        A.small(ax, 56, y + 1.6, 15.5, 8.6, "start_meting", keuze)
        A.arrow(ax, 71.8, y + 5.9, 74.6, y + 5.9)
        A.small(ax, 74.8, y + 1.6, 21.7, 8.6, wat, sub, fc=BOX)
        A.arrow(ax, 35.6, 28, 42.2, y + 5.9, color=ACCENT, lw=1.6)
    ax.text(14, 7.5, "Elke laptop bewaart alles in\nmetingen\\naam.csv:\n"
            "drie kopieën van de vlucht", ha="center", va="top", fontsize=8,
            color=MUTED)
    U.save(fig, "overzicht.png")


# ── 2. Het verloop van de vlucht, en wanneer de buzzer piept ─────────
def vluchtverloop():
    sys.path.insert(0, os.path.join(REPO, "cansat", "tools"))
    import gen_test_csv as g
    rows = g.vlucht_regels(random.Random(7))           # de oefenvlucht
    t = [ti for ti, _ in rows]
    alt = [float(r.split(",")[3]) for _, r in rows]
    base = sum(alt[:5]) / 5
    i0 = next(i for i, a in enumerate(alt) if a - base > 1) - 1
    x = [(ti - t[i0]) / 60 for ti in t]
    h = [max(a - base, 0.0) for a in alt]
    i_top = max(range(len(h)), key=lambda i: h[i])
    i_land = next(i for i in range(i_top, len(h)) if h[i] < 2)
    x_top, x_land = x[i_top], x[i_land]
    x += [8.0]                      # daarna ligt de CanSat stil op de grond
    h += [0.0]

    fig, (ax, bz) = plt.subplots(
        2, 1, figsize=(11, 5.4), dpi=150, sharex=True, facecolor="white",
        gridspec_kw=dict(height_ratios=[5, 1.15], hspace=0.08))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.9, bottom=0.12)
    fases = ((-1.0, 0.0, "op de grond"), (0.0, x_land, "de vlucht"),
             (x_land, 6.0, "geland: de radio zendt nog"), (6.0, 8.0, "de buzzer piept"))
    for k, (a, b, naam) in enumerate(fases):
        for axis in (ax, bz):
            axis.axvspan(a, b, color=BOX if k % 2 == 0 else "white", lw=0, zorder=0)
        ax.text((a + b) / 2, 1085, naam, ha="center", va="center", fontsize=9,
                color=MUTED)
    ax.plot(x, h, color=ACCENT, lw=2, zorder=3, solid_capstyle="round")
    ax.set_ylim(-30, 1150)
    ax.set_ylabel("hoogte boven de lanceerplaats (m)", fontsize=9, color=MUTED)
    ax.set_yticks([0, 250, 500, 750, 1000])
    ax.grid(axis="y", color=LINE, lw=0.6, zorder=1)
    for axis in (ax, bz):
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(LINE)
        axis.tick_params(colors=MUTED, labelsize=8.5, length=0)
    kw = dict(fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("lancering:\n50 m hoger\nbinnen 5 s", xy=(0.02, 40), xytext=(-0.93, 330),
                ha="left", va="center", **kw)
    ax.annotate(f"hoogste punt ± {round(h[i_top], -1):.0f} m", xy=(x_top, h[i_top]),
                xytext=(1.05, 960), ha="left", va="center", **kw)
    ax.annotate(f"landing na ± {x_land:.0f} minuten", xy=(x_land, 5),
                xytext=(x_land + 0.35, 230), ha="left", **kw)
    ax.axvline(6.0, color=BUZZER, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.text(6.08, 640, "6 minuten na de lancering:\nde buzzer begint.\nDe radio en de "
            "SD-kaart\nstoppen.", ha="left", va="center", fontsize=9, color=INK)
    ax.text(-1.0, 1235, "De vlucht en de buzzer (de oefenvlucht)", ha="left",
            va="bottom", fontsize=11, fontweight="bold", color=INK)
    # de buzzer: stil tijdens de vlucht, daarna 3 s aan en 7 s uit
    bz.broken_barh([(6.0 + k / 6, 0.05) for k in range(12)], (0.25, 0.5),
                   color=BUZZER, zorder=3)
    bz.text(-0.96, 0.5, "buzzer", ha="left", va="center", fontsize=9,
            fontweight="bold", color=INK)
    bz.text(3.0, 0.5, "stil tijdens de vlucht: de microfoon meet", ha="center",
            va="center", fontsize=9, color=MUTED)
    bz.text(7.0, 1.05, "3 s aan, 7 s uit", ha="center", va="bottom", fontsize=8.5,
            color=INK)
    bz.set_ylim(0, 1.45)
    bz.set_yticks([])
    bz.set_xlim(-1.0, 8.0)
    bz.set_xticks(range(-1, 9))
    bz.set_xlabel("minuten na de lancering", fontsize=9, color=MUTED)
    U.save(fig, "vluchtverloop.png")


# ── 3. De schermen tijdens de oefenvlucht ────────────────────────────
DALING_S = 150            # "tijdens de daling": anderhalve minuut na de lancering


def oefenvlucht():
    """De oefenvlucht via de radio, zoals START_METING ze maakt als je 'oefen'
    typt: [(seconde, rij van de logger)]. Verloren pakketten zitten er niet
    in."""
    sys.path.insert(0, os.path.join(REPO, "cansat", "tools"))
    import gen_test_csv as g
    import serial_logger as sl
    rng = random.Random(1)                         # dezelfde vlucht als 'oefen'
    rows = []
    for t, regel in g.vlucht_regels(rng):
        rssi, snr, lost = g.vlucht_radio(t, regel, rng)
        if not lost:
            parts = g.radio_packet(regel, t, opwarmen=False) + [str(rssi), f"{snr:.1f}"]
            millis = int(regel.split(",", 1)[0]) - 5212 + 2380
            rows.append((t, sl.radio_row(parts, millis)))
    return rows


def meting(rows, tot_s):
    """Het bestand van de logger, met de pakketten tot seconde tot_s."""
    import serial_logger as sl
    pad = os.path.join(tempfile.mkdtemp(), "wedstrijd_1.csv")
    with open(pad, "w", newline="", encoding="utf-8") as fh:
        fh.write(sl.HEADER + "\r\n")
        for t, row in rows:
            if t <= tot_s:
                fh.write(sl.csv_line(row, sl.COLUMNS) + "\r\n")
    return pad


def schermen(rows):
    """Scherm 1 en scherm 2 zoals op laptop 1: live, via de radio."""
    sys.path.insert(0, os.path.join(REPO, "cansat", "dashboard"))
    import dashboard_scherm1 as d1
    import dashboard_scherm2 as d2
    einde = rows[-1][0]
    for name, cls, tot_s in (("dashboard1_radio.png", d1.Dashboard, DALING_S),
                             ("dashboard2_radio.png", d2.Dashboard2, DALING_S),
                             ("dashboard2_geland.png", d2.Dashboard2, einde)):
        d1.DATA_MODE, d1.LIVE_CSV, d1.REPLAY_CSV = "live", meting(rows, tot_s), None
        random.seed(4)
        dash = cls()
        dash.fig.set_size_inches(13.66, 6.9)    # 13-inch laptop, venster
        dash.fit.rescale()                      # eerst de grootte, dan tekenen
        dash._wall = None
        dash.update(0)
        path = os.path.join(U.OUT, name)
        dash.fig.savefig(path, dpi=100, facecolor=dash.fig.get_facecolor())
        plt.close("all")
        print("geschreven:", path)


def replay_einde():
    """Scherm 1 aan het einde van een replay van het bestand van de SD-kaart
    (G3): de hele vlucht in één beeld."""
    sys.path.insert(0, os.path.join(REPO, "cansat", "dashboard"))
    import gen_test_csv as g
    import dashboard_scherm1 as d1
    pad = os.path.join(tempfile.mkdtemp(), "vlucht.csv")
    with open(pad, "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(g.COLUMNS) + "\r\n")
        for _t, regel in g.vlucht_regels(random.Random(1)):
            fh.write(regel + "\r\n")
    d1.DATA_MODE, d1.LIVE_CSV, d1.REPLAY_CSV = "replay", None, pad
    snelheid, d1.SIM_SPEED = d1.SIM_SPEED, 1e6      # het hele bestand in één stap
    dash = d1.Dashboard()
    dash.fig.set_size_inches(13.66, 6.9)
    dash.fit.rescale()
    dash._wall = None
    dash.update(0)                                  # alle rijen
    dash.update(0)                                  # het einde: "· ended"
    d1.SIM_SPEED = snelheid
    path = os.path.join(U.OUT, "dashboard1_replay.png")
    dash.fig.savefig(path, dpi=100, facecolor=dash.fig.get_facecolor())
    plt.close("all")
    print("geschreven:", path)


def livestream(rows):
    """Het streamdashboard zoals op laptop 2 (keuze 5): het leest mee met de
    meting."""
    sys.path.insert(0, os.path.join(REPO, "livestream", "stream"))
    import serial_logger as sl
    import stream_dashboard as sd
    dash = sd.StreamDashboard()
    for t, row in rows:
        if t > DALING_S:
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
    vluchtverloop()
    U.pico_drawing()
    vlucht = oefenvlucht()
    schermen(vlucht)
    replay_einde()
    livestream(vlucht)
