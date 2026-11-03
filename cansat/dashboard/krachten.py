"""
CanSat 2027 — forces on the can (shared model)
==============================================

One place for the data of OUR CanSat and for the physics of the forces
on it. Used by:
  dashboard_scherm1.py            Cd of the parachute (live)
  dashboard_scherm2.py            the coloured can: load per zone (live)
  ../tools/krachten_analyse.py    the full analysis after the flight

The model
---------
* The accelerometer measures how many g the CanSat feels: the load
  factor n (1 g when it stands still). Every part then pushes or pulls
  with n times its own weight:  F = m · n · g
* The force enters the can at one place, the SUPPORT:
    bottom  on the pad, during the launch (the rocket pushes) and at the
            landing (the bottom hits the ground)   → the can is pressed
    top     when the parachute pulls (opening, descent)
                                                   → the can is pulled
* A horizontal slice of the can carries all the mass on the far side of
  it, seen from the support:   N(z) = n · g · m_far(z)
  So the closer to the support, the larger the force.
* The parachute (after the flight):   F = ½ · ρ · v² · Cd · A
  with the air density ρ = p / (R · T) from our OWN pressure and
  temperature.

Only forces along the axis of the can are modelled. Sideways forces
(bending) stay small: in the rocket the tube holds the can along its
whole length, and under the parachute the can hangs in line with the
cord. tools/krachten_analyse.py checks this with the BNO055.
"""

import math

import numpy as np

# ── OUR CANSAT: weigh, measure and fill in ───────────────────
MASS_KG = 0.330               # the whole CanSat WITH parachute (weighed)
PARACHUTE_MASS_KG = 0.0       # the parachute alone. 0 = not weighed yet:
                              # the forces in the can then come out a
                              # little too high (the safe side)
PARACHUTE_DIAMETER_M = 0.45   # diameter of the parachute, laid out flat
CAN_DIAMETER_M = 0.066
CAN_HEIGHT_M = 0.115
# Heavy parts: (name, mass in kg, height of its middle above the bottom
# in m). The rest of the mass is spread evenly over the height.
# An empty list spreads all mass evenly: a good first estimate.
HEAVY_PARTS = [
    # ("battery", 0.045, 0.015),
    # ("Teensy + sensors", 0.030, 0.060),
]
BOTTOM_DOWN_IN_ROCKET = True  # the CanSat sits in the rocket bottom down

# ── Limits ───────────────────────────────────────────────────
DESIGN_LOAD_G = 20.0          # ESA: a CanSat must withstand 20 g
SENSOR_MAX_G = 16.0           # LSM6DSO range in the flight code (±16 g)
DESCENT_RATE_MS = (8.0, 11.0)  # ESA: descent rate between 8 and 11 m/s

# ── Physics ──────────────────────────────────────────────────
G = 9.81                      # m/s²
R_AIR = 287.05                # J/(kg·K), dry air

# A shock this close to the ground during the descent is the landing:
# then the bottom hits first, the parachute no longer pulls.
IMPACT_AGL_M = 25.0
IMPACT_G = 2.5


def finite(v):
    """True for a real number (not None, not nan, not inf)."""
    return isinstance(v, (int, float, np.floating)) and math.isfinite(v)


def parachute_area_m2():
    """Area of the parachute (m²), from its diameter."""
    return math.pi * PARACHUTE_DIAMETER_M ** 2 / 4.0


def can_mass_kg():
    """The can alone, without the parachute (kg)."""
    return MASS_KG - PARACHUTE_MASS_KG


# ── air and parachute ────────────────────────────────────────
def air_density(press_hpa, temp_c):
    """Air density ρ = p / (R · T) in kg/m³, from our own pressure (hPa)
    and temperature (°C). Works on numbers and on numpy arrays."""
    return (np.asarray(press_hpa, dtype=float) * 100.0 /
            (R_AIR * (np.asarray(temp_c, dtype=float) + 273.15)))


def air_density_std(alt_asl_m):
    """Air density of the standard atmosphere at this altitude (kg/m³)."""
    return 1.225 * (1 - 2.25577e-5 * alt_asl_m) ** 4.25588


def row_air_density(row, alt_asl_m=None):
    """ρ for one telemetry row: from its pressure and temperature, or from
    the standard atmosphere when those are missing."""
    p, t = row.get("press_hPa"), row.get("temp_C")
    if finite(p) and finite(t) and p > 100:
        return float(air_density(p, t))
    if alt_asl_m is not None:
        return air_density_std(alt_asl_m)
    return float("nan")


def drag_coefficient(v_ms, rho, mass_kg=None, area_m2=None):
    """Cd from a steady descent, where drag = weight:
    Cd = 2 · m · g / (ρ · v² · A)."""
    m = MASS_KG if mass_kg is None else mass_kg
    a = parachute_area_m2() if area_m2 is None else area_m2
    return 2.0 * m * G / (rho * a * np.asarray(v_ms, dtype=float) ** 2)


def drag_load_g(v_ms, rho, cd, mass_kg=None, area_m2=None):
    """How many g the parachute pulls at speed v: ½·ρ·v²·Cd·A / (m·g)."""
    m = MASS_KG if mass_kg is None else mass_kg
    a = parachute_area_m2() if area_m2 is None else area_m2
    return 0.5 * rho * np.asarray(v_ms, dtype=float) ** 2 * cd * a / (m * G)


def terminal_speed(rho, cd, mass_kg=None, area_m2=None):
    """Descent rate where drag = weight: v = √(2·m·g / (ρ·Cd·A))."""
    m = MASS_KG if mass_kg is None else mass_kg
    a = parachute_area_m2() if area_m2 is None else area_m2
    return np.sqrt(2.0 * m * G / (np.asarray(rho, dtype=float) * cd * a))


# ── forces inside the can ────────────────────────────────────
def mass_below(z_m, total_kg):
    """Mass (kg) of the can below height z (m above the bottom)."""
    z = np.clip(np.asarray(z_m, dtype=float), 0.0, CAN_HEIGHT_M)
    parts = sum(m for _, m, _ in HEAVY_PARTS)
    below = max(0.0, total_kg - parts) * z / CAN_HEIGHT_M
    for _, m, zc in HEAVY_PARTS:
        below = below + m * (z > zc)
    return below


def axial_force_n(n_g, support, z_m):
    """Force (N) through a horizontal slice of the can at height z (m
    above the bottom), at load factor n (g).
    support "bottom": the slice carries everything above it, including
                      the packed parachute → pressed
    support "top":    the parachute pulls; the slice carries everything
                      below it → pulled"""
    m_can = can_mass_kg()
    below = mass_below(z_m, m_can)
    if support == "bottom":
        far = m_can - below + PARACHUTE_MASS_KG
    else:
        far = below
    return n_g * G * far


def design_force_n():
    """The largest force of the ESA design load: 20 g on the bottom (N)."""
    return DESIGN_LOAD_G * G * MASS_KG


def zone_share(n_g, support, z_m):
    """Force at each height as a share of the ESA design force
    (0 = nothing, 1 = 20 g on the bottom)."""
    return axial_force_n(n_g, support, z_m) / design_force_n()


def support_for(phase, agl_m=None, n_g=None):
    """Where the force enters the can: "bottom" or "top".
    phase: PRELAUNCH, ASCENT, APOGEE, DESCENT or LANDED."""
    if phase in ("APOGEE", "DESCENT"):
        if (finite(agl_m) and finite(n_g) and agl_m < IMPACT_AGL_M
                and n_g > IMPACT_G):
            return "bottom"           # landing: the bottom hits the ground
        return "top"                  # the parachute pulls
    if phase == "ASCENT" and not BOTTOM_DOWN_IN_ROCKET:
        return "top"
    return "bottom"


def load_factor_g(row):
    """How many g the can feels in this telemetry row.
    Best: the peak of the LSM6DSO (acc_peak_g, 416 measurements per
    second). Without it (radio, older files): the BNO055 at this moment."""
    peak = row.get("acc_peak_g")
    if finite(peak):
        return float(peak)
    lacc = [row.get(k) for k in ("lacc_x", "lacc_y", "lacc_z")]
    grav = [row.get(k) for k in ("grav_x", "grav_y", "grav_z")]
    if not all(finite(v) for v in lacc):
        return 1.0
    if all(finite(v) for v in grav) and any(v != 0 for v in grav):
        return math.sqrt(sum((a + b) ** 2 for a, b in zip(lacc, grav))) / G
    # no gravity vector (radio): an upper estimate
    return 1.0 + math.sqrt(sum(a * a for a in lacc)) / G
