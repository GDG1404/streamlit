from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "nr": 6,
    "titel": "Lijsten",
    "kort": "index, append, slices",
    "spiek": ["container-types", "indexing", "list-ops", "generic-ops"],
    "doel": "Je kan met indexen werken (ook negatieve) en weet wat append, len, sum en slices doen.",
    "uitleg": [
        les(
            "Een lijst bevat meerdere waarden",
            """
            Een lijst schrijf je tussen vierkante haken, met komma's tussen de
            elementen: `lst = [10, 20, 30, 40, 50]`. Een lijst kan getallen,
            tekst of zelfs andere lijsten bevatten. `[]` is een lege lijst.
            """,
            """
            lst = [10, 20, 30, 40, 50]
            print(lst)
            print(len(lst))
            leeg = []
            print(len(leeg))
            """,
        ),
        les(
            "De index begint bij 0",
            """
            Elk element heeft een **positie** (index). De eerste heeft index **0**!
            Kijk naar de tekening op je spiekbrief (*Sequence Containers Indexing*):

            - `lst[0]` is het eerste element (10)
            - `lst[4]` is het laatste (50): de laatste index is altijd `len(lst) - 1`
            - `lst[-1]` is ook het laatste, `lst[-2]` het voorlaatste

            Een index die niet bestaat (zoals `lst[5]`) geeft een **IndexError**.
            """,
            """
            lst = [10, 20, 30, 40, 50]
            print(lst[0], lst[1])
            print(lst[-1], lst[-2])
            print(lst[len(lst) - 1])
            """,
        ),
        les(
            "Een lijst aanpassen",
            """
            Een lijst kan je veranderen (spiekbrief: *Operations on Lists*):
            - `lst[1] = 25` vervangt het element op index 1
            - `lst.append(60)` voegt 60 toe **achteraan**
            - `lst.insert(0, 5)` voegt 5 toe op index 0
            - `lst.pop()` haalt het laatste element weg (en geeft het terug)
            - `lst.remove(30)` verwijdert de eerste 30
            """,
            """
            lst = [10, 20, 30]
            lst[1] = 25
            lst.append(40)
            print(lst)
            lst.remove(10)
            laatste = lst.pop()
            print(lst, laatste)
            """,
        ),
        les(
            "Handige functies",
            """
            Uit *Generic Operations on Containers*:
            - `len(lst)` aantal elementen
            - `sum(lst)`, `min(lst)`, `max(lst)`
            - `sorted(lst)` geeft een **nieuwe**, gesorteerde lijst
            - `x in lst` is True als x in de lijst zit

            Let op het verschil: `sorted(lst)` laat lst ongemoeid,
            `lst.sort()` sorteert de lijst zelf.
            """,
            """
            lst = [4, 8, 15, 16, 23, 42]
            print(len(lst), sum(lst), min(lst), max(lst))
            print(15 in lst, 7 in lst)
            print(sorted([3, 1, 2]))
            """,
        ),
        les(
            "Slices: een stuk van een lijst",
            """
            `lst[start:einde]` geeft een **nieuwe lijst** met de elementen van
            index start tot (niet met) einde. Net als bij `range`: het einde zit er niet in.
            - `lst[:3]` de eerste drie
            - `lst[3:]` alles vanaf index 3
            - `lst[::-1]` de lijst achterstevoren

            Slices werken ook op tekst: `"python"[0:2]` geeft `"py"`.
            """,
            """
            lst = [10, 20, 30, 40, 50]
            print(lst[1:3])
            print(lst[:2], lst[3:])
            print(lst[::-1])
            print("python"[0:2])
            """,
        ),
        les(
            "Een lijst opbouwen in een lus",
            """
            Heel vaak begin je met een lege lijst en voeg je in een lus telkens
            iets toe met `append`.
            """,
            """
            kwadraten = []
            for i in range(1, 6):
                kwadraten.append(i * i)
            print(kwadraten)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            lst = [10, 20, 30, 40, 50]
            print(lst[0])
            print(lst[2])
            print(lst[-1])
            """,
            "Index 0 is het eerste element, index 2 het derde. `-1` is het laatste.",
        ),
        voorspel(
            """
            lst = [4, 8, 15]
            print(len(lst))
            print(sum(lst))
            print(max(lst))
            """,
            "3 elementen, som 4 + 8 + 15 = 27, grootste 15.",
        ),
        keuze(
            'Gegeven `lst = ["a", "b", "c", "d"]`. Wat geeft `lst[4]`?',
            ['"d"', '"a"', "Een fout (IndexError)", 'Een lege tekst ""'],
            2,
            "De indexen gaan van 0 tot 3. Index 4 bestaat niet: **IndexError**. Het laatste element is `lst[3]` of `lst[-1]`.",
        ),
        voorspel(
            """
            lst = [1, 2, 3]
            lst.append(4)
            lst[0] = 10
            print(lst)
            """,
            "`append` zet 4 achteraan. Daarna wordt het element op index 0 vervangen door 10.",
        ),
        voorspel(
            """
            lst = [10, 20, 30, 40, 50]
            print(lst[1:3])
            print(lst[:2])
            print(lst[3:])
            """,
            "Index 1 en 2 (3 zit er niet in). De eerste twee. Vanaf index 3 tot het einde.",
        ),
        voorspel(
            """
            getallen = [5, 3, 8]
            for g in getallen:
                print(g * 2)
            """,
            "De lus loopt over elk element en toont het dubbel.",
        ),
        voorspel(
            """
            lst = [3, 1, 2]
            nieuw = sorted(lst)
            print(lst)
            print(nieuw)
            """,
            "`sorted` maakt een nieuwe lijst. De oude lijst blijft zoals ze was.",
        ),
        voorspel(
            """
            lst = []
            for i in range(4):
                lst.append(i * i)
            print(lst)
            """,
            "i is 0, 1, 2, 3, en telkens komt i² achteraan bij.",
        ),
        voorspel(
            """
            kleuren = ["rood", "groen", "blauw"]
            print("groen" in kleuren)
            print("geel" in kleuren)
            """,
            "`in` controleert of iets in de lijst zit.",
        ),
        fout(
            "Dit programma moet het **laatste** element tonen. Welke regel is fout?",
            """
            lst = [7, 3, 9, 4]
            print(lst[len(lst)])
            """,
            2,
            """
            lst = [7, 3, 9, 4]
            print(lst[len(lst) - 1])
            """,
            "`len(lst)` is 4, maar de laatste index is 3. Gebruik `len(lst) - 1` of gewoon `-1`.",
        ),
        aanvullen(
            "Vul aan zodat 6 achteraan de lijst wordt toegevoegd.",
            """
            lst = [2, 4]
            lst.___(6)
            print(lst)
            """,
            [["append"]],
            "`append` voegt één element achteraan toe.",
        ),
        keuze(
            "Wat doet dit programma?",
            [
                "Het zoekt het grootste getal",
                "Het zoekt het kleinste getal",
                "Het telt de getallen op",
                "Het sorteert de lijst",
            ],
            1,
            "r begint bij het eerste getal. Telkens als er een **kleiner** getal komt, wordt dat de nieuwe r. Op het einde is r = 1.",
            code="""
            lst = [4, 7, 1, 9]
            r = lst[0]
            for x in lst:
                if x < r:
                    r = x
            print(r)
            """,
            lees=True,
        ),
        voorspel(
            """
            lst = [5, 10, 15, 20]
            lst.pop()
            lst.insert(0, 0)
            print(lst, len(lst))
            """,
            "`pop()` haalt 20 weg. `insert(0, 0)` zet 0 vooraan. Er zijn nog steeds 4 elementen.",
        ),
        schrijf(
            """
            Maak een lege lijst. Vraag met een **for-lus** drie keer een geheel getal
            en voeg het telkens toe aan de lijst. Toon daarna de lijst.
            Typt de gebruiker 4, 7 en 1, dan verschijnt `[4, 7, 1]`.
            """,
            """
            getallen = []
            for i in range(3):
                g = int(input("Getal: "))
                getallen.append(g)
            print(getallen)
            """,
            "Vergeet `int(...)` niet, anders komen er teksten in de lijst: `['4', '7', '1']`.",
            ptests=[(["4", "7", "1"], "[4, 7, 1]"), (["0", "-2", "5"], "[0, -2, 5]")],
        ),
        schrijf(
            """
            Gegeven `lst = [3, 8, 2, 9, 4]`.
            Toon elk getal dat **groter is dan 5**, elk op een eigen regel.
            """,
            """
            lst = [3, 8, 2, 9, 4]
            for x in lst:
                if x > 5:
                    print(x)
            """,
            "Een for-lus over de lijst met een if erin: dit patroon heet **filteren**.",
            ptests=[([], "8\n9")],
            start="lst = [3, 8, 2, 9, 4]",
        ),
    ],
}
