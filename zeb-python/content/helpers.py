"""Kleine hulpfuncties om de inhoud leesbaar te kunnen schrijven.

Elke functie aanvaardt ook:
- boek="Opgave 7.10": de oefening komt (aangepast) uit het cursusboek
  "De Programmeursleerling" van Pieter Spronck (CC BY-NC 3.0);
- bestanden={"pc_rose.txt": "..."}: tekstbestanden die de code kan openen
  (ze bestaan alleen in het geheugen, in de build en in de browser).
"""

import textwrap


def c(code: str) -> str:
    """Code-blok: haal gemeenschappelijke inspringing en lege randregels weg."""
    return textwrap.dedent(code).strip("\n").rstrip()


def t(tekst: str) -> str:
    """Tekstblok (mini-markup): `code`, **vet**, '- ' voor opsommingen."""
    return textwrap.dedent(tekst).strip()


def _extra(d, boek=None, bestanden=None):
    if boek:
        d["boek"] = boek
    if bestanden:
        d["bestanden"] = {naam: textwrap.dedent(inhoud).lstrip("\n") for naam, inhoud in bestanden.items()}
    return d


def les(titel, tekst, code=None, inputs=None, papier=None, **extra):
    """Een uitlegkaart. Als er code is, berekent de build de uitvoer."""
    d = {"titel": titel, "tekst": t(tekst)}
    if code:
        d["code"] = c(code)
    if inputs:
        d["inputs"] = inputs
    if papier:
        d["papier"] = t(papier)
    return _extra(d, **extra)


def voorspel(code, uitleg, tip=None, inputs=None, vraag=None, **extra):
    """'Wat print dit?' - de build berekent de juiste uitvoer en de stappen."""
    d = {"t": "voorspel", "code": c(code), "uitleg": t(uitleg)}
    if tip:
        d["tip"] = t(tip)
    if inputs:
        d["inputs"] = inputs
    if vraag:
        d["vraag"] = t(vraag)
    return _extra(d, **extra)


def keuze(vraag, opties, juist, uitleg, code=None, inputs=None, lees=False,
          controleer_uitvoer=False, draai=True, **extra):
    """Meerkeuze. Met controleer_uitvoer=True moet de juiste optie gelijk zijn
    aan de echte uitvoer van de code (de build controleert dat)."""
    d = {"t": "lees" if lees else "keuze", "vraag": t(vraag), "opties": opties,
         "juist": juist, "uitleg": t(uitleg)}
    if code:
        d["code"] = c(code)
    if inputs:
        d["inputs"] = inputs
    if controleer_uitvoer:
        d["controleer_uitvoer"] = True
    if not draai:
        d["draai"] = False
    return _extra(d, **extra)


def fout(vraag, code, regel, verbeterd, uitleg, inputs=None, **extra):
    """'Zoek de fout' - klik op de regel met de fout."""
    d = {"t": "fout", "vraag": t(vraag), "code": c(code), "regel": regel,
         "verbeterd": c(verbeterd), "uitleg": t(uitleg)}
    if inputs:
        d["inputs"] = inputs
    return _extra(d, **extra)


def aanvullen(vraag, code, antwoorden, uitleg, inputs=None, tip=None, **extra):
    """'Vul aan' - elke ___ in de code is een vakje. antwoorden: per vakje een
    list aanvaarde antwoorden (het eerste wordt gebruikt om te testen)."""
    d = {"t": "aanvullen", "vraag": t(vraag), "code": c(code),
         "antwoorden": antwoorden, "uitleg": t(uitleg)}
    if inputs:
        d["inputs"] = inputs
    if tip:
        d["tip"] = t(tip)
    return _extra(d, **extra)


def schrijf(vraag, oplossing, uitleg, tests=None, ptests=None, start=None,
            tip=None, verboden=None, uitdaging=False, **extra):
    """'Schrijf op papier'.
    tests:  list van (python-expressie, verwachte waarde) voor functies.
    ptests: list van (invoer, verwachte uitvoer) voor programma's."""
    d = {"t": "schrijf", "vraag": t(vraag), "oplossing": c(oplossing),
         "uitleg": t(uitleg)}
    if tests:
        d["tests"] = [[e, repr(v)] for e, v in tests]
    if ptests:
        d["ptests"] = [[i, o] for i, o in ptests]
    if start:
        d["start"] = c(start)
    if tip:
        d["tip"] = t(tip)
    if verboden:
        d["verboden"] = verboden
    if uitdaging:
        d["uitdaging"] = True
    return _extra(d, **extra)
