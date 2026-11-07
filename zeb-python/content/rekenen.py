from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "rekenen",
    "titel": "Rekenen",
    "kort": "+ - * / // % ** en math",
    "hoofdstuk": "3, 4 en 5",
    "spiek": ["maths", "assignment", "imports"],
    "doel": "Je kan elke rekenbewerking uitrekenen zoals Python het doet, ook `//` en `%`.",
    "uitleg": [
        les(
            "De gewone bewerkingen",
            """
            `+` optellen, `-` aftrekken, `*` vermenigvuldigen, `/` delen en
            `**` machtsverheffen.

            Let op: `/` geeft **altijd** een kommagetal (`float`), ook als de
            deling opgaat. `6 / 2` geeft `3.0`, niet `3`.
            """,
            """
            print(7 + 2)
            print(7 * 2)
            print(7 / 2)
            print(6 / 2)
            print(2 ** 3)
            """,
        ),
        les(
            "Gehele deling // en rest %",
            """
            Denk aan de lagere school: **17 gedeeld door 5 is 3, rest 2**.
            - `17 // 5` geeft het quotiënt: `3`
            - `17 % 5` geeft de rest: `2`

            De rest `%` (spreek uit: *modulo*) is super handig:
            - `n % 2 == 0` betekent: n is **even**
            - `n % 10` geeft het **laatste cijfer** van n
            - `n // 10` haalt het laatste cijfer **weg**
            """,
            """
            print(17 // 5)
            print(17 % 5)
            print(4728 % 10)
            print(4728 // 10)
            """,
        ),
        les(
            "Volgorde van bewerkingen",
            """
            Zoals in de wiskunde: eerst haakjes, dan `**`, dan `*` `/` `//` `%`,
            en pas daarna `+` en `-`. Op je spiekbrief: *Priority (...)*.

            Twijfel je? Zet haakjes. Dat is nooit fout.
            """,
            """
            print(2 + 3 * 4)
            print((2 + 3) * 4)
            print(10 - 2 ** 2)
            """,
        ),
        les(
            "Kortere schrijfwijze: +=",
            """
            `x += 3` is hetzelfde als `x = x + 3`. Zo bestaan er ook `-=`, `*=`,
            `/=`, `//=` en `%=`. Je spiekbrief noemt dat *increment* en *decrement*.
            """,
            """
            x = 10
            x += 3
            x -= 1
            x *= 2
            print(x)
            """,
        ),
        les(
            "int en float samen",
            """
            Reken je met een `int` en een `float`, dan is het resultaat een `float`.
            `round(x, n)` rondt af op n cijfers na de komma. Met `round(x)` krijg je
            een geheel getal. `abs(x)` geeft de absolute waarde.
            """,
            """
            print(3 + 1.5)
            print(round(3.57, 1))
            print(round(3.57))
            print(abs(-3.2))
            """,
        ),
        les(
            "Wiskundige functies uit math",
            """
            Voor vierkantswortel, sinus, pi enzovoort moet je eerst **importeren**
            uit de module `math` (spiekbrief: *Maths* en *Modules/Names Imports*).

            Twee manieren:
            - `from math import sqrt, pi` en dan gewoon `sqrt(16)`
            - `import math` en dan `math.sqrt(16)`
            """,
            """
            from math import sqrt, pi
            print(sqrt(81))
            print(round(pi, 2))
            import math
            print(math.floor(12.5), math.ceil(12.5))
            """,
        ),

        les(
            "Kommagetallen zijn niet altijd exact",
            """
            Een float wordt in de computer **benaderd** opgeslagen. Daardoor geeft
            `(431 / 100) * 100` niet 431 maar `430.99999999999994` (cursus 3.2.3).
            Weet je dat de uitkomst een geheel getal moet zijn, rond dan af met `round()`.

            En onthoud: zodra er een `/` in een berekening staat, is de uitkomst een
            float, ook als er geen decimalen zijn.
            """,
            """
            print((431 / 100) * 100)
            print(round((431 / 100) * 100))
            print(5 * 2 - 3 + 4 / 2)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            print(7 / 2)
            print(7 // 2)
            print(7 % 2)
            """,
            "`/` geeft 3.5. `//` geeft het quotiënt 3. `%` geeft de rest: 7 = 2·3 + **1**.",
        ),
        voorspel(
            """
            print(2 + 3 * 4)
            print((2 + 3) * 4)
            """,
            "Vermenigvuldigen gaat voor optellen: 2 + 12 = 14. Met haakjes eerst 5, dan maal 4 = 20.",
        ),
        keuze(
            "Wat toont `print(17 % 5)`?",
            ["3", "2", "3.4", "12"],
            1,
            "17 = 5 · 3 + 2. De rest is 2.",
            code='print(17 % 5)',
            controleer_uitvoer=True,
        ),
        voorspel(
            """
            x = 10
            x += 5
            x *= 2
            print(x)
            """,
            "10, dan 15, dan 30.",
        ),
        voorspel(
            """
            print(2 ** 3)
            print(10 / 5)
            """,
            "`2 ** 3` is 2·2·2 = 8. `10 / 5` is een gewone deling, dus een float: `2.0`.",
            tip="Gewone deling met / geeft altijd een kommagetal.",
        ),
        keuze(
            "Hoe controleer je of het getal `n` **even** is?",
            ["n / 2 == 0", "n % 2 == 0", "n // 2 == 0", "n % 2 == 1"],
            1,
            """
            Een even getal heeft rest 0 bij deling door 2. `n % 2 == 1` controleert
            net of n **oneven** is.
            """,
        ),
        voorspel(
            """
            seconden = 135
            minuten = seconden // 60
            rest = seconden % 60
            print(minuten, "min", rest, "s")
            """,
            "135 seconden = 2 keer 60 (= 120) en nog 15 over.",
        ),
        voorspel(
            """
            from math import sqrt
            print(sqrt(16))
            print(abs(-7))
            print(round(3.14159, 2))
            """,
            "`sqrt` geeft altijd een float: `4.0`. `abs(-7)` is 7. Afronden op 2 cijfers: 3.14.",
        ),
        fout(
            "Dit programma moet het gemiddelde van a en b tonen (dus 6.0). Welke regel is fout?",
            """
            a = 8
            b = 4
            gem = a + b / 2
            print(gem)
            """,
            3,
            """
            a = 8
            b = 4
            gem = (a + b) / 2
            print(gem)
            """,
            """
            Zonder haakjes rekent Python eerst `b / 2` (= 2.0) en telt dan a erbij: 10.0.
            Er komt geen foutmelding, maar het resultaat is fout. Zo'n **logische fout**
            is het gevaarlijkst.
            """,
        ),
        aanvullen(
            "Vul aan zodat het programma het **laatste cijfer** van het getal toont (8).",
            """
            getal = 4728
            laatste = getal ___ 10
            print(laatste)
            """,
            [["%"]],
            "De rest bij deling door 10 is altijd het laatste cijfer.",
        ),
        voorspel(
            """
            a = 7
            b = 2
            print(a // b * b + a % b)
            """,
            """
            `7 // 2` = 3, maal 2 = 6, plus `7 % 2` = 1, geeft 7. Dat klopt altijd:
            quotiënt maal deler plus rest geeft het oorspronkelijke getal.
            """,
        ),
        voorspel(
            """
            x = 5
            y = 2
            x = x ** y
            y = x // 3
            print(x, y)
            """,
            "x wordt 5² = 25. Dan y = 25 // 3 = 8 (want 3 · 8 = 24, rest 1).",
        ),
        schrijf(
            """
            Gegeven: `celsius = 25`.
            Reken om naar Fahrenheit met de formule F = C × 9/5 + 32 en toon het resultaat.
            """,
            """
            celsius = 25
            fahrenheit = celsius * 9 / 5 + 32
            print(fahrenheit)
            """,
            "Door `/` krijg je een float, dus het resultaat is `77.0`.",
            ptests=[([], "77.0")],
            start="celsius = 25",
        ),
        schrijf(
            """
            Gegeven: `totaal = 1000` (minuten).
            Toon hoeveel uren en minuten dat is, in de vorm `16 u 40 min`.
            """,
            """
            totaal = 1000
            uren = totaal // 60
            minuten = totaal % 60
            print(uren, "u", minuten, "min")
            """,
            "`//` geeft het aantal volle uren, `%` de minuten die overblijven.",
            ptests=[([], "16 u 40 min")],
            start="totaal = 1000",
        ),

        voorspel(
            """
            print(5 * 2 - 3 + 4 / 2)
            print((5 * 2) - (3 + 4) / 2)
            """,
            """
            Eerst `5 * 2` = 10 en `4 / 2` = 2.0, dan 10 - 3 + 2.0 = 9.0 (een float, door de `/`).
            Spaties veranderen niets aan de volgorde. Met haakjes: 10 - 7 / 2 = 10 - 3.5 = 6.5.
            """,
            boek="Voorbeeld in 3.3.2",
        ),
        voorspel(
            """
            aantal_bananen = 100
            aantal_bananen += 12
            aantal_bananen -= 13
            aantal_bananen *= 19
            aantal_bananen /= aantal_bananen
            print(aantal_bananen)
            """,
            """
            100 → 112 → 99 → 1881. Daarna delen door zichzelf: 1881 / 1881 = 1.0.
            Het is een float omdat `/=` een gewone deling is.
            """,
            boek="Opgave in 4.5",
        ),
        keuze(
            "`print((431 / 100) * 100)` toont `430.99999999999994`. Waarom?",
            [
                "Python rekent fout met haakjes",
                "Kommagetallen (floats) worden in de computer benaderd opgeslagen",
                "Omdat 431 een priemgetal is",
                "`/` rondt altijd naar beneden af",
            ],
            1,
            "Floats zijn benaderingen. Gebruik `round()` als je een geheel getal verwacht.",
        ),
        schrijf(
            """
            Gegeven `bedrag = 287` (in centen). Druk het bedrag uit in zo weinig mogelijk
            muntjes: dollars (100 ct), kwartjes (25 ct), dubbeltjes (10 ct), stuivers (5 ct)
            en centen (1 ct). Toon de vijf aantallen op één regel, in die volgorde.
            Voor 287 is dat `2 3 1 0 2`.
            """,
            """
            bedrag = 287
            dollars = bedrag // 100
            bedrag = bedrag % 100
            kwartjes = bedrag // 25
            bedrag = bedrag % 25
            dubbeltjes = bedrag // 10
            bedrag = bedrag % 10
            stuivers = bedrag // 5
            centen = bedrag % 5
            print(dollars, kwartjes, dubbeltjes, stuivers, centen)
            """,
            """
            Telkens hetzelfde patroon: `//` geeft hoeveel muntjes er passen, `%` geeft
            wat er overblijft voor de volgende, kleinere munt.
            """,
            ptests=[([], "2 3 1 0 2")],
            start="bedrag = 287",
            boek="Opgave 4.3",
            uitdaging=True,
        ),
    ],
}
