"""Maakt downloads/CanSat_wedstrijd.zip (geen bovenste map: uitpakken in
C:\\CanSat). Neemt de bestanden zoals ze in git staan (HEAD).

  python maak_zip.py <pad naar de repository>
  python maak_zip.py <pad naar de repository> --map <doelmap>
      zet dezelfde bestanden uit de werkmap in een gewone map (om te testen)

De sensortest zit er bewust niet in: op de wedstrijd hoort alleen de
vluchtcode op de CanSat.
"""
import os
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.abspath(sys.argv[1])
OUT = os.path.join(REPO, "downloads", "CanSat_wedstrijd.zip")
STAMP = (2026, 11, 12, 12, 0, 0)      # vaste datum: zelfde inhoud = zelfde zip

# (plaats in de zip, bron in de repository)
FILES = [
    ("HANDLEIDING.html", "wedstrijd/HANDLEIDING.html"),
    ("HANDLEIDING.md", "wedstrijd/HANDLEIDING.md"),
    ("START_METING.bat", "wedstrijd/START_METING.bat"),
    ("DASHBOARD_OPNIEUW.bat", "wedstrijd/DASHBOARD_OPNIEUW.bat"),
    ("INSTALLEER_PAKKETTEN.bat", "wedstrijd/INSTALLEER_PAKKETTEN.bat"),
    ("FLIGHT_REPORT.bat", "wedstrijd/FLIGHT_REPORT.bat"),
    ("requirements.txt", "cansat/dashboard/requirements.txt"),
    ("start_meting.py", "cansat/start_meting.py"),
    ("dashboard/dashboard_scherm1.py", "cansat/dashboard/dashboard_scherm1.py"),
    ("dashboard/dashboard_scherm2.py", "cansat/dashboard/dashboard_scherm2.py"),
    ("dashboard/krachten.py", "cansat/dashboard/krachten.py"),
    ("dashboard/requirements.txt", "cansat/dashboard/requirements.txt"),
    ("stream/stream_dashboard.py", "livestream/stream/stream_dashboard.py"),
    ("logos/LEES_MIJ.txt", "livestream/logos/LEES_MIJ.txt"),
    ("logos/voorbeeld_logo_school.png", "livestream/logos/voorbeeld_logo_school.png"),
    ("logos/voorbeeld_logo_team.png", "livestream/logos/voorbeeld_logo_team.png"),
    ("obs/start.png", "livestream/obs/start.png"),
    ("obs/pauze.png", "livestream/obs/pauze.png"),
    ("obs/einde.png", "livestream/obs/einde.png"),
    ("obs/naambalk.png", "livestream/obs/naambalk.png"),
    ("tools/serial_logger.py", "cansat/tools/serial_logger.py"),
    ("tools/check_csv.py", "cansat/tools/check_csv.py"),
    ("tools/gen_test_csv.py", "cansat/tools/gen_test_csv.py"),
    ("tools/krachten_analyse.py", "cansat/tools/krachten_analyse.py"),
    ("tools/flight_report.py", "cansat/tools/flight_report.py"),
    ("Cansat2027_teensy/Cansat2027_teensy.ino",
     "vluchtcode/Cansat2027_teensy/Cansat2027_teensy.ino"),
    ("pico/main.py", "cansat/pico/main.py"),
    ("schema/CanSat_draadschema.pdf", "downloads/CanSat_draadschema.pdf"),
    ("schema/CanSat_breadbord.pdf", "downloads/CanSat_breadbord.pdf"),
]
for name in sorted(os.listdir(os.path.join(REPO, "wedstrijd", "beelden"))):
    FILES.append((f"beelden/{name}", f"wedstrijd/beelden/{name}"))


def from_git(path):
    return subprocess.run(["git", "-C", REPO, "show", f"HEAD:{path}"],
                          check=True, capture_output=True).stdout


def windows(arc, data):
    if arc.endswith((".bat", ".txt")):            # Windows: CRLF
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data


def naar_map(doel):
    """Dezelfde bestanden uit de werkmap (niet uit git), om te testen."""
    for arc, src in FILES:
        pad = os.path.join(doel, *arc.split("/"))
        os.makedirs(os.path.dirname(pad), exist_ok=True)
        with open(os.path.join(REPO, src), "rb") as fh:
            data = fh.read()
        with open(pad, "wb") as fh:
            fh.write(windows(arc, data))
    print(f"{doel}: {len(FILES)} bestanden uit de werkmap")


def main():
    if sys.argv[2:3] == ["--map"]:
        doel = os.path.abspath(sys.argv[3])
        shutil.rmtree(doel, ignore_errors=True)
        naar_map(doel)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc, src in FILES:
            info = zipfile.ZipInfo(arc, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, windows(arc, from_git(src)))
    print(f"{OUT}: {len(FILES)} bestanden, {os.path.getsize(OUT) // 1024} kB")


if __name__ == "__main__":
    main()
