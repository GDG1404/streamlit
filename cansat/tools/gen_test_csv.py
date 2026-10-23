"""
CanSat 2027 — test-CSV generator (zonder hardware)
===================================================

Schrijft een CSV in EXACT hetzelfde formaat als sensortest_fft.ino
(zelfde kolommen, decimalen en CRLF-regeleinden), voor een bureautest
van 2 minuten:

   0–25 s  geen GPS-fix (sketch logt dan placeholder-coördinaten)
     35 s  tik op de tafel: korte schok (~7 g in acc_peak_g)
  40–55 s  CanSat met de hand geschud (trilling ~4–5 Hz, ~0,6 g)
     60 s  handklap (piek in audio_rms)
  70–90 s  trap op gelopen (~6 m hoger), GPS ziet 1,2 m/s richting oost

Met --radio komt er een bestand zoals de logger het maakt als de gegevens
via de Pico-ontvanger (radio) binnenkomen: alleen de 13 waarden van het
radiopakket (de rest is 'nan'), met RSSI en SNR. Het scenario is dan een
afstandstest: de CanSat gaat van 1 m tot 100 m ver, een paar pakketten
gaan verloren. Het pakket bevat ook de FFT (sterkte en 5 trillingsbanden).

Met --vlucht komt er een volledige oefenvlucht, berekend met de
natuurkunde: 60 s op de lanceerplaats, lancering (10 g), hoogste punt op
ongeveer 1 km, parachute, daling en landing. De massa en de parachute
komen uit dashboard/krachten.py. De Cd van de parachute is CD_OEFEN (0,50):
tools/krachten_analyse.py moet die terugvinden. Werkt ook met --radio en
--live.

Gebruik:
  python gen_test_csv.py test_000.csv            # in één keer (replay)
  python gen_test_csv.py cansat27_live.csv --live  # 1 regel/s (live)
  python gen_test_csv.py radio_test.csv --radio  # zoals via de radio
  python gen_test_csv.py oefenvlucht.csv --vlucht  # een volledige vlucht
"""

import argparse
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "dashboard"))
import serial_logger  # noqa: E402  (zelfde omzetting als bij een echte meting)
import krachten as K  # noqa: E402  (massa en parachute van onze CanSat)

COLUMNS = [  # identiek aan CSV_HEADER in sensortest_fft.ino
    "millis", "temp_C", "press_hPa", "alt_m", "lat", "lon", "time_utc",
    "gyro_x", "gyro_y", "gyro_z", "lacc_x", "lacc_y", "lacc_z",
    "grav_x", "grav_y", "grav_z", "heading", "roll", "pitch",
    "qw", "qx", "qy", "qz", "fft_peak_hz", "fft_peak_amp", "audio_rms",
    "acc_peak_g", "gps_course_deg", "gps_speed_ms",
    "vib_0_10_g", "vib_10_30_g", "vib_30_60_g", "vib_60_120_g", "vib_120_208_g",
]
BAND_EDGES_HZ = (0, 10, 30, 60, 120, 208)
DURATION_S = 120


def make_row(t, t_ms):
    """Eén logregel zoals writeCSV() in de sketch hem opbouwt."""
    shake = 40 <= t < 55
    alt = 612.3 + random.gauss(0, 0.08) + (min(t - 70, 20) * 0.3 if t >= 70 else 0)
    press = 1014.0 * (1 - alt / 44330.0) ** 5.255
    temp = 21.4 + random.gauss(0, 0.02)
    if t >= 25:  # GPS-fix
        lat = 50.846712 + random.gauss(0, 3e-6)
        lon = 4.352417 + random.gauss(0, 3e-6)
        s = t + 25
        utc = f"09:{12 + s // 60:02d}:{s % 60:02d}"
    else:        # placeholder van de sketch
        lat, lon, utc = 50.457303, 6.221376, "00:00:00"
    a = 6.0 if shake else 0.05
    lacc = [random.gauss(0, a) for _ in range(3)]
    gyro = [random.gauss(0, 60 if shake else 0.2) for _ in range(3)]
    heading = (123.4 + (random.gauss(0, 30) if shake else 0)) % 360
    roll = random.gauss(0, 15 if shake else 0.1)
    pitch = random.gauss(0, 15 if shake else 0.1)
    h2 = math.radians(heading) / 2
    tilt = math.radians(roll) / 2   # kleine kanteling → qx ≠ 0
    q = (math.cos(h2) * math.cos(tilt), math.sin(tilt) * 0.5,
         math.sin(tilt) * 0.3, math.sin(h2) * math.cos(tilt))
    grav = (0.12 + random.gauss(0, 0.01), -0.05 + random.gauss(0, 0.01),
            9.80 + random.gauss(0, 0.005))
    if shake:
        fhz, famp = 4.5 + random.gauss(0, 0.6), 0.6 + random.gauss(0, 0.1)
    else:
        fhz, famp = random.uniform(1, 200), 0.002 + abs(random.gauss(0, 0.001))
    audio = 0.0031 + abs(random.gauss(0, 0.0004)) + (0.21 if t == 60 else 0)
    # grootste versnelling in deze seconde (incl. zwaartekracht, rust ≈ 1 g)
    if t == 35:
        peak = 7.2 + random.gauss(0, 0.3)            # korte schok
    elif shake:
        peak = 2.6 + abs(random.gauss(0, 0.5))
    else:
        peak = 1.0 + abs(random.gauss(0, 0.01))

    # GPS: richting en snelheid over de grond (alleen met fix)
    if t >= 25 and 70 <= t < 90:
        course, speed = 90 + random.gauss(0, 8), 1.2 + random.gauss(0, 0.15)
    elif t >= 25:
        course, speed = random.uniform(0, 360), abs(random.gauss(0, 0.1))
    else:
        course, speed = 0.0, 0.0

    # trilling per frequentieband (g RMS): ruis van de sensor (~1 mg over
    # 208 Hz, verdeeld volgens de breedte van de band) + wat er gebeurt
    bands = [0.001 * math.sqrt((hi - lo) / 208) * (1 + random.gauss(0, 0.1))
             for lo, hi in zip(BAND_EDGES_HZ, BAND_EDGES_HZ[1:])]
    if shake:      # schudden: één lage trilling (~4,5 Hz) → alleen band 0–10
        bands[0] = math.hypot(bands[0], famp / math.sqrt(2))
    if t == 35:    # schok: breedband → alle banden tegelijk
        bands = [b + 0.12 + abs(random.gauss(0, 0.03)) for b in bands]

    def f(v, n):
        return f"{v:.{n}f}"

    return ",".join([
        str(t_ms), f(temp, 2), f(press, 2), f(alt, 2), f(lat, 6), f(lon, 6), utc,
        *(f(g, 3) for g in gyro), *(f(x, 3) for x in lacc),
        *(f(g, 3) for g in grav),
        f(heading, 2), f(roll, 2), f(pitch, 2), *(f(x, 4) for x in q),
        f(fhz, 1), f(famp, 3), f(audio, 4), f(peak, 2),
        f(course % 360, 1), f(max(0.0, speed), 2),
        *(f(abs(b), 4) for b in bands),
    ])


def radio_packet(row, t, opwarmen=True):
    """Het LoRa-pakket dat de vluchtcode van deze meting maakt (19 waarden,
    zelfde decimalen als String(waarde, n) in sendAndLog)."""
    v = dict(zip(COLUMNS, row.split(",")))
    if opwarmen:
        v["temp_C"] = float(v["temp_C"]) + 0.006 * t  # buiten: warmt wat op
    digits = {"temp_C": 1, "press_hPa": 1, "alt_m": 1, "lat": 5, "lon": 5,
              "lacc_x": 2, "lacc_y": 2, "lacc_z": 2, "heading": 1, "roll": 1,
              "pitch": 1, "fft_peak_hz": 0, "audio_rms": 3, "fft_peak_amp": 3,
              **{c: 4 for c in COLUMNS[29:]}}            # de 5 trillingsbanden
    return [f"{float(v[k]):.{n}f}" for k, n in digits.items()]


def radio_quality(t):
    """Afstandstest: van 1 m tot 100 m in 2 minuten, met tussen 80 en 100 s
    een gebouw tussen zender en ontvanger. Geeft RSSI (dBm), SNR (dB) en of
    het pakket verloren gaat."""
    d = 1 + 99 * t / (DURATION_S - 1)
    wall = 80 <= t < 100
    rssi = -40 - 25 * math.log10(d) - (20 if wall else 0) + random.gauss(0, 2)
    snr = max(-10.0, min(10.0, (rssi + 112) / 2 + random.gauss(0, 0.7)))
    lost = random.random() < (0.15 if wall else 0.02)
    return round(rssi), round(snr * 4) / 4, lost


# ── OEFENVLUCHT (--vlucht) ───────────────────────────────────
CD_OEFEN = 0.50        # Cd van de parachute in de oefenvlucht
LANCERING_S = 60.0     # zoveel seconden staat de CanSat op de lanceerplaats
BOOST_G, BOOST_S = 10.0, 1.5   # de motor duwt 1,5 s met 10 g
VRIJE_VAL_S = 1.8      # na het uitwerpen: zo lang vrije val tot de parachute opengaat
OPEN_S = 0.35          # zo lang duurt het openklappen van de parachute
NA_LANDING_S = 25.0    # zo lang ligt de CanSat nog stil na de landing
WIND_MS, WIND_NAAR = 4.5, 65.0    # wind: 4,5 m/s, de CanSat drijft naar 65° (ONO)
LAT0, LON0 = 50.4583, 6.2219      # lanceerplaats (zoals de simulator van de dashboards)
P_ZEE, H_VELD, T_VELD = 1016.0, 290.0, 15.5   # weer: druk op zeeniveau (hPa),
                                              # hoogte van het veld (m), °C


def _druk(h):
    """Luchtdruk (hPa) op h meter boven het veld (standaardatmosfeer)."""
    return P_ZEE * (1 - 2.25577e-5 * (H_VELD + h)) ** 5.25588


def _lucht_temp(h):
    return T_VELD - 0.0065 * h


def _quaternion(heading, roll, pitch):
    """Euler-hoeken (graden) → quaternion (w, x, y, z)."""
    cy, sy = math.cos(math.radians(heading) / 2), math.sin(math.radians(heading) / 2)
    cp, sp = math.cos(math.radians(pitch) / 2), math.sin(math.radians(pitch) / 2)
    cr, sr = math.cos(math.radians(roll) / 2), math.sin(math.radians(roll) / 2)
    return (cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy)


def vlucht_regels(rng):
    """Rekent een volledige vlucht uit, 416 keer per seconde (zoals de
    LSM6DSO), en geeft de logregels: een lijst van (t in s, regel).

    Natuurkunde: de motor duwt 1,5 s met 10 g, daarna vliegt de raket vrij
    door tot het hoogste punt (~1 km). Daar wordt de CanSat uitgeworpen
    (kleine schok), valt VRIJE_VAL_S vrij, en dan gaat de parachute open:
    F = ½·ρ·v²·Cd·A, met Cd = CD_OEFEN en de massa en parachute uit
    krachten.py. De landing geeft een schok groter dan 16 g: elke as wordt
    afgeknipt op 16 g, net als bij de echte LSM6DSO. Daarna valt de CanSat
    om en ligt hij op zijn zij."""
    g, m, area = K.G, K.MASS_KG, K.parachute_area_m2()
    dt = 1.0 / 416
    t = h = v = 0.0                # v: + = omhoog
    x = y = ux = uy = 0.0          # drift (m) en snelheid (m/s) naar oost/noord
    t_top = t_uit = t_open = t_land = None
    temp_sensor = T_VELD + 1.0     # binnen in de can: iets warmer, en traag
    heading = 0.0
    piek = 0.0
    gezien = set()                 # fases sinds de vorige logregel
    volgende = 5.212               # eerste logregel, zoals na setup()
    regels = []
    wind_e = WIND_MS * math.sin(math.radians(WIND_NAAR))
    wind_n = WIND_MS * math.cos(math.radians(WIND_NAAR))

    while t_land is None or t < t_land + NA_LANDING_S:
        t += dt
        # ── welke fase, en welke kracht voelt de CanSat (in g, x/y/z) ──
        fx = fy = 0.0
        if t < LANCERING_S:
            fase, fz = "grond", 1.0
        elif t < LANCERING_S + BOOST_S:
            fase = "motor"
            fz = BOOST_G * min(1.0, (t - LANCERING_S) / 0.05)
            fz += 1.2 * math.sin(2 * math.pi * 85 * t)          # trilling motor
            fx, fy = rng.gauss(0, 0.3), rng.gauss(0, 0.3)
            v += (fz - 1.0) * g * dt
        elif t_uit is None or t < t_uit:
            fase, fz = "stijgen", 0.0                           # vrije vlucht
            fx, fy = rng.gauss(0, 0.05), rng.gauss(0, 0.05)
            v -= g * dt
            if t_top is None and v <= 0:
                t_top = t
                t_uit = t + 0.4
        elif t < t_uit + VRIJE_VAL_S:
            fase = "vrije val"
            rho = float(K.air_density(_druk(h), _lucht_temp(h)))
            drag = 0.5 * rho * v * v * 0.006                     # blik zonder parachute
            fz = drag / (m * g) + (4.0 if t < t_uit + 0.012 else 0.0)   # uitwerpschok
            fx, fy = rng.gauss(0, 0.2), rng.gauss(0, 0.2)
            v += (-g + drag / m) * dt
            t_open = t_uit + VRIJE_VAL_S
        elif h > 0:
            fase = "parachute"
            tau = t - t_open
            vul = min(1.0, (tau / OPEN_S) ** 2)
            cda = CD_OEFEN * area * vul * (
                1 + 0.12 * vul * math.exp(-max(0.0, tau - OPEN_S) / 0.15))
            rho = float(K.air_density(_druk(h), _lucht_temp(h)))
            drag = 0.5 * rho * v * v * cda
            fz = drag / (m * g) + 0.03 * math.sin(2 * math.pi * 0.31 * t)  # windstoten
            fx = 0.12 * math.sin(2 * math.pi * 0.7 * t) + rng.gauss(0, 0.02)  # slingeren
            fy = 0.08 * math.cos(2 * math.pi * 0.7 * t) + rng.gauss(0, 0.02)
            v += (-g + drag / m) * dt
        else:
            if t_land is None:
                t_land, v_land = t, -v
                v, h = 0.0, 0.0
            tau = t - t_land
            if tau < 0.02:                                       # de klap
                fase, fz, fx, fy = "landing", v_land / 0.02 / g + 1.0, 2.5, 0.0
            elif tau < 0.5:
                fase, fz = "geland", 1.0
            elif tau < 0.53:                                     # valt om
                fase, fz, fx = "geland", 0.3, 3.0
            else:
                fase, fz, fx = "geland", 0.0, 1.0                # ligt op zijn zij
        h = max(0.0, h + v * dt) if t_land is None else 0.0
        if t_uit is not None and t >= t_uit:                     # drijft mee met de wind
            if t_land is None:
                ux += (wind_e - ux) * dt / 2.0
                uy += (wind_n - uy) * dt / 2.0
            else:
                ux = uy = 0.0
            x += ux * dt
            y += uy * dt

        # LSM6DSO: elke as tot ±16 g, de grootste versnelling per logregel
        ruis = (rng.gauss(0, 0.01), rng.gauss(0, 0.01), rng.gauss(0, 0.01))
        f16 = [max(-K.SENSOR_MAX_G, min(K.SENSOR_MAX_G, a + r))
               for a, r in zip((fx, fy, fz), ruis)]
        piek = max(piek, math.sqrt(sum(a * a for a in f16)))
        # temperatuursensor: volgt de lucht traag (20 s), 1 °C warmer
        temp_sensor += (_lucht_temp(h) + 1.0 - temp_sensor) * dt / 20.0

        gezien.add(fase)
        if t < volgende:
            continue
        # ── één logregel, zoals sendAndLog() in de vluchtcode ──
        volgende += 1.0 + rng.choice([0, 0, 0.001])
        p = _druk(h) + rng.gauss(0, 0.018)
        alt = 44330.0 * (1 - (p / 1014.0) ** 0.1903)            # zoals de vluchtcode
        ligt = fase == "geland" and t - t_land >= 0.53
        roll = 0.0 if ligt else (4 * math.sin(0.9 * t) if fase == "parachute"
                                 else rng.gauss(0, 0.3))
        pitch = -90.0 if ligt else (4 * math.cos(0.7 * t) if fase == "parachute"
                                    else rng.gauss(0, 0.3))
        gyro_z = {"motor": 30.0, "stijgen": 30.0, "vrije val": 200.0,
                  "parachute": 20 + 70 * math.exp(-0.05 * (t - (t_open or t)))
                  }.get(fase, 0.0)
        gyro = (rng.gauss(0, 15 if fase == "vrije val" else 0.3),
                rng.gauss(0, 15 if fase == "vrije val" else 0.3),
                gyro_z + rng.gauss(0, 1.0))
        heading = (heading + gyro_z * 1.0) % 360
        rp, rr = math.radians(pitch), math.radians(roll)
        grav = (-g * math.sin(rp), g * math.sin(rr) * math.cos(rp),
                g * math.cos(rr) * math.cos(rp))
        f4 = [max(-4 * g, min(4 * g, a * g + rng.gauss(0, 0.05)))   # BNO055: ±4 g
              for a in (fx, fy, fz)]
        lacc = [a - b for a, b in zip(f4, grav)]
        q = _quaternion(heading, roll, pitch)
        # trilling (FFT) en geluid: de felste fase sinds de vorige regel
        fase_fft = next((f for f in ("landing", "motor", "vrije val",
                                     "parachute", "stijgen") if f in gezien), fase)
        trilling = {"motor": (85.0, 1.2, 3), "stijgen": (140.0, 0.15, 4),
                    "vrije val": (35.0, 0.3, 2), "parachute": (2.5, 0.05, 0),
                    "landing": (60.0, 0.5, 3)}
        fhz, famp, band = trilling.get(fase_fft, (rng.uniform(1, 200), 0.002, None))
        bands = [0.001 * math.sqrt((hi - lo) / 208) * (1 + rng.gauss(0, 0.1))
                 for lo, hi in zip(BAND_EDGES_HZ, BAND_EDGES_HZ[1:])]
        if band is not None:
            bands[band] = math.hypot(bands[band], famp / math.sqrt(2))
        if fase_fft in ("motor", "landing"):                     # breedband
            bands = [b + 0.15 for b in bands]
        audio = {"motor": 0.35, "stijgen": 0.05, "vrije val": 0.08,
                 "landing": 0.2}.get(fase_fft, 0.003)
        if fase_fft == "parachute":
            audio = 0.01 + 0.0004 * v * v
        audio += abs(rng.gauss(0, 0.0004))
        # GPS: fix na 20 s; richting en snelheid van de drift
        if t >= 20:
            lat = LAT0 + (y + rng.gauss(0, 1.5)) / 111_320.0
            lon = LON0 + (x + rng.gauss(0, 1.5)) / (111_320.0 * math.cos(math.radians(LAT0)))
            s = int(t)
            utc = f"10:{30 + s // 60:02d}:{s % 60:02d}"
            speed = math.hypot(ux, uy) + abs(rng.gauss(0, 0.1))
            course = math.degrees(math.atan2(ux, uy)) % 360 if speed > 0.5 else rng.uniform(0, 360)
        else:
            lat, lon, utc, speed, course = 50.457303, 6.221376, "00:00:00", 0.0, 0.0

        def f(val, n):
            return f"{val:.{n}f}"

        regels.append((t, ",".join([
            str(int(round(t * 1000))), f(temp_sensor, 2), f(p, 2), f(alt, 2),
            f(lat, 6), f(lon, 6), utc,
            *(f(a, 3) for a in gyro), *(f(a, 3) for a in lacc),
            *(f(a, 3) for a in grav),
            f(heading, 2), f(roll, 2), f(pitch, 2), *(f(a, 4) for a in q),
            f(fhz, 1), f(famp, 3), f(audio, 4), f(piek, 2),
            f(course, 1), f(speed, 2), *(f(b, 4) for b in bands),
        ])))
        piek = 0.0
        gezien = set()
    return regels


def vlucht_radio(t, regel, rng):
    """RSSI, SNR en verlies voor een pakket van de oefenvlucht: de ontvanger
    staat 100 m van de lanceerplaats. In de raket zit de antenne binnenin
    (zwakker), op de grond na de landing ook."""
    v = dict(zip(COLUMNS, regel.split(",")))
    dx = (float(v["lon"]) - LON0) * 111_320.0 * math.cos(math.radians(LAT0))
    dy = (float(v["lat"]) - LAT0) * 111_320.0 - 100.0
    h = 44330.0 * (1 - (float(v["press_hPa"]) / 1014.0) ** 0.1903) - (
        44330.0 * (1 - (_druk(0) / 1014.0) ** 0.1903))
    d_km = max(0.01, math.sqrt(dx * dx + dy * dy + h * h) / 1000.0)
    rssi = 14 + 4 - (20 * math.log10(d_km) + 20 * math.log10(868) + 32.44)
    if LANCERING_S <= t < LANCERING_S + 16:
        rssi -= 15                     # in de raket
    if h < 3 and t > LANCERING_S + 20:
        rssi -= 20                     # op de grond, in het gras
    rssi += rng.gauss(0, 2)
    snr = max(-10.0, min(10.0, (rssi + 112) / 2 + rng.gauss(0, 0.7)))
    lost = rng.random() < (0.3 if rssi < -110 else 0.02)
    return round(rssi), round(snr * 4) / 4, lost


def main():
    p = argparse.ArgumentParser(description="Maak een test-CSV zoals de Teensy.")
    p.add_argument("out", help="uitvoerbestand (.csv)")
    p.add_argument("--live", action="store_true",
                   help="schrijf 1 regel per seconde (test voor --live)")
    p.add_argument("--radio", action="store_true",
                   help="zoals via de Pico-ontvanger (radio), met RSSI en SNR")
    p.add_argument("--vlucht", action="store_true",
                   help="een volledige oefenvlucht (lancering tot landing)")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    random.seed(args.seed)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    cols = serial_logger.COLUMNS if args.radio else COLUMNS
    if args.vlucht:
        schrijf_vlucht(args, cols)
        return
    n = 0
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\r\n")      # Arduino println = CRLF
        t_ms = 5212                             # eerste regel na setup()
        for t in range(DURATION_S):
            row = make_row(t, t_ms)
            if args.radio:
                rssi, snr, lost = radio_quality(t)
                if not lost:
                    parts = radio_packet(row, t) + [str(rssi), f"{snr:.1f}"]
                    rrow = serial_logger.radio_row(parts, t_ms - 5212 + 2380)
                    fh.write(serial_logger.csv_line(rrow, cols) + "\r\n")
                    n += 1
            else:
                fh.write(row + "\r\n")
                n += 1
            t_ms += 1000 + random.choice([0, 0, 1])
            if args.live:
                fh.flush()
                print(f"\r{t + 1}/{DURATION_S} s", end="", flush=True)
                time.sleep(1.0)
    print(f"\n{args.out}: {n} regels, {len(cols)} kolommen")


def schrijf_vlucht(args, cols):
    """Schrijft de oefenvlucht (--vlucht), eventueel zoals via de radio."""
    rng = random.Random(args.seed)
    regels = vlucht_regels(rng)
    n = 0
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\r\n")
        for i, (t, regel) in enumerate(regels):
            if args.radio:
                rssi, snr, lost = vlucht_radio(t, regel, rng)
                if not lost:
                    parts = radio_packet(regel, t, opwarmen=False) + [
                        str(rssi), f"{snr:.1f}"]
                    millis = int(regel.split(",", 1)[0]) - 5212 + 2380
                    rrow = serial_logger.radio_row(parts, millis)
                    fh.write(serial_logger.csv_line(rrow, cols) + "\r\n")
                    n += 1
            else:
                fh.write(regel + "\r\n")
                n += 1
            if args.live:
                fh.flush()
                print(f"\r{i + 1}/{len(regels)} s", end="", flush=True)
                time.sleep(1.0)
    print(f"\n{args.out}: oefenvlucht, {n} regels, {len(cols)} kolommen "
          f"(Cd van de parachute = {CD_OEFEN})")


if __name__ == "__main__":
    main()
