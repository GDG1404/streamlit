"""
CanSat 2027 — krachten op de CanSat, na de vlucht
=================================================

Rekent na de vlucht uit welke krachten op de CanSat werkten, en waar:

  1. de vlucht: lancering, hoogste punt, parachute, landing;
  2. de Cd van de parachute, uit de rustige daling (daar is de
     luchtweerstand even groot als het gewicht);
  3. de controle: de kracht volgens de parachute (met die Cd) naast de
     kracht die de sensor mat;
  4. de kracht door de CanSat op elke hoogte, voor elk moment;
  5. de zones: waar de CanSat het meest en het minst belast werd;
  6. de energie: hoogte-energie, bewegingsenergie en hoeveel energie de
     parachute omzet in warmte en wervelingen;
  7. de kracht die het blik voelt in 3D: hoe groot en in welke richting,
     gezien vanuit het blik zelf.

Gebruik (in de map C:\\CanSat):
  py tools\\krachten_analyse.py metingen\\vlucht.csv

De figuren (PNG) en een tabel per seconde (CSV) komen in de map
metingen\\vlucht_krachten. De gegevens van jullie CanSat (massa, parachute,
zware onderdelen) staan bovenaan in dashboard\\krachten.py.

Oefenen zonder vlucht:
  py tools\\gen_test_csv.py metingen\\oefenvlucht.csv --vlucht
  py tools\\krachten_analyse.py metingen\\oefenvlucht.csv
In de oefenvlucht is de Cd van de parachute 0,50. Vindt het script dat
terug? Dan werkt de methode.

Gebruik het bestand van de SD-kaart. Daarin staat elke seconde de grootste
versnelling (acc_peak_g). In het radiobestand zit die niet.
"""

import argparse
import csv
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")            # alleen figuren maken, geen venster
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402
from matplotlib.patches import Ellipse, FancyArrowPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dashboard"))
import krachten as K  # noqa: E402  (gegevens van onze CanSat + het model)

# ── kleuren en stijl van de figuren (licht, goed leesbaar op een dia) ──
OPP, INKT, INKT2, GRIJS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
RASTER, AS = "#e1e0d9", "#c3c2b7"
BLAUW, ORANJE, AQUA, GEEL = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
ROOD = "#d03b3b"
# groen = weinig, rood = veel: zoals het blikje op scherm 2
WARMTE = LinearSegmentedColormap.from_list(
    "belasting", ["#0ca30c", "#fab219", "#ec835a", ROOD])
STIJL = {
    "figure.facecolor": OPP, "axes.facecolor": OPP, "savefig.facecolor": OPP,
    "axes.edgecolor": AS, "axes.linewidth": 0.8, "axes.labelcolor": INKT2,
    "axes.titlecolor": INKT, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.labelsize": 11, "axes.grid": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": RASTER, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "xtick.color": GRIJS, "ytick.color": GRIJS, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "xtick.labelcolor": INKT2, "ytick.labelcolor": INKT2,
    "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
    "lines.solid_joinstyle": "round", "legend.frameon": False,
    "legend.fontsize": 10, "font.size": 11, "text.color": INKT,
}
FIG = (12.8, 7.2)                # 16:9, 1600 × 900 pixels
DPI = 125

# fases per rij (Engels, zoals in de figuren) → fase van het model
FASE_MODEL = {"pad": "PRELAUNCH", "ascent": "ASCENT",
              "chute opening": "APOGEE", "descent": "DESCENT",
              "landing": "LANDED", "landed": "LANDED"}


# ═════════════════════════════════════════════════════════════
#  INLEZEN
# ═════════════════════════════════════════════════════════════
def lees(pad):
    """Leest het meetbestand: een dict kolomnaam → numpy-array (nan als
    een waarde ontbreekt)."""
    with open(pad, newline="", encoding="utf-8", errors="replace") as f:
        regels = list(csv.reader(f))
    kop, rijen = None, []
    for r in regels:
        if not r:
            continue
        if r[0].strip() == "millis":       # kopregel (ook na een herstart)
            kop = [k.strip() for k in r]
            continue
        if kop and len(r) == len(kop):
            rijen.append(r)
    if kop is None:
        raise ValueError("geen kopregel gevonden (die begint met millis,...)")
    data = {}
    for j, k in enumerate(kop):
        if k == "time_utc":
            continue
        kolom = np.full(len(rijen), np.nan)
        for i, r in enumerate(rijen):
            try:
                kolom[i] = float(r[j])
            except ValueError:
                pass
        data[k] = kolom
    for k in ("millis", "press_hPa", "temp_C", "alt_m"):
        if k not in data:
            raise ValueError(f"de kolom {k} ontbreekt")
    goed = np.isfinite(data["millis"]) & np.isfinite(data["alt_m"])
    return {k: v[goed] for k, v in data.items()}


def kies_vlucht(d):
    """Is de Teensy herstart (de tijd springt terug)? Neem dan het stuk met
    het grootste hoogteverschil: dat is de vlucht."""
    t = d["millis"]
    knip = [0] + [i for i in range(1, len(t)) if t[i] < t[i - 1]] + [len(t)]
    if len(knip) == 2:
        return d, False
    a, b = max(zip(knip, knip[1:]),
               key=lambda ab: np.ptp(d["alt_m"][ab[0]:ab[1]]) if ab[1] > ab[0] else -1)
    return {k: v[a:b] for k, v in d.items()}, True


def kolom(d, naam):
    return d.get(naam, np.full(len(d["millis"]), np.nan))


def max_of_nan(a):
    a = np.asarray(a, dtype=float)
    return float(np.nanmax(a)) if np.isfinite(a).any() else float("nan")


# ═════════════════════════════════════════════════════════════
#  DE VLUCHT IN STUKKEN
# ═════════════════════════════════════════════════════════════
def zoek_fases(t, h, piek):
    """Zoekt de belangrijke momenten. Geeft een dict met indexen, of None
    als er geen vlucht in het bestand zit."""
    i_top = int(np.argmax(h))
    if i_top < 3:
        return None
    laag = float(np.min(h[:i_top]))
    # lancering: van halverwege de klim terug tot de klim begint
    i = max(j for j in range(i_top) if h[j] < laag + 0.5 * (h[i_top] - laag))
    while i > 0 and (h[i] - h[i - 1]) / max(t[i] - t[i - 1], 1e-3) > 2.0:
        i -= 1
    i_lancering = i
    grond = float(np.median(h[max(0, i_lancering - 30):i_lancering + 1]))
    if h[i_top] - grond < 30:
        return None
    hoogte = h - grond
    daal = -np.gradient(hoogte, t)              # daalsnelheid, + = naar beneden
    # landing: de hoogte daalt niet meer
    start = next((j for j in range(i_top, len(t)) if daal[j] > 3.0), len(t) - 1)
    i_land, geland = len(t) - 1, False
    for j in range(start, len(t) - 2):
        if np.all(daal[j:j + 3] < 1.0):
            i_land, geland = j, True
            break
    # de klap van de landing: de grootste piek vlak voor of op dat moment
    lo = max(start, i_land - 3)
    if np.isfinite(piek[lo:i_land + 2]).any():
        i_klap = lo + int(np.nanargmax(piek[lo:i_land + 2]))
    else:
        i_klap = max(start, i_land - 1)
    # parachute open: de snelste val, in de eerste 20 s na het hoogste punt
    eind = min(i_top + 20, i_klap)
    i_vmax = i_top + int(np.argmax(daal[i_top:eind + 1]))
    # de rustige daling: de snelheid blijft dicht bij de gewone daalsnelheid
    mid = daal[i_vmax + (i_klap - i_vmax) // 4:i_klap - (i_klap - i_vmax) // 4]
    v_mid = float(np.median(mid)) if len(mid) else float("nan")
    versn = np.gradient(daal, t)
    rustig = np.zeros(len(t), dtype=bool)
    for j in range(i_vmax + 2, i_klap - 2):
        rustig[j] = (daal[j] > 2.0 and abs(daal[j] - v_mid) < 0.2 * v_mid
                     and abs(versn[j]) < 0.6)
    i_rustig = int(np.argmax(rustig)) if rustig.any() else i_klap
    return {"top": i_top, "lancering": i_lancering, "vmax": i_vmax,
            "rustig0": i_rustig, "klap": i_klap, "geland": geland,
            "grond": grond, "hoogte": hoogte, "daal": daal, "rustig": rustig}


def fase_per_rij(n, f):
    fase = []
    for i in range(n):
        if i < f["lancering"]:
            fase.append("pad")
        elif i < f["top"]:
            fase.append("ascent")
        elif i < f["rustig0"]:
            fase.append("chute opening")
        elif i < f["klap"]:
            fase.append("descent")
        elif i == f["klap"]:
            fase.append("landing")
        else:
            fase.append("landed")
    return fase


# ═════════════════════════════════════════════════════════════
#  DE BEREKENING
# ═════════════════════════════════════════════════════════════
def analyse(d):
    t = (d["millis"] - d["millis"][0]) / 1000.0
    h = d["alt_m"]
    piek = kolom(d, "acc_peak_g")
    f = zoek_fases(t, h, piek)
    if f is None:
        return None
    r = {"t_bestand": float(t[f["lancering"]]), "f": f, "piek": piek,
         "heeft_piek": bool(np.isfinite(piek).any())}
    t = t - t[f["lancering"]]          # tijd vanaf de lancering
    r["t"] = t
    hoogte, daal = f["hoogte"], f["daal"]

    # luchtdichtheid uit onze eigen druk en temperatuur
    rho = K.air_density(d["press_hPa"], d["temp_C"])
    rho = np.where(np.isfinite(rho), rho, K.air_density_std(h))
    r["rho"] = rho

    # Cd uit de rustige daling: luchtweerstand = gewicht
    rustig = f["rustig"]
    cd = np.full(len(t), np.nan)
    cd[rustig] = K.drag_coefficient(daal[rustig], rho[rustig])
    r["cd_rij"] = cd
    if rustig.sum() >= 5:
        r["cd"] = float(np.median(cd[rustig]))
        r["cd_p10"], r["cd_p90"] = (float(np.percentile(cd[rustig], q))
                                    for q in (10, 90))
        # verandert de Cd met de hoogte? (helling van een rechte door de punten)
        r["cd_per_100m"] = float(np.polyfit(hoogte[rustig], cd[rustig], 1)[0] * 100)
        r["v_rustig"] = float(np.median(daal[rustig]))
        r["v_p10"], r["v_p90"] = (float(np.percentile(daal[rustig], q))
                                  for q in (10, 90))
        i0 = f["lancering"]
        rho_grond = float(np.median(rho[max(0, i0 - 30):i0 + 1]))
        r["v_grond"] = float(K.terminal_speed(rho_grond, r["cd"]))
    else:
        r["cd"] = float("nan")

    # kracht volgens het parachutemodel (alleen als de parachute open is)
    model = np.full(len(t), np.nan)
    if np.isfinite(r["cd"]):
        sl = slice(f["vmax"], f["klap"])
        model[sl] = K.drag_load_g(np.clip(daal[sl], 0, None), rho[sl], r["cd"])
    r["model"] = model

    # kracht volgens de BNO055 op het moment van de logregel: f = lacc + grav
    lacc = np.vstack([kolom(d, k) for k in ("lacc_x", "lacc_y", "lacc_z")]).T
    grav = np.vstack([kolom(d, k) for k in ("grav_x", "grav_y", "grav_z")]).T
    fv = lacc + grav
    bno = np.linalg.norm(fv, axis=1) / K.G
    bno[~np.isfinite(bno)] = np.nan
    r["bno"] = bno
    # zijwaarts: de as van het blik = de richting van de zwaartekracht in de
    # rustige daling (het blik hangt dan recht onder de parachute)
    r["zij_max"] = r["as_g"] = float("nan")
    r["fv"], r["as_vec"] = fv, None
    gr = grav[rustig]
    voor = grav[max(0, f["lancering"] - 30):f["lancering"]]
    if np.isfinite(voor).all() and len(voor):     # geen rustige daling: de
        r["as_vec"] = voor.mean(axis=0)           # lanceerplaats (rechtop)
        r["as_vec"] = r["as_vec"] / np.linalg.norm(r["as_vec"])
    if rustig.sum() >= 5 and np.isfinite(gr).all():
        u = gr.mean(axis=0)
        u /= np.linalg.norm(u)
        r["as_vec"] = u
        sl = slice(f["vmax"], f["klap"])
        langs = fv[sl] @ u
        zij = np.linalg.norm(fv[sl] - np.outer(langs, u), axis=1) / K.G
        r["zij_max"] = max_of_nan(zij[rustig[sl]])
        r["zij_open"] = max_of_nan(zij)
        r["as_g"] = float(np.nanmedian((fv[rustig] @ u) / K.G))

    # de belasting in g voor elke rij: de piek van de LSM6DSO als die er is,
    # anders de BNO055, anders het parachutemodel
    n = np.where(np.isfinite(piek), piek, np.where(np.isfinite(bno), bno, model))
    r["n"] = np.where(np.isfinite(n), n, 1.0)
    r["fase"] = fase_per_rij(len(t), f)

    # ── de momenten ──
    def piek_in(a, b):
        return max_of_nan(piek[max(0, a):b + 1])

    i0, it = f["lancering"], f["top"]
    v_open = float(daal[f["vmax"]])
    rho_open = float(rho[f["vmax"]])
    r["v_open"] = v_open
    r["open_model"] = (float(K.drag_load_g(v_open, rho_open, r["cd"]))
                       if np.isfinite(r["cd"]) else float("nan"))
    r["open_sensor"] = piek_in(it - 2, f["rustig0"])
    r["t_open"] = (float(t[it - 2 + int(np.nanargmax(piek[it - 2:f["rustig0"] + 1]))])
                   if np.isfinite(r["open_sensor"]) else float(t[f["vmax"]]))
    dal_g = (float(np.nanmedian(bno[f["rustig"]])) if np.isfinite(bno[f["rustig"]]).any()
             else 1.0)
    momenten = [
        ("launch", piek_in(i0 - 1, i0 + 4), "bottom" if K.BOTTOM_DOWN_IN_ROCKET else "top"),
        ("chute opens", r["open_sensor"] if np.isfinite(r["open_sensor"])
         else r["open_model"], "top"),
        ("descent", dal_g, "top"),
        ("landing", piek_in(f["klap"], f["klap"]) if f["geland"] else float("nan"),
         "bottom"),
    ]
    r["momenten"] = momenten
    r["afgeknipt"] = {naam: (np.isfinite(g) and g >= K.SENSOR_MAX_G - 0.1)
                      for naam, g, _ in momenten}

    # ── de kracht op elke hoogte ──
    z = np.linspace(0.0, K.CAN_HEIGHT_M, 116)
    r["z"] = z
    r["krachten"] = {naam: K.axial_force_n(g, steun, z)
                     for naam, g, steun in momenten if np.isfinite(g)}
    r["volledig"] = len(r["krachten"]) == len(momenten)
    if r["krachten"]:
        r["omhulsel"] = np.max(np.vstack(list(r["krachten"].values())), axis=0)
    energie(r, f, t)
    return r


def energie(r, f, t):
    """Energie uit de hoogtemeter (m = de hele CanSat met parachute):
    hoogte-energie m·g·h, bewegingsenergie ½·m·v² (verticaal) en het
    vermogen van de parachute: de energie die per seconde verdwijnt."""
    m = K.MASS_KG
    e_pot = m * K.G * f["hoogte"]
    e_kin = 0.5 * m * f["daal"] ** 2
    e_tot = e_pot + e_kin
    r["e_pot"], r["e_kin"], r["e_tot"] = e_pot, e_kin, e_tot
    i0, it, io, ik = f["lancering"], f["top"], f["vmax"], f["klap"]
    # de laatste rij die nog boven de grond is (de klap zelf telt niet mee)
    ie = ik - 1
    while ie > io and f["hoogte"][ie] <= 1.0:
        ie -= 1
    vermogen = np.full(len(t), np.nan)
    vermogen[io:ie + 1] = -np.gradient(e_tot, t)[io:ie + 1]
    r["vermogen"] = vermogen
    r["e_top"] = float(e_pot[it])
    # uitvliegen na de motor: beweging wordt hoogte, de som blijft (bijna) gelijk
    uit = e_tot[i0 + 3:it + 1]
    r["e_uitvliegen"] = (float(uit.min()), float(uit.max())) if len(uit) >= 3 else None
    # daling: wat de parachute omzet, van het openen tot vlak voor de landing
    r["e_omgezet"] = float(e_tot[io] - e_tot[ie])
    rust = f["rustig"]
    if rust.any():
        r["p_rustig"] = float(np.median(vermogen[rust]))
        r["p_mgv"] = float(np.median(m * K.G * f["daal"][rust]))
        r["e_kin_land"] = float(0.5 * m * np.median(f["daal"][rust][-5:]) ** 2)


# ═════════════════════════════════════════════════════════════
#  DE FIGUREN
# ═════════════════════════════════════════════════════════════
def titel(fig, tekst, sub):
    fig.text(0.012, 0.975, tekst, fontsize=16, fontweight="bold", color=INKT,
             va="top")
    fig.text(0.012, 0.925, sub, fontsize=11, color=INKT2, va="top")


def gebeurtenissen(r):
    t, f = r["t"], r["f"]
    return [(t[f["lancering"]], "launch"), (t[f["top"]], "apogee"),
            (r["t_open"], "chute opens"), (t[f["klap"]], "landing")]


def fig_vlucht(r, naam, pad):
    t, f = r["t"], r["f"]
    x0 = t[f["lancering"]] - 20
    x1 = t[f["klap"]] + 15
    with plt.rc_context(STIJL):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=FIG, sharex=True)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.09, hspace=0.32)
        titel(fig, "Flight overview", naam)
        a1.plot(t, f["hoogte"], color=BLAUW)
        a1.set_title("Height above the ground (barometer)")
        a1.set_ylabel("height (m)")
        a1.set_ylim(-0.05 * f["hoogte"][f["top"]], 1.22 * f["hoogte"][f["top"]])
        # de momenten, bij de curve
        hoog = np.interp(r["t_open"], t, f["hoogte"])
        for (te, he, lab, dx, dy, ha) in (
                (t[f["lancering"]], 0.0, "launch", -8, 26, "right"),
                (t[f["top"]], f["hoogte"][f["top"]],
                 f"apogee {f['hoogte'][f['top']]:.0f} m", -10, 10, "right"),
                (r["t_open"], hoog, "chute opens", 10, 10, "left"),
                (t[f["klap"]], 0.0, "landing", -8, 26, "right")):
            a1.plot(te, he, "o", ms=8, color=BLAUW, markeredgecolor=OPP,
                    markeredgewidth=2, zorder=5)
            a1.annotate(lab, (te, he), xytext=(dx, dy), textcoords="offset points",
                        ha=ha, va="bottom", fontsize=11, color=INKT)
        if r["heeft_piek"]:
            a2.plot(t, r["piek"], color=ORANJE, marker="o", ms=3)
            a2.set_title("Largest acceleration in each second (LSM6DSO, 416 per second)")
        else:
            a2.plot(t, r["n"], color=ORANJE, marker="o", ms=3)
            a2.set_title("Load (no peak data in this file: estimate)")
        a2.set_ylabel("load (g)")
        a2.set_xlabel("time since the launch (s)")
        a2.set_ylim(0, K.DESIGN_LOAD_G + 2.5)
        for y, tekst, kleur in ((1.0, "1 g = standing still", AS),
                                (K.SENSOR_MAX_G, "sensor limit 16 g", GRIJS),
                                (K.DESIGN_LOAD_G, "ESA design load 20 g", ROOD)):
            a2.axhline(y, color=kleur, lw=1.2, ls="-" if y == 1.0 else (0, (4, 3)))
            a2.text(x0 + 1, y + 0.3, tekst, ha="left", va="bottom", fontsize=9,
                    color=INKT2)
        for (te, lab) in gebeurtenissen(r):
            for a in (a1, a2):
                a.axvline(te, color=AS, lw=1, zorder=0)
        # de pieken van de momenten
        tijd = {"launch": t[f["lancering"]], "chute opens": r["t_open"],
                "landing": t[f["klap"]]}
        for naam_m, g, _ in r["momenten"]:
            if naam_m in tijd and np.isfinite(g) and r["heeft_piek"]:
                ti = tijd[naam_m]
                j = int(np.argmin(np.abs(t - ti)))
                lo, hi = max(0, j - 1), min(len(t), j + 5)
                j = lo + int(np.nanargmax(r["piek"][lo:hi]))
                pre = "≥ " if r["afgeknipt"][naam_m] else ""
                a2.plot(t[j], r["piek"][j], "o", ms=9, color=ORANJE,
                        markeredgecolor=OPP, markeredgewidth=2, zorder=5)
                a2.annotate(f"{pre}{g:.1f} g", (t[j], r["piek"][j]),
                            xytext=(7, 4), textcoords="offset points",
                            fontsize=11, color=INKT, fontweight="bold")
        a1.set_xlim(x0, x1)
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def fig_cd(r, naam, pad):
    f = r["f"]
    rust = f["rustig"]
    h, v, cd = f["hoogte"][rust], f["daal"][rust], r["cd_rij"][rust]
    with plt.rc_context(STIJL):
        fig, (b1, b2) = plt.subplots(1, 2, figsize=FIG, sharey=True)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.10, wspace=0.08)
        titel(fig, f"Parachute: Cd = {r['cd']:.2f}  "
                   f"({r['cd_p10']:.2f} to {r['cd_p90']:.2f})",
              f"{naam} · from {rust.sum()} s of steady descent · "
              f"Cd = 2·m·g / (ρ·v²·A) with m = {K.MASS_KG * 1000:.0f} g, "
              f"A = {K.parachute_area_m2():.3f} m² · ρ from our own pressure "
              f"and temperature")
        lo, hi = K.DESCENT_RATE_MS
        b1.axvspan(lo, hi, color="#0ca30c", alpha=0.08, lw=0)
        b1.text((lo + hi) / 2, 0.99, f"ESA: {lo:.0f} to {hi:.0f} m/s",
                transform=b1.get_xaxis_transform(), ha="center", va="top",
                fontsize=10, color=INKT2)
        b1.scatter(v, h, s=26, color=BLAUW, edgecolor=OPP, linewidth=1,
                   label="measured (barometer)", zorder=3)
        orde = np.argsort(h)
        vm = K.terminal_speed(r["rho"][rust][orde], r["cd"])
        b1.plot(vm, h[orde], color=ORANJE,
                label=f"parachute model with Cd = {r['cd']:.2f}", zorder=4)
        b1.set_title("Descent rate: faster where the air is thinner")
        b1.set_xlabel("descent rate (m/s)")
        b1.set_ylabel("height above the ground (m)")
        b1.set_xlim(min(lo - 1, np.min(v) - 0.5), max(hi + 1, np.max(v) + 0.5))
        b1.legend(loc="lower right")
        b2.axvspan(r["cd_p10"], r["cd_p90"], color=BLAUW, alpha=0.10, lw=0)
        b2.scatter(cd, h, s=26, color=BLAUW, edgecolor=OPP, linewidth=1, zorder=3)
        b2.axvline(r["cd"], color=INKT2, lw=1.5)
        b2.text(r["cd"], 0.99, f"  median {r['cd']:.2f}",
                transform=b2.get_xaxis_transform(), ha="left", va="top",
                fontsize=10, color=INKT2)
        b2.set_title("Cd in each second")
        b2.set_xlabel("drag coefficient Cd")
        marge = max(0.05, 3 * (r["cd_p90"] - r["cd_p10"]))
        b2.set_xlim(r["cd"] - marge, r["cd"] + marge)
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def fig_controle(r, naam, pad):
    t, f = r["t"], r["f"]
    t0 = t[f["top"]]
    sl = slice(max(0, f["top"] - 3), max(f["top"] + 1, f["klap"] - 1))
    tr = t[sl] - t0
    with plt.rc_context(STIJL):
        fig, c = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.10)
        titel(fig, "Check: the parachute model against the sensor",
              f"{naam} · model: F = ½·ρ·v²·Cd·A with Cd = {r['cd']:.2f} and the "
              f"descent rate from the barometer · until just before the landing")
        c.axhline(1.0, color=AS, lw=1.2)
        c.text(tr[0] + 0.55 * (tr[-1] - tr[0]), 0.9, "1 g: drag = weight",
               ha="center", va="top", fontsize=10, color=INKT2)
        if r["heeft_piek"]:
            c.plot(tr, r["piek"][sl], color=BLAUW, marker="o", ms=4,
                   label="sensor: largest in each second (LSM6DSO)")
        if np.isfinite(r["bno"][sl]).any():
            c.plot(tr, r["bno"][sl], color=AQUA, lw=0, marker="o", ms=4,
                   label="sensor: at the moment of the log line (BNO055)")
        c.plot(tr, r["model"][sl], color=ORANJE,
               label="parachute model: ½·ρ·v²·Cd·A / (m·g)")
        top = np.nanmax([r["open_sensor"], r["open_model"], 2.0])
        c.set_ylim(0, top * 1.35)
        to = r["t_open"] - t0
        tekst = f"chute opens\nmodel {r['open_model']:.1f} g"
        if np.isfinite(r["open_sensor"]):
            tekst += f" · sensor {r['open_sensor']:.1f} g"
        c.annotate(tekst, (to, top), xytext=(14, 0), textcoords="offset points",
                   fontsize=11, color=INKT, va="center")
        c.set_xlabel("time since the highest point (s)")
        c.set_ylabel("load (g)")
        c.set_title("Load on the CanSat from the highest point to the landing")
        c.legend(loc="upper right")
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def ONBEKEND(r):
    return [naam_m for naam_m, g, _ in r["momenten"] if not np.isfinite(g)]


def fig_kracht_hoogte(r, naam, pad):
    z_mm = r["z"] * 1000
    kleur = {"launch": BLAUW, "chute opens": ORANJE, "descent": AQUA,
             "landing": GEEL}
    soort = {"bottom": "pressed", "top": "pulled"}
    with plt.rc_context(STIJL):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.09, right=0.74, top=0.82, bottom=0.10)
        titel(fig, "Force through the can at each height",
              f"{naam} · F = n · g · (mass on the far side, seen from where the "
              f"force comes in) · CanSat {K.MASS_KG * 1000:.0f} g")
        if r["volledig"]:
            a.fill_betweenx(z_mm, 0, r["omhulsel"], color=INKT, alpha=0.06, lw=0,
                            label="highest in the whole flight")
        for naam_m, g, steun in r["momenten"]:
            if naam_m not in r["krachten"]:
                continue
            F = r["krachten"][naam_m]
            pre = "≥ " if r["afgeknipt"][naam_m] else ""
            a.plot(F, z_mm, color=kleur[naam_m],
                   label=f"{naam_m}: {pre}{g:.1f} g, {soort[steun]}")
            j = int(np.argmax(F))
            a.annotate(f"{pre}{F[j]:.0f} N", (F[j], z_mm[j]),
                       xytext=(6, 6 if j == 0 else -14), textcoords="offset points",
                       fontsize=10, color=INKT)
        fd = K.design_force_n()
        a.axvline(fd, color=ROOD, lw=1.2, ls=(0, (4, 3)))
        a.text(fd, 1.01, f"ESA 20 g: {fd:.0f} N", transform=a.get_xaxis_transform(),
               ha="center", va="bottom", fontsize=10, color=INKT2)
        if r["volledig"]:
            jmin = int(np.argmin(r["omhulsel"][1:-1])) + 1
            a.plot(r["omhulsel"][jmin], z_mm[jmin], "o", ms=9, color=INKT2,
                   markeredgecolor=OPP, markeredgewidth=2, zorder=5)
            a.annotate(f"least: {r['omhulsel'][jmin]:.0f} N at {z_mm[jmin]:.0f} mm",
                       (r["omhulsel"][jmin], z_mm[jmin]), xytext=(10, 0),
                       textcoords="offset points", va="center", fontsize=10,
                       color=INKT)
        else:
            a.text(0.98, 0.04, "incomplete: " + ", ".join(ONBEKEND(r)) +
                   " not measured in this file",
                   transform=a.transAxes, ha="right", fontsize=11, color=ROOD)
        a.set_xlim(0, fd * 1.08)
        a.set_ylim(0, z_mm[-1])
        a.set_yticks([0, 25, 50, 75, 100, round(z_mm[-1])])
        a.set_yticklabels(["0 bottom", "25", "50", "75", "100",
                           f"{z_mm[-1]:.0f} lid"])
        a.set_xlabel("force through the can (N)")
        a.set_ylabel("height in the can (mm)")
        a.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
        a.text(1.01, 0.30, "pressed: the force comes in at the\nbottom "
               "(rocket, ground)\npulled: the parachute pulls at\nthe top",
               transform=a.transAxes, fontsize=10, color=INKT2, va="top")
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def teken_can(a, x0, aandeel, titel_can, onder_tekst, steun):
    """Een blik van opzij, gekleurd per hoogte (aandeel van de ESA-kracht)."""
    W, H, E = K.CAN_DIAMETER_M * 1000, K.CAN_HEIGHT_M * 1000, 14.0
    norm = Normalize(0, 1)
    a.add_patch(Ellipse((x0 + W / 2, 0), W, E, facecolor=WARMTE(norm(aandeel[0])),
                        edgecolor=INKT2, lw=1, zorder=1))
    a.imshow(aandeel[:, None], extent=(x0, x0 + W, 0, H), origin="lower",
             cmap=WARMTE, norm=norm, aspect="auto", interpolation="bilinear",
             zorder=2)
    a.plot([x0, x0], [0, H], color=INKT2, lw=1, zorder=3)
    a.plot([x0 + W, x0 + W], [0, H], color=INKT2, lw=1, zorder=3)
    a.add_patch(Ellipse((x0 + W / 2, H), W, E, facecolor=WARMTE(norm(aandeel[-1])),
                        edgecolor=INKT2, lw=1, zorder=4))
    mid = x0 + W / 2
    if steun == "bottom":
        a.add_patch(FancyArrowPatch((mid, -48), (mid, -10), arrowstyle="-|>",
                                    mutation_scale=18, color=INKT2, lw=2))
        a.text(mid, -54, "pushed from below", ha="center", va="top",
               fontsize=9, color=INKT2)
    elif steun == "top":
        a.add_patch(FancyArrowPatch((mid, H + 8), (mid, H + 46), arrowstyle="-|>",
                                    mutation_scale=18, color=INKT2, lw=2))
        a.text(mid, H + 52, "parachute pulls", ha="center", va="bottom",
               fontsize=9, color=INKT2)
    a.text(mid, -78, titel_can, ha="center", va="top", fontsize=12,
           fontweight="bold", color=INKT)
    a.text(mid, -96, onder_tekst, ha="center", va="top", fontsize=10,
           color=INKT2, linespacing=1.4)


def fig_zones(r, naam, pad):
    z = r["z"]
    fd = K.design_force_n()
    kans = []
    plek = {"bottom": "at the bottom", "top": "at the top"}
    for naam_m, g, steun in r["momenten"]:
        if naam_m not in r["krachten"]:
            continue
        F = r["krachten"][naam_m]
        pre = "≥ " if r["afgeknipt"][naam_m] else ""
        kans.append((F / fd, naam_m, f"{pre}{g:.1f} g\n{pre}{F.max():.0f} N "
                     f"{plek[steun]}", steun))
    if r["volledig"]:
        om = r["omhulsel"]
        jmin = int(np.argmin(om[1:-1])) + 1
        kans.append((om / fd, "whole flight",
                     f"highest at every height\nleast at {z[jmin] * 1000:.0f} mm "
                     f"({om[jmin]:.0f} N)", None))
    W, gap = K.CAN_DIAMETER_M * 1000, 52.0
    with plt.rc_context(STIJL):
        fig, a = plt.subplots(figsize=FIG)
        fig.subplots_adjust(left=0.02, right=0.90, top=0.84, bottom=0.02)
        titel(fig, "Which zones of the can carry the most?",
              f"{naam} · colour = force at that height as a share of the ESA "
              f"design load (20 g on the bottom = {fd:.0f} N) · model from the "
              f"measured g")
        for i, (aandeel, tit, onder, steun) in enumerate(kans):
            teken_can(a, i * (W + gap), aandeel, tit, onder, steun)
        if not r["volledig"]:
            fig.text(0.012, 0.875, "incomplete: " + ", ".join(ONBEKEND(r)) +
                     " not measured in this file", fontsize=11, color=ROOD,
                     va="top")
        a.set_xlim(-gap * 0.6, max(len(kans), 5) * (W + gap) - gap * 0.4)
        a.set_ylim(-150, K.CAN_HEIGHT_M * 1000 + 75)
        a.set_aspect("equal")
        a.axis("off")
        cax = fig.add_axes([0.92, 0.25, 0.018, 0.5])
        cb = fig.colorbar(ScalarMappable(Normalize(0, 1), WARMTE), cax=cax)
        cb.set_ticks([0, 0.25, 0.5, 0.75, 1])
        cb.set_ticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
        cb.outline.set_visible(False)
        cax.set_title("share of\n20 g", fontsize=10, color=INKT2, pad=8)
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def fig_energie(r, naam, pad):
    t, f = r["t"], r["f"]
    x0, x1 = t[f["lancering"]] - 10, t[f["klap"]] + 10
    with plt.rc_context(STIJL):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=FIG, sharex=True,
                                     gridspec_kw={"height_ratios": [3, 2]})
        fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.09, hspace=0.32)
        titel(fig, "Energy: where does it go?",
              f"{naam} · from the barometer · m = {K.MASS_KG * 1000:.0f} g · "
              f"height energy m·g·h, motion energy ½·m·v² (vertical)")
        a1.plot(t, r["e_tot"] / 1000, color=INKT, label="total")
        a1.plot(t, r["e_pot"] / 1000, color=BLAUW, label="height energy  m·g·h")
        a1.plot(t, r["e_kin"] / 1000, color=ORANJE, label="motion energy  ½·m·v²")
        a1.set_title("Energy of the CanSat")
        a1.set_ylabel("energy (kJ)")
        a1.set_ylim(-0.05 * r["e_top"] / 1000, 1.3 * r["e_top"] / 1000)
        a1.legend(loc="upper right")
        it = f["top"]
        a1.annotate(f"apogee: {r['e_top'] / 1000:.2f} kJ",
                    (t[it], r["e_tot"][it] / 1000), xytext=(10, 10),
                    textcoords="offset points", fontsize=11, color=INKT)
        if np.isfinite(r["e_omgezet"]):
            mid = (r["t_open"] + t[f["klap"]]) / 2
            a1.annotate(f"the parachute turns {r['e_omgezet'] / 1000:.2f} kJ\n"
                        "into heat and swirls of air",
                        (mid, np.interp(mid, t, r["e_tot"]) / 1000),
                        xytext=(12, 22), textcoords="offset points",
                        fontsize=11, color=INKT)
        a2.plot(t, r["vermogen"], color=BLAUW, marker="o", ms=3,
                label="energy lost per second (from the data)")
        if "p_mgv" in r:
            a2.axhline(r["p_mgv"], color=ORANJE, lw=2,
                       label=f"m·g·v = {r['p_mgv']:.0f} W (steady descent)")
        a2.axhline(0, color=AS, lw=1)
        a2.set_title("Power of the parachute")
        a2.set_ylabel("power (W)")
        a2.set_xlabel("time since the launch (s)")
        p = r["vermogen"][np.isfinite(r["vermogen"])]
        gewoon = r.get("p_mgv", float(np.median(p)) if len(p) else 1.0)
        top = min(float(p.max()) if len(p) else gewoon, 4 * gewoon)  # opening: max 4×
        a2.set_ylim(min(0.0, float(p.min()) if len(p) else 0.0) - 2, 1.25 * top + 2)
        a2.legend(loc="upper right")
        for (te, _) in gebeurtenissen(r):
            for a in (a1, a2):
                a.axvline(te, color=AS, lw=1, zorder=0)
        a1.set_xlim(x0, x1)
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def fig_kracht_3d(r, naam, pad):
    """De kracht die het blik voelt (BNO055: linacc + grav), één punt per
    seconde, in 3D gezien vanuit het blik zelf: z = de as naar het deksel.
    Links de hele vlucht, rechts een close-up rond 1 g."""
    u = r["as_vec"]
    fv = r["fv"] / K.G
    goed = np.isfinite(fv).all(axis=1)
    ex = np.array([1.0, 0.0, 0.0]) if abs(u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    ex = ex - (ex @ u) * u
    ex /= np.linalg.norm(ex)
    ey = np.cross(u, ex)
    P = np.column_stack([fv @ ex, fv @ ey, fv @ u])
    grootte = np.linalg.norm(P, axis=1)
    hoek = np.degrees(np.arccos(np.clip(P[:, 2] / np.maximum(grootte, 1e-9), -1, 1)))
    fase = np.array(r["fase"])
    # op de lanceerplaats en onder de parachute voelt het blik hetzelfde
    # (1 g langs de as): open ringen, zodat beide zichtbaar blijven
    groepen = [("on the pad", ("pad",),
                dict(s=80, facecolors="none", edgecolors=BLAUW, linewidths=1.6)),
               ("in the rocket", ("ascent",),
                dict(s=30, color=ORANJE, edgecolor=OPP, linewidth=0.6)),
               ("under the parachute", ("chute opening", "descent"),
                dict(s=22, color=AQUA, edgecolor=OPP, linewidth=0.5)),
               ("after the landing", ("landing", "landed"),
                dict(s=30, color=GEEL, edgecolor=INKT2, linewidth=0.6))]
    tekst = []
    for label, sleutels, _ in groepen:
        sel = goed & np.isin(fase, sleutels)
        sterk = sel & (grootte > 0.3)              # bij ~0 g is er geen richting
        if sterk.any():
            tekst.append(f"{label}: {np.median(grootte[sterk]):.1f} g, "
                         f"{np.median(hoek[sterk]):.0f}° from the axis")
        elif sel.any():
            tekst.append(f"{label}: about 0 g")
    lim_alles = max(1.5, float(np.nanmax(grootte[goed])) * 1.1)
    with plt.rc_context(STIJL):
        fig = plt.figure(figsize=FIG)
        fig.subplots_adjust(left=0.0, right=1.0, top=0.83, bottom=0.17, wspace=0.0)
        titel(fig, "The force on the can in 3D",
              f"{naam} · what the can feels: linacc + grav (BNO055, one point per "
              f"second, up to 4 g) · seen from the can itself · the peaks of the "
              f"LSM6DSO have no direction")
        handles = []
        for k, (lim, sub) in enumerate(((lim_alles, "whole flight"),
                                        (1.3, "close-up around 1 g"))):
            a = fig.add_subplot(1, 2, k + 1, projection="3d")
            a.set_facecolor(OPP)
            th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, 37), np.linspace(0, np.pi, 19))
            a.plot_wireframe(np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph),
                             np.cos(ph), color=RASTER, linewidth=0.6)
            T, Z = np.meshgrid(np.linspace(0, 2 * np.pi, 37),
                               np.array([-0.17, 0.17]) * lim)
            a.plot_surface(0.06 * lim * np.cos(T), 0.06 * lim * np.sin(T), Z,
                           color=GRIJS, alpha=0.25, linewidth=0, shade=False)
            a.plot([0, 0], [0, 0], [-lim, lim], color=INKT2, lw=1)
            a.text(0, 0, lim * 1.04, "lid", color=INKT2, fontsize=10, ha="center")
            a.text(0, 0, -lim * 1.12, "bottom", color=INKT2, fontsize=10, ha="center")
            for label, sleutels, stijl in groepen:
                sel = goed & np.isin(fase, sleutels) & (grootte <= lim)
                if sel.any():
                    h = a.scatter(P[sel, 0], P[sel, 1], P[sel, 2], depthshade=False,
                                  label=label, **stijl)
                    if k == 0:
                        handles.append(h)
            a.set_xlim(-lim, lim)
            a.set_ylim(-lim, lim)
            a.set_zlim(-lim, lim)
            try:
                a.set_box_aspect((1, 1, 1))
            except AttributeError:
                pass
            a.set_xlabel("sideways x (g)", labelpad=6)
            a.set_ylabel("sideways y (g)", labelpad=6)
            a.set_zlabel("along the can (g)", labelpad=6)
            a.view_init(elev=18, azim=-55)
            a.set_title(sub + ("" if k == 0 else f" (points above {lim} g left out)"),
                        fontsize=12, color=INKT, loc="center")
        fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.012, 0.09),
                   ncol=4, fontsize=11)
        fig.text(0.012, 0.075, "median where the force is larger than 0.3 g "
                 "(the grey sphere is 1 g):", fontsize=10, color=INKT2, va="top")
        fig.text(0.012, 0.04, "  ·  ".join(tekst), fontsize=10, color=INKT2, va="top")
        fig.savefig(pad, dpi=DPI)
        plt.close(fig)


def schrijf_tabel(r, pad):
    kol = ["t_s", "phase", "height_agl_m", "descent_rate_ms", "air_density_kgm3",
           "cd", "n_sensor_peak_g", "n_sensor_bno_g", "n_parachute_model_g",
           "support", "force_bottom_n", "force_top_n",
           "energy_height_j", "energy_motion_j", "energy_total_j",
           "parachute_power_w"]
    f = r["f"]
    with open(pad, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(kol)
        for i in range(len(r["t"])):
            fase = r["fase"][i]
            n = r["n"][i]
            steun = ("bottom" if fase == "landing" else
                     K.support_for(FASE_MODEL[fase]))
            w.writerow([f"{r['t'][i]:.3f}", fase, f"{f['hoogte'][i]:.2f}",
                        f"{f['daal'][i]:.2f}", f"{r['rho'][i]:.4f}",
                        "" if not np.isfinite(r["cd_rij"][i]) else f"{r['cd_rij'][i]:.3f}",
                        *("" if not np.isfinite(x) else f"{x:.2f}"
                          for x in (r["piek"][i], r["bno"][i], r["model"][i])),
                        steun,
                        f"{float(K.axial_force_n(n, steun, 0.0)):.1f}",
                        f"{float(K.axial_force_n(n, steun, K.CAN_HEIGHT_M)):.1f}",
                        f"{r['e_pot'][i]:.1f}", f"{r['e_kin'][i]:.1f}",
                        f"{r['e_tot'][i]:.1f}",
                        "" if not np.isfinite(r["vermogen"][i])
                        else f"{r['vermogen'][i]:.1f}"])


# ═════════════════════════════════════════════════════════════
#  HET VERSLAG
# ═════════════════════════════════════════════════════════════
def getal(x, n=1):
    """Een getal met een komma, zoals in het Nederlands."""
    return f"{x:.{n}f}".replace(".", ",")


def verslag(r, naam, map_uit, herstart):
    t, f = r["t"], r["f"]
    lijn = "=" * 70
    print(lijn)
    print(f" KRACHTEN OP DE CANSAT — {naam}")
    print(lijn)
    print(f"CanSat: {K.MASS_KG * 1000:.0f} g met parachute · parachute "
          f"Ø {K.PARACHUTE_DIAMETER_M * 100:.0f} cm "
          f"({getal(K.parachute_area_m2(), 3)} m²)")
    print("        (aanpassen: bovenaan in dashboard\\krachten.py)")
    if herstart:
        print("LET OP: de Teensy is tijdens de meting herstart. Ik gebruik het "
              "stuk met de vlucht.")
    if not r["heeft_piek"]:
        print("LET OP: in dit bestand staat geen acc_peak_g (bv. het "
              "radiobestand).\n        Gebruik het bestand van de SD-kaart "
              "voor de schokken.")
    print("\n1. DE VLUCHT (tijd vanaf de lancering)")
    print(f"   lancering      {r['t_bestand']:.0f} s na het begin van het bestand")
    print(f"   hoogste punt   {f['hoogte'][f['top']]:.0f} m boven de grond, "
          f"na {t[f['top']]:.0f} s")
    print(f"   parachute open na {r['t_open']:.0f} s (snelste val volgens de "
          f"hoogtemeter: {getal(r['v_open'])} m/s)")
    eind = "landing" if f["geland"] else "einde bestand (geen landing gevonden)"
    print(f"   {eind:<14} na {t[f['klap']]:.0f} s "
          f"(daling: {t[f['klap']] - t[f['top']]:.0f} s)")

    print(f"\n2. DE PARACHUTE (Cd), uit {f['rustig'].sum()} s rustige daling")
    if not np.isfinite(r["cd"]):
        print("   Te weinig rustige daling gevonden: geen Cd.")
    else:
        lo, hi = K.DESCENT_RATE_MS
        ok = ("te traag" if r["v_grond"] < lo else
              "te snel" if r["v_grond"] > hi else "OK")
        print(f"   daalsnelheid   {getal(r['v_rustig'])} m/s "
              f"({getal(r['v_p10'])} tot {getal(r['v_p90'])}); "
              f"aan de grond {getal(r['v_grond'])} m/s")
        print(f"                  ESA vraagt {lo:.0f} tot {hi:.0f} m/s → {ok}")
        rr = r["rho"][f["rustig"]]
        print(f"   luchtdichtheid {getal(rr.min(), 2)} tot {getal(rr.max(), 2)} "
              f"kg/m³ (uit jullie druk en temperatuur)")
        print(f"   Cd             {getal(r['cd'], 2)} "
              f"({getal(r['cd_p10'], 2)} tot {getal(r['cd_p90'], 2)}); "
              f"verandering per 100 m hoogte: {getal(r['cd_per_100m'], 3)}")

    print("\n3. CONTROLE: de kracht volgens de parachute en volgens de sensor")
    if np.isfinite(r["cd"]):
        dal = (f"{getal(r['as_g'], 2)} g (BNO055)" if np.isfinite(r["as_g"])
               else "niet gemeten")
        print(f"   rustige daling   model 1,00 g   · sensor {dal}")
        sens = (f"{getal(r['open_sensor'])} g (LSM6DSO)" if np.isfinite(r["open_sensor"])
                else "niet gemeten")
        print(f"   parachute open   model {getal(r['open_model'])} g    · sensor {sens}")
        print("                    (het model rekent met de snelheid van de "
              "hoogtemeter:\n                     een gemiddelde over 2 s, "
              "dus de echte topsnelheid is hoger)")
    if np.isfinite(r["zij_max"]):
        print(f"   zijwaarts        hoogstens {getal(r['zij_max'], 2)} g in de "
              f"rustige daling (klein: het blik hangt recht)")

    print("\n4. KRACHTEN PER MOMENT (de grootste kracht in het blik)")
    plek = {"bottom": "onderaan", "top": "bovenaan"}
    soort = {"bottom": "samengedrukt", "top": "uitgerekt"}
    nl = {"launch": "lancering", "chute opens": "parachute open",
          "descent": "daling", "landing": "landing"}
    for naam_m, g, steun in r["momenten"]:
        if not np.isfinite(g):
            print(f"   {nl[naam_m]:<15} onbekend (niet gemeten in dit bestand)")
            continue
        F = float(np.max(r["krachten"][naam_m]))
        pre = "≥" if r["afgeknipt"][naam_m] else " "
        extra = "  ← sensor afgeknipt bij 16 g!" if r["afgeknipt"][naam_m] else ""
        print(f"   {nl[naam_m]:<15}{pre}{getal(g):>5} g  {plek[steun]:<9}"
              f"{pre}{getal(F):>5} N  ({soort[steun]}){extra}")
    fd = K.design_force_n()
    print(f"   {'ESA-eis':<15} {getal(K.DESIGN_LOAD_G):>5} g  {'onderaan':<9} "
          f"{getal(fd):>5} N")

    if r.get("krachten") and not r["volledig"]:
        print("\n5. ZONES: niet volledig. Deze momenten zitten niet in dit bestand: "
              + ", ".join(nl[m] for m in ONBEKEND(r)) + ".")
        print("   Gebruik het bestand van de SD-kaart (met acc_peak_g) en de hele "
              "vlucht tot na de landing.")
    elif r.get("krachten"):
        z, om = r["z"], r["omhulsel"]
        jmin = int(np.argmin(om[1:-1])) + 1
        print("\n5. ZONES (de grootste kracht tijdens de hele vlucht)")
        for j, tekst in ((0, "bodem"), (len(z) // 2, "midden"), (len(z) - 1, "deksel")):
            print(f"   {tekst:<7} ({z[j] * 1000:3.0f} mm)   {getal(om[j]):>5} N   "
                  f"{100 * om[j] / fd:3.0f} % van de ESA-eis")
        print(f"   minst belast: op {z[jmin] * 1000:.0f} mm hoogte, "
              f"{getal(om[jmin])} N")
    print(f"\n6. ENERGIE (uit de hoogtemeter, m = {K.MASS_KG * 1000:.0f} g)")
    if r["e_uitvliegen"]:
        lo, hi = r["e_uitvliegen"]
        print(f"   na de motor      totale energie {getal(lo / 1000, 2)} tot "
              f"{getal(hi / 1000, 2)} kJ: bijna gelijk")
        print("                    (bewegingsenergie wordt hoogte-energie)")
    print(f"   hoogste punt     hoogte-energie m·g·h = {getal(r['e_top'] / 1000, 2)} kJ")
    tot = "vlak voor de landing" if f["geland"] else "het einde van het bestand"
    print(f"   daling           de parachute zet {getal(r['e_omgezet'] / 1000, 2)} kJ "
          f"om in warmte en wervelingen\n"
          f"                    (van het openen tot {tot})")
    if "p_rustig" in r:
        print(f"                    gemiddeld {getal(r['p_rustig'])} W "
              f"(m·g·v = {getal(r['p_mgv'])} W)")
        if f["geland"]:
            print(f"   landing          nog {getal(r['e_kin_land'], 0)} J "
                  f"bewegingsenergie (½·m·v²)")
    print(f"\nFiguren en tabel: {map_uit}")


# ═════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="Krachten op de CanSat na de vlucht (Cd, controle, zones, "
                    "energie).")
    p.add_argument("csv", help="het meetbestand, bv. metingen\\vlucht.csv")
    args = p.parse_args()

    naam = os.path.basename(args.csv)
    try:
        d = lees(args.csv)
    except (OSError, ValueError) as e:
        print(f"Kan {args.csv} niet lezen: {e}")
        return 1
    d, herstart = kies_vlucht(d)
    r = analyse(d)
    if r is None:
        print(f"Geen vlucht gevonden in {naam}: het hoogste punt is maar "
              f"{np.ptp(d['alt_m']):.0f} m boven het laagste.\n"
              "Gebruik het bestand van de vlucht. Of oefen eerst met:\n"
              "  py tools\\gen_test_csv.py metingen\\oefenvlucht.csv --vlucht")
        return 1

    map_uit = os.path.splitext(args.csv)[0] + "_krachten"
    os.makedirs(map_uit, exist_ok=True)
    verslag(r, naam, map_uit, herstart)
    fig_vlucht(r, naam, os.path.join(map_uit, "1_vlucht.png"))
    if np.isfinite(r["cd"]):
        fig_cd(r, naam, os.path.join(map_uit, "2_parachute_cd.png"))
        fig_controle(r, naam, os.path.join(map_uit, "3_controle.png"))
    if r.get("krachten"):
        fig_kracht_hoogte(r, naam, os.path.join(map_uit, "4_kracht_per_hoogte.png"))
        fig_zones(r, naam, os.path.join(map_uit, "5_zones.png"))
    fig_energie(r, naam, os.path.join(map_uit, "6_energie.png"))
    if r["as_vec"] is not None and np.isfinite(r["fv"]).all(axis=1).any():
        fig_kracht_3d(r, naam, os.path.join(map_uit, "7_kracht_3d.png"))
    else:
        print("Geen 3D-figuur: in dit bestand staat de richting niet "
              "(grav_x/y/z ontbreken, bv. het radiobestand).")
    schrijf_tabel(r, os.path.join(map_uit, "krachten_per_seconde.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
