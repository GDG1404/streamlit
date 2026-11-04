#!/usr/bin/env python3
"""Bouwt 'Python op papier' tot één HTML-bestand.

Wat dit script doet:
1. Laadt de inhoud uit content/ (niveaus, spiekbrief, instaptest).
2. Voert ALLE code uit met echte Python en noteert de uitvoer en elke stap
   (welke regel, welke variabelen). Zo klopt elk antwoord in de app gegarandeerd.
3. Controleert dat elke modeloplossing slaagt voor zijn tests, dat 'vul aan'
   met het eerste antwoord werkt, en dat meerkeuze-antwoorden over uitvoer kloppen.
4. Zet alles samen met template/ tot dist/python-op-papier.html (voor de
   Artifact-pagina) en dist/index.html (een volledig HTML-bestand).

Gebruik:  python3 build.py
"""

from __future__ import annotations

import builtins
import contextlib
import importlib
import io
import json
import re
import sys
import traceback
import types
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER / "content"))

MAX_STAPPEN = 400
FOUTEN: list[str] = []


# --------------------------------------------------------------------------- #
# Code uitvoeren met tracer
# --------------------------------------------------------------------------- #
class TeVeelStappen(Exception):
    pass


def fmt(v) -> str:
    r = repr(v)
    return r if len(r) <= 80 else r[:77] + "..."


def is_zichtbaar(v) -> bool:
    return not isinstance(
        v, (types.FunctionType, types.ModuleType, type, types.BuiltinFunctionType)
    )


def voer_uit(code: str, inputs=(), trace=True):
    """Voer code uit. Geeft (uitvoer, fout, stappen) terug.

    stappen: lijst van {"l": regel die nu aan de beurt is, "fr": frames,
    "o": aantal tekens uitvoer tot nu}. Een stap met "ret" is een return uit
    een functie. De laatste stap heeft "end": True.
    """
    out = io.StringIO()
    voeding = list(inputs)

    def nep_input(prompt=""):
        if not voeding:
            raise EOFError("geen invoer meer")
        return voeding.pop(0)

    g = {"__name__": "__main__", "input": nep_input}
    basis = set(g) | {"__builtins__"}
    stappen: list[dict] = []

    def globale_vars(gl):
        return [
            [k, fmt(v)]
            for k, v in gl.items()
            if k not in basis and not k.startswith("__") and is_zichtbaar(v)
        ]

    def momentopname(frame, soort, extra=None):
        stapel = []
        f = frame
        while f is not None:
            naam = f.f_code.co_name
            if f.f_code.co_filename == "<zeb>" and (
                naam == "<module>" or not naam.startswith("<")
            ):
                stapel.append(f)
            f = f.f_back
        stapel.reverse()
        frames = []
        for fr in stapel:
            if fr.f_code.co_name == "<module>":
                frames.append({"f": "", "v": globale_vars(fr.f_globals)})
            else:
                frames.append(
                    {
                        "f": fr.f_code.co_name,
                        "v": [[k, fmt(v)] for k, v in fr.f_locals.items() if is_zichtbaar(v)],
                    }
                )
        st = {"l": frame.f_lineno, "fr": frames, "o": len(out.getvalue())}
        if soort == "return":
            st["ret"] = [frame.f_code.co_name, fmt(extra)]
        stappen.append(st)
        if len(stappen) > MAX_STAPPEN:
            raise TeVeelStappen()

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != "<zeb>":
            return None
        naam = frame.f_code.co_name
        if naam != "<module>" and naam.startswith("<"):
            return None
        if event == "line":
            momentopname(frame, "line")
        elif event == "return" and naam != "<module>":
            momentopname(frame, "return", arg)
        return tracer

    fout = None
    try:
        co = compile(code, "<zeb>", "exec")
    except SyntaxError as e:
        return "", [type(e).__name__, e.msg, e.lineno], []

    oud = sys.gettrace()
    with contextlib.redirect_stdout(out):
        if trace:
            sys.settrace(tracer)
        try:
            exec(co, g)
        except TeVeelStappen:
            fout = ["TeVeelStappen", "te veel stappen", None]
        except Exception as e:  # noqa: BLE001 - we willen elke fout tonen
            ln = None
            for fr in traceback.extract_tb(e.__traceback__):
                if fr.filename == "<zeb>":
                    ln = fr.lineno
            fout = [type(e).__name__, str(e), ln]
        finally:
            sys.settrace(oud)
    if trace:
        stappen.append(
            {"l": None, "fr": [{"f": "", "v": globale_vars(g)}], "o": len(out.getvalue()), "end": True}
        )
    return out.getvalue(), fout, (stappen if trace else []), g


def run(code, inputs=(), trace=True):
    r = voer_uit(code, inputs, trace)
    if len(r) == 3:  # syntaxfout
        return r[0], r[1], r[2], {}
    return r


def norm(s: str) -> str:
    """Zelfde normalisatie als in de app: spaties op het einde van elke regel
    en lege regels op het einde tellen niet mee."""
    lijnen = [ln.rstrip() for ln in s.replace("\r", "").split("\n")]
    while lijnen and lijnen[-1] == "":
        lijnen.pop()
    return "\n".join(lijnen)


def fout_melding(waar: str, wat: str):
    FOUTEN.append(f"{waar}: {wat}")


# --------------------------------------------------------------------------- #
# Inhoud verwerken
# --------------------------------------------------------------------------- #
def verwerk_les(les: dict, waar: str):
    if "code" in les:
        uit, fout, _, _ = run(les["code"], les.get("inputs", []), trace=False)
        if fout:
            fout_melding(waar, f"uitlegcode geeft fout {fout}")
        les["uitvoer"] = uit
        # Ook stap-voor-stap voor uitlegcode (handig in de app).
        _, _, stappen, _ = run(les["code"], les.get("inputs", []), trace=True)
        les["stappen"] = stappen


def verwerk_oefening(oef: dict, waar: str):
    t = oef["t"]
    if t == "voorspel":
        uit, fout, stappen, _ = run(oef["code"], oef.get("inputs", []))
        if fout:
            fout_melding(waar, f"voorspel-code geeft fout {fout}")
        if not uit.strip():
            fout_melding(waar, "voorspel-code toont niets")
        oef["uitvoer"] = uit
        oef["stappen"] = stappen

    elif t in ("keuze", "lees"):
        if not (0 <= oef["juist"] < len(oef["opties"])):
            fout_melding(waar, "juist-index buiten bereik")
        if "code" in oef and oef.get("draai", True):
            uit, fout, stappen, _ = run(oef["code"], oef.get("inputs", []))
            oef["uitvoer"] = uit
            oef["stappen"] = stappen
            if fout:
                oef["fout"] = fout
            if oef.get("controleer_uitvoer"):
                if norm(uit) != norm(oef["opties"][oef["juist"]]):
                    fout_melding(
                        waar,
                        f"juiste optie {oef['opties'][oef['juist']]!r} != uitvoer {uit!r}",
                    )

    elif t == "fout":
        uit, fout, stappen, _ = run(oef["code"], oef.get("inputs", []))
        oef["uitvoer"] = uit
        oef["stappen"] = stappen
        if fout:
            oef["fout"] = fout
        uit2, fout2, stappen2, _ = run(oef["verbeterd"], oef.get("inputs", []))
        if fout2:
            fout_melding(waar, f"verbeterde code geeft fout {fout2}")
        if norm(uit2) == norm(uit) and not fout:
            fout_melding(waar, "verbeterde code geeft dezelfde uitvoer als de foute code")
        oef["uitvoer_verbeterd"] = uit2
        n_regels = len(oef["code"].split("\n"))
        if not (1 <= oef["regel"] <= n_regels):
            fout_melding(waar, "foutregel buiten bereik")

    elif t == "aanvullen":
        n_vakjes = oef["code"].count("___")
        if n_vakjes != len(oef["antwoorden"]):
            fout_melding(waar, f"{n_vakjes} vakjes maar {len(oef['antwoorden'])} antwoordlijsten")
        code = oef["code"]
        for opties in oef["antwoorden"]:
            code = code.replace("___", opties[0], 1)
        uit, fout, stappen, _ = run(code, oef.get("inputs", []))
        if fout:
            fout_melding(waar, f"ingevulde code geeft fout {fout}")
        oef["ingevuld"] = code
        oef["uitvoer"] = uit
        oef["stappen"] = stappen

    elif t == "schrijf":
        sol = oef["oplossing"]
        if "tests" in oef:
            uit, fout, _, g = run(sol, [], trace=False)
            if fout:
                fout_melding(waar, f"oplossing geeft fout {fout}")
            for expr, verwacht in oef["tests"]:
                try:
                    waarde = eval(expr, g)  # noqa: S307 - eigen inhoud
                except Exception as e:  # noqa: BLE001
                    fout_melding(waar, f"test {expr} geeft fout {e!r}")
                    continue
                if waarde != eval(verwacht):  # noqa: S307
                    fout_melding(waar, f"test {expr}: {waarde!r} != {verwacht}")
        if "ptests" in oef:
            for inputs, verwacht in oef["ptests"]:
                uit, fout, _, _ = run(sol, inputs, trace=False)
                if fout:
                    fout_melding(waar, f"oplossing met invoer {inputs} geeft fout {fout}")
                if norm(uit) != norm(verwacht):
                    fout_melding(waar, f"invoer {inputs}: uitvoer {uit!r} != {verwacht!r}")
        if "tests" not in oef and "ptests" not in oef:
            fout_melding(waar, "schrijfopdracht zonder tests")
        for v in oef.get("verboden", []):
            if v in sol:
                fout_melding(waar, f"oplossing gebruikt verboden {v!r}")
    else:
        fout_melding(waar, f"onbekend type {t}")


def laad():
    niveaus = []
    for i in range(8):
        mod = importlib.import_module(f"n{i}")
        niv = mod.NIVEAU
        assert niv["nr"] == i, f"n{i}.py heeft nr {niv['nr']}"
        for j, les in enumerate(niv["uitleg"]):
            verwerk_les(les, f"niveau {i} uitleg {j + 1}")
        for j, oef in enumerate(niv["oefeningen"]):
            oef["id"] = f"{i}-{j + 1}"
            verwerk_oefening(oef, f"niveau {i} oefening {j + 1}")
        niveaus.append(niv)

    later = importlib.import_module("later").LATER
    vakken = importlib.import_module("spiekbrief").VAKKEN
    ids = {v["id"] for v in vakken}
    for v in vakken:
        if "code" in v:
            uit, fout, _, _ = run(v["code"], [], trace=False)
            if fout and v["id"] != "exceptions":
                fout_melding(f"spiekbrief {v['id']}", f"code geeft fout {fout}")
            v["uitvoer"] = uit
    for niv in niveaus + later:
        for s in niv["spiek"]:
            if s not in ids:
                fout_melding(f"niveau {niv['nr']}", f"onbekend spiekbrief-vak {s}")

    vragen = importlib.import_module("instaptest").VRAGEN
    for j, v in enumerate(vragen):
        v["id"] = f"test-{j + 1}"
        verwerk_oefening(v, f"instaptest vraag {j + 1}")

    return {"niveaus": niveaus, "later": later, "spiekbrief": vakken, "instaptest": vragen}


# --------------------------------------------------------------------------- #
# HTML samenstellen
# --------------------------------------------------------------------------- #
def bouw_html(data: dict) -> str:
    tpl = (HIER / "template" / "app.html").read_text(encoding="utf-8")
    css = (HIER / "template" / "app.css").read_text(encoding="utf-8")
    js = (HIER / "template" / "app.js").read_text(encoding="utf-8")
    runner = (HIER / "template" / "runner.py").read_text(encoding="utf-8")
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")
    runner_json = json.dumps(runner, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__CSS__*/", css)
    html = html.replace("/*__DATA__*/", f"const DATA = {data_json};\nconst RUNNER_PY = {runner_json};")
    html = html.replace("/*__JS__*/", js)
    return html


def main():
    data = laad()
    if FOUTEN:
        print("FOUTEN in de inhoud:")
        for f in FOUTEN:
            print("  -", f)
        sys.exit(1)

    n_oef = sum(len(n["oefeningen"]) for n in data["niveaus"])
    n_les = sum(len(n["uitleg"]) for n in data["niveaus"])
    print(f"OK: {len(data['niveaus'])} niveaus, {n_les} uitlegkaarten, {n_oef} oefeningen, "
          f"{len(data['spiekbrief'])} spiekbrief-vakken, {len(data['instaptest'])} testvragen")

    html = bouw_html(data)
    dist = HIER / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "python-op-papier.html").write_text(html, encoding="utf-8")
    volledig = (
        "<!doctype html><html lang=\"nl\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
        "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
        "body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>"
        "</head><body>" + html + "</body></html>"
    )
    (dist / "index.html").write_text(volledig, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024
    print(f"Geschreven: dist/python-op-papier.html ({kb:.0f} kB) en dist/index.html")


if __name__ == "__main__":
    main()
