"""Maakt de pagina over het breadboard (Teensy, vier sensoren, radio).

  python maak_breadbord.py <pad naar de repository> [--pdf] [--png MAP]

Schrijft:
  assemblage/breadbord.html        de pagina (zonder <html>-skelet: zo wordt
                                   ze als artifact gepubliceerd)
  downloads/CanSat_breadbord.pdf   met --pdf: om af te drukken (A4, fig. 1
                                   op een liggend blad)
Met --png MAP komen er ook schermafbeeldingen in MAP (licht en donker). De
tekeningen staan in breadbord_svg.py.
"""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breadbord_svg  # noqa: E402
from maak_draadschema import chrome, fonts_inline, volledig  # noqa: E402


def bouw(repo):
    with open(os.path.join(repo, "assemblage_bron", "breadbord_bron.html"),
              encoding="utf-8") as fh:
        page = fh.read()
    for naam, fn in (("breadbord", breadbord_svg.breadbord),
                     ("vrij", breadbord_svg.vrij_gaatje)):
        plek = f"<!-- FIGUUR:{naam} -->"
        assert plek in page, plek
        page = page.replace(plek, fn())
    uit = os.path.join(repo, "assemblage", "breadbord.html")
    with open(uit, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"{uit}: {len(page) // 1024} kB")
    return page


def pdf(repo, page):
    uit = os.path.join(repo, "downloads", "CanSat_breadbord.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        html = os.path.join(tmp, "breadbord.html")
        with open(html, "w", encoding="utf-8") as fh:
            fh.write(volledig(fonts_inline(page), "light"))
        chrome("--no-pdf-header-footer", f"--print-to-pdf={uit}", f"file://{html}")
    print(f"{uit}: {os.path.getsize(uit) // 1024} kB")


def png(page, map_, breedte=1280, hoogte=9000):
    os.makedirs(map_, exist_ok=True)
    page = fonts_inline(page)
    for theme in ("light", "dark"):
        html = os.path.join(map_, f"breadbord_{theme}.html")
        with open(html, "w", encoding="utf-8") as fh:
            fh.write(volledig(page, theme))
        uit = os.path.join(map_, f"breadbord_{theme}.png")
        chrome(f"--window-size={breedte},{hoogte}", f"--screenshot={uit}", f"file://{html}")
        print("geschreven:", uit)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("--pdf", action="store_true")
    p.add_argument("--png", metavar="MAP")
    a = p.parse_args()
    repo = os.path.abspath(a.repo)
    page = bouw(repo)
    if a.pdf:
        pdf(repo, page)
    if a.png:
        png(page, a.png)


if __name__ == "__main__":
    main()
