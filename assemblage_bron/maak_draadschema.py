"""Maakt het draadschema voor de assemblage van de CanSat.

  python maak_draadschema.py <pad naar de repository> [--pdf] [--png MAP]

Schrijft:
  assemblage/draadschema.html        de pagina (zonder <html>-skelet: zo
                                     wordt ze als artifact gepubliceerd)
  downloads/CanSat_draadschema.pdf   met --pdf: om af te drukken (A4,
                                     fig. 1 en 3 liggend)
Met --png MAP komen er ook schermafbeeldingen in MAP (licht en donker), om
na te kijken. De tekeningen zelf staan in schema_svg.py.
"""
import argparse
import base64
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema_svg  # noqa: E402

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS = re.compile(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">')
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")


def bouw(repo):
    bron = os.path.join(repo, "assemblage_bron", "draadschema_bron.html")
    with open(bron, encoding="utf-8") as fh:
        page = fh.read()
    for naam, fn in (("overzicht", schema_svg.overzicht),
                     ("pinnen", schema_svg.teensy_pinnen),
                     ("voeding", schema_svg.voeding),
                     ("antenne", schema_svg.antenne)):
        plek = f"<!-- FIGUUR:{naam} -->"
        assert plek in page, plek
        page = page.replace(plek, fn())
    uit = os.path.join(repo, "assemblage", "draadschema.html")
    os.makedirs(os.path.dirname(uit), exist_ok=True)
    with open(uit, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"{uit}: {len(page) // 1024} kB")
    return page


def curl(url):
    return subprocess.run(["curl", "-sSL", "--max-time", "30", "-A", UA, url],
                          check=True, capture_output=True).stdout


def fonts_inline(page):
    """De Google Fonts in de pagina zetten (de PDF-printer haalt niets op)."""
    m = FONTS.search(page)
    if not m:
        return page
    css = curl(m.group(1).replace("&amp;", "&")).decode()

    def embed(mt):
        data = base64.b64encode(curl(mt.group(1))).decode()
        return f"url(data:font/woff2;base64,{data})"
    css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", embed, css)
    return page.replace(m.group(0), f"<style>{css}</style>")


def volledig(page, theme=None):
    attr = f' data-theme="{theme}"' if theme else ""
    return (f'<!doctype html><html lang="nl"{attr}><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'</head><body>{page}</body></html>')


def chrome(*args):
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--hide-scrollbars", "--virtual-time-budget=4000", *args],
                   check=True, capture_output=True)


def pdf(repo, page):
    uit = os.path.join(repo, "downloads", "CanSat_draadschema.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        html = os.path.join(tmp, "draadschema.html")
        with open(html, "w", encoding="utf-8") as fh:
            fh.write(volledig(fonts_inline(page), "light"))
        chrome("--no-pdf-header-footer", f"--print-to-pdf={uit}", f"file://{html}")
    print(f"{uit}: {os.path.getsize(uit) // 1024} kB")


def png(page, map_, breedte=1280, hoogte=9000):
    os.makedirs(map_, exist_ok=True)
    page = fonts_inline(page)
    for theme in ("light", "dark"):
        html = os.path.join(map_, f"pagina_{theme}.html")
        with open(html, "w", encoding="utf-8") as fh:
            fh.write(volledig(page, theme))
        uit = os.path.join(map_, f"pagina_{theme}.png")
        chrome(f"--window-size={breedte},{hoogte}", f"--screenshot={uit}",
               f"file://{html}")
        print("geschreven:", uit)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("--pdf", action="store_true")
    p.add_argument("--png", metavar="MAP")
    a = p.parse_args()
    page = bouw(os.path.abspath(a.repo))
    if a.pdf:
        pdf(os.path.abspath(a.repo), page)
    if a.png:
        png(page, a.png)


if __name__ == "__main__":
    main()
