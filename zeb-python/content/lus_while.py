from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "while",
    "titel": "while loop",
    "kort": "herhalen zolang iets waar is",
    "hoofdstuk": "7.1 en 7.5",
    "spiek": ["while", "loop-control"],
    "doel": "Je kan een while loop ronde per ronde volgen met een variabelentabel.",
    "uitleg": [
        les(
            "while: herhaal zolang het waar is",
            """
            `while conditie:` voert het ingesprongen blok uit **zolang** de
            conditie waar is. Na elke ronde gaat Python terug naar boven en
            controleert de conditie opnieuw. Is ze onwaar, dan gaat het programma
            verder na de loop.
            """,
            """
            i = 1
            while i <= 3:
                print("ronde", i)
                i = i + 1
            print("klaar")
            """,
        ),
        les(
            "De drie onderdelen van een loop",
            """
            Bijna elke while loop heeft drie stukken. Je spiekbrief toont ze bij
            *Conditional Loop Statement*:
            - een **beginwaarde** vóór de loop (`i = 1`)
            - een **conditie** (`i <= 100`)
            - iets in de loop dat de variabele **verandert** (`i = i + 1`)

            Vergeet je dat laatste, dan stopt de loop nooit: een **eindeloze loop**.
            Je spiekbrief waarschuwt: *beware of infinite loops!*
            """,
            """
            s = 0
            i = 1
            while i <= 100:
                s = s + i ** 2
                i = i + 1
            print("sum:", s)
            """,
            papier="Dit is exact het voorbeeld van je spiekbrief: de som van de kwadraten van 1 tot 100.",
        ),
        les(
            "Patroon: optellen in een loop",
            """
            Wil je iets optellen of tellen in een loop, dan:
            1. zet je **vóór** de loop een variabele op 0 (`som = 0` of `aantal = 0`)
            2. tel je er **in** de loop telkens iets bij
            3. gebruik je het resultaat **na** de loop

            Dat patroon komt op elk examen terug.
            """,
            """
            som = 0
            getal = 1
            while getal <= 5:
                som = som + getal
                getal = getal + 1
            print(som)
            """,
        ),
        les(
            "Tot de gebruiker stopt",
            """
            Een while loop is ideaal als je **niet op voorhand weet** hoe vaak je moet
            herhalen, bijvoorbeeld tot de gebruiker 0 intypt.
            """,
            """
            totaal = 0
            getal = int(input("Getal (0 = stop): "))
            while getal != 0:
                totaal = totaal + getal
                getal = int(input("Getal (0 = stop): "))
            print("Totaal:", totaal)
            """,
            inputs=["5", "3", "0"],
            papier="Hier typte de gebruiker 5, 3 en dan 0.",
        ),
        les(
            "break: de loop meteen verlaten",
            """
            `break` stopt de loop onmiddellijk, ook als de conditie nog waar is
            (spiekbrief: *Loop Control*). Handig om te stoppen zodra je gevonden
            hebt wat je zocht.
            """,
            """
            n = 1
            while True:
                if n * n > 50:
                    break
                n = n + 1
            print(n)
            """,
            papier="`while True` lijkt oneindig, maar `break` stopt de loop zodra n² groter is dan 50.",
        ),

        les(
            "De loop-en-een-half",
            """
            Soms moet je eerst iets doen (een getal vragen) en pas **daarna** kan
            je beslissen of de loop stopt. Je cursus noemt dat de
            **loop-en-een-half** (7.5): een `while True` met een `break` in het midden.
            """,
            """
            while True:
                getal = int(input("Positief getal: "))
                if getal > 0:
                    break
                print("Dat mag niet, probeer opnieuw.")
            print("Bedankt voor", getal)
            """,
            inputs=["-4", "0", "7"],
            papier="Hier typte de gebruiker -4, 0 en dan 7.",
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            i = 1
            while i <= 3:
                print(i)
                i = i + 1
            """,
            "Ronde 1: i=1, ronde 2: i=2, ronde 3: i=3. Dan is i=4 en is `4 <= 3` onwaar.",
        ),
        voorspel(
            """
            i = 10
            while i > 0:
                print(i)
                i = i - 3
            """,
            "i wordt 10, 7, 4, 1 en dan -2. Bij -2 is `i > 0` onwaar, dus -2 wordt niet meer getoond.",
        ),
        voorspel(
            """
            s = 0
            i = 1
            while i <= 4:
                s = s + i
                i = i + 1
            print(s)
            """,
            "s wordt 0+1=1, 1+2=3, 3+3=6, 6+4=10. De print staat na de loop, dus één keer: 10.",
            tip="Maak een tabel met kolommen i en s, één rij per ronde.",
        ),
        keuze(
            'Hoe vaak verschijnt "hallo"?',
            ["4 keer", "5 keer", "6 keer", "Oneindig vaak"],
            1,
            "i gaat van 0 tot en met 4: dat zijn 5 rondes. Bij i = 5 is `5 < 5` onwaar.",
            code="""
            i = 0
            while i < 5:
                print("hallo")
                i += 1
            """,
        ),
        keuze(
            "Wat gebeurt er met dit programma?",
            [
                "Het toont 1, 2, 3, 4",
                "Het toont 1, 2, 3, 4, 5",
                "Het toont één keer 1",
                "Het stopt nooit: het toont oneindig vaak 1",
            ],
            3,
            "i verandert nooit in de loop. `1 < 5` blijft altijd waar: een **eindeloze loop**.",
            code="""
            i = 1
            while i < 5:
                print(i)
            """,
            draai=False,
        ),
        voorspel(
            """
            n = 1
            while n < 100:
                n = n * 2
            print(n)
            """,
            "n verdubbelt: 1, 2, 4, 8, 16, 32, 64, 128. Bij 128 is `128 < 100` onwaar.",
        ),
        voorspel(
            """
            x = 5
            while x > 5:
                print("in de loop")
            print("klaar")
            """,
            "`5 > 5` is meteen onwaar. Het blok wordt **nul keer** uitgevoerd.",
        ),
        fout(
            "Dit programma moet de getallen 1 tot en met 5 tonen. Welke regel is fout?",
            """
            i = 1
            while i < 5:
                print(i)
                i = i + 1
            """,
            2,
            """
            i = 1
            while i <= 5:
                print(i)
                i = i + 1
            """,
            "Met `i < 5` stopt de loop al na 4. Je hebt `i <= 5` (of `i < 6`) nodig.",
        ),
        aanvullen(
            "Vul aan zodat het programma aftelt: 5, 4, 3, 2, 1.",
            """
            i = 5
            while i ___ 0:
                print(i)
                i = i ___ 1
            """,
            [[">", "!="], ["-"]],
            "Zolang i groter is dan 0, toon je i en trek je er 1 af.",
        ),
        voorspel(
            """
            getal = 1234
            aantal = 0
            while getal > 0:
                getal = getal // 10
                aantal += 1
            print(aantal)
            """,
            "Elke ronde haalt `// 10` het laatste cijfer weg: 123, 12, 1, 0. Dat zijn 4 rondes, dus het aantal cijfers.",
        ),
        keuze(
            "Wat doet dit programma?",
            [
                "Het telt hoeveel cijfers het getal heeft",
                "Het berekent de som van de cijfers",
                "Het keert het getal om",
                "Het toont het laatste cijfer",
            ],
            1,
            "`n % 10` is telkens het laatste cijfer, dat bij s wordt opgeteld. Daarna wordt dat cijfer weggehaald. Voor 523: 3 + 2 + 5 = 10.",
            code="""
            n = 523
            s = 0
            while n > 0:
                s = s + n % 10
                n = n // 10
            print(s)
            """,
            lees=True,
        ),
        voorspel(
            """
            a = 48
            b = 18
            while b != 0:
                a, b = b, a % b
            print(a)
            """,
            """
            Rondes: (48, 18) → (18, 12) → (12, 6) → (6, 0). Dan stopt de loop en is a = 6.
            Dit is het algoritme van Euclides voor de **grootste gemene deler**.
            """,
            tip="Maak een tabel met kolommen a, b en a % b.",
        ),
        schrijf(
            """
            Vraag een geheel getal n en toon de som 1 + 2 + ... + n.
            Gebruik een **while loop**. Bij 4 verschijnt `10`.
            """,
            """
            n = int(input("n: "))
            som = 0
            i = 1
            while i <= n:
                som = som + i
                i = i + 1
            print(som)
            """,
            "Het patroon: beginwaarde vóór de loop, optellen in de loop, tonen na de loop.",
            ptests=[(["4"], "10"), (["1"], "1"), (["100"], "5050")],
        ),
        schrijf(
            """
            Vraag telkens een getal, tot de gebruiker `0` intypt.
            Toon daarna de som van alle ingetypte getallen.
            Typt de gebruiker 3, 5, 2 en 0, dan verschijnt `10`.
            """,
            """
            som = 0
            getal = int(input("Getal: "))
            while getal != 0:
                som = som + getal
                getal = int(input("Getal: "))
            print(som)
            """,
            """
            Vraag het eerste getal **vóór** de loop en het volgende getal **op het einde** van de loop.
            Zo wordt de 0 nooit meegeteld.
            """,
            ptests=[(["3", "5", "2", "0"], "10"), (["0"], "0"), (["-4", "4", "7", "0"], "7")],
            uitdaging=True,
        ),

        schrijf(
            """
            Schrijf code die aftelt van 10 tot 1, elk getal op een eigen regel.
            Daarna toont het programma `Start!` (de 0 wordt niet getoond).
            Gebruik een **while loop**.
            """,
            """
            teller = 10
            while teller > 0:
                print(teller)
                teller -= 1
            print("Start!")
            """,
            "`Start!` staat **na** de loop, niet erin.",
            ptests=[([], "\n".join(str(i) for i in range(10, 0, -1)) + "\nStart!")],
            boek="Opgave in 7.1.5",
        ),
        schrijf(
            """
            Vraag een positief geheel getal n en toon n! (de faculteit:
            n · (n-1) · ... · 1). Gebruik een **while loop**. Bij 5 verschijnt `120`.
            """,
            """
            n = int(input("n: "))
            resultaat = 1
            while n > 1:
                resultaat *= n
                n -= 1
            print(resultaat)
            """,
            "Bij vermenigvuldigen begin je bij 1, niet bij 0.",
            ptests=[(["5"], "120"), (["1"], "1"), (["10"], "3628800")],
            boek="Opgave in 7.1.5",
        ),
        schrijf(
            """
            De Fibonacci-reeks begint met 1 en 1. Elk volgend getal is de som van de
            twee vorige: 1, 1, 2, 3, 5, 8, 13, ... Toon alle Fibonacci-getallen die
            **kleiner zijn dan 1000**, elk op een eigen regel.
            """,
            """
            a = 1
            b = 1
            while a < 1000:
                print(a)
                a, b = b, a + b
            """,
            """
            Je hebt twee variabelen nodig: het huidige en het volgende getal.
            `a, b = b, a + b` schuift ze allebei één plaats op.
            """,
            ptests=[([], "1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n89\n144\n233\n377\n610\n987")],
            tip="Maak eerst op papier een tabel met a en b voor de eerste 5 rondes.",
            boek="Opgave 7.5",
        ),
        schrijf(
            """
            Vraag een positief geheel getal. Zolang de gebruiker 0 of een negatief getal
            intypt, toon je `Dat mag niet` en vraag je opnieuw. Toon daarna het
            **kwadraat** van het getal. Gebruik een loop-en-een-half.
            """,
            """
            while True:
                getal = int(input("Getal: "))
                if getal > 0:
                    break
                print("Dat mag niet")
            print(getal * getal)
            """,
            "`while True` met een `break` zodra het getal goed is.",
            ptests=[(["-3", "0", "5"], "Dat mag niet\nDat mag niet\n25"), (["4"], "16")],
            boek="Opgave in 7.5",
        ),
    ],
}
