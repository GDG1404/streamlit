"""Maakt alle beelden voor het livestream-pakket (niet nodig voor de leerlingen).

  python maak_beelden.py <pad naar livestream/>

Schrijft:
  obs/start.png, obs/pauze.png, obs/einde.png, obs/naambalk.png
  logos/voorbeeld_logo_school.png, logos/voorbeeld_logo_team.png
  beelden/*.png  (schermafbeeldingen en voorbeelden van de OBS-scènes)
"""
import math
import os
import random
import sys

import matplotlib
matplotlib.use("Agg")
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(sys.argv[1])
FONTS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
W, H = 1920, 1080
PAGE, SURFACE, BORDER = (13, 13, 13), (26, 26, 25), (44, 44, 42)
INK, INK2, MUTED, ACCENT = (240, 239, 236), (195, 194, 183), (137, 135, 129), (57, 135, 229)


def font(size, bold=False):
    return ImageFont.truetype(os.path.join(
        FONTS, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)


def centered(d, y, text, f, fill, x_mid=W // 2, spacing=0):
    if spacing:                                   # letter-spaced text
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = x_mid - total / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=f, fill=fill)
            x += w + spacing
        return
    w = d.textlength(text, font=f)
    d.text((x_mid - w / 2, y), text, font=f, fill=fill)


def background():
    """Donkere achtergrond met een zachte gloed en een baan (orbit)."""
    img = Image.new("RGB", (W, H), PAGE)
    glow = Image.new("RGB", (W, H), PAGE)
    gd = ImageDraw.Draw(glow)
    for r in range(900, 0, -12):                  # radiale gloed rechtsboven
        t = r / 900
        c = tuple(int(p + (s - p) * (1 - t) * 0.55) for p, s in zip(PAGE, (22, 36, 58)))
        gd.ellipse([1500 - r, 120 - r, 1500 + r, 120 + r], fill=c)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(40)), 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    d.arc([-700, 380, 2600, 2300], start=200, end=338, fill=(57, 135, 229, 90), width=3)
    d.ellipse([1508, 436, 1532, 460], fill=ACCENT)          # "satelliet" op de baan
    return img


def screen(title_small, title_big, line):
    img = background()
    d = ImageDraw.Draw(img)
    centered(d, 380, title_small, font(40, True), ACCENT, spacing=10)
    centered(d, 450, title_big, font(120, True), INK)
    centered(d, 620, line, font(40), INK2)
    d.line([(W // 2 - 60, 720), (W // 2 + 60, 720)], fill=ACCENT, width=4)
    return img


def name_bar():
    """Doorzichtige laag (1920×1080) met een naambalk linksonder."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([80, 890, 1100, 1030], radius=18, fill=(26, 26, 25, 230))
    d.rounded_rectangle([80, 890, 92, 1030], radius=6, fill=ACCENT + (255,))
    return img


def logo_school():
    img = Image.new("RGBA", (640, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(40, 30), (220, 30), (220, 160), (130, 270), (40, 160)], fill=(29, 52, 97, 255),
              outline=(240, 239, 236, 255))
    d.text((84, 80), "S", font=font(110, True), fill=INK)
    d.text((250, 70), "SCHOOL", font=font(72, True), fill=INK)
    d.text((252, 160), "LOGO", font=font(72), fill=INK2)
    return img


def logo_team():
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([10, 10, 390, 390], fill=ACCENT + (255,))
    d.rounded_rectangle([150, 90, 250, 250], radius=14, fill=INK + (255,))    # het blikje
    d.ellipse([150, 75, 250, 105], fill=(220, 219, 214, 255))
    d.line([(200, 250), (200, 300)], fill=INK, width=6)                       # touw
    d.arc([120, 20, 280, 120], start=180, end=360, fill=INK, width=8)         # parachute
    w = d.textlength("TEAM", font=font(54, True))
    d.text((200 - w / 2, 300), "TEAM", font=font(54, True), fill=INK)
    return img


def camera_illustration(w, h, label=True, label_top=False):
    """Getekend voorbeeld van een camerabeeld (geen echte foto)."""
    S = 2
    img = Image.new("RGB", (w * S, h * S))
    d = ImageDraw.Draw(img)
    hor = int(h * S * 0.70)
    for y in range(hor):
        t = y / hor
        d.line([(0, y), (w * S, y)], fill=tuple(int(a + (b - a) * t) for a, b in
                                                 zip((74, 134, 206), (196, 221, 240))))
    for y in range(hor, h * S):
        t = (y - hor) / (h * S - hor)
        d.line([(0, y), (w * S, y)], fill=tuple(int(a + (b - a) * t) for a, b in
                                                 zip((112, 158, 82), (64, 110, 48))))
    random.seed(4)
    x = 0
    while x < w * S:
        r = random.randint(18, 42) * S * w // 1344
        d.ellipse([x - r, hor - r * 1.3, x + r, hor + r * 0.4], fill=(46, 82, 46))
        x += max(4, int(r * 1.2))
    clouds = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    k = w * S / 1344
    for cx, cy, s in ((0.18, 0.22, 1.0), (0.80, 0.14, 0.8), (0.45, 0.35, 0.6)):
        for dx, dy, r in ((0, 0, 40), (45, 8, 32), (-42, 10, 30), (20, -18, 30)):
            R = r * s * 2 * k
            px, py = cx * w * S + dx * s * 2 * k, cy * h * S + dy * s * 2 * k
            cd.ellipse([px - R, py - R * 0.7, px + R, py + R * 0.7], fill=(255, 255, 255, 170))
    clouds = clouds.filter(ImageFilter.GaussianBlur(6 * k))
    img.paste(clouds, (0, 0), clouds)
    smoke = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(smoke)
    x0, y0, x1, y1 = 0.60 * w * S, hor - 6 * k, 0.66 * w * S, 0.20 * h * S
    for i in range(140):
        t = i / 139
        px = x0 + (x1 - x0) * t + math.sin(t * 7) * 6 * k * (1 - t)
        py = y0 + (y1 - y0) * t
        r = (16 - 11 * t) * 2 * k
        sd.ellipse([px - r, py - r, px + r, py + r], fill=(245, 245, 245, int(200 * (1 - 0.55 * t))))
    smoke = smoke.filter(ImageFilter.GaussianBlur(3 * k))
    img.paste(smoke, (0, 0), smoke)
    d = ImageDraw.Draw(img)
    ang = math.atan2(y1 - y0, x1 - x0)

    def rot(px, py):
        return (x1 + px * math.cos(ang) - py * math.sin(ang),
                y1 + px * math.sin(ang) + py * math.cos(ang))
    q = 2 * k
    d.polygon([rot(-30 * q, -5 * q), rot(14 * q, -5 * q), rot(26 * q, 0),
               rot(14 * q, 5 * q), rot(-30 * q, 5 * q)], fill=(240, 240, 240))
    d.polygon([rot(-30 * q, -5 * q), rot(-38 * q, -12 * q), rot(-22 * q, -5 * q)], fill=(200, 60, 50))
    d.polygon([rot(-30 * q, 5 * q), rot(-38 * q, 12 * q), rot(-22 * q, 5 * q)], fill=(200, 60, 50))
    d.polygon([rot(-30 * q, -3 * q), rot(-44 * q, 0), rot(-30 * q, 3 * q)], fill=(250, 178, 25))
    img = img.resize((w, h), Image.LANCZOS)
    if label:
        dl = ImageDraw.Draw(img, "RGBA")
        f = font(28 if label_top else 17)
        text = "Voorbeeld (tekening) — hier komt jullie camerabeeld"
        tw = dl.textlength(text, font=f)
        pad = 12
        y = pad if label_top else h - pad - f.size - 2 * pad
        dl.rectangle([pad, y, pad * 3 + tw, y + f.size + 2 * pad], fill=(13, 13, 13, 190))
        dl.text((pad * 2, y + pad * 0.7), text, font=f, fill=INK)
    return img


def paste_logo(canvas, logo, x, y, height, anchor="left"):
    w = int(logo.width * height / logo.height)
    lg = logo.resize((w, height), Image.LANCZOS)
    if anchor == "right":
        x -= w
    canvas.paste(lg, (x, y), lg)


def dashboard_shots(school, team):
    """Echte schermafbeeldingen van het streamdashboard (1920×1080)."""
    sys.path.insert(0, os.path.join(ROOT, "stream"))
    matplotlib.use = lambda *a, **k: None
    import stream_dashboard as sd
    tmp = os.path.join(ROOT, "beelden", "_logos")
    os.makedirs(tmp, exist_ok=True)
    school.save(os.path.join(tmp, "logo_school.png"))
    team.save(os.path.join(tmp, "logo_team.png"))
    sd.LOGO_DIR = tmp
    sd.TITLE = "CanSat 2027 · Team Kepler"
    random.seed(11)

    d = sd.StreamDashboard(demo=True)
    for k in range(96):
        if k in (41, 63):
            continue
        d.q.put(("line", sd.demo_packet(k), 100.0 + k))
        d.tick(now=100.0 + k + 0.05)
    d.fig.savefig(os.path.join(ROOT, "beelden", "dashboard_demo.png"),
                  facecolor=sd.C["page"], dpi=150)

    lines = [l for l in open(sys.argv[2], newline="").read().split("\r\n") if l][1:]
    d2 = sd.StreamDashboard()
    for k, line in enumerate(lines[:85]):
        d2.q.put(("line", line, 500.0 + k))
        d2.tick(now=500.0 + k + 0.05)
    d2.fig.savefig(os.path.join(ROOT, "beelden", "dashboard_droogtest.png"),
                   facecolor=sd.C["page"], dpi=150)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


def obs_sketch():
    """Schets van het hoofdvenster van OBS (geen echte schermafbeelding)."""
    img = Image.new("RGB", (1600, 1000), (36, 38, 46))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1600, 40], fill=(28, 30, 36))
    d.text((20, 9), "File   Edit   View   Docks   Profile   Scene Collection   Tools   Help",
           font=font(18), fill=(200, 200, 205))
    d.rectangle([40, 60, 1560, 640], fill=(10, 10, 12), outline=(80, 82, 90), width=2)
    centered(d, 320, "VOORBEELD (preview): wat de kijkers zien", font(30, True), (200, 200, 205),
             x_mid=800)
    panels = [("Scenes", ["Start", "Camera", "Dashboard", "Pause", "End"]),
              ("Sources", ["Dashboard (window)", "Camera", "Logo team"]),
              ("Audio Mixer", ["Desktop Audio  (mute!)", "Mic/Aux"]),
              ("Scene Transitions", ["Fade   300 ms"]),
              ("Controls", ["Start Streaming", "Start Recording", "Studio Mode", "Settings", "Exit"])]
    x = 40
    widths = [300, 330, 330, 260, 260]
    for (title, items), pw in zip(panels, widths):
        d.rectangle([x, 670, x + pw, 980], fill=(44, 46, 56), outline=(80, 82, 90), width=2)
        d.text((x + 14, 680), title, font=font(22, True), fill=INK)
        for i, it in enumerate(items):
            box = [x + 12, 720 + i * 50, x + pw - 12, 760 + i * 50]
            if title == "Controls":
                d.rounded_rectangle(box, radius=6, fill=(70, 74, 90))
            d.text((x + 24, 728 + i * 50), it, font=font(19), fill=(220, 220, 225))
        x += pw + 15
    tag = "Schets — jullie OBS ziet er ongeveer zo uit"
    d.text((1560 - d.textlength(tag, font=font(20)), 12), tag, font=font(20), fill=(250, 178, 25))
    return img


def main():
    for sub in ("obs", "logos", "beelden"):
        os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
    start = screen("STARTING SOON", "CanSat 2027", "The livestream starts in a few minutes")
    pause = screen("SHORT BREAK", "We'll be right back", "Stay tuned")
    end = screen("THANKS FOR WATCHING", "CanSat 2027", "See you at the next launch")
    start.save(os.path.join(ROOT, "obs", "start.png"))
    pause.save(os.path.join(ROOT, "obs", "pauze.png"))
    end.save(os.path.join(ROOT, "obs", "einde.png"))
    bar = name_bar()
    bar.save(os.path.join(ROOT, "obs", "naambalk.png"))
    school, team = logo_school(), logo_team()
    school.save(os.path.join(ROOT, "logos", "voorbeeld_logo_school.png"))
    team.save(os.path.join(ROOT, "logos", "voorbeeld_logo_team.png"))

    dashboard_shots(school, team)

    # voorbeelden van de vier OBS-scènes
    s = start.copy()
    paste_logo(s, school, 80, 70, 150)
    paste_logo(s, team, 1840, 70, 150, anchor="right")
    ds = ImageDraw.Draw(s)
    centered(ds, 780, "Today 14:00 · Team Kepler", font(44, True), INK)
    s.save(os.path.join(ROOT, "beelden", "scene_start.png"))

    cam = camera_illustration(W, H, label_top=True).convert("RGBA")
    cam.alpha_composite(bar)
    dc = ImageDraw.Draw(cam)
    dc.text((130, 905), "Team Kepler", font=font(48, True), fill=INK)
    dc.text((130, 968), "CanSat 2027 · live from the launch site", font=font(30), fill=INK2)
    paste_logo(cam, team, 1840, 50, 110, anchor="right")
    cam.convert("RGB").save(os.path.join(ROOT, "beelden", "scene_camera.png"))

    dash = Image.open(os.path.join(ROOT, "beelden", "dashboard_demo.png")).convert("RGB")
    dash = dash.resize((W, H), Image.LANCZOS)
    dash.paste(camera_illustration(672, 378), (1200, 150))
    dash.save(os.path.join(ROOT, "beelden", "scene_dashboard.png"))

    e = end.copy()
    paste_logo(e, school, 80, 70, 150)
    paste_logo(e, team, 1840, 70, 150, anchor="right")
    e.save(os.path.join(ROOT, "beelden", "scene_einde.png"))

    obs_sketch().save(os.path.join(ROOT, "beelden", "obs_schets.png"))
    print("klaar:", sorted(os.listdir(os.path.join(ROOT, "beelden"))))


if __name__ == "__main__":
    main()
