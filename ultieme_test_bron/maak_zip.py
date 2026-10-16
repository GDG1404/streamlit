"""Maakt downloads/Ultieme_test_breadbord.zip (geen bovenste map: uitpakken in
C:\\UltiemeTest). Neemt de bestanden zoals ze in git staan (HEAD).

  python maak_zip.py <pad naar de repository>
"""
import os
import subprocess
import sys
import zipfile

REPO = os.path.abspath(sys.argv[1])
OUT = os.path.join(REPO, "downloads", "Ultieme_test_breadbord.zip")
STAMP = (2026, 10, 16, 12, 0, 0)      # vaste datum: zelfde inhoud = zelfde zip

# (plaats in de zip, bron in de repository)
FILES = [
    ("HANDLEIDING.html", "ultieme_test/HANDLEIDING.html"),
    ("HANDLEIDING.md", "ultieme_test/HANDLEIDING.md"),
    ("START_METING.bat", "ultieme_test/START_METING.bat"),
    ("INSTALLEER_PAKKETTEN.bat", "ultieme_test/INSTALLEER_PAKKETTEN.bat"),
    ("requirements.txt", "cansat/dashboard/requirements.txt"),
    ("start_meting.py", "cansat/start_meting.py"),
    ("dashboard/dashboard_scherm1.py", "cansat/dashboard/dashboard_scherm1.py"),
    ("dashboard/dashboard_scherm2.py", "cansat/dashboard/dashboard_scherm2.py"),
    ("dashboard/requirements.txt", "cansat/dashboard/requirements.txt"),
    ("tools/serial_logger.py", "cansat/tools/serial_logger.py"),
    ("tools/check_csv.py", "cansat/tools/check_csv.py"),
    ("tools/gen_test_csv.py", "cansat/tools/gen_test_csv.py"),
    ("teensy/Cansat2027_teensy/Cansat2027_teensy.ino",
     "vluchtcode/Cansat2027_teensy/Cansat2027_teensy.ino"),
    ("pico/main.py", "cansat/pico/main.py"),
]
for name in sorted(os.listdir(os.path.join(REPO, "ultieme_test", "beelden"))):
    FILES.append((f"beelden/{name}", f"ultieme_test/beelden/{name}"))


def from_git(path):
    return subprocess.run(["git", "-C", REPO, "show", f"HEAD:{path}"],
                          check=True, capture_output=True).stdout


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc, src in FILES:
            data = from_git(src)
            if arc.endswith((".bat", ".txt")):        # Windows: CRLF
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            info = zipfile.ZipInfo(arc, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    print(f"{OUT}: {len(FILES)} bestanden, {os.path.getsize(OUT) // 1024} kB")


if __name__ == "__main__":
    main()
