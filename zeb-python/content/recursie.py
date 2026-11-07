from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "recursie",
    "titel": "Recursie",
    "kort": "een functie die zichzelf aanroept",
    "hoofdstuk": "9",
    "spiek": ["def", "call"],
    "doel": "Je kan een recursieve functie op papier volgen, aanroep per aanroep, en zelf een eenvoudige recursieve functie schrijven.",
    "uitleg": [
        les(
            "Wat is recursie?",
            """
            Een functie is **recursief** als ze **zichzelf** aanroept (cursus 9.1).
            Dat werkt alleen als elke recursieve functie twee delen heeft:
            - een **stopgeval** (basisgeval): een eenvoudig geval waarvoor je het
              antwoord meteen kent, zonder nieuwe aanroep
            - een **recursieve stap**: de functie roept zichzelf aan met een
              **kleiner** probleem, dat dichter bij het stopgeval ligt

            Het klassieke voorbeeld is de faculteit: n! = n · (n−1)!, en 1! = 1.
            """,
            """
            def faculteit(n):
                if n <= 1:
                    return 1
                return n * faculteit(n - 1)

            print(faculteit(4))
            """,
        ),
        les(
            "Volg de aanroepen op papier",
            """
            Elke aanroep heeft zijn **eigen** variabelen. `faculteit(4)` wacht op
            `faculteit(3)`, die wacht op `faculteit(2)`, enzovoort. Pas als het
            stopgeval een antwoord geeft, komen de antwoorden één voor één terug.

            Op papier schrijf je dat als een trap:
            - faculteit(4) = 4 · faculteit(3)
            - faculteit(3) = 3 · faculteit(2)
            - faculteit(2) = 2 · faculteit(1)
            - faculteit(1) = 1 (stopgeval)

            en dan terug naar boven: 2 · 1 = 2, 3 · 2 = 6, 4 · 6 = 24.
            Klik op **Stap voor stap** om de aanroepen te zien verschijnen en verdwijnen.
            """,
            """
            def aftellen(n):
                if n == 0:
                    print("Start!")
                else:
                    print(n)
                    aftellen(n - 1)

            aftellen(3)
            """,
        ),
        les(
            "Recursieve definities",
            """
            Sommige dingen zijn in de wiskunde al recursief gedefinieerd
            (cursus 9.2). Het n-de Fibonacci-getal is de som van de twee vorige:
            fib(n) = fib(n−1) + fib(n−2), met fib(1) = fib(2) = 1.

            Zo'n definitie kan je bijna letterlijk in Python schrijven. Maar let op:
            `fib()` roept zichzelf **twee** keer aan, en wordt daardoor heel traag
            voor grote n (cursus opgave 9.3). Een while loop is hier sneller.
            """,
            """
            def fib(n):
                if n <= 2:
                    return 1
                return fib(n - 1) + fib(n - 2)

            print(fib(6))
            """,
        ),
        les(
            "Wanneer gebruik je recursie?",
            """
            Recursie is handig als een probleem bestaat uit een **kleinere versie
            van hetzelfde probleem** (cursus 9.2.1): de grootste gemene deler, de
            Torens van Hanoi, een doolhof doorzoeken, geneste lists.

            Vergeet je het stopgeval, of wordt het probleem niet kleiner, dan roept
            de functie zichzelf eindeloos aan. Python stopt dan met een
            **RecursionError**.
            """,
            """
            def ggd(a, b):
                if b == 0:
                    return a
                return ggd(b, a % b)

            print(ggd(14, 21))
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            def f(n):
                if n == 0:
                    return 0
                return n + f(n - 1)

            print(f(4))
            """,
            "f(4) = 4 + f(3) = 4 + 3 + f(2) = ... = 4 + 3 + 2 + 1 + 0 = 10.",
            tip="Schrijf de trap van aanroepen op papier, tot je bij f(0) komt.",
        ),
        voorspel(
            """
            def aftellen(n):
                if n == 0:
                    print("Start!")
                else:
                    print(n)
                    aftellen(n - 1)

            aftellen(3)
            """,
            "Elke aanroep toont eerst zijn n en roept dan aftellen(n - 1) aan. Bij 0: `Start!`.",
        ),
        voorspel(
            """
            def g(n):
                if n > 0:
                    g(n - 1)
                print(n)

            g(3)
            """,
            """
            Hier staat de `print` **na** de recursieve aanroep. g(3) roept eerst g(2) aan,
            die eerst g(1), die eerst g(0). g(0) toont als eerste 0, daarna toont g(1) 1,
            enzovoort. Dus 0, 1, 2, 3.
            """,
            tip="Wat doet g(0)? Schrijf dat eerst op, dan g(1), dan g(2).",
        ),
        voorspel(
            """
            def fib(n):
                if n <= 2:
                    return 1
                return fib(n - 1) + fib(n - 2)

            print(fib(6))
            """,
            "1, 1, 2, 3, 5, 8: het zesde Fibonacci-getal is 8.",
        ),
        keuze(
            "Wat gebeurt er met dit programma?",
            [
                "Het toont 0",
                "Het toont 5, 4, 3, 2, 1",
                "De functie roept zichzelf eindeloos aan: RecursionError",
                "Het toont niets en stopt meteen",
            ],
            2,
            "Er is geen stopgeval. De functie roept zichzelf altijd opnieuw aan, tot Python stopt met een RecursionError.",
            code="""
            def f(n):
                return f(n - 1)

            print(f(5))
            """,
            draai=False,
        ),
        keuze(
            "Wat doet de functie `raadsel`?",
            [
                "Ze telt de cijfers van het getal op",
                "Ze telt hoeveel cijfers het getal heeft",
                "Ze geeft het laatste cijfer terug",
                "Ze keert het getal om",
            ],
            1,
            "Elke aanroep haalt met `// 10` één cijfer weg en telt 1 op. Een getal onder 10 heeft 1 cijfer. Voor 4721: 4.",
            code="""
            def raadsel(n):
                if n < 10:
                    return 1
                return 1 + raadsel(n // 10)

            print(raadsel(4721))
            """,
            lees=True,
        ),
        aanvullen(
            "Vul aan zodat `faculteit(n)` recursief n! berekent.",
            """
            def faculteit(n):
                if n ___ 1:
                    return ___
                return n * faculteit(___)

            print(faculteit(4))
            """,
            [["<=", "=="], ["1"], ["n - 1", "n-1"]],
            "Stopgeval: n is 1 (of kleiner), dan is het antwoord 1. Anders n maal de faculteit van n − 1.",
        ),
        voorspel(
            """
            def hanoi(n, van, naar, via):
                if n == 0:
                    return
                hanoi(n - 1, van, via, naar)
                print(van, "->", naar)
                hanoi(n - 1, via, naar, van)

            hanoi(2, "A", "C", "B")
            """,
            """
            De Torens van Hanoi met 2 schijven: de kleine schijf naar B, de grote naar C,
            en de kleine van B naar C. Elke `hanoi(0, ...)` doet niets.
            """,
            tip="Begin met hanoi(1, ...): die toont precies één zet.",
            boek="Opgave 9.6 (met 2 schijven)",
        ),
        schrijf(
            """
            Schrijf een **recursieve** functie `fib(n)` die het n-de Fibonacci-getal teruggeeft.
            fib(1) en fib(2) zijn 1, en fib(n) = fib(n−1) + fib(n−2).
            """,
            """
            def fib(n):
                if n <= 2:
                    return 1
                return fib(n - 1) + fib(n - 2)
            """,
            "Stopgeval eerst, dan de recursieve stap. De code volgt letterlijk de definitie.",
            tests=[("fib(1)", 1), ("fib(2)", 1), ("fib(6)", 8), ("fib(10)", 55)],
            start="def fib(n):",
            boek="Opgave 9.1",
        ),
        schrijf(
            """
            Schrijf een **recursieve** functie `ggd(a, b)` voor de grootste gemene deler,
            met het algoritme van Euclides: is b gelijk aan 0, dan is het antwoord a;
            anders is het antwoord `ggd(b, a % b)`.
            """,
            """
            def ggd(a, b):
                if b == 0:
                    return a
                return ggd(b, a % b)
            """,
            "Bij elke aanroep worden de getallen kleiner, tot de rest 0 is.",
            tests=[("ggd(14, 21)", 7), ("ggd(48, 18)", 6), ("ggd(7, 5)", 1), ("ggd(10, 0)", 10)],
            start="def ggd(a, b):",
            boek="Opgave 9.4",
        ),
        schrijf(
            """
            Schrijf een **recursieve** functie `som_cijfers(n)` die de som van de cijfers van
            een positief geheel getal teruggeeft. `som_cijfers(523)` geeft 10.
            Gebruik geen loop.
            """,
            """
            def som_cijfers(n):
                if n < 10:
                    return n
                return n % 10 + som_cijfers(n // 10)
            """,
            "Het laatste cijfer is `n % 10`, de rest van het getal is `n // 10`.",
            tests=[("som_cijfers(523)", 10), ("som_cijfers(7)", 7), ("som_cijfers(0)", 0), ("som_cijfers(9999)", 36)],
            start="def som_cijfers(n):",
            verboden=["for ", "while "],
        ),
        schrijf(
            """
            Schrijf een **recursieve** functie `macht(x, n)` die x tot de macht n berekent
            (n is een geheel getal ≥ 0), **zonder** `**` of `pow`. Gebruik: x⁰ = 1 en
            xⁿ = x · xⁿ⁻¹.
            """,
            """
            def macht(x, n):
                if n == 0:
                    return 1
                return x * macht(x, n - 1)
            """,
            "Stopgeval n = 0 geeft 1. Elke stap vermenigvuldigt met x en verlaagt n met 1.",
            tests=[("macht(2, 10)", 1024), ("macht(5, 0)", 1), ("macht(3, 3)", 27)],
            start="def macht(x, n):",
            verboden=["**", "pow("],
            uitdaging=True,
        ),
    ],
}
