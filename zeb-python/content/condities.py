from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "condities",
    "titel": "Condities",
    "kort": "if, elif, else, and, or, in",
    "hoofdstuk": "6",
    "spiek": ["boolean-logic", "conditional", "blocks"],
    "doel": "Je kan voorspellen welk blok van een if/elif/else wordt uitgevoerd en zelf condities schrijven.",
    "uitleg": [
        les(
            "Vergelijken geeft True of False",
            """
            Een vergelijking is een vraag met als antwoord `True` (waar) of `False` (onwaar):
            - `<` `>` `<=` `>=` kleiner, groter, kleiner of gelijk, groter of gelijk
            - `==` is gelijk aan
            - `!=` is niet gelijk aan

            **Valkuil nummer één:** `=` steekt iets in een variabele, `==` vergelijkt.
            """,
            """
            x = 7
            print(x > 5)
            print(x == 5)
            print(x != 5)
            """,
        ),
        les(
            "if: alleen als het waar is",
            """
            `if conditie:` voert het **ingesprongen blok** eronder uit, maar
            alleen als de conditie waar is. Daarna gaat het programma gewoon verder.

            Twee dingen die je op papier niet mag vergeten:
            - de **dubbele punt** `:` op het einde van de if-regel
            - het **inspringen** (4 spaties) van alles wat bij de if hoort
            """,
            """
            punten = 14
            if punten >= 10:
                print("Geslaagd!")
                print("Proficiat")
            print("Einde")
            """,
        ),
        les(
            "if ... else",
            """
            Met `else:` geef je aan wat er moet gebeuren als de conditie **niet**
            waar is. Precies één van de twee blokken wordt uitgevoerd.
            """,
            """
            n = 7
            if n % 2 == 0:
                print("even")
            else:
                print("oneven")
            """,
        ),
        les(
            "if ... elif ... else",
            """
            Met `elif` (kort voor *else if*) test je meerdere condities na elkaar.
            Python neemt **het eerste blok waarvan de conditie waar is** en
            slaat de rest over. Zo staat het ook op je spiekbrief:
            *Only the block of first true condition is executed.*
            """,
            """
            age = 70
            if age <= 18:
                state = "Kid"
            elif age > 65:
                state = "Retired"
            else:
                state = "Active"
            print(state)
            """,
        ),
        les(
            "and, or, not",
            """
            Condities combineren (spiekbrief: *Boolean Logic*):
            - `a and b` is waar als **allebei** waar zijn
            - `a or b` is waar als **minstens één** waar is
            - `not a` draait om: waar wordt onwaar en omgekeerd
            """,
            """
            temp = 22
            zon = True
            print(temp > 20 and zon)
            print(temp > 30 or zon)
            print(not zon)
            """,
        ),
        les(
            "Blokken en inspringen",
            """
            In Python bepaalt het **inspringen** wat bij elkaar hoort
            (spiekbrief: *Statements Blocks*). Alles wat even ver ingesprongen
            staat onder een regel met `:`, hoort bij dat blok.

            Op papier: spring duidelijk in, bijvoorbeeld 2 hokjes. Je mag een
            dun verticaal lijntje trekken om te tonen waar het blok stopt.
            """,
            """
            x = 3
            if x > 5:
                print("groot")
                print("echt groot")
            print("klaar")
            """,
            papier="x is niet groter dan 5, dus beide ingesprongen regels worden overgeslagen.",
        ),

        les(
            "De in-operator",
            """
            Met `in` test je of een string **in** een andere string voorkomt
            (cursus 6.1.3). Het resultaat is `True` of `False`. Met `not in`
            test je het omgekeerde.
            """,
            """
            naam = "Zeb Degrave"
            print("e" in naam)
            print("Deg" in naam)
            print("x" not in naam)
            """,
        ),
        les(
            "Strings vergelijken",
            """
            Je kan ook strings vergelijken met `<` en `>`. Python vergelijkt dan
            **teken per teken**, zoals in een woordenboek. Daarom is `"3" < "13"`
            `False`: het eerste teken `"3"` komt na `"1"`.

            Getallen vergelijk je dus als getallen, niet als tekst!
            """,
            """
            print(3 < 13)
            print("3" < "13")
            print("appel" < "banaan")
            """,
        ),
        les(
            "Geneste condities",
            """
            Een if mag in een ander if-blok staan (cursus 6.2.6). Het binnenste
            blok springt dan **twee keer** in. Vaak kan je het ook met `and` of
            met `elif` schrijven; kies wat het duidelijkst is.

            In je cursus zie je zulke beslissingen ook als **stroomdiagram**
            (6.2.4): een ruit is een conditie met een ja- en een nee-pijl,
            een rechthoek is een opdracht.
            """,
            """
            x = 41
            if x % 7 == 0:
                print("deelbaar door 7")
            else:
                if x % 11 == 0:
                    print("deelbaar door 11")
                else:
                    print("deelbaar door 7 noch 11")
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            print(5 > 3)
            print(5 == 3)
            print(5 != 3)
            """,
            "5 is groter dan 3: True. 5 is niet gelijk aan 3: False. Niet gelijk? Ja: True.",
        ),
        voorspel(
            """
            x = 7
            if x > 5:
                print("groot")
            print("einde")
            """,
            "7 > 5 is waar, dus het blok wordt uitgevoerd. `einde` staat niet ingesprongen en komt altijd.",
        ),
        voorspel(
            """
            x = 3
            if x > 5:
                print("groot")
                print("echt groot")
            print("einde")
            """,
            "3 > 5 is onwaar: beide ingesprongen regels worden overgeslagen.",
        ),
        voorspel(
            """
            x = 3
            if x > 5:
                print("groot")
            else:
                print("klein")
            """,
            "De conditie is onwaar, dus het else-blok wordt uitgevoerd.",
        ),
        voorspel(
            """
            punten = 14
            if punten >= 16:
                print("onderscheiding")
            elif punten >= 10:
                print("geslaagd")
            else:
                print("niet geslaagd")
            """,
            "14 >= 16 is onwaar. 14 >= 10 is waar: `geslaagd`. Het else-blok wordt dan overgeslagen.",
        ),
        keuze(
            "Wat toont dit programma?",
            ["A", "B", "A en daarna B", "C"],
            0,
            """
            20 > 5 is waar, dus `A`. Ook 20 > 10 is waar, maar bij `elif` kijkt Python
            **niet meer** zodra er al een blok uitgevoerd is.
            """,
            code="""
            x = 20
            if x > 5:
                print("A")
            elif x > 10:
                print("B")
            else:
                print("C")
            """,
            controleer_uitvoer=True,
        ),
        voorspel(
            """
            a = 4
            b = 9
            print(a > 3 and b > 10)
            print(a > 3 or b > 10)
            print(not a > 3)
            """,
            "`a > 3` is waar, `b > 10` is onwaar. and: niet allebei waar, dus False. or: één is waar, dus True. not True is False.",
        ),
        fout(
            "Dit programma moet `even` tonen als n even is. Op welke regel zit de fout?",
            """
            n = 6
            if n % 2 = 0:
                print("even")
            """,
            2,
            """
            n = 6
            if n % 2 == 0:
                print("even")
            """,
            "Om te vergelijken heb je `==` nodig. Eén `=` geeft een **SyntaxError**.",
        ),
        fout(
            "Op welke regel zit de fout?",
            """
            x = 5
            if x > 0
                print("positief")
            """,
            2,
            """
            x = 5
            if x > 0:
                print("positief")
            """,
            "De dubbele punt na de conditie ontbreekt. Op papier vergeet je die snel!",
        ),
        aanvullen(
            "Vul aan zodat het programma `warm` toont als het 20 graden of meer is, en anders `fris`.",
            """
            temp = 25
            if temp ___ 20:
                print("warm")
            ___:
                print("fris")
            """,
            [[">="], ["else"]],
            "`>=` betekent groter dan of gelijk aan. Het andere geval komt in `else:`.",
        ),
        keuze(
            "Wat doet dit programma?",
            [
                "Het toont enkel negatieve getallen",
                "Het toont het getal maal -1",
                "Het toont het getal zonder minteken (de absolute waarde)",
                "Het geeft een fout bij negatieve getallen",
            ],
            2,
            """
            Is n negatief, dan wordt het `-n`, dus positief. Een positief getal blijft
            gewoon staan. Dat is de absolute waarde, wat `abs(n)` ook doet.
            """,
            code="""
            n = int(input())
            if n < 0:
                n = -n
            print(n)
            """,
            lees=True,
            draai=False,
        ),
        voorspel(
            """
            x = 15
            if x % 3 == 0 and x % 5 == 0:
                print("FizzBuzz")
            elif x % 3 == 0:
                print("Fizz")
            elif x % 5 == 0:
                print("Buzz")
            else:
                print(x)
            """,
            "15 is deelbaar door 3 én door 5. Het eerste blok is waar, dus `FizzBuzz`.",
        ),
        schrijf(
            """
            Vraag een geheel getal. Toon `positief` als het groter is dan 0,
            `negatief` als het kleiner is dan 0, en anders `nul`.
            """,
            """
            n = int(input("Getal: "))
            if n > 0:
                print("positief")
            elif n < 0:
                print("negatief")
            else:
                print("nul")
            """,
            "Drie gevallen: daar is `if / elif / else` voor gemaakt.",
            ptests=[(["5"], "positief"), (["-3"], "negatief"), (["0"], "nul")],
        ),
        schrijf(
            """
            Vraag een jaartal en toon `schrikkeljaar` of `geen schrikkeljaar`.

            Een jaar is een schrikkeljaar als het deelbaar is door 4,
            **behalve** als het deelbaar is door 100. Maar is het deelbaar
            door 400, dan is het tóch een schrikkeljaar.
            (2024: ja, 1900: nee, 2000: ja)
            """,
            """
            jaar = int(input("Jaar: "))
            if jaar % 400 == 0:
                print("schrikkeljaar")
            elif jaar % 100 == 0:
                print("geen schrikkeljaar")
            elif jaar % 4 == 0:
                print("schrikkeljaar")
            else:
                print("geen schrikkeljaar")
            """,
            """
            Begin met het **strengste** geval (400), dan 100, dan 4. Het kan ook in één conditie:
            `if jaar % 4 == 0 and (jaar % 100 != 0 or jaar % 400 == 0):`
            """,
            ptests=[(["2024"], "schrikkeljaar"), (["2023"], "geen schrikkeljaar"),
                    (["1900"], "geen schrikkeljaar"), (["2000"], "schrikkeljaar")],
            tip="Test je oplossing op papier met 2024, 2023, 1900 en 2000.",
            uitdaging=True,
        ),

        voorspel(
            """
            print(3 < 13)
            print("3" < "13")
            print("a" in "banaan", "ban" in "banaan", "x" in "banaan")
            """,
            """
            Getallen: 3 is kleiner dan 13. Strings: Python vergelijkt teken per teken,
            en `"3"` komt na `"1"`, dus False. `in` zoekt een stukje tekst.
            """,
            boek="Opgave in 6.1.2",
        ),
        voorspel(
            """
            x = 12
            if x > 10:
                if x % 2 == 0:
                    print("groot en even")
                else:
                    print("groot en oneven")
            else:
                print("klein")
            """,
            "x > 10 is waar, dus naar het binnenste if. 12 is even: `groot en even`.",
        ),
        fout(
            "Dit programma moet bij een score van 98 de letter `A` geven. Het toont `D`. Welke regel is de oorzaak?",
            """
            score = 98
            if score >= 60:
                oordeel = "D"
            elif score >= 70:
                oordeel = "C"
            elif score >= 80:
                oordeel = "B"
            elif score >= 90:
                oordeel = "A"
            else:
                oordeel = "F"
            print(oordeel)
            """,
            2,
            """
            score = 98
            if score >= 90:
                oordeel = "A"
            elif score >= 80:
                oordeel = "B"
            elif score >= 70:
                oordeel = "C"
            elif score >= 60:
                oordeel = "D"
            else:
                oordeel = "F"
            print(oordeel)
            """,
            """
            98 is groter dan 60, dus de **eerste** conditie is al waar en de rest wordt
            overgeslagen. Bij een elif-ketting test je de **strengste** conditie eerst.
            """,
            boek="Opgave 6.2",
        ),
        schrijf(
            """
            Een cijfer ligt tussen 0 en 10 (afgerond op halve punten). Vraag een cijfer
            (een float) en toon de letter:
            - 8.5 tot en met 10: `A`
            - 7.5 en 8: `B`
            - 6.5 en 7: `C`
            - 5.5 en 6: `D`
            - 5 en lager: `F`

            Ligt het cijfer niet tussen 0 en 10, toon dan `Ongeldig cijfer`.
            """,
            """
            cijfer = float(input("Cijfer: "))
            if cijfer < 0 or cijfer > 10:
                print("Ongeldig cijfer")
            elif cijfer >= 8.5:
                print("A")
            elif cijfer >= 7.5:
                print("B")
            elif cijfer >= 6.5:
                print("C")
            elif cijfer >= 5.5:
                print("D")
            else:
                print("F")
            """,
            "Eerst de ongeldige cijfers wegfilteren, dan van hoog naar laag.",
            ptests=[(["9"], "A"), (["8"], "B"), (["6.5"], "C"), (["5.5"], "D"), (["3"], "F"),
                    (["11"], "Ongeldig cijfer"), (["-1"], "Ongeldig cijfer")],
            boek="Opgave 6.1",
        ),
    ],
}
