from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "tuples",
    "titel": "Tuples",
    "kort": "vaste reeksen tussen ronde haken",
    "hoofdstuk": "11",
    "spiek": ["container-types", "assignment", "indexing"],
    "doel": "Je kan tuples maken, uitpakken, vergelijken en als retourwaarde gebruiken, en je weet dat ze onveranderbaar zijn.",
    "uitleg": [
        les(
            "Een tuple",
            """
            Een **tuple** is een reeks waarden tussen **ronde** haakjes, gescheiden
            door komma's (cursus 11.1): `(3, 4)` of `("appel", "peer", "kers")`.
            Het lijkt op een list, maar een tuple kan je **niet veranderen**.

            Eigenlijk maakt de **komma** de tuple, niet de haakjes. Een tuple met één
            element schrijf je daarom met een komma: `(5,)`. Zonder komma is `(5)`
            gewoon het getal 5.
            """,
            """
            fruit = ("appel", "peer", "kers")
            print(fruit)
            print(len(fruit), fruit[0], fruit[-1])
            enkel = (5,)
            print(len(enkel))
            """,
        ),
        les(
            "Tuple assignment: uitpakken",
            """
            Je kan een tuple in één keer **uitpakken** in meerdere variabelen
            (cursus 11.1.1). Het aantal variabelen moet gelijk zijn aan het aantal
            elementen. Zo werkt ook `a, b = b, a`: rechts staat een tuple.
            """,
            """
            punt = (3, 4)
            x, y = punt
            print(x, y)
            a, b = 1, 2
            a, b = b, a
            print(a, b)
            """,
        ),
        les(
            "Index, slices en loops",
            """
            Net als bij strings en lists (cursus 11.1.2): `t[0]`, `t[-1]`, `t[1:3]`,
            `len(t)`, `x in t` en `for x in t:`.
            """,
            """
            t = (10, 20, 30, 40)
            print(t[1:3])
            for i in range(len(t)):
                print(i, t[i])
            """,
        ),
        les(
            "Tuples vergelijken",
            """
            Tuples worden **element per element** vergeleken (cursus 11.1.3): eerst de
            eerste elementen; zijn die gelijk, dan de tweede, enzovoort. Net zoals
            woorden in een woordenboek.
            """,
            """
            print((1, 2, 3) < (1, 3, 0))
            print((2, 1) == (1, 2))
            print((1, 2) < (1, 2, 0))
            """,
        ),
        les(
            "Tuples als retourwaarde en onveranderbaar",
            """
            Een functie die meerdere waarden teruggeeft (`return a, b`), geeft
            eigenlijk **één tuple** terug (cursus 11.1.4).

            Een tuple kan je niet aanpassen: `t[0] = 5` geeft een **TypeError**
            (cursus 11.2). Daarom gebruik je tuples voor gegevens die bij elkaar horen
            en vast liggen, zoals een punt (x, y) of een datum (dag, maand, jaar).
            """,
            """
            def min_max(a, b, c):
                return min(a, b, c), max(a, b, c)

            resultaat = min_max(7, 2, 9)
            print(resultaat)
            laag, hoog = resultaat
            print(laag, hoog)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            t = ("appel", "peer", "kers")
            print(t[1], len(t), t[-1])
            """,
            "Index 1 is het tweede element. Er zijn 3 elementen. -1 is het laatste.",
        ),
        voorspel(
            """
            a, b, c = (1, 2, 3)
            print(c, b, a)
            """,
            "De tuple wordt uitgepakt: a = 1, b = 2, c = 3.",
        ),
        voorspel(
            """
            print((1, 2, 3) < (1, 3, 0))
            print((2, 1) == (1, 2))
            print(("Zeb", 18) < ("Zeb", 19))
            """,
            """
            Eerst de eerste elementen vergelijken. Bij (1, 2, 3) en (1, 3, 0) zijn die gelijk,
            dan 2 < 3: True. (2, 1) en (1, 2) zijn niet gelijk: de volgorde telt.
            """,
        ),
        voorspel(
            """
            t = (10, 20, 30)
            for i in range(len(t)):
                print(i, t[i])
            """,
            "Met `range(len(t))` loop je over de indexen 0, 1 en 2.",
            boek="Opgave in 11.1.2",
        ),
        voorspel(
            """
            print(len((5,)), len((5, 6)))
            print((5) + 1)
            """,
            "`(5,)` is een tuple met één element. `(5)` is gewoon het getal 5, dus `(5) + 1` is 6.",
        ),
        keuze(
            "Wat gebeurt er als je dit uitvoert?",
            ["Het toont (5, 2, 3)", "Het toont (1, 2, 3)", "Een fout (TypeError): een tuple kan je niet veranderen",
             "Het toont 5"],
            2,
            "Tuples zijn onveranderbaar. Wil je een andere waarde, maak dan een nieuwe tuple: `t = (5,) + t[1:]`.",
            code="""
            t = (1, 2, 3)
            t[0] = 5
            print(t)
            """,
        ),
        voorspel(
            """
            def deel(a, b):
                return a // b, a % b

            r = deel(17, 5)
            print(r, r[0])
            """,
            "De functie geeft één tuple `(3, 2)` terug. `r[0]` is het eerste element.",
        ),
        schrijf(
            """
            Een complex getal a + bi stellen we voor als tuple `(a, b)`.
            Schrijf een functie `complex_som(z1, z2)` die de som teruggeeft, ook als tuple:
            (a + bi) + (c + di) = (a + c) + (b + d)i.
            """,
            """
            def complex_som(z1, z2):
                a, b = z1
                c, d = z2
                return (a + c, b + d)
            """,
            "Pak beide tuples eerst uit; dan is de berekening eenvoudig.",
            tests=[("complex_som((1, 2), (3, 4))", (4, 6)), ("complex_som((0, 0), (5, -1))", (5, -1))],
            start="def complex_som(z1, z2):",
            boek="Opgave 11.1",
        ),
        schrijf(
            """
            Schrijf een functie `complex_maal(z1, z2)` die twee complexe getallen (als tuples)
            vermenigvuldigt: (a + bi) · (c + di) = (ac − bd) + (ad + bc)i.
            """,
            """
            def complex_maal(z1, z2):
                a, b = z1
                c, d = z2
                return (a * c - b * d, a * d + b * c)
            """,
            "Uitpakken, en dan de formule letterlijk overnemen.",
            tests=[("complex_maal((1, 2), (3, 4))", (-5, 10)), ("complex_maal((0, 1), (0, 1))", (-1, 0))],
            start="def complex_maal(z1, z2):",
            boek="Opgave 11.2",
        ),
        schrijf(
            """
            Schrijf een functie `min_max(t)` die van een (niet-lege) tuple getallen een tuple
            `(kleinste, grootste)` teruggeeft, **zonder** `min` en `max`.
            """,
            """
            def min_max(t):
                kleinste = t[0]
                grootste = t[0]
                for x in t:
                    if x < kleinste:
                        kleinste = x
                    if x > grootste:
                        grootste = x
                return (kleinste, grootste)
            """,
            "Het algoritme van hoofdstuk 7: start met het eerste element en verbeter onderweg.",
            tests=[("min_max((3, 9, 2))", (2, 9)), ("min_max((5,))", (5, 5)), ("min_max((-1, -7, 4))", (-7, 4))],
            start="def min_max(t):",
            verboden=["min(", "max("],
        ),
    ],
}
