# Draait in de browser (Brython, in een Web Worker).
# Voert code van de leerling uit en test ze. Geeft altijd JSON-tekst terug.
# build.py zet nepbestanden.py (maak_open, geeft_fout) vóór deze code.
import sys
import json
import traceback
from browser import self as W


class Uit:
    def __init__(self):
        self.buf = []

    def write(self, s):
        self.buf.append(str(s))

    def flush(self):
        pass


def _foutinfo(e):
    ln = getattr(e, "lineno", None)
    try:
        for fr in traceback.extract_tb(e.__traceback__):
            if fr.filename == "<zeb>":
                ln = fr.lineno
    except Exception:
        pass
    msg = str(e)
    if isinstance(e, SyntaxError):
        msg = getattr(e, "msg", None) or msg
    return [type(e).__name__, msg, ln]


def _voer_uit(src, inputs, echo, bestanden):
    uit = Uit()
    voeding = list(inputs)

    def nep_input(prompt=""):
        if echo:
            uit.write(str(prompt))
        if not voeding:
            raise EOFError("Er is geen invoer meer om te lezen.")
        v = voeding.pop(0)
        if echo:
            uit.write(v + "\n")
        return v

    g = {"__name__": "__main__", "input": nep_input, "open": maak_open(dict(bestanden)),
         "geeft_fout": geeft_fout}
    oud = sys.stdout
    sys.stdout = uit
    fout = None
    try:
        exec(compile(src, "<zeb>", "exec"), g)
    except BaseException as e:
        fout = _foutinfo(e)
    finally:
        sys.stdout = oud
    return g, "".join(uit.buf), fout


def _norm(s):
    lijnen = [ln.rstrip() for ln in s.replace("\r", "").split("\n")]
    while lijnen and lijnen[-1] == "":
        lijnen.pop()
    return "\n".join(lijnen)


def zeb_run(src, inputs_json, bestanden_json):
    _, uit, fout = _voer_uit(src, json.loads(inputs_json), True, json.loads(bestanden_json))
    return json.dumps({"uit": uit, "fout": fout})


def zeb_test(src, tests_json, ptests_json, bestanden_json):
    tests = json.loads(tests_json)
    ptests = json.loads(ptests_json)
    bestanden = json.loads(bestanden_json)
    resultaten = []
    algemene_fout = None
    if tests:
        g, uit, fout = _voer_uit(src, [], False, bestanden)
        if fout:
            algemene_fout = fout
        else:
            for expr, verwacht in tests:
                r = {"vraag": expr, "verwacht": verwacht}
                try:
                    waarde = eval(expr, g)
                    r["kreeg"] = repr(waarde)
                    r["ok"] = waarde == eval(verwacht)
                except BaseException as e:
                    r["fout"] = _foutinfo(e)
                    r["ok"] = False
                resultaten.append(r)
    for inputs, verwacht in ptests:
        _, uit, fout = _voer_uit(src, inputs, False, bestanden)
        r = {"invoer": inputs, "verwacht": verwacht, "kreeg": uit}
        if fout:
            r["fout"] = fout
        r["ok"] = (fout is None) and _norm(uit) == _norm(verwacht)
        resultaten.append(r)
    return json.dumps({"resultaten": resultaten, "fout": algemene_fout})


W.zebRun = zeb_run
W.zebTest = zeb_test
