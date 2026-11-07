"""De spiekbrief (Python 3 Mémento van Laurent Pointal) uitgelegd in gewone taal.

belang: 3 = moet je echt kennen, 2 = handig, 1 = mag je voorlopig overslaan.
niveau: de sleutel van het niveau in de app waar dit vak aan bod komt.
"""

from helpers import c, t


def vak(id, naam, nl, kant, belang, niveau, uitleg, kennen, overslaan=None, code=None):
    d = {"id": id, "naam": naam, "nl": nl, "kant": kant, "belang": belang,
         "niveau": niveau, "uitleg": t(uitleg), "kennen": kennen,
         "overslaan": overslaan or []}
    if code:
        d["code"] = c(code)
    return d


VAKKEN = [
    # ---------------- VOORKANT ----------------
    vak(
        "base-types", "Base Types", "Basistypes", "voorkant", 3, "start",
        """
        De soorten enkelvoudige waarden. Elke waarde in Python heeft een type.
        """,
        [
            "`int`: geheel getal, zoals `783`, `0`, `-192`",
            "`float`: kommagetal met een **punt**: `9.23`, `0.0`",
            "`-1.7e-6` betekent -1,7 · 10⁻⁶ (wetenschappelijke notatie)",
            "`bool`: `True` of `False` (met hoofdletter!)",
            "`str`: tekst tussen `\"...\"` of `'...'`",
            "`\\n` in een tekst betekent: nieuwe regel",
        ],
        [
            "`0b010`, `0o642`, `0xF3` (binair, octaal, hexadecimaal)",
            "`bytes` (`b\"toto\"`)",
            "tekst over meerdere regels met `\"\"\"`",
        ],
        """
        print(type(783), type(9.23))
        print(type(True), type("Zeb"))
        print(-1.7e-6)
        print("One\\nTwo")
        """,
    ),
    vak(
        "container-types", "Container Types", "Containers: lists en co", "voorkant", 2, "lists",
        """
        Waarden die **meerdere** waarden bevatten. Bovenaan staan de *geordende
        reeksen* (met een index), onderaan de *sleutel-containers*.
        """,
        [
            "`list`: `[1, 5, 9]`, kan je aanpassen; `[]` is leeg",
            "`tuple`: `(1, 5, 9)`, kan je **niet** aanpassen",
            "`str` is ook een reeks: van letters",
            "`dict`: `{\"sleutel\": \"waarde\"}` (cursus hoofdstuk 13)",
        ],
        [
            "`set` en `frozenset`",
            "`bytes`",
            "de opmerking over *hashable values*",
            "`(\"mot\",)`: een tuple met één element heeft een komma nodig",
        ],
        """
        lst = [1, 5, 9]
        tup = (1, 5, 9)
        d = {"één": 1, "twee": 2}
        print(lst[0], tup[1], d["twee"])
        """,
    ),
    vak(
        "identifiers", "Identifiers", "Namen", "voorkant", 2, "start",
        """
        De regels voor namen van variabelen en functies.
        """,
        [
            "letters, cijfers en `_`; niet beginnen met een cijfer",
            "geen Python-woorden (`if`, `for`, `and`, ...)",
            "hoofdletters tellen: `Naam` ≠ `naam`",
            "goed: `a`, `toto`, `x7`, `y_max`, `BigOne`; fout: `8y`, `and`, `for`",
        ],
        ["accenten (*diacritics*) mogen, maar vermijd ze"],
    ),
    vak(
        "assignment", "Variables assignment", "Toekennen met =", "voorkant", 3, "start",
        """
        `=` koppelt een naam aan een waarde. Python rekent **eerst de rechterkant
        uit** en steekt het resultaat daarna in de naam links.
        """,
        [
            "`x = 1.2 + 8`: rechts eerst uitrekenen",
            "`a = b = c = 0`: drie variabelen tegelijk op 0",
            "`y, z, r = 9.2, -7.6, 0`: meerdere tegelijk",
            "`a, b = b, a`: twee waarden wisselen",
            "`x += 3` is `x = x + 3`; zo ook `-=`, `*=`, `/=`, `%=`",
            "`x = None`: een lege waarde, \"nog niets\"",
        ],
        ["`a, *b = seq` (uitpakken met sterretje)", "`del x`"],
        """
        a = b = 0
        y, z = 9.2, -7.6
        a, b = 3, 8
        a, b = b, a
        a += 3
        print(a, b, y, z)
        """,
    ),
    vak(
        "conversions", "Conversions", "Omzetten", "voorkant", 3, "functies-basis",
        """
        Een waarde omzetten naar een ander type. Nodig na `input`, want dat geeft
        altijd tekst.
        """,
        [
            "`int(\"15\")` → `15`",
            "`int(15.56)` → `15`: kapt af, rondt **niet** af!",
            "`float(\"2.5\")` → `2.5`",
            "`str(15)` → `\"15\"`",
            "`round(15.56, 1)` → `15.6`",
            "`list(\"abc\")` → `['a', 'b', 'c']`",
            "`type(x)` toont het type",
        ],
        [
            "`int(\"3f\", 16)` (andere talstelsels)",
            "`bool(x)`, `chr`/`ord`, `repr`, `bytes`",
            "`dict(...)` en `set(...)`",
            "`split` en `join` (die komen bij Strings, hoofdstuk 10)",
            "`[int(x) for x in ...]` (list comprehension, bij Lists, hoofdstuk 12)",
        ],
        """
        print(int("15") + 1)
        print(int(15.56), round(15.56, 1))
        print(float("2.5") * 2, str(15) + "!")
        print(list("abc"))
        """,
    ),
    vak(
        "indexing", "Sequence Containers Indexing", "Index en slices", "voorkant", 3, "strings",
        """
        Hoe je één element of een stuk uit een list (of tekst) haalt. De tekening
        met `lst = [10, 20, 30, 40, 50]` is het belangrijkste deel van deze kant.
        """,
        [
            "de index begint bij **0**: `lst[0]` → 10",
            "negatief telt van achteren: `lst[-1]` → 50 (laatste)",
            "`len(lst)` → 5; de laatste index is `len(lst) - 1`",
            "`lst[1:3]` → `[20, 30]`: het einde zit er **niet** in",
            "`lst[:3]` de eerste drie, `lst[3:]` vanaf index 3",
            "`lst[::-1]` achterstevoren",
            "`lst[4] = 25` verandert een element",
        ],
        [
            "`lst[::2]`, `lst[::-2]` (met stap)",
            "`del lst[3:5]` en `lst[1:4] = [15, 25]`",
            "*shallow copy* met `lst[:]`",
        ],
        """
        lst = [10, 20, 30, 40, 50]
        print(lst[0], lst[-1], len(lst))
        print(lst[1:3], lst[:3], lst[3:])
        print(lst[::-1])
        """,
    ),
    vak(
        "boolean-logic", "Boolean Logic", "Waar of onwaar", "voorkant", 3, "condities",
        """
        Vergelijkingen geven `True` of `False`. Met `and`, `or` en `not`
        combineer je ze.
        """,
        [
            "`<`, `>`, `<=`, `>=`, `==` (gelijk), `!=` (niet gelijk)",
            "`a and b`: allebei waar",
            "`a or b`: minstens één waar",
            "`not a`: omgekeerd",
            "`=` is toekennen, `==` is vergelijken",
        ],
        ["de *pitfall* over wat `and`/`or` teruggeven: gebruik ze gewoon met True/False"],
        """
        a, b = 4, 9
        print(a < b, a == b, a != b)
        print(a > 3 and b > 10, a > 3 or b > 10, not a > 3)
        """,
    ),
    vak(
        "blocks", "Statements Blocks", "Blokken en inspringen", "voorkant", 3, "condities",
        """
        Na een regel met `:` (if, for, while, def) komt een **blok** dat
        ingesprongen staat. Alles wat even ver ingesprongen staat, hoort bij dat blok.
        """,
        [
            "dubbele punt `:` op het einde van de regel",
            "4 spaties inspringen",
            "het blok stopt waar het inspringen stopt",
            "blokken kunnen in elkaar zitten (een if in een for)",
        ],
        ["de tip over je editor instellen"],
    ),
    vak(
        "imports", "Modules/Names Imports", "Importeren", "voorkant", 2, "rekenen",
        """
        Extra functies (zoals `sqrt`) zitten in **modules**. Die moet je eerst
        importeren.
        """,
        [
            "`from math import sqrt, pi`: daarna gewoon `sqrt(16)`",
            "`import math`: daarna `math.sqrt(16)`",
        ],
        ["`as` (hernoemen)", "`sys.path`", "een module is een bestand `truc.py`"],
        """
        from math import sqrt, pi
        import math
        print(sqrt(16), math.sqrt(16), round(pi, 3))
        """,
    ),
    vak(
        "conditional", "Conditional Statement", "Als ... dan (if)", "voorkant", 3, "condities",
        """
        Een blok wordt alleen uitgevoerd als de conditie waar is. Met `elif` en
        `else` kies je tussen meerdere gevallen: **alleen het eerste ware blok**
        wordt uitgevoerd.
        """,
        [
            "`if conditie:` + ingesprongen blok",
            "zoveel `elif` als je wil, maximaal één `else` op het einde",
            "het voorbeeld met `age` en `state`",
        ],
        ["`if x:` als kortere versie van `if bool(x) == True:` (handig, maar niet nodig)"],
        """
        age = 30
        if age <= 18:
            state = "Kid"
        elif age > 65:
            state = "Retired"
        else:
            state = "Active"
        print(state)
        """,
    ),
    vak(
        "maths", "Maths", "Rekenen", "voorkant", 3, "rekenen",
        """
        De rekenbewerkingen en de module `math`. Kommagetallen zijn **benaderingen**:
        `0.1 + 0.2` is niet exact `0.3`.

        Klein detail: op het blad staat `pow(4,3)→64.0`. In Python 3 geeft
        `pow(4, 3)` gewoon `64`; alleen `math.pow(4, 3)` geeft `64.0`.
        """,
        [
            "`+ - * /` en `**` (macht)",
            "`//` gehele deling, `%` rest",
            "voorrang: haakjes, dan `**`, dan `* / // %`, dan `+ -`",
            "`abs(-3.2)` → 3.2, `round(3.57, 1)` → 3.6",
            "`sqrt`, `floor`, `ceil`, `pi` uit `math`",
            "hoeken in **radialen**",
        ],
        [
            "`@` (matrices)",
            "`log`, `sin`, `cos` (tenzij je prof ze gebruikt)",
            "de modules `statistics`, `random`, `decimal`, `numpy`",
        ],
        """
        from math import sqrt, floor, ceil
        print(17 // 5, 17 % 5, 2 ** 10)
        print(abs(-3.2), round(3.57, 1), sqrt(81))
        print(floor(12.5), ceil(12.5), pow(4, 3))
        print(0.1 + 0.2)
        """,
    ),
    vak(
        "exceptions", "Exceptions on Errors", "Fouten opvangen", "voorkant", 2, "exceptions",
        """
        Een fout (*exception*) stopt normaal je programma. Met `try` / `except`
        vang je ze op. Dat staat in hoofdstuk 17 van je cursus.
        """,
        [
            "weten hoe een foutmelding eruitziet: `NameError`, `TypeError`, `IndexError`, ...",
        ],
        ["`raise`", "`finally`", "het schema met de pijlen"],
        """
        try:
            x = int("abc")
        except ValueError:
            print("Dat is geen getal")
        """,
    ),
    # ---------------- ACHTERKANT ----------------
    vak(
        "while", "Conditional Loop Statement", "Herhalen met while", "achterkant", 3, "while",
        """
        Het blok wordt herhaald **zolang** de conditie waar is. Het voorbeeld
        berekent de som van i² voor i van 1 tot 100.
        """,
        [
            "beginwaarde vóór de loop (`s = 0`, `i = 1`)",
            "conditie (`while i <= 100:`)",
            "de variabele verandert in de loop (`i = i + 1`)",
            "*beware of infinite loops*: verandert er niets, dan stopt de loop nooit",
        ],
        ["het sommatieteken Σ is gewoon de wiskundige uitleg"],
        """
        s = 0
        i = 1
        while i <= 100:
            s = s + i ** 2
            i = i + 1
        print("sum:", s)
        """,
    ),
    vak(
        "for", "Iterative Loop Statement", "Herhalen met for", "achterkant", 3, "for",
        """
        Het blok wordt uitgevoerd **voor elk element** van een reeks. Er staan twee
        manieren: over de **waarden** lopen en over de **indexen** lopen.
        """,
        [
            "`for c in s:`: over de waarden (voorbeeld: e's tellen)",
            "`for idx in range(len(lst)):`: over de indexen, als je `lst[idx]` wil aanpassen",
            "*good habit*: verander de loop-variabele niet zelf",
        ],
        [
            "`enumerate` (handig, maar niet nodig)",
            "loops over een dict of set",
        ],
        """
        lst = [11, 18, 9, 12, 23, 4, 17]
        lost = []
        for idx in range(len(lst)):
            val = lst[idx]
            if val > 15:
                lost.append(val)
                lst[idx] = 15
        print("modif:", lst, "-lost:", lost)
        """,
    ),
    vak(
        "loop-control", "Loop Control", "break en continue", "achterkant", 2, "for",
        """
        Een loop vroeger stoppen of een ronde overslaan.
        """,
        [
            "`break`: stop de loop meteen",
            "`continue`: sla de rest van deze ronde over",
        ],
        ["`else` na een loop"],
        """
        for i in range(10):
            if i == 2:
                continue
            if i == 5:
                break
            print(i, end=" ")
        """,
    ),
    vak(
        "display", "Display", "print", "achterkant", 3, "start",
        """
        `print` toont waarden, variabelen en uitkomsten van berekeningen.
        """,
        [
            "komma's: er komt automatisch een spatie tussen",
            "`sep=\"-\"`: iets anders dan een spatie ertussen",
            "`end=\"\"`: niet naar een nieuwe regel springen",
        ],
        ["`file=sys.stdout`"],
        """
        x, y = 3, 5
        print("v=", 3, "cm :", x, ",", y + 4)
        print(1, 2, 3, sep="-")
        print("op", end=" ")
        print("één regel")
        """,
    ),
    vak(
        "input", "Input", "input", "achterkant", 3, "functies-basis",
        """
        `input` vraagt iets aan de gebruiker. Het geeft **altijd tekst** terug.
        """,
        [
            "`s = input(\"Vraag: \")` geeft een `str`",
            "voor een getal: `int(input(...))` of `float(input(...))`",
        ],
    ),
    vak(
        "generic-ops", "Generic Operations on Containers", "Functies voor lists en co", "achterkant", 3, "lists",
        """
        Functies die werken op lists, tuples, tekst, ... Een paar zie je heel vaak.
        """,
        [
            "`len(c)`, `min(c)`, `max(c)`, `sum(c)`",
            "`sorted(c)`: een **nieuwe** gesorteerde list",
            "`x in c` en `x not in c`",
            "`c + c2` aan elkaar plakken, `c * 5` herhalen",
            "`c.index(x)` positie, `c.count(x)` aantal keer",
        ],
        [
            "`enumerate` en `zip` (handig, maar niet nodig)",
            "`all`, `any`, `reversed`",
            "`copy` en `deepcopy`",
        ],
        """
        c = [4, 8, 15, 16, 8]
        print(len(c), min(c), max(c), sum(c))
        print(sorted(c), 8 in c, 7 not in c)
        print(c.index(15), c.count(8), [1, 2] + [3], [0] * 3)
        """,
    ),
    vak(
        "range", "Integer Sequences", "range", "achterkant", 3, "for",
        """
        `range(start, einde, stap)` maakt een reeks gehele getallen. **Het einde
        zit er nooit in.**
        """,
        [
            "`range(5)` → 0 1 2 3 4",
            "`range(3, 8)` → 3 4 5 6 7",
            "`range(2, 12, 3)` → 2 5 8 11",
            "`range(20, 5, -5)` → 20 15 10",
            "`range(len(seq))` → alle indexen van seq",
        ],
        ["*immutable sequence ... constructed as needed*"],
        """
        print(*range(5))
        print(*range(3, 8))
        print(*range(2, 12, 3))
        print(*range(20, 5, -5))
        """,
    ),
    vak(
        "list-ops", "Operations on Lists", "Lists aanpassen", "achterkant", 3, "lists",
        """
        Methodes die de list **zelf** veranderen.
        """,
        [
            "`lst.append(x)`: achteraan toevoegen",
            "`lst.insert(i, x)`: invoegen op index i",
            "`lst.remove(x)`: eerste x verwijderen",
            "`lst.pop()`: laatste verwijderen en teruggeven",
            "`lst.sort()`: de list zelf sorteren",
        ],
        ["`extend`, `reverse`"],
        """
        lst = [3, 1, 2]
        lst.append(5)
        lst.insert(0, 9)
        lst.remove(1)
        x = lst.pop()
        lst.sort()
        print(lst, x)
        """,
    ),
    vak(
        "def", "Function Definition", "Een functie maken", "achterkant", 3, "functies",
        """
        Met `def` maak je een functie: een **zwarte doos** met invoer
        (parameters) en uitvoer (`return`).
        """,
        [
            "`def naam(x, y):` met dubbele punt",
            "`return res` geeft het resultaat terug",
            "zonder return geeft de functie `None` terug",
            "variabelen in de functie bestaan alleen in die functie",
        ],
        [
            "de documentatie tussen `\"\"\"`: mag, moet niet",
            "*Advanced*: `*args`, `**kwargs`",
            "*Advanced*: standaardwaarden zoals `a=3` staan wel in je cursus (8.2.4)",
        ],
        """
        def fct(x, y, z):
            \"\"\"telt drie getallen op\"\"\"
            res = x + y + z
            return res

        print(fct(1, 2, 3))
        """,
    ),
    vak(
        "call", "Function Call", "Een functie aanroepen", "achterkant", 3, "functies",
        """
        Een functie doet pas iets als je ze **aanroept**: naam plus haakjes.
        """,
        [
            "`r = fct(3, i + 2, 2 * i)`: het resultaat in r steken",
            "één argument per parameter, in dezelfde volgorde",
            "zonder haakjes wordt de functie niet uitgevoerd",
        ],
        ["*Advanced*: `*sequence`, `**dict`"],
        """
        def fct(a, b, c):
            return a * 100 + b * 10 + c

        i = 2
        r = fct(3, i + 2, 2 * i)
        print(r)
        """,
    ),
    vak(
        "dict-ops", "Operations on Dictionaries", "Woordenboeken", "achterkant", 2, "dictionaries",
        """
        Een dict koppelt **sleutels** aan **waarden**, zoals een woordenboek.
        In je cursus is dat hoofdstuk 13.
        """,
        [
            "`d[sleutel] = waarde`: toevoegen of aanpassen",
            "`d[sleutel]`: opzoeken",
            "`d.get(sleutel, standaard)`: opzoeken zonder fout",
            "`d.keys()`, `d.values()`, `d.items()`",
        ],
        ["`update`, `pop`, `popitem`, `setdefault`, `clear`"],
        """
        punten = {"Zeb": 14, "Lies": 16}
        punten["Tom"] = 12
        print(punten["Zeb"], punten.get("An", 0))
        for naam, p in punten.items():
            print(naam, p)
        """,
    ),
    vak(
        "set-ops", "Operations on Sets", "Verzamelingen", "achterkant", 2, "sets",
        """
        Een set is een verzameling zonder dubbels en zonder volgorde. Met de
        bewerkingen van de wiskunde: unie `|`, doorsnede `&`, verschil `-`.
        """,
        [
            "een set heeft geen dubbels en geen vaste volgorde",
            "`s.add(x)`, `s.remove(x)`, `s.discard(x)`",
            "`a | b` of `a.union(b)`: vereniging",
            "`a & b` of `a.intersection(b)`: doorsnede",
            "`a - b` of `a.difference(b)`: verschil",
        ],
        ["`^` (symmetrisch verschil)", "`frozenset`", "inclusie met `<` en `<=`"],
        """
        a = {1, 2, 3}
        b = {2, 3, 4}
        print(a | b, a & b, a - b)
        """,
    ),
    vak(
        "string-ops", "Operations on Strings", "Tekst bewerken", "achterkant", 2, "strings",
        """
        Methodes voor tekst. Ze geven altijd een **nieuwe** tekst terug; de
        oorspronkelijke tekst verandert niet (cursus hoofdstuk 10).
        """,
        [
            "`s.upper()`, `s.lower()`",
            "`s.strip()`: spaties vooraan en achteraan weg",
            "`s.split(\",\")`: opsplitsen in een list",
            "`\",\".join(list)`: list samenvoegen tot tekst",
            "`s.count(\"e\")`, `s.find(\"e\")`, `s.startswith(\"a\")`",
        ],
        ["`partition`, `casefold`, `center`, `ljust`, `rjust`, `zfill`, `encode`, `swapcase`"],
        """
        s = "  Python op papier  "
        print(s.strip().upper())
        print("1,4,8,2".split(","))
        print("-".join(["a", "b", "c"]))
        print("programmeren".count("r"))
        """,
    ),
    vak(
        "files", "Files", "Bestanden", "achterkant", 2, "bestanden",
        """
        Tekst opslaan in een bestand en terug inlezen (cursus hoofdstuk 16).
        """,
        [
            "`fp = open(\"pc_rose.txt\")` en op het einde `fp.close()`",
            "`fp.read()` (alles), `fp.readline()` (één regel), `fp.readlines()` (list van regels)",
            "`with open(\"file.txt\") as fp:` sluit het bestand vanzelf (onderaan rechts)",
            "`for line in f:` leest regel per regel",
            "modes: `\"r\"` lezen, `\"w\"` schrijven, `\"a\"` toevoegen",
        ],
        ["`seek`, `tell`, `flush`, `truncate`", "binaire modus `b`"],
    ),
    vak(
        "formatting", "Formatting", "Opmaak", "achterkant", 2, "functies-basis",
        """
        Getallen netjes in tekst zetten, bijvoorbeeld met 2 cijfers na de komma.
        """,
        [
            "`\"{:.2f}\".format(x)`: 2 cijfers na de komma",
            "`\"{} en {}\".format(a, b)`: waarden invullen",
        ],
        ["alle andere codes (`!r`, `>10s`, `+2.3f`, ...)"],
        """
        x = 45.72793
        print("{:.2f}".format(x))
        print("{} en {}".format("Zeb", 18))
        """,
    ),
]
