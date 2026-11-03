"""De vier tekeningen van het draadschema, als inline SVG.

Alle pinnen volgen vluchtcode/Cansat2027_teensy.ino. De kleuren komen uit
CSS-variabelen van de pagina (klassen n3v3, n5v, ...), zodat de tekening
in het lichte en het donkere thema leesbaar blijft.
"""
import html

CHAR_W = 6.9          # breedte van één teken (IBM Plex Mono, 11.5 px)


def esc(s):
    return html.escape(s, quote=True)


class Svg:
    def __init__(self, w, h, label, pid):
        self.w, self.h, self.label, self.pid = w, h, label, pid
        self.out = []

    def add(self, frag):
        self.out.append(frag)

    def line(self, x1, y1, x2, y2, cls):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')

    def path(self, pts, cls, arrow=None):
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        m = f' marker-end="url(#{self.pid}-pijl-{arrow})"' if arrow else ""
        self.add(f'<path d="{d}" class="{cls}"{m}/>')

    def rect(self, x, y, w, h, cls, rx=0):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>')

    def circle(self, x, y, r, cls):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" class="{cls}"/>')

    def text(self, x, y, t, cls, anchor="start"):
        self.add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{esc(t)}</text>')

    def dot(self, x, y, net):
        self.circle(x, y, 3.8, f"dot {net}")

    # ── draad van (x1, y) naar (x2, y) met een pijl halverwege ──
    def signal(self, x1, x2, y, net, arrow=True):
        if not arrow:
            self.path([(x1, y), (x2, y)], f"wire {net}")
            return
        xm = (x1 + x2) / 2 + (6 if x2 > x1 else -6)
        self.path([(x1, y), (xm, y)], f"wire {net}", arrow=net)
        self.path([(xm, y), (x2, y)], f"wire {net}")

    # ── netlabel: afgerond kaartje met de naam van het net ──
    def tag(self, x, y, t, net, side="left"):
        """side: waar het kaartje ligt t.o.v. het einde (x, y) van de draad."""
        w = len(t) * CHAR_W + 14
        if side == "left":
            x0, y0 = x - w, y - 9
        elif side == "right":
            x0, y0 = x, y - 9
        else:                                   # "below": hangt onder (x, y)
            x0, y0 = x - w / 2, y
        self.rect(x0, y0, w, 18, f"tag {net}", rx=9)
        self.text(x0 + w / 2, y0 + 13, t, f"tagt {net}", "middle")

    # ── module: kader met kop en pinnen op één zijde ──
    def module(self, x, y, w, title, sub, pins, side="left", note=None):
        """pins: [(label, net)]. Geeft {label: (x, y) van het einde van de
        pinstomp} en de onderkant van het kader terug."""
        first, step = y + 46, 21
        bottom = first + (len(pins) - 1) * step + 13 + (15 if note else 0)
        self.rect(x, y, w, bottom - y, "box", rx=6)
        self.path([(x, y + 34), (x + w, y + 34)], "boxrule")
        self.text(x + 10, y + 16, title, "tt")
        self.text(x + 10, y + 29, sub, "ts")
        ends = {}
        for i, (lab, net) in enumerate(pins):
            py = first + i * step
            if side == "left":
                self.line(x - 12, py, x, py, f"wire {net}")
                self.rect(x - 3, py - 3, 6, 6, f"pad {net}")
                self.text(x + 10, py + 4, lab, "tp")
                ends[lab] = (x - 12, py)
            else:
                self.line(x + w, py, x + w + 12, py, f"wire {net}")
                self.rect(x + w - 3, py - 3, 6, 6, f"pad {net}")
                self.text(x + w - 10, py + 4, lab, "tp", "end")
                ends[lab] = (x + w + 12, py)
        if note:
            self.text(x + 10, bottom - 9, note, "tn")
        return ends, bottom

    def diode(self, x, y, direction, cls="comp"):
        """Diode met het midden op (x, y); direction = richting van de stroom
        (anode → kathode): 'right', 'left', 'down' of 'up'."""
        a = 9
        if direction in ("right", "left"):
            s = 1 if direction == "right" else -1
            self.add(f'<polygon points="{x - s * a},{y - a} {x - s * a},{y + a} '
                     f'{x + s * a},{y}" class="{cls} fillsheet"/>')
            self.line(x + s * a, y - a, x + s * a, y + a, cls)
        else:
            s = 1 if direction == "down" else -1
            self.add(f'<polygon points="{x - a},{y - s * a} {x + a},{y - s * a} '
                     f'{x},{y + s * a}" class="{cls} fillsheet"/>')
            self.line(x - a, y + s * a, x + a, y + s * a, cls)

    def resistor(self, x1, y1, x2, y2, cls="comp"):
        """Weerstand (IEC-blokje) tussen twee punten op één lijn."""
        if y1 == y2:
            self.rect(min(x1, x2), y1 - 6, abs(x2 - x1), 12, f"{cls} fillsheet", rx=1)
        else:
            self.rect(x1 - 6, min(y1, y2), 12, abs(y2 - y1), f"{cls} fillsheet", rx=1)

    def render(self):
        nets = ("n3v3", "n5v", "ngnd", "ni2c", "nuart", "ni2s", "nspi", "nctl", "nink")
        markers = "".join(
            f'<marker id="{self.pid}-pijl-{n}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" class="ah {n}"/></marker>' for n in nets)
        return (f'<svg class="schema" viewBox="0 0 {self.w} {self.h}" role="img" '
                f'aria-label="{esc(self.label)}" xmlns="http://www.w3.org/2000/svg">'
                f'<defs>{markers}</defs>{"".join(self.out)}</svg>')


# ═════════════════════════════════════════════════════════════════════
#  Figuur 1 — het volledige schema
# ═════════════════════════════════════════════════════════════════════
def overzicht():
    s = Svg(1180, 916, "Volledig draadschema: Teensy 4.1 in het midden; links de "
            "voeding met batterij, PowerBoost, schakelaar en twee diodes, de buzzer "
            "met transistor en de radio; rechts de drie I2C-sensoren, de GPS en de "
            "microfoon.", "f1")
    TX, TW, TY, TB = 480, 200, 70, 830          # Teensy-kader
    TR = TX + TW                                # rechterrand
    MX, MW = 880, 230                           # modules rechts
    SDA_X, SCL_X = 760, 790                     # I2C-bus

    # ── modules rechts ──
    bmp, b1 = s.module(MX, 70, MW, "BMP390", "Adafruit · I²C 0x77 · druk",
                       [("SDI (= SDA)", "ni2c"), ("SCK (= SCL)", "ni2c"),
                        ("VIN", "n3v3"), ("GND", "ngnd")])
    bno, b2 = s.module(MX, b1 + 14, MW, "BNO055", "Adafruit · I²C 0x28 · oriëntatie",
                       [("SDA", "ni2c"), ("SCL", "ni2c"), ("VIN", "n3v3"),
                        ("GND", "ngnd")])
    lsm, b3 = s.module(MX, b2 + 14, MW, "LSM6DSO", "SparkFun · I²C 0x6B · trillingen",
                       [("SDA", "ni2c"), ("SCL", "ni2c"), ("3V3", "n3v3"),
                        ("GND", "ngnd")], note="SCX en SDX niet gebruiken")
    gps, b4 = s.module(MX, b3 + 14, MW, "GPS PA1616D", "Adafruit Ultimate GPS · UART",
                       [("TX", "nuart"), ("RX", "nuart"), ("VIN", "n3v3"),
                        ("GND", "ngnd")], note="CR1220-knoopcel in de houder")
    mic, b5 = s.module(MX, b4 + 14, MW, "SPH0645", "Adafruit · I²S · microfoon",
                       [("BCLK", "ni2s"), ("LRCL", "ni2s"), ("DOUT", "ni2s"),
                        ("SEL", "ngnd"), ("3V", "n3v3"), ("GND", "ngnd")])

    # ── Teensy-kader ──
    s.rect(560, TY - 14, 40, 14, "box usb", rx=2)
    s.text(580, TY - 20, "USB (laptop)", "ts", "middle")
    s.rect(TX, TY, TW, TB - TY, "box teensy", rx=8)
    s.text(TX + TW / 2, TY + 22, "TEENSY 4.1", "tt big", "middle")
    s.text(TX + TW / 2, TY + 36, "PJRC · 3,3 V-logica", "ts", "middle")

    def tpin(y, label, net, right):
        x = TR if right else TX
        s.rect(x - 3, y - 3, 6, 6, f"pad {net}")
        if right:
            s.text(x - 10, y + 4, label, "tp strong", "end")
        else:
            s.text(x + 10, y + 4, label, "tp strong")

    # rechts: I2C, UART, I2S
    y_sda, y_scl = bmp["SDI (= SDA)"][1], bmp["SCK (= SCL)"][1]
    tpin(y_sda, "18 · SDA", "ni2c", True)
    tpin(y_scl, "19 · SCL", "ni2c", True)
    tpin(gps["TX"][1], "0 · RX1", "nuart", True)
    tpin(gps["RX"][1], "1 · TX1", "nuart", True)
    tpin(mic["BCLK"][1], "21 · BCLK1", "ni2s", True)
    tpin(mic["LRCL"][1], "20 · LRCLK1", "ni2s", True)
    tpin(mic["DOUT"][1], "8 · IN1", "ni2s", True)

    # I2C-bus: SDA en SCL naar de drie sensoren
    xe = MX - 12
    s.path([(TR, y_sda), (xe, y_sda)], "wire ni2c")
    s.path([(TR, y_scl), (xe, y_scl)], "wire ni2c")
    s.path([(SDA_X, y_sda), (SDA_X, lsm["SDA"][1]), (xe, lsm["SDA"][1])], "wire ni2c")
    s.path([(SCL_X, y_scl), (SCL_X, lsm["SCL"][1]), (xe, lsm["SCL"][1])], "wire ni2c")
    s.path([(SDA_X, bno["SDA"][1]), (xe, bno["SDA"][1])], "wire ni2c")
    s.path([(SCL_X, bno["SCL"][1]), (xe, bno["SCL"][1])], "wire ni2c")
    for x, y in ((SDA_X, y_sda), (SCL_X, y_scl), (SDA_X, bno["SDA"][1]),
                 (SCL_X, bno["SCL"][1])):
        s.dot(x, y, "ni2c")

    # GPS en microfoon: rechte draden met de richting van het signaal
    s.signal(xe, TR, gps["TX"][1], "nuart")              # GPS TX → RX1
    s.signal(TR, xe, gps["RX"][1], "nuart")              # TX1 → GPS RX
    s.signal(TR, xe, mic["BCLK"][1], "ni2s")
    s.signal(TR, xe, mic["LRCL"][1], "ni2s")
    s.signal(xe, TR, mic["DOUT"][1], "ni2s")

    # voedingslabels aan de modules
    for ends in (bmp, bno, lsm, gps, mic):
        for lab, (x, y) in ends.items():
            if lab in ("VIN", "3V3", "3V"):
                s.tag(x, y, "3V3", "n3v3")
            elif lab in ("GND", "SEL"):
                s.tag(x, y, "GND", "ngnd")

    # ── links: pinnen van de Teensy ──
    Y_VUSB, Y_VIN, Y_33, Y_GND, Y_14 = 134, 168, 202, 236, 390
    tpin(Y_VUSB, "VUSB-pad", "n5v", False)
    s.text(TX + 10, Y_VUSB + 18, "pads VIN–VUSB doorgesneden", "tn")
    tpin(Y_VIN, "VIN", "n5v", False)
    tpin(Y_33, "3.3V", "n3v3", False)
    s.text(TX + 10, Y_33 + 18, "samen max. 250 mA", "tn")
    tpin(Y_GND, "GND", "ngnd", False)
    tpin(Y_14, "14 · buzzer", "nctl", False)

    s.line(TX - 16, Y_33, TX, Y_33, "wire n3v3")
    s.tag(TX - 16, Y_33, "3V3", "n3v3")
    s.line(TX - 16, Y_GND, TX, Y_GND, "wire ngnd")
    s.tag(TX - 16, Y_GND, "GND", "ngnd")

    # ── voeding: LiPo → PowerBoost → D2 → VIN, en USB → D1 → VIN ──
    PB_X, PB_W, PB_Y, PB_B = 150, 140, 104, 252
    s.rect(196, PB_Y - 12, 48, 12, "box usb", rx=2)
    s.text(220, PB_Y - 18, "micro-USB: laden", "ts", "middle")
    s.rect(PB_X, PB_Y, PB_W, PB_B - PB_Y, "box", rx=6)
    s.path([(PB_X, PB_Y + 34), (PB_X + PB_W, PB_Y + 34)], "boxrule")
    s.text(PB_X + 10, PB_Y + 16, "PowerBoost 1000C", "tt")
    s.text(PB_X + 10, PB_Y + 29, "Adafruit · laden + 5,2 V", "ts")
    s.text(PB_X + 10, Y_VIN + 4, "BAT", "tp")
    s.text(PB_X + PB_W - 10, Y_VIN + 4, "5V", "tp", "end")
    s.text(PB_X + PB_W - 10, 214, "GND", "tp", "end")
    s.text(220, PB_B - 10, "EN", "tp", "middle")
    for x, y, net in ((PB_X, Y_VIN, "nink"), (PB_X + PB_W, Y_VIN, "n5v"),
                      (PB_X + PB_W, 210, "ngnd"), (220, PB_B, "nctl")):
        s.rect(x - 3, y - 3, 6, 6, f"pad {net}")
    s.line(PB_X + PB_W, 210, PB_X + PB_W + 14, 210, "wire ngnd")
    s.tag(PB_X + PB_W + 14, 210, "GND", "ngnd", "right")

    # LiPo-cel met JST-stekker
    s.rect(34, 146, 74, 44, "box cell", rx=5)
    s.rect(108, 160, 6, 16, "box cell", rx=1)
    s.text(71, 165, "LiPo", "tt", "middle")
    s.text(71, 181, "3,7 V", "ts", "middle")
    s.path([(114, 163), (PB_X, 163)], "wire nink")
    s.path([(114, 173), (PB_X, 173)], "wire nink")
    s.text(122, 158, "+", "tp strong", "middle")
    s.text(122, 188, "−", "tp strong", "middle")
    s.text(71, 208, "2000 mAh, beveiligd", "tn", "middle")
    s.text(71, 222, "JST-PH-stekker", "tn", "middle")

    # D2 en de VIN-lijn
    s.path([(PB_X + PB_W, Y_VIN), (326, Y_VIN)], "wire n5v")
    s.diode(335, Y_VIN, "right", "comp n5v")
    s.path([(344, Y_VIN), (TX, Y_VIN)], "wire n5v")
    s.text(335, Y_VIN - 15, "D2", "tp strong", "middle")
    s.text(335, Y_VIN + 24, "1N5817", "tn", "middle")
    # D1 over de doorgesneden pads
    s.path([(TX, Y_VUSB), (440, Y_VUSB), (440, 142)], "wire n5v")
    s.diode(440, 151, "down", "comp n5v")
    s.path([(440, 160), (440, Y_VIN)], "wire n5v")
    s.text(452, 152, "D1", "tp strong")
    s.dot(440, Y_VIN, "n5v")
    s.text(392, Y_VIN - 8, "VIN 5 V", "tn n5vt", "end")

    # schakelaar S1 op EN
    s.path([(220, PB_B), (220, 266)], "wire nctl")
    s.circle(220, 270, 3.5, "contact nctl")
    s.circle(198, 300, 3.5, "contact ngnd")
    s.circle(242, 300, 3.5, "contact nctl")
    s.line(222, 273, 240, 296, "wire nctl blade")
    s.text(206, 274, "S1", "tp strong", "end")
    s.text(190, 304, "UIT", "tp", "end")
    s.text(250, 304, "AAN (open)", "tp")
    s.path([(198, 304), (198, 318)], "wire ngnd")
    s.tag(198, 318, "GND", "ngnd", "below")

    # ── buzzer: VIN → BZ1 → Q1 → GND, pin 14 → R1 → basis ──
    BX = 400
    s.dot(BX, Y_VIN, "n5v")
    s.path([(BX, Y_VIN), (BX, 300)], "wire n5v")
    s.rect(BX - 15, 300, 30, 36, "box buz", rx=4)
    s.text(BX, 323, "BZ", "tp strong", "middle")
    s.text(BX + 20, 300, "+", "tp strong")
    s.text(BX - 22, 316, "BZ1", "tp strong", "end")
    s.text(BX - 22, 330, "actief, 5 V", "tn", "end")
    s.path([(BX, 296), (432, 296), (432, 308)], "wire nink")
    s.diode(432, 318, "up", "comp nink")
    s.path([(432, 328), (432, 344), (BX, 344)], "wire nink")
    s.text(442, 322, "D3", "tp strong")
    s.dot(BX, 296, "n5v")
    s.path([(BX, 336), (BX, 372)], "wire nink")
    s.dot(BX, 344, "nink")
    # Q1 (NPN, basis rechts)
    s.circle(404, 390, 17, "comp fillsheet")
    s.line(412, 378, 412, 402, "comp")
    s.line(412, 383, BX, 372, "comp")
    s.path([(412, 397), (BX + 1, 408)], "comp", arrow="nink")
    s.path([(BX, 407), (BX, 436)], "wire ngnd")
    s.text(382, 386, "Q1", "tp strong", "end")
    s.text(382, 400, "BC337", "tn", "end")
    s.path([(412, 390), (430, 390)], "wire nctl")
    s.dot(430, 390, "nctl")
    s.resistor(438, 390, 466, 390, "comp nctl")
    s.path([(430, 390), (438, 390)], "wire nctl")
    s.path([(466, 390), (TX, 390)], "wire nctl")
    s.text(452, 380, "R1 1k", "tn", "middle")
    s.resistor(430, 400, 430, 424, "comp nctl")
    s.path([(430, 390), (430, 400)], "wire nctl")
    s.path([(430, 424), (430, 436), (BX, 436)], "wire ngnd")
    s.text(440, 416, "R2", "tn")
    s.text(440, 429, "10k", "tn")
    s.dot(BX, 436, "ngnd")
    s.path([(BX, 436), (BX, 448)], "wire ngnd")
    s.tag(BX, 448, "GND", "ngnd", "below")

    # ── radio RFM95W (SPI) ──
    rfm, b6 = s.module(230, 500, 180, "RFM95W", "Adafruit · SPI · 868 MHz",
                       [("VIN", "n3v3"), ("GND", "ngnd"), ("SCK", "nspi"),
                        ("MISO", "nspi"), ("MOSI", "nspi"), ("CS", "nspi"),
                        ("RST", "nspi"), ("G0", "nspi")], side="right")
    spi = [("SCK", "13 · SCK", False), ("MISO", "12 · MISO", True),
           ("MOSI", "11 · MOSI", False), ("CS", "10 · CS", False),
           ("RST", "9 · RST", False), ("G0", "2 · G0", True)]
    for lab, tlab, to_teensy in spi:
        x, y = rfm[lab]
        tpin(y, tlab, "nspi", False)
        if to_teensy:
            s.signal(x, TX, y, "nspi")
        else:
            s.signal(TX, x, y, "nspi")
    s.tag(*rfm["VIN"], "3V3", "n3v3", "right")
    s.tag(*rfm["GND"], "GND", "ngnd", "right")
    # antenne aan ANT (linkerkant van de radio)
    ya = 604
    s.rect(227, ya - 3, 6, 6, "pad nink")
    s.text(240, ya + 4, "ANT", "tp")
    s.path([(230, ya), (200, ya), (200, 556)], "wire nink")
    s.add('<polygon points="186,542 214,542 200,558" class="comp nink fillsheet"/>')
    s.text(184, 548, "antenne", "tp strong", "end")
    s.text(184, 562, "2 × 8,2 cm, zie fig. 4", "tn", "end")

    # ── Teensy: ingebouwde microSD ──
    s.text(TX + TW / 2, TB - 30, "microSD (ingebouwd)", "tp", "middle")
    s.text(TX + TW / 2, TB - 15, "kaart erin, tape erover", "tn", "middle")

    # ── legende ──
    lx, ly = 24, 752
    s.text(lx, ly, "LEGENDE", "tl strong")
    items = [("n3v3", "3V3: 3.3V-pin van de Teensy"), ("n5v", "VIN: 5 V"),
             ("ngnd", "GND: alles aan elkaar"), ("ni2c", "I²C: SDA en SCL"),
             ("nuart", "UART: GPS"), ("ni2s", "I²S: microfoon"),
             ("nspi", "SPI: radio"), ("nctl", "stuurdraad (EN, pin 14)")]
    for i, (net, lab) in enumerate(items):
        col, row = i % 2, i // 2
        x, y = lx + col * 222, ly + 22 + row * 21
        s.line(x, y - 4, x + 26, y - 4, f"wire {net}")
        s.text(x + 34, y, lab, "tl")
    s.dot(lx + 13, ly + 116, "nink")
    s.text(lx + 34, ly + 120, "= verbonden; kruising zonder bolletje = niet verbonden",
           "tl")
    s.path([(lx, ly + 141), (lx + 22, ly + 141)], "wire nink", arrow="nink")
    s.text(lx + 34, ly + 145, "= richting van het signaal", "tl")

    # ── titelblok ──
    bx, by, bw, bh = 700, 846, 468, 62
    s.rect(bx, by, bw, bh, "box titleblock")
    s.line(bx, by + 31, bx + bw, by + 31, "boxrule")
    s.line(bx + 340, by, bx + 340, by + bh, "boxrule")
    s.text(bx + 10, by + 21, "CanSat 2027 · draadschema vlucht", "tt")
    s.text(bx + 10, by + 52, "pinnen: vluchtcode Cansat2027_teensy.ino", "ts")
    s.text(bx + 350, by + 21, "Rev. A · blad 1/1", "ts")
    s.text(bx + 350, by + 52, "21-10-2026", "ts")
    return s.render()


# ═════════════════════════════════════════════════════════════════════
#  Figuur 2 — waar zitten de pinnen op de echte Teensy 4.1?
# ═════════════════════════════════════════════════════════════════════
# Bovenaanzicht, USB boven (zoals het kaartje van PJRC)
T41_LEFT = (["GND"] + [str(i) for i in range(13)] + ["3.3V"]
            + [str(i) for i in range(24, 33)])
T41_RIGHT = (["VIN", "GND", "3.3V"] + [str(i) for i in range(23, 12, -1)]
             + ["GND"] + [str(i) for i in range(41, 32, -1)])
USED = {
    "L:GND": ("ngnd", "GND"), "L:0": ("nuart", "GPS TX"),
    "L:1": ("nuart", "GPS RX"), "L:2": ("nspi", "radio G0"),
    "L:8": ("ni2s", "microfoon DOUT"), "L:9": ("nspi", "radio RST"),
    "L:10": ("nspi", "radio CS"), "L:11": ("nspi", "radio MOSI"),
    "L:12": ("nspi", "radio MISO"),
    "R:VIN": ("n5v", "D1 + D2 (5 V)"), "R:GND": ("ngnd", "GND"),
    "R:3.3V": ("n3v3", "3V3 naar alle modules"),
    "R:21": ("ni2s", "microfoon BCLK"), "R:20": ("ni2s", "microfoon LRCL"),
    "R:19": ("ni2c", "SCL (I²C)"), "R:18": ("ni2c", "SDA (I²C)"),
    "R:14": ("nctl", "buzzer, via R1"), "R:13": ("nspi", "radio SCK"),
}


def teensy_pinnen():
    s = Svg(760, 660, "Bovenaanzicht van de Teensy 4.1 met de USB-poort boven. "
            "De gebruikte pinnen zijn gekleurd en benoemd.", "f2")
    bx, bw, top, pitch = 310, 140, 104, 22
    xl, xr = bx + 16, bx + bw - 16
    bottom = top + 23 * pitch
    s.rect(bx, top - 40, bw, bottom - top + 64, "box board", rx=10)
    s.rect(bx + bw / 2 - 22, top - 58, 44, 22, "box usb", rx=3)
    s.text(bx + bw / 2, top - 64, "USB", "ts", "middle")
    s.text(bx + bw / 2, top + 11 * pitch, "TEENSY", "tt big", "middle")
    s.text(bx + bw / 2, top + 11 * pitch + 20, "4.1", "tt big", "middle")
    s.text(bx + bw / 2, top + 11 * pitch + 40, "bovenkant", "ts", "middle")
    seen_gnd = {"L": False, "R": False}
    for side, names, x in (("L", T41_LEFT, xl), ("R", T41_RIGHT, xr)):
        for i, name in enumerate(names):
            y = top + i * pitch
            key = f"{side}:{name}"
            used = key in USED
            if name == "GND":                  # één GND per kant volstaat
                used = used and not seen_gnd[side]
                seen_gnd[side] = seen_gnd[side] or used
            if name == "3.3V" and side == "L":
                used = False
            net, func = USED[key] if used else ("nink", "")
            s.circle(x, y, 6 if used else 4, f"pin {net}" + ("" if used else " unused"))
            if side == "L":
                s.text(bx - 10, y + 4, name, "tp strong" if used else "tp dim", "end")
                if used:
                    s.line(bx - 52, y, bx - 44, y, f"wire {net}")
                    s.text(bx - 58, y + 4, func, f"tp {net}t", "end")
            else:
                s.text(bx + bw + 10, y + 4, name, "tp strong" if used else "tp dim")
                if used:
                    s.line(bx + bw + 46, y, bx + bw + 54, y, f"wire {net}")
                    s.text(bx + bw + 60, y + 4, func, f"tp {net}t")
    s.text(380, bottom + 48, "Controleer met het pinout-kaartje van PJRC.", "tn", "middle")
    return s.render()


# ═════════════════════════════════════════════════════════════════════
#  Figuur 3 — de voeding, met meetpunten
# ═════════════════════════════════════════════════════════════════════
def voeding():
    s = Svg(1000, 400, "Voeding: LiPo naar PowerBoost 1000C; de 5V-uitgang gaat via "
            "diode D2 naar VIN; de USB-poort via diode D1 over de doorgesneden pads "
            "naar VIN; schakelaar S1 legt EN aan GND om uit te schakelen.", "f3")
    # LiPo
    s.rect(30, 160, 92, 56, "box cell", rx=6)
    s.rect(122, 178, 7, 20, "box cell", rx=1)
    s.text(76, 184, "LiPo 3,7 V", "tt", "middle")
    s.text(76, 202, "2000 mAh", "ts", "middle")
    s.text(76, 236, "met beveiliging", "tn", "middle")
    s.path([(129, 183), (200, 183)], "wire nink")
    s.path([(129, 193), (200, 193)], "wire nink")
    s.text(164, 176, "+", "tp strong", "middle")
    s.text(164, 211, "−", "tp strong", "middle")
    s.text(164, 230, "JST-PH", "tn", "middle")
    # PowerBoost
    px, py, pw, ph = 200, 90, 210, 210
    s.rect(px + 80, py - 14, 50, 14, "box usb", rx=2)
    s.text(px + 105, py - 20, "micro-USB: laden (1 A)", "ts", "middle")
    s.rect(px, py, pw, ph, "box", rx=8)
    s.path([(px, py + 40), (px + pw, py + 40)], "boxrule")
    s.text(px + 12, py + 19, "PowerBoost 1000C", "tt")
    s.text(px + 12, py + 34, "Adafruit · laadt en maakt 5,2 V", "ts")
    s.text(px + 12, 192, "BAT", "tp")
    s.text(px + pw - 12, 134, "5V", "tp", "end")
    s.text(px + pw - 12, 254, "GND", "tp", "end")
    s.text(px + 105, py + ph - 12, "EN", "tp", "middle")
    for x, y, net in ((px, 188, "nink"), (px + pw, 130, "n5v"),
                      (px + pw, 250, "ngnd"), (px + 105, py + ph, "nctl")):
        s.rect(x - 3, y - 3, 6, 6, f"pad {net}")
    # 5V → TP1 → D2 → VIN
    s.path([(px + pw, 130), (520, 130)], "wire n5v")
    s.circle(452, 130, 5, "tp-ring n5v")
    s.text(452, 112, "TP1", "tp strong", "middle")
    s.diode(530, 130, "right", "comp n5v")
    s.text(530, 112, "D2", "tp strong", "middle")
    s.text(530, 154, "1N5817", "tn", "middle")
    s.path([(539, 130), (760, 130)], "wire n5v")
    s.dot(640, 130, "n5v")
    s.circle(700, 130, 5, "tp-ring n5v")
    s.text(700, 112, "TP2", "tp strong", "middle")
    # Teensy (deel)
    tx, ty, tw, th = 760, 60, 220, 270
    s.rect(tx + 90, ty - 14, 40, 14, "box usb", rx=2)
    s.text(tx + 110, ty - 20, "USB (laptop)", "ts", "middle")
    s.rect(tx, ty, tw, th, "box teensy", rx=8)
    s.text(tx + tw - 12, ty + 22, "TEENSY 4.1", "tt", "end")
    s.text(tx + 14, 94, "VUSB-pad", "tp strong")
    s.text(tx + 14, 134, "VIN", "tp strong")
    s.text(tx + 14, 214, "3.3V", "tp strong")
    s.text(tx + 14, 254, "GND", "tp strong")
    for y, net in ((90, "n5v"), (130, "n5v"), (210, "n3v3"), (250, "ngnd")):
        s.rect(tx - 3, y - 3, 6, 6, f"pad {net}")
    # het spoor tussen VUSB en VIN, doorgesneden
    s.path([(tx + 90, 90), (tx + 116, 90), (tx + 116, 104)], "wire n5v trace")
    s.path([(tx + 116, 116), (tx + 116, 130), (tx + 90, 130)], "wire n5v trace")
    s.line(tx + 107, 107, tx + 125, 101, "cut")
    s.line(tx + 107, 119, tx + 125, 113, "cut")
    s.text(tx + 134, 107, "spoor", "tn")
    s.text(tx + 134, 120, "doorsnijden", "tn")
    # D1 van VUSB naar VIN
    s.path([(tx, 90), (640, 90), (640, 99)], "wire n5v")
    s.diode(640, 108, "down", "comp n5v")
    s.path([(640, 117), (640, 130)], "wire n5v")
    s.text(626, 98, "D1", "tp strong", "end")
    s.text(626, 112, "1N5817", "tn", "end")
    # 3.3V en GND
    s.path([(tx, 210), (640, 210)], "wire n3v3")
    s.circle(700, 210, 5, "tp-ring n3v3")
    s.text(700, 196, "TP3", "tp strong", "middle")
    s.tag(640, 210, "3V3 naar alle modules", "n3v3")
    s.path([(px + pw, 250), (tx, 250)], "wire ngnd")
    s.text(585, 244, "GND (gemeenschappelijk)", "tn", "middle")
    # schakelaar
    ex = px + 105
    s.path([(ex, py + ph), (ex, 318)], "wire nctl")
    s.circle(ex, 322, 3.5, "contact nctl")
    s.circle(ex - 26, 356, 3.5, "contact ngnd")
    s.circle(ex + 26, 356, 3.5, "contact nctl")
    s.line(ex + 2, 325, ex + 24, 352, "wire nctl blade")
    s.text(ex - 14, 326, "S1", "tp strong", "end")
    s.text(ex - 36, 360, "UIT", "tp strong", "end")
    s.text(ex + 36, 360, "AAN: contact open, EN hoog", "tp")
    s.path([(ex - 26, 360), (ex - 26, 372)], "wire ngnd")
    s.tag(ex - 26, 372, "GND", "ngnd", "below")
    # meetwaarden
    s.text(422, 180, "TP1: 5,0–5,2 V bij AAN, 0 V bij UIT", "tn")
    s.text(700, 160, "TP2: ± 4,9 V", "tn", "middle")
    s.text(700, 236, "TP3: 3,3 V", "tn", "middle")
    return s.render()


# ═════════════════════════════════════════════════════════════════════
#  Figuur 4 — zijaanzicht: waar de antennes komen
# ═════════════════════════════════════════════════════════════════════
def antenne():
    k = 1.6                                   # px per mm
    s = Svg(700, 560, "Zijaanzicht van de CanSat onder de parachute: GPS bovenaan "
            "met de patch naar boven; de radio onderaan; een draad van 8,2 cm aan ANT "
            "steekt recht naar beneden uit de bodem; een draad van 8,2 cm aan GND "
            "loopt binnen tegen de wand naar boven.", "f4")
    cx = 240
    cw, ch = 66 * k, 115 * k
    x0, y0 = cx - cw / 2, 150
    y1 = y0 + ch
    ant = 82 * k
    xr = x0 + cw + 30                         # begin van de labels rechts
    # parachute
    s.add(f'<path d="M{cx - 120} 66 Q{cx} -14 {cx + 120} 66 Z" class="canopy"/>')
    for x in (cx - 120, cx - 40, cx + 40, cx + 120):
        s.line(x, 66, cx - cw / 2 + 6 if x < cx else cx + cw / 2 - 6, y0, "shroud")
    s.text(cx + 128, 50, "parachute", "tl")
    # blik
    s.rect(x0, y0, cw, ch, "box can", rx=6)
    s.text(x0 + cw + 8, y1 + 16, "blik: Ø 66 mm, 115 mm hoog", "tn")

    def label(y, tekst, x_from):
        s.line(x_from, y, xr - 4, y, "leader")
        s.text(xr, y + 4, tekst, "tl")

    # GPS bovenaan
    s.rect(x0 + 14, y0 + 14, cw - 28, 6, "comp fillsheet")
    s.rect(cx - 10, y0 + 6, 20, 8, "comp patch")
    label(y0 + 12, "GPS: patch naar boven, niets erboven", x0 + cw - 12)
    # IMU's plat
    yi = y0 + 66
    s.rect(x0 + 14, yi, cw - 40, 5, "comp fillsheet")
    s.path([(cx - 6, yi), (cx - 6, yi - 24)], "wire nink", arrow="nink")
    s.text(cx + 2, yi - 14, "Z", "tp strong")
    label(yi + 2, "BNO055 en LSM6DSO plat, Z naar boven", x0 + cw - 24)
    # schakelaar in de rechterwand
    ys = y0 + 98
    s.rect(x0 + cw - 4, ys - 7, 8, 14, "comp nctl fillsheet")
    label(ys, "schakelaar in de wand, bereikbaar", x0 + cw + 6)
    # batterij rechtop tegen de wand
    s.rect(x0 + cw - 24, y0 + 112, 14, 56, "comp cellfill")
    label(y0 + 140, "LiPo rechtop, vastgezet", x0 + cw - 8)
    # radio onderaan
    yr = y1 - 22
    s.rect(cx - 30, yr, 60, 7, "comp fillsheet")
    label(yr + 3, "RFM95W onderaan", cx + 32)
    # antenne: ANT naar beneden, GND naar boven langs de wand
    xa = cx - 20
    s.path([(xa, yr + 7), (xa, y1 + ant)], "wire antwire")
    s.circle(xa, y1, 3, "comp fillsheet")
    xg = x0 + 8
    s.path([(cx - 26, yr + 3), (xg, yr + 3), (xg, yr + 3 - ant)], "wire counter")
    # maatlijnen
    s.line(xa + 26, y1, xa + 26, y1 + ant, "dim-line")
    for y in (y1, y1 + ant):
        s.line(xa + 20, y, xa + 32, y, "dim-line")
    s.text(xa + 38, y1 + ant / 2 - 4, "8,2 cm aan ANT,", "tp strong")
    s.text(xa + 38, y1 + ant / 2 + 12, "recht naar beneden", "tl")
    s.line(xg - 18, yr + 3 - ant, xg - 18, yr + 3, "dim-line")
    for y in (yr + 3 - ant, yr + 3):
        s.line(xg - 24, y, xg - 12, y, "dim-line")
    s.text(xg - 26, yr + 3 - ant / 2 - 6, "8,2 cm aan GND,", "tp strong", "end")
    s.text(xg - 26, yr + 3 - ant / 2 + 10, "binnen tegen de wand", "tl", "end")
    s.text(xa, y1 + ant + 30, "naar de grond", "tn", "middle")
    s.path([(xa, y1 + ant + 36), (xa, y1 + ant + 54)], "wire nink", arrow="nink")
    return s.render()
