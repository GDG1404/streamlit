"""Instaptest: een korte test om te zien bij welk niveau je best begint.
Elke vraag hoort bij een niveau ('n'). Er is altijd een knop 'Ik weet het niet'."""

from helpers import voorspel, keuze

VRAGEN = [
    dict(n=0, **voorspel(
        """
        x = 3
        x = x + 2
        print(x)
        """,
        "x wordt eerst 3, daarna 3 + 2 = 5.",
    )),
    dict(n=0, **keuze(
        "Wat doet `naam = \"Zeb\"`?",
        ["Het toont Zeb op het scherm", "Het steekt de tekst Zeb in de variabele naam",
         "Het vergelijkt naam met Zeb", "Het vraagt de gebruiker een naam"],
        1,
        "Eén `=` is een toekenning.",
    )),
    dict(n=1, **voorspel(
        """
        print(7 // 2, 7 % 2)
        """,
        "`//` is de gehele deling (3), `%` de rest (1).",
    )),
    dict(n=2, **voorspel(
        """
        a = "4"
        b = "2"
        print(a + b)
        """,
        "Het zijn teksten: `+` plakt ze aan elkaar.",
    )),
    dict(n=2, **keuze(
        "De gebruiker typt `5` bij `x = input()`. Wat is x?",
        ["Het getal 5", 'De tekst "5"', "5.0", "Een fout"],
        1,
        "`input` geeft altijd tekst terug.",
    )),
    dict(n=3, **voorspel(
        """
        x = 12
        if x > 20:
            print("A")
        elif x > 10:
            print("B")
        else:
            print("C")
        """,
        "12 > 20 is onwaar, 12 > 10 is waar: B.",
    )),
    dict(n=3, **keuze(
        "Wanneer is `a > 0 and b > 0` waar?",
        ["Als a of b positief is", "Als a en b allebei positief zijn",
         "Als a positief is", "Altijd"],
        1,
        "`and` is alleen waar als beide delen waar zijn.",
    )),
    dict(n=4, **voorspel(
        """
        s = 0
        i = 1
        while i <= 3:
            s = s + i
            i = i + 1
        print(s)
        """,
        "s wordt 1, 3, 6.",
    )),
    dict(n=5, **keuze(
        "Welke getallen geeft `range(1, 5)`?",
        ["1 2 3 4 5", "1 2 3 4", "0 1 2 3 4", "2 3 4 5"],
        1,
        "Start bij 1, het einde (5) zit er niet in.",
    )),
    dict(n=5, **voorspel(
        """
        n = 0
        for c in "banaan":
            if c == "a":
                n = n + 1
        print(n)
        """,
        "Er staan drie a's in banaan.",
    )),
    dict(n=6, **voorspel(
        """
        lst = [5, 10, 15, 20]
        print(lst[1], lst[-1])
        print(lst[1:3])
        """,
        "Index 1 is het tweede element. -1 is het laatste. `[1:3]` geeft index 1 en 2.",
    )),
    dict(n=7, **voorspel(
        """
        def f(x):
            print(x * 2)

        y = f(4)
        print(y)
        """,
        "f toont 8 maar heeft geen return, dus y is None.",
    )),
]
