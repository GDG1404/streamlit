from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "for",
    "titel": "for loop",
    "kort": "for, range, break, geneste loops",
    "hoofdstuk": "7.2 tot 7.7",
    "spiek": ["for", "range", "loop-control"],
    "doel": "Je weet precies welke getallen `range` geeft en kan een for loop op papier uitvoeren.",
    "uitleg": [
        les(
            "for: voor elk element één keer",
            """
            `for var in reeks:` voert het blok één keer uit **voor elk element**
            van de reeks. De variabele krijgt telkens het volgende element.
            Je hoeft die variabele zelf niet te verhogen: `for` doet dat voor jou.
            """,
            """
            for kleur in ["rood", "groen", "blauw"]:
                print("Ik hou van", kleur)
            """,
        ),
        les(
            "range: een reeks getallen",
            """
            `range` maakt een reeks gehele getallen (spiekbrief: *Integer Sequences*):
            - `range(5)` geeft 0 1 2 3 4: start bij 0, **5 zit er niet in**
            - `range(2, 6)` geeft 2 3 4 5
            - `range(0, 10, 3)` geeft 0 3 6 9: de derde waarde is de **stap**
            - `range(5, 0, -1)` geeft 5 4 3 2 1: aftellen met een negatieve stap

            De regel om te onthouden: **het einde zit er nooit in**.
            `range(n)` geeft precies n getallen.
            """,
            """
            for i in range(5):
                print(i, end=" ")
            print()
            for i in range(2, 12, 3):
                print(i, end=" ")
            print()
            """,
        ),
        les(
            "for over tekst",
            """
            Tekst is ook een reeks, namelijk van letters. `for letter in "abc"`
            loopt over `a`, dan `b`, dan `c`.

            Het voorbeeld van je spiekbrief telt hoeveel keer de letter `e`
            voorkomt in een tekst.
            """,
            """
            s = "Some text"
            cnt = 0
            for c in s:
                if c == "e":
                    cnt = cnt + 1
            print("found", cnt, "'e'")
            """,
        ),
        les(
            "while of for?",
            """
            - **for**: als je op voorhand weet hoe vaak, of als je over een reeks
              loopt (een list, een tekst, `range`).
            - **while**: als je herhaalt **tot** er iets gebeurt (de gebruiker typt 0,
              een getal wordt groter dan 100, ...).

            Elke for loop met `range` kan je ook als while loop schrijven. Deze twee doen hetzelfde:
            """,
            """
            for i in range(1, 4):
                print(i)
            i = 1
            while i < 4:
                print(i)
                i = i + 1
            """,
        ),
        les(
            "break en continue",
            """
            - `break` stopt de hele loop meteen
            - `continue` slaat de rest van **deze ronde** over en gaat naar de volgende
            """,
            """
            for i in range(10):
                if i == 2:
                    continue
                if i == 5:
                    break
                print(i)
            """,
        ),
        les(
            "Een loop in een loop",
            """
            Een loop mag in een andere loop staan. Voor **elke ronde** van de buitenste
            loop loopt de binnenste loop **helemaal**.
            """,
            """
            for rij in range(1, 4):
                for kol in range(1, 4):
                    print(rij * kol, end=" ")
                print()
            """,
        ),

        les(
            "else na een loop",
            """
            Een loop kan een `else` hebben (cursus 7.3.1). Dat blok wordt uitgevoerd
            als de loop **gewoon** eindigt, dus **niet** als hij stopt door `break`.
            Handig bij zoeken: "niet gevonden" komt in de `else`.
            """,
            """
            for getal in [4, 9, 15, 22]:
                if getal % 5 == 0:
                    print("Gevonden:", getal)
                    break
            else:
                print("Geen veelvoud van 5")
            """,
        ),
        les(
            "Een algoritme ontwerpen",
            """
            Je cursus (7.6 en 7.7) geeft een paar vaste stappen:
            - **Verwerk de gegevens één voor één.** Hou in variabelen bij wat je
              tot nu toe weet: het grootste tot nu toe, een teller, een som.
            - **Begin klein.** Laat eerst één ding werken (één getal vragen),
              breid dan uit (een loop errond, dan de berekening).
            - **Test met de hand** op een klein voorbeeld.

            Het klassieke voorbeeld: de grootste, de kleinste en het aantal getallen
            dat deelbaar is door 3.
            """,
            """
            getallen = [4, 9, 2, 12, 7]
            grootste = getallen[0]
            kleinste = getallen[0]
            deelbaar = 0
            for g in getallen:
                if g > grootste:
                    grootste = g
                if g < kleinste:
                    kleinste = g
                if g % 3 == 0:
                    deelbaar += 1
            print(grootste, kleinste, deelbaar)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            for i in range(4):
                print(i)
            """,
            "`range(4)` geeft 0, 1, 2, 3: vier getallen, startend bij 0. De 4 zit er niet in.",
        ),
        voorspel(
            """
            for i in range(2, 6):
                print(i, end=" ")
            """,
            "Van 2 tot (niet met) 6. Door `end=\" \"` blijft alles op één regel.",
        ),
        keuze(
            "Welke getallen geeft `range(1, 10, 3)`?",
            ["1 4 7 10", "1 4 7", "1 3 5 7 9", "3 6 9"],
            1,
            "Start bij 1, telkens 3 erbij: 1, 4, 7. De volgende zou 10 zijn, maar het einde (10) zit er nooit in.",
            code="print(*range(1, 10, 3))",
            controleer_uitvoer=True,
        ),
        voorspel(
            """
            for letter in "Zeb":
                print(letter)
            """,
            "De loop loopt over elke letter van de tekst.",
        ),
        voorspel(
            """
            s = 0
            for i in range(1, 5):
                s += i
            print(s)
            """,
            "i is 1, 2, 3, 4. s wordt 1, 3, 6, 10.",
        ),
        voorspel(
            """
            for i in range(3):
                print("*" * (i + 1))
            """,
            "i is 0, 1, 2, dus 1, 2 en 3 sterretjes.",
        ),
        voorspel(
            """
            tel = 0
            for c in "programmeren":
                if c == "r":
                    tel += 1
            print(tel)
            """,
            "Tel de r'en in p-**r**-o-g-**r**-a-m-m-e-**r**-e-n: 3.",
        ),
        voorspel(
            """
            for i in range(5, 0, -2):
                print(i)
            """,
            "Start bij 5, telkens 2 eraf: 5, 3, 1. De volgende zou -1 zijn, maar die ligt voorbij het einde (0).",
        ),
        voorspel(
            """
            for i in range(10):
                if i == 3:
                    break
                print(i)
            """,
            "Bij i = 3 stopt `break` de loop, nog vóór de print. Dus 0, 1, 2.",
        ),
        voorspel(
            """
            for i in range(1, 3):
                for j in range(1, 3):
                    print(i, j)
            """,
            "Voor i = 1 loopt j over 1 en 2, daarna voor i = 2 opnieuw over 1 en 2.",
            tip="Schrijf eerst alle waarden van i onder elkaar, en per i alle waarden van j.",
        ),
        fout(
            "Dit programma moet de getallen 1 tot en met 10 tonen. Welke regel is fout?",
            """
            for i in range(1, 10):
                print(i)
            """,
            1,
            """
            for i in range(1, 11):
                print(i)
            """,
            "`range(1, 10)` stopt bij 9. Voor 1 tot en met 10 heb je `range(1, 11)` nodig.",
        ),
        aanvullen(
            "Vul aan zodat het programma de even getallen van 0 tot en met 10 toont.",
            """
            for i in range(0, ___, ___):
                print(i)
            """,
            [["11", "12"], ["2"]],
            "Stap 2 vanaf 0. Het einde moet **groter** zijn dan 10, want het einde zit er zelf nooit in.",
        ),
        keuze(
            "Wat doet dit programma?",
            [
                "Het toont de tekst achterstevoren",
                "Het telt het aantal letters",
                "Het toont de tekst twee keer",
                "Het toont enkel de eerste letter",
            ],
            0,
            "Elke letter wordt **vóór** wat er al stond geplakt. Voor `abc`: `a`, `ba`, `cba`.",
            code="""
            woord = "abc"
            omgekeerd = ""
            for letter in woord:
                omgekeerd = letter + omgekeerd
            print(omgekeerd)
            """,
            lees=True,
        ),
        schrijf(
            """
            Vraag een getal n en toon de tafel van n, van 1 tot en met 10.
            Elke regel heeft de vorm `i * n = uitkomst`. Voor n = 3 is de eerste regel
            `1 * 3 = 3` en de laatste `10 * 3 = 30`.
            """,
            """
            n = int(input("Tafel van: "))
            for i in range(1, 11):
                print(i, "*", n, "=", i * n)
            """,
            "Let op `range(1, 11)` om tot en met 10 te gaan.",
            ptests=[(["3"], "\n".join(f"{i} * 3 = {i*3}" for i in range(1, 11))),
                    (["7"], "\n".join(f"{i} * 7 = {i*7}" for i in range(1, 11)))],
            boek="Opgave 7.1",
        ),
        schrijf(
            """
            Vraag een woord en toon hoeveel klinkers (a, e, i, o, u) erin zitten.
            Bij `programmeren` verschijnt `4`.
            """,
            """
            woord = input("Woord: ")
            aantal = 0
            for letter in woord:
                if letter in "aeiou":
                    aantal += 1
            print(aantal)
            """,
            "`letter in \"aeiou\"` is True als de letter één van de klinkers is. Zo hoef je geen vijf keer `or` te schrijven.",
            ptests=[(["programmeren"], "4"), (["xyz"], "0"), (["aeiou"], "5")],
            tip="Gebruik een teller die vóór de loop op 0 staat.",
        ),

        aanvullen(
            "Vul aan zodat het programma de veelvouden van 3 toont, aftellend van 21 tot en met 3.",
            """
            for i in range(21, ___, -3):
                print(i)
            """,
            [["0", "1", "2"]],
            "Met stap -3 tel je af. Het einde zit er niet in, dus het moet onder 3 liggen (maar boven -1).",
            boek="Opgave in 7.2.3",
        ),
        voorspel(
            """
            for i in range(3):
                if i == 5:
                    print("gevonden")
                    break
            else:
                print("niet gevonden")
            """,
            "i wordt nooit 5, dus er is geen `break`. Daarom wordt het else-blok uitgevoerd.",
        ),
        schrijf(
            """
            Gegeven `getallen = [3, -2, 5, 0, 7]`. Loop met een for loop over de getallen:
            - een **negatief** getal sla je over (`continue`)
            - bij een **0** stop je meteen (`break`)
            - andere getallen toon je

            Na de loop toon je `Klaar`. Hier verschijnt dus `3`, `5` en `Klaar`.
            """,
            """
            getallen = [3, -2, 5, 0, 7]
            for g in getallen:
                if g < 0:
                    continue
                if g == 0:
                    break
                print(g)
            print("Klaar")
            """,
            "`continue` gaat naar het volgende getal, `break` verlaat de loop helemaal.",
            ptests=[([], "3\n5\nKlaar")],
            start="getallen = [3, -2, 5, 0, 7]",
            boek="Opgave in 7.3.3",
        ),
        schrijf(
            """
            Toon alle paren `i j` waarbij i en j van 0 tot en met 3 gaan,
            maar **nooit gelijk** zijn. Eén paar per regel, bijvoorbeeld `0 1`.
            """,
            """
            for i in range(4):
                for j in range(4):
                    if i != j:
                        print(i, j)
            """,
            "Twee geneste loops, en een if die de gelijke paren overslaat.",
            ptests=[([], "\n".join(f"{i} {j}" for i in range(4) for j in range(4) if i != j))],
            boek="Opgave in 7.4",
        ),
        schrijf(
            """
            Vraag 5 gehele getallen. Toon daarna, elk op een eigen regel: het grootste,
            het kleinste, en hoeveel getallen deelbaar zijn door 3.
            Gebruik **geen** `max` of `min`.
            """,
            """
            for i in range(5):
                g = int(input("Getal: "))
                if i == 0:
                    grootste = g
                    kleinste = g
                    deelbaar = 0
                if g > grootste:
                    grootste = g
                if g < kleinste:
                    kleinste = g
                if g % 3 == 0:
                    deelbaar += 1
            print(grootste)
            print(kleinste)
            print(deelbaar)
            """,
            """
            Het eerste getal is meteen het grootste én kleinste tot nu toe. Je kan ook
            eerst één getal vragen vóór de loop, en dan nog 4 in de loop.
            """,
            ptests=[(["4", "9", "2", "12", "7"], "12\n2\n2"), (["-1", "-5", "-3", "-2", "-4"], "-1\n-5\n1")],
            verboden=["max(", "min("],
            boek="Opgave 7.3 (met 5 getallen)",
        ),
        schrijf(
            """
            Vraag een geheel getal groter dan 0 en toon `priemgetal` of `geen priemgetal`.
            Een priemgetal is enkel deelbaar door 1 en door zichzelf (1 is géén priemgetal).
            """,
            """
            n = int(input("Getal: "))
            priem = n > 1
            for d in range(2, n):
                if n % d == 0:
                    priem = False
                    break
            if priem:
                print("priemgetal")
            else:
                print("geen priemgetal")
            """,
            """
            Test alle mogelijke delers van 2 tot n-1. Vind je er één, dan is het geen
            priemgetal. Een variabele `priem` (True/False) houdt bij wat je weet.
            """,
            ptests=[(["7"], "priemgetal"), (["9"], "geen priemgetal"), (["2"], "priemgetal"),
                    (["1"], "geen priemgetal"), (["97"], "priemgetal")],
            boek="Opgave 7.10",
            uitdaging=True,
        ),
    ],
}
