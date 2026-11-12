"""Het breadboard van bovenaf: twee borden van 830 gaatjes boven elkaar.

Onder: de Teensy 4.1 (USB links), de radio en de GPS.
Boven: de microfoon (I2S, recht boven de Teensy) en de drie I2C-sensoren.
In het midden liggen twee railparen: het bovenste geeft 3V3/GND aan de
sensoren, het onderste is de I2C-bus (SDA/SCL, met tape gemerkt). Het
onderste railpaar van het onderste bord geeft 3V3/GND aan radio en GPS.

Eenheden: r = rij in tienden van een inch (rij A van het onderste bord is
0, omhoog positief), c = kolom 1..63. Alle pinnen volgen de vluchtcode.
"""
import html

P = 16                      # px per gaatje (0,1 inch)
GAT = 5.4                   # zijde van een gaatje
X0 = 74                     # x van kolom 1
RTOP = 41.5                 # r bovenaan de tekening
YT = 14                     # y van RTOP
W, H = 1178, 836

# rijen van het onderste bord (L): A..E = 0..4, F..J = 7..11
RIJ = {k: v for k, v in zip("ABCDEFGHIJ", (0, 1, 2, 3, 4, 7, 8, 9, 10, 11))}
U1 = 23.0                   # bovenste bord: rij het dichtst bij de rail
RAIL = {"R4+": -3.5, "R4-": -4.5, "R3-": 14.5, "R3+": 15.5,
        "R2-": 18.5, "R2+": 19.5, "R1-": 37.5, "R1+": 38.5}
RAILKOL = [c for c in range(3, 62) if (c - 3) % 6 != 5]   # groepjes van 5


def X(c):
    return X0 + (c - 1) * P


def Y(r):
    return YT + (RTOP - r) * P


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def esc(s):
    return html.escape(s, quote=True)


class Tekening:
    def __init__(self):
        self.out = []

    def add(self, s):
        self.out.append(s)

    def rect(self, x, y, w, h, cls, rx=0, extra=""):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" '
                 f'rx="{f(rx)}" class="{cls}"{extra}/>')

    def line(self, x1, y1, x2, y2, cls):
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def text(self, x, y, t, cls, anchor="middle", rot=None):
        tr = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot is not None else ""
        self.add(f'<text x="{f(x)}" y="{f(y)}" class="{cls}" text-anchor="{anchor}"{tr}>'
                 f'{esc(t)}</text>')

    def path(self, d, cls):
        self.add(f'<path d="{d}" class="{cls}"/>')

    # ── het bord ──
    def bord(self, onder, boven, strips, rails, nummers):
        """onder/boven: r van de randen; strips: lijst (r_laag, r_hoog) van
        blokken van 5 rijen; rails: namen uit RAIL."""
        x1, x2 = X(1) - 26, X(63) + 26
        self.rect(x1, Y(boven), x2 - x1, Y(onder) - Y(boven), "bb-board", rx=7)
        # een rij gaatjes = één gestippelde lijn (klein, ook in de PDF)
        for lo, hi in strips:
            for r in range(int(lo), int(hi) + 1):
                self.line(X(1) - GAT / 2, Y(r), X(63) + GAT / 2, Y(r), "bb-gaten")
        if len(strips) == 2:                    # middengleuf
            g = (strips[0][1] + strips[1][0]) / 2
            self.rect(X(1) - 10, Y(g) - 5, 62 * P + 20, 10, "bb-groove", rx=2)
        for naam in rails:
            r = RAIL[naam]
            self.line(X(3) - GAT / 2, Y(r), X(61) + GAT / 2, Y(r), "bb-railgaten")
            plus = naam.endswith("+")
            ry = Y(r) - P * 0.62 if plus else Y(r) + P * 0.62
            self.line(X(2), ry, X(62), ry, "bb-red" if plus else "bb-blue")
            self.text(X(1) - 12, Y(r) + 4, "+" if plus else "−",
                      "bb-sign " + ("bb-signred" if plus else "bb-signblue"))
        if nummers:
            for c in [1] + list(range(5, 61, 5)):
                self.text(X(c), Y(-1.55) + 3, str(c), "bb-num")
            for k, r in RIJ.items():
                self.text(X(1) - 15, Y(r) + 3.5, k, "bb-num")
                self.text(X(63) + 15, Y(r) + 3.5, k, "bb-num")

    # ── modules ──
    def pcb(self, cl, cr, rb, rt, soort, rx=5):
        """Printplaat van kolom cl tot cr (kan halve waarden) en r rb..rt."""
        self.rect(X(cl), Y(rt), X(cr) - X(cl), Y(rb) - Y(rt), f"pcb {soort}", rx=rx)

    def pinnen(self, c0, r, labels, gebruikt=(), boven=True):
        """Header op rij r vanaf kolom c0. Het label staat op de print, boven
        of onder de pin. gebruikt: kolommen die een draad krijgen."""
        for i, lab in enumerate(labels):
            x, y = X(c0 + i), Y(r)
            self.rect(x - 4.2, y - 4.2, 8.4, 8.4, "pin", rx=1.2)
            if not lab:
                continue
            cls = "silk" if c0 + i in gebruikt else "silk dim"
            if len(lab) > 3:
                cls += " sm"
            self.text(x, y - 8 if boven else y + 15, lab, cls)

    # ── draden ──
    def draad(self, d, kleur, eind=True):
        """Een draad (SVG-pad d) met een rand, zodat kruisingen leesbaar zijn.
        eind: de stekkertjes aan beide uiteinden tekenen."""
        self.path(d, "w-halo")
        self.path(d, "w-rand")
        self.path(d, f"w {kleur}")
        if eind:
            for x, y in _uiteinden(d):
                self.rect(x - 4.5, y - 4.5, 9, 9, "plug", rx=1.5)

    def recht(self, c, r1, r2, kleur):
        self.draad(f"M{f(X(c))} {f(Y(r1))} L{f(X(c))} {f(Y(r2))}", kleur)

    def boog(self, c1, r1, c2, r2, laag, kleur):
        """Boog van (c1, r1) naar (c2, r2), die zakt tot ongeveer r = laag."""
        x1, y1, x2, y2 = X(c1), Y(r1), X(c2), Y(r2)
        dy = (Y(laag) - max(y1, y2)) / 0.75
        self.draad(f"M{f(x1)} {f(y1)} C{f(x1)} {f(y1 + dy)} {f(x2)} {f(y2 + dy)} "
                   f"{f(x2)} {f(y2)}", kleur)

    def badge(self, x, y, n):
        self.add(f'<circle cx="{f(x)}" cy="{f(y)}" r="10.5" class="badge"/>')
        self.text(x, y + 4.2, str(n), "badge-t")

    def railtag(self, naam, tekst, kleur):
        y = Y(RAIL[naam])
        x = X(63) + 34
        self.rect(x, y - 7, 46, 14, f"railtag {kleur}", rx=7)
        self.text(x + 23, y + 3.6, tekst, "railtag-t")


def _uiteinden(d):
    nums = [float(v) for v in d.replace("M", " ").replace("L", " ").replace("C", " ").split()]
    return [(nums[0], nums[1]), (nums[-2], nums[-1])]


# ═════════════════════════════════════════════════════════════════════
#  De modules
# ═════════════════════════════════════════════════════════════════════
TEENSY_ONDER = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
                "12", "3V3", "24", "25", "26", "27", "28", "29", "30", "31", "32"]
TEENSY_BOVEN = ["VIN", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17", "16",
                "15", "14", "13", "GND", "41", "40", "39", "38", "37", "36", "35", "34",
                "33"]


def teensy(t):
    """Teensy 4.1 over de gleuf van het onderste bord: pinnen in rij D en H,
    kolom 3 tot 26, USB links."""
    t.pcb(2.5, 26.5, 2.5, 9.5, "pcb-teensy", rx=4)
    # USB-stekker en kabel naar links
    t.rect(X(2.5) - 8, Y(7.3), 22, Y(4.7) - Y(7.3), "metal", rx=2)
    t.rect(X(2.5) - 52, Y(7.7), 44, Y(4.3) - Y(7.7), "plugbody", rx=3)
    t.path(f"M{f(X(2.5) - 52)} {f(Y(6))} C{f(X(2.5) - 64)} {f(Y(6))} 18 {f(Y(8))} 0 {f(Y(9))}",
           "kabel")
    t.rect(X(23.6), Y(7.6), X(26.6) - X(23.6), Y(4.4) - Y(7.6), "metal", rx=2)   # SD-kaart
    t.rect(X(10.2), Y(7.5), X(13.4) - X(10.2), Y(4.5) - Y(7.5), "chip", rx=2)
    t.text(X(18), Y(6.4), "TEENSY 4.1", "pcb-title")
    t.text(X(18), Y(5.25), "USB naar de laptop ←", "pcb-sub")
    t.pinnen(3, RIJ["D"], TEENSY_ONDER, {3, 4, 5, 6, 13, 14, 15, 16, 17}, boven=True)
    t.pinnen(3, RIJ["H"], TEENSY_BOVEN, {4, 5, 10, 11, 16}, boven=False)


def bno055(t, c):
    """Adafruit BNO055 (STEMMA QT-versie): hoofdrij op rij 3 van het bovenste
    bord, de rij INT..PS1 0,6 inch hoger."""
    r = U1 + 2
    t.pcb(c - 3, c + 7, r - 0.7, r + 7.3, "pcb-ada")
    t.rect(X(c - 3) - 3, Y(r + 4.6), 9, Y(r + 2.4) - Y(r + 4.6), "stemma", rx=1.5)
    t.rect(X(c + 7) - 6, Y(r + 4.6), 9, Y(r + 2.4) - Y(r + 4.6), "stemma", rx=1.5)
    t.rect(X(c + 4.6), Y(r + 3.9), X(c + 6.0) - X(c + 4.6), Y(r + 2.5) - Y(r + 3.9), "chip", rx=1)
    t.text(X(c + 1.9), Y(r + 3.2) + 5, "BNO055", "pcb-title")
    t.pinnen(c, r, ["VIN", "3Vo", "GND", "SCL", "SDA", "RST"], {c, c + 2, c + 3, c + 4})
    t.pinnen(c, r + 6, ["INT", "ADR", "PS0", "PS1"], (), boven=False)


def lsm6dso(t, c):
    """SparkFun LSM6DSO (Qwiic): hoofdrij op rij 2 van het bovenste bord, de
    andere rij 1,0 inch hoger (rij 10)."""
    r = U1 + 1
    t.pcb(c - 2.3, c + 7.7, r - 0.5, r + 10.5, "pcb-sfe")
    t.rect(X(c + 7.7) - 7, Y(r + 6.6), 10, Y(r + 4.0) - Y(r + 6.6), "stemma", rx=1.5)
    t.rect(X(c + 1.8), Y(r + 5.9), X(c + 3.2) - X(c + 1.8), Y(r + 4.5) - Y(r + 5.9), "chip", rx=1)
    t.text(X(c + 2.5), Y(r + 3.0), "LSM6DSO", "pcb-title")
    t.pinnen(c, r, ["GND", "3V3", "SDA", "SCL", "SDO", "CS"], {c, c + 1, c + 2, c + 3})
    t.pinnen(c, r + 10, ["INT2", "INT1", "OCS", "SCX", "SDX", "SDOX"], (), boven=False)


def microfoon(t, c):
    """Adafruit SPH0645 (I2S): één rij van 6 pinnen op rij 3 van het bovenste
    bord. De volgorde van de pinnen is niet nagekeken op het echte bordje."""
    r = U1 + 2
    t.pcb(c - 1, c + 6, r - 0.6, r + 5.4, "pcb-ada")
    t.rect(X(c + 1.9), Y(r + 4.6), X(c + 3.1) - X(c + 1.9), Y(r + 3.5) - Y(r + 4.6), "metal", rx=1)
    t.text(X(c + 2.5), Y(r + 2.2) + 4, "SPH0645", "pcb-title small")
    t.pinnen(c, r, ["3V", "GND", "BCLK", "DOUT", "LRCL", "SEL"], set(range(c, c + 6)))


def bmp390(t, c):
    """Adafruit BMP390: één rij van 8 pinnen, op rij 3 van het bovenste bord."""
    r = U1 + 2
    t.pcb(c - 1.5, c + 8.5, r - 0.6, r + 6.4, "pcb-ada")
    t.rect(X(c - 1.5) - 3, Y(r + 4.4), 9, Y(r + 2.4) - Y(r + 4.4), "stemma", rx=1.5)
    t.rect(X(c + 8.5) - 6, Y(r + 4.4), 9, Y(r + 2.4) - Y(r + 4.4), "stemma", rx=1.5)
    t.rect(X(c + 3.1), Y(r + 4.1), X(c + 3.9) - X(c + 3.1), Y(r + 3.3) - Y(r + 4.1), "chip", rx=1)
    t.text(X(c + 3.5), Y(r + 5.3), "BMP390", "pcb-title")
    t.pinnen(c, r, ["VIN", "3Vo", "GND", "SCK", "SDO", "SDI", "CS", "INT"],
             {c, c + 2, c + 3, c + 5})


def rfm95w(t, c):
    """Adafruit RFM95W: header op rij D, de print ligt over de gleuf. ANT
    zit rechtsboven."""
    r = RIJ["D"]
    t.pcb(c - 2, c + 10, r - 0.6, r + 9.4, "pcb-ada")
    t.rect(X(c + 1.2), Y(r + 8.2), X(c + 6.8) - X(c + 1.2), Y(r + 2.4) - Y(r + 8.2), "metal", rx=2)
    t.text(X(c + 4), Y(r + 5.6), "RFM95W", "pcb-title dark")
    t.text(X(c + 4), Y(r + 4.5), "868 MHz", "pcb-sub dark")
    t.pinnen(c, r, ["VIN", "GND", "EN", "G0", "SCK", "MISO", "MOSI", "CS", "RST"],
             set(range(c, c + 9)) - {c + 2})
    ax, ay = X(c + 9.1), Y(r + 8.4)
    t.add(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="5.2" class="antpad"/>')
    t.text(ax - 9, ay + 3.5, "ANT", "silk", "end")
    return ax, ay


def gps(t, c):
    """Adafruit Ultimate GPS (PA1616D): header op rij B, de print ligt over
    de gleuf. Van de 9 pinnen gebruik je er 4 (rechts)."""
    r = RIJ["B"]
    t.pcb(c - 1, c + 9, r - 0.5, r + 13.3, "pcb-ada")
    t.rect(X(c + 1), Y(r + 11.6), X(c + 7) - X(c + 1), Y(r + 5.6) - Y(r + 11.6), "patch", rx=3)
    t.add(f'<circle cx="{f(X(c + 4))}" cy="{f(Y(r + 8.6))}" r="5" class="patchdot"/>')
    t.text(X(c + 4), Y(r + 4.2), "GPS PA1616D", "pcb-title")
    t.text(X(c + 2), Y(r + 1.7), "5 pinnen vrij", "pcb-sub")
    t.pinnen(c, r, ["", "", "", "", "", "TX", "RX", "GND", "VIN"], {c + 5, c + 6, c + 7, c + 8})


# ═════════════════════════════════════════════════════════════════════
#  De hele tekening
# ═════════════════════════════════════════════════════════════════════
def breadbord():
    t = Tekening()
    t.rect(0, 0, W, H, "bb-bg", rx=8)
    # onderste bord (L) en bovenste bord (U)
    t.bord(-5.9, 16.9, [(0, 4), (7, 11)], ["R4+", "R4-", "R3-", "R3+"], True)
    t.bord(17.1, 39.9, [(U1, U1 + 4), (U1 + 7, U1 + 11)], ["R2-", "R2+", "R1-", "R1+"], False)
    # tape over de I2C-rails
    for naam, kleur, tekst in (("R3+", "tape-sda", "SDA"), ("R3-", "tape-scl", "SCL")):
        r = RAIL[naam]
        ty = Y(r) - P * 0.62 if naam.endswith("+") else Y(r) + P * 0.62
        t.rect(X(1) - 22, ty - 5, X(63) - X(1) + 44, 10, kleur, rx=1.5)
        for c in (1.2, 21, 41, 61.8):
            t.text(X(c), ty + 3.2, tekst, "tape-t")

    teensy(t)
    microfoon(t, 6)
    bno055(t, 21)
    lsm6dso(t, 33)
    bmp390(t, 52)
    ax, ay = rfm95w(t, 30)
    gps(t, 44)

    # ── draden boven: naar de middelste rails ──
    J, A = RIJ["J"], RIJ["A"]
    for c, rail, k in ((4, "R2-", "w-gnd"), (5, "R2+", "w-3v3"),
                       (10, "R3-", "w-scl"), (11, "R3+", "w-sda")):
        t.recht(c, J, RAIL[rail], k)
    for c0, pins in ((6, ((0, "R2+"), (1, "R2-"), (5, "R2-"))),                    # microfoon
                     (21, ((0, "R2+"), (2, "R2-"), (3, "R3-"), (4, "R3+"))),      # BNO055
                     (33, ((0, "R2-"), (1, "R2+"), (2, "R3+"), (3, "R3-"))),      # LSM6DSO
                     (52, ((0, "R2+"), (2, "R2-"), (3, "R3-"), (5, "R3+")))):     # BMP390
        for dc, rail in pins:
            k = {"R2+": "w-3v3", "R2-": "w-gnd", "R3+": "w-sda", "R3-": "w-scl"}[rail]
            t.recht(c0 + dc, U1, RAIL[rail], k)

    # microfoon (I2S): pin 21 en 20 zitten bovenaan, pin 8 onderaan. De knikken
    # liggen tussen de borden, boven de I2C-draden van pin 18 en 19.
    t.recht(8, J, U1, "w-i2s")                                         # BCLK ← 21
    t.draad(f"M{f(X(9))} {f(Y(J))} L{f(X(9))} {f(Y(16.6))} L{f(X(10))} {f(Y(16.6))} "
            f"L{f(X(10))} {f(Y(U1))}", "w-i2s")                        # LRCL ← 20
    t.draad(f"M{f(X(12))} {f(Y(RIJ['C']))} L{f(X(12.5))} {f(Y(2.6))} L{f(X(12.5))} "
            f"{f(Y(17.8))} L{f(X(9))} {f(Y(17.8))} L{f(X(9))} {f(Y(U1))}", "w-i2s")  # DOUT ← 8

    # ── draden onder ──
    # radio: SPI en G0 in bogen onder de pinnen door
    B = RIJ["B"]
    for c1, c2, laag in ((13, 38, -2.9), (14, 37, -2.3), (15, 36, -1.7), (16, 35, -1.1)):
        t.boog(c1, B, c2, B, laag, "w-spi")
    t.boog(6, B, 33, B, -0.5, "w-spi")
    # SCK: van pin 13 (bovenrij) rond het einde van de Teensy
    xs, xc = X(27.25), X(34)
    t.draad(f"M{f(X(16))} {f(Y(J))} C{f(X(16))} {f(Y(12.7))} {f(X(16.5))} {f(Y(12.7))} "
            f"{f(X(18))} {f(Y(12.7))} L{f(X(26))} {f(Y(12.7))} C{f(xs)} {f(Y(12.7))} "
            f"{f(xs)} {f(Y(12.7))} {f(xs)} {f(Y(11.4))} L{f(xs)} {f(Y(3.2))} C{f(xs)} "
            f"{f(Y(2))} {f(xs)} {f(Y(2))} {f(X(28.5))} {f(Y(2))} L{f(xc)} {f(Y(2))}", "w-spi")
    # GPS: TX en RX in een grote boog onder het bord door
    t.boog(4, A, 49, A, -7.4, "w-gps")
    t.boog(5, A, 50, A, -8.1, "w-gps")
    # voeding van radio en GPS: korte draden naar de onderste rails (bovenop
    # getekend, zodat je ze ziet)
    for c, rail in ((3, "R4-"), (17, "R4+"), (30, "R4+"), (31, "R4-"), (51, "R4-"), (52, "R4+")):
        t.recht(c, A, RAIL[rail], "w-3v3" if rail.endswith("+") else "w-gnd")

    # antenne: staat recht omhoog
    t.add(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="3.6" class="antwire"/>')
    t.add(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="9" class="antring"/>')
    t.text(ax + 6, Y(12.95) + 4, "antenne: 8,2 cm recht omhoog", "ant-t", "end")

    # rails benoemen
    for naam, tekst, k in (("R1+", "vrij", "rt-vrij"), ("R1-", "vrij", "rt-vrij"),
                           ("R2+", "3V3", "rt-3v3"), ("R2-", "GND", "rt-gnd"),
                           ("R3+", "SDA", "rt-sda"), ("R3-", "SCL", "rt-scl"),
                           ("R4+", "3V3", "rt-3v3"), ("R4-", "GND", "rt-gnd")):
        t.railtag(naam, tekst, k)

    # bouwvolgorde
    t.badge(X(1) - 52, (Y(14.5) + Y(15.5)) / 2, 1)
    t.badge(X(7.5), Y(6), 2)
    t.badge(X(6.5), Y(13.3), 3)
    t.badge(X(18) + 6, Y(U1 + 9.3) - 6, 4)
    t.badge(X(30.7) + 14, Y(U1 + 11.5) + 14, 5)
    t.badge(X(50.5) + 14, Y(U1 + 8.4) + 14, 6)
    t.badge(X(5) + 6, Y(U1 + 7.4) - 6, 7)
    t.badge(X(28) + 14, Y(12.4) + 14, 8)
    t.badge(X(43) + 14, Y(14.3) + 14, 9)

    label = ("Breadboard van bovenaf. Onder: Teensy 4.1 met USB links, de radio "
             "RFM95W en de GPS. Boven: de microfoon SPH0645, BNO055, LSM6DSO en "
             "BMP390. De middelste "
             "rails geven 3V3 en GND aan de sensoren en dragen de I2C-bus SDA en SCL. "
             "De onderste rails geven 3V3 en GND aan de radio en de GPS.")
    return (f'<svg class="bb" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(t.out)}</svg>')


# ═════════════════════════════════════════════════════════════════════
#  Detail: laat een vrij gaatje naast elke pin
# ═════════════════════════════════════════════════════════════════════
def vrij_gaatje():
    Q = 22
    t = Tekening()
    t.rect(0, 0, 534, 244, "bb-bg", rx=8)

    def paneel(ox, pinrij, goed):
        rij = {k: 0 for k in "ABCDE"}
        for i, k in enumerate("ABCDE"):
            rij[k] = 150 - i * Q
        xs = [ox + 34 + i * Q for i in range(9)]
        t.rect(ox, 14, 9 * Q + 46, 226, "bb-board", rx=6)
        for k, y in rij.items():
            t.text(ox + 14, y + 4, k, "bb-num")
            for x in xs:
                t.rect(x - 3.4, y - 3.4, 6.8, 6.8, "bb-hole", rx=1)
        for y, cls in ((192, "bb-red"), (214, "bb-blue")):
            for x in xs:
                t.rect(x - 3.4, y - 3.4, 6.8, 6.8, "bb-hole", rx=1)
        t.line(xs[0] - 8, 180, xs[-1] + 8, 180, "bb-red")
        t.line(xs[0] - 8, 226, xs[-1] + 8, 226, "bb-blue")
        t.text(ox + 14, 196, "+", "bb-sign bb-signred")
        t.text(ox + 14, 218, "−", "bb-sign bb-signblue")
        # het bordje: pinnen in pinrij, de print loopt naar boven
        yp = rij[pinrij]
        t.rect(xs[1] - Q / 2, 6, 6 * Q, yp + Q * 0.45 - 6, "pcb pcb-sfe", rx=4)
        for i, lab in enumerate(("GND", "3V3", "SDA", "SCL", "SDO", "CS")):
            x = xs[1 + i]
            t.rect(x - 5, yp - 5, 10, 10, "pin", rx=1.5)
            t.text(x, yp - 11, lab, "silk")
        t.text(xs[-1] + 4, 40, "GOED" if goed else "FOUT", "goed-t" if goed else "fout-t", "end")
        if goed:
            t.draad(f"M{f(xs[1])} {f(rij['A'])} L{f(xs[1])} 214", "w-gnd")
            t.draad(f"M{f(xs[2])} {f(rij['A'])} L{f(xs[2])} 192", "w-3v3")
        else:
            for x in (xs[1], xs[2]):
                t.line(x - 7, rij["A"] + 18, x + 7, rij["A"] + 32, "kruis")
                t.line(x + 7, rij["A"] + 18, x - 7, rij["A"] + 32, "kruis")

    paneel(0, "B", True)
    paneel(290, "A", False)
    label = ("Twee bordjes op een breadboard. Links goed: de pinnen zitten in rij B, "
             "rij A blijft vrij voor de draden naar de rails. Rechts fout: de pinnen "
             "zitten in de buitenste rij A en het bordje dekt de andere gaatjes af.")
    return (f'<svg class="bb klein" viewBox="0 0 534 244" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(t.out)}</svg>')
