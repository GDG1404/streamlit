from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "lists",
    "titel": "Lists",
    "kort": "index, append, alias, comprehensions",
    "hoofdstuk": "12",
    "spiek": ["container-types", "indexing", "list-ops", "generic-ops"],
    "doel": "Je kan met indexen werken (ook negatieve), kent de list methodes, weet wat een alias is en kan een list comprehension lezen.",
    "uitleg": [
        les(
            "Een list bevat meerdere waarden",
            """
            Een list schrijf je tussen vierkante haken, met komma's tussen de
            elementen: `lst = [10, 20, 30, 40, 50]`. Een list kan getallen,
            tekst of zelfs andere lists bevatten. `[]` is een lege list.
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
            "Een list aanpassen",
            """
            Een list kan je veranderen (spiekbrief: *Operations on Lists*):
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
            - `sorted(lst)` geeft een **nieuwe**, gesorteerde list
            - `x in lst` is True als x in de list zit

            Let op het verschil: `sorted(lst)` laat lst ongemoeid,
            `lst.sort()` sorteert de list zelf.
            """,
            """
            lst = [4, 8, 15, 16, 23, 42]
            print(len(lst), sum(lst), min(lst), max(lst))
            print(15 in lst, 7 in lst)
            print(sorted([3, 1, 2]))
            """,
        ),
        les(
            "Slices: een stuk van een list",
            """
            `lst[start:einde]` geeft een **nieuwe list** met de elementen van
            index start tot (niet met) einde. Net als bij `range`: het einde zit er niet in.
            - `lst[:3]` de eerste drie
            - `lst[3:]` alles vanaf index 3
            - `lst[::-1]` de list achterstevoren

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
            "Een list opbouwen in een loop",
            """
            Heel vaak begin je met een lege list en voeg je in een loop telkens
            iets toe met `append`.
            """,
            """
            kwadraten = []
            for i in range(1, 6):
                kwadraten.append(i * i)
            print(kwadraten)
            """,
        ),

        les(
            "Meer list methodes",
            """
            Naast `append`, `insert`, `remove`, `pop` en `sort` (cursus 12.4):
            - `lst.extend(andere)`: alle elementen van een andere list achteraan toevoegen
            - `del lst[i]`: het element op index i verwijderen
            - `lst.index(x)`: op welke index staat x (de eerste keer)?
            - `lst.count(x)`: hoeveel keer komt x voor?
            - `lst.reverse()`: de list zelf omdraaien
            """,
            """
            lst = [3, 1, 3, 2]
            lst.extend([5, 3])
            print(lst.count(3), lst.index(2))
            del lst[0]
            lst.reverse()
            print(lst)
            """,
        ),
        les(
            "Alias: twee namen voor één list",
            """
            `b = a` maakt **geen kopie** van een list: a en b zijn twee namen voor
            **dezelfde** list (cursus 12.5). Verander je b, dan verandert a mee.
            Met `a is b` test je of het dezelfde list is.

            Een echte (ondiepe) kopie maak je met `a[:]`, `list(a)` of `a.copy()`.
            """,
            """
            a = [1, 2, 3]
            b = a
            c = a[:]
            b.append(4)
            print(a)
            print(c)
            print(a is b, a is c)
            """,
        ),
        les(
            "Lists als argument",
            """
            Geef je een list mee aan een functie, dan krijgt de functie **dezelfde**
            list (een alias). Past de functie de list aan, dan zie je dat ook
            buiten de functie (cursus 12.5.3).
            """,
            """
            def voeg_nul_toe(lst):
                lst.append(0)

            getallen = [5, 7]
            voeg_nul_toe(getallen)
            print(getallen)
            """,
        ),
        les(
            "Geneste lists",
            """
            Een list kan lists bevatten (cursus 12.6). Zo maak je een tabel of
            matrix: `m[rij][kolom]`. Eerst kies je de rij, dan het element in die rij.
            """,
            """
            m = [[1, 2, 3],
                 [4, 5, 6]]
            print(m[1])
            print(m[1][0])
            for rij in m:
                print(sum(rij))
            """,
        ),
        les(
            "List comprehensions",
            """
            Een **list comprehension** maakt in één regel een nieuwe list
            (cursus 12.8):

            `[uitdrukking for x in reeks if conditie]`

            Lees het als: "maak een list van *uitdrukking*, voor elke x in *reeks*,
            als *conditie* waar is". Het `if`-deel mag je weglaten.
            """,
            """
            kwadraten = [x * x for x in range(1, 6)]
            print(kwadraten)
            groot = [x for x in [5, 12, 7, 20] if x > 6]
            print(groot)
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
            "De loop loopt over elk element en toont het dubbel.",
        ),
        voorspel(
            """
            lst = [3, 1, 2]
            nieuw = sorted(lst)
            print(lst)
            print(nieuw)
            """,
            "`sorted` maakt een nieuwe list. De oude list blijft zoals ze was.",
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
            "`in` controleert of iets in de list zit.",
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
            "Vul aan zodat 6 achteraan de list wordt toegevoegd.",
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
                "Het sorteert de list",
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
            Maak een lege list. Vraag met een **for loop** drie keer een geheel getal
            en voeg het telkens toe aan de list. Toon daarna de list.
            Typt de gebruiker 4, 7 en 1, dan verschijnt `[4, 7, 1]`.
            """,
            """
            getallen = []
            for i in range(3):
                g = int(input("Getal: "))
                getallen.append(g)
            print(getallen)
            """,
            "Vergeet `int(...)` niet, anders komen er teksten in de list: `['4', '7', '1']`.",
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
            "Een for loop over de list met een if erin: dit patroon heet **filteren**.",
            ptests=[([], "8\n9")],
            start="lst = [3, 8, 2, 9, 4]",
        ),

        voorspel(
            """
            a = [1, 2, 3]
            b = a
            b.append(4)
            print(a)
            """,
            "`b = a` maakt geen kopie: a en b zijn **dezelfde** list. Dus a verandert mee.",
        ),
        voorspel(
            """
            a = [1, 2, 3]
            b = a[:]
            b.append(4)
            print(a, b)
            """,
            "`a[:]` maakt een kopie. Nu verandert alleen b.",
        ),
        voorspel(
            """
            m = [[1, 2, 3], [4, 5, 6]]
            print(m[1][0])
            print(len(m), len(m[0]))
            """,
            "`m[1]` is de tweede rij `[4, 5, 6]`, en daarvan index 0 is 4. Er zijn 2 rijen van 3 elementen.",
        ),
        voorspel(
            """
            print([x * 2 for x in range(4)])
            print([x for x in [5, 12, 7, 20] if x > 6])
            """,
            "Eerst elk getal van 0 tot 3 maal 2. Dan enkel de getallen groter dan 6.",
        ),
        voorspel(
            """
            lst = [3, 1, 3, 2]
            print(lst.count(3), lst.index(2))
            lst.reverse()
            print(lst)
            """,
            "3 komt 2 keer voor, 2 staat op index 3. `reverse()` draait de list zelf om.",
        ),
        keuze(
            "Wat toont dit programma?",
            ["[1]", "[1, 0]", "[0, 1]", "None"],
            1,
            "De functie krijgt **dezelfde** list (een alias) en voegt er 0 aan toe. Dat zie je ook buiten de functie.",
            code="""
            def voeg_toe(lst):
                lst.append(0)

            x = [1]
            voeg_toe(x)
            print(x)
            """,
            controleer_uitvoer=True,
        ),
        schrijf(
            """
            Schrijf een functie `omgekeerd(lst)` die een **nieuwe** list teruggeeft met
            dezelfde elementen in omgekeerde volgorde. Gebruik **geen** `reverse` en geen `[::-1]`.
            De originele list mag niet veranderen.
            """,
            """
            def omgekeerd(lst):
                nieuw = []
                for x in lst:
                    nieuw.insert(0, x)
                return nieuw
            """,
            """
            Elk element vooraan invoegen draait de volgorde om. Een andere manier:
            een while loop die van de laatste index naar 0 loopt en `append` gebruikt.
            """,
            tests=[("omgekeerd([1, 2, 3])", [3, 2, 1]), ("omgekeerd([])", []), ("omgekeerd(['a'])", ["a"])],
            start="def omgekeerd(lst):",
            verboden=["reverse", "[::-1]"],
        ),
        schrijf(
            """
            Schrijf een functie `gemiddelde(lst)` die het gemiddelde van een (niet-lege) list
            getallen teruggeeft. Gebruik een for loop, **geen** `sum`.
            """,
            """
            def gemiddelde(lst):
                totaal = 0
                for x in lst:
                    totaal += x
                return totaal / len(lst)
            """,
            "Optellen in een loop, en na de loop delen door het aantal elementen.",
            tests=[("gemiddelde([2, 4, 6])", 4.0), ("gemiddelde([5])", 5.0), ("gemiddelde([1, 2])", 1.5)],
            start="def gemiddelde(lst):",
            verboden=["sum("],
        ),
        schrijf(
            """
            Schrijf een functie `aantal_even(lst)` die **teruggeeft** hoeveel even getallen
            er in de list zitten. `aantal_even([1, 2, 3, 4])` geeft `2`.
            """,
            """
            def aantal_even(lst):
                aantal = 0
                for x in lst:
                    if x % 2 == 0:
                        aantal += 1
                return aantal
            """,
            "Teller op 0 vóór de loop, +1 als het getal even is, return **na** de loop (niet erin!).",
            tests=[("aantal_even([1, 2, 3, 4])", 2), ("aantal_even([])", 0), ("aantal_even([7, 9])", 0),
                   ("aantal_even([2, 2, 8])", 3)],
            start="def aantal_even(lst):",
        ),
        schrijf(
            """
            Schrijf een functie `grootste(lst)` die het grootste getal uit een (niet-lege)
            list teruggeeft, **zonder** `max` te gebruiken.
            """,
            """
            def grootste(lst):
                g = lst[0]
                for x in lst:
                    if x > g:
                        g = x
                return g
            """,
            """
            Begin met het **eerste element** als voorlopig grootste, niet met 0:
            bij een list met enkel negatieve getallen zou 0 anders fout zijn.
            """,
            tests=[("grootste([3, 9, 2])", 9), ("grootste([-5, -2, -9])", -2), ("grootste([7])", 7)],
            start="def grootste(lst):",
            verboden=["max("],
            uitdaging=True,
        ),
    ],
}
