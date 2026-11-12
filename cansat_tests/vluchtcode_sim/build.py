"""Compiles a flight sketch (.ino) for the computer, with the mock libraries.

  python build.py <sketch.ino> <name> <path to arduinoFFT/src>

The result is build/<name>: run it as  build/<name> <scenario> <out dir> <seconds>.
Needs g++ and the source of the real arduinoFFT library (version 2.x):
  git clone --depth 1 https://github.com/kosme/arduinoFFT
"""
import os
import re
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))


def build(ino, name, fft_src):
    build_dir = os.path.join(here, "build")
    os.makedirs(build_dir, exist_ok=True)
    link = os.path.join(build_dir, "arduinoFFT_src")
    if os.path.islink(link):
        os.remove(link)
    os.symlink(os.path.abspath(fft_src), link)
    src = open(ino, encoding="utf-8").read()
    # the Arduino IDE adds the prototypes of all functions itself
    protos = []
    for m in re.finditer(r"^(?:static\s+)?(?:void|bool|int|float|double|uint32_t|unsigned long)\s+\w+\s*\([^;{]*\)\s*\{",
                         src, re.M):
        sig = m.group(0).rstrip("{").strip()
        if not re.match(r"void\s+(setup|loop)\b", sig):
            protos.append(sig + ";")
    last_inc = max(m.end() for m in re.finditer(r"^#include.*$", src, re.M))
    cpp = os.path.join(build_dir, name + ".cpp")
    with open(cpp, "w", encoding="utf-8") as fh:
        fh.write('#include "Arduino.h"\n' + src[:last_inc] + "\n// prototypes\n" + "\n".join(protos)
                 + '\n#line 1 "sketch"\n' + src[last_inc:])
    fft_o = os.path.join(build_dir, "fft.o")
    subprocess.check_call(["g++", "-O2", "-c", "-DArduinoFFT=ArduinoFFT_real", "-w",
                           os.path.join(fft_src, "arduinoFFT.cpp"), "-o", fft_o])
    cmd = ["g++", "-O2", "-std=gnu++17", "-Wall", "-Wextra", "-Wno-unused-parameter",
           "-I", os.path.join(here, "mock"), "-I", build_dir,
           cpp, os.path.join(here, "driver.cpp"), fft_o, "-o", os.path.join(build_dir, name)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stderr:
        print(r.stderr[-6000:])
    return r.returncode


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(build(sys.argv[1], sys.argv[2], sys.argv[3]))
