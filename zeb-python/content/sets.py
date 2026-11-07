from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "sets",
    "titel": "Sets",
    "kort": "verzamelingen zonder dubbels",
    "hoofdstuk": "14",
    "spiek": ["set-ops", "container-types"],
    "doel": "Je weet wat een set is en kan vereniging, doorsnede en verschil gebruiken.",
    "uitleg": [
        les(
            "Set basis",
            """
            Een **set** is een verzameling, zoals in de wiskunde (cursus 14.1):
            - elk element komt er **maar één keer** in voor
            - er is **geen vaste volgorde**, dus ook geen index

            Je schrijft een set met accolades: `{1, 2, 3}`. Een **lege** set maak je
            met `set()`, want `{}` is een lege dictionary! Met `set(...)` maak je een
            set van een string of list: de dubbels verdwijnen.
            """,
            """
            s = {3, 1, 3, 2, 1}
            print(len(s))
            letters = set("banaan")
            print(sorted(letters))
            print(2 in s)
            """,
            papier="Omdat een set geen volgorde heeft, gebruiken we `sorted()` om hem netjes te tonen.",
        ),
        les(
            "Set methodes",
            """
            Een set aanpassen (cursus 14.2):
            - `s.add(x)` voegt één element toe, `s.update(lst)` meerdere
            - `s.remove(x)` verwijdert x, maar geeft een **KeyError** als x er niet in zit
            - `s.discard(x)` verwijdert x als het erin zit, **zonder** fout
            - `s.clear()` maakt de set leeg, `s.copy()` maakt een kopie
            """,
            """
            s = {1, 2}
            s.add(2)
            s.add(5)
            s.update([7, 8])
            s.discard(100)
            s.remove(1)
            print(sorted(s))
            """,
        ),
        les(
            "Verzamelingen combineren",
            """
            Zoals in de wiskunde (cursus 14.2.5 tot 14.2.7):
            - **vereniging**: `a.union(b)` of `a | b`: alles wat in a **of** b zit
            - **doorsnede**: `a.intersection(b)` of `a & b`: wat in a **en** b zit
            - **verschil**: `a.difference(b)` of `a - b`: wat in a zit maar niet in b
            """,
            """
            a = {1, 2, 3}
            b = {2, 3, 4}
            print(sorted(a | b))
            print(sorted(a & b))
            print(sorted(a - b), sorted(b - a))
            """,
        ),
        les(
            "Deelverzamelingen",
            """
            (cursus 14.2.8)
            - `a.issubset(b)`: zit alles van a ook in b?
            - `a.issuperset(b)`: zit alles van b ook in a?
            - `a.isdisjoint(b)`: hebben a en b **niets** gemeen?

            Een **frozenset** (cursus 14.3) is een set die je niet kan veranderen,
            zoals een tuple een list is die je niet kan veranderen.
            """,
            """
            print({1, 2}.issubset({1, 2, 3}))
            print({1, 2, 3}.issuperset({1, 4}))
            print({1, 2}.isdisjoint({3, 4}))
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            print(len({1, 2, 2, 3, 3, 3}))
            print(sorted(set("banaan")))
            """,
            "Dubbels tellen niet mee: {1, 2, 3}. In banaan zitten de letters a, b en n.",
        ),
        voorspel(
            """
            a = {1, 2, 3}
            b = {2, 3, 4}
            print(sorted(a | b))
            print(sorted(a & b))
            print(sorted(a - b))
            """,
            "Vereniging: alles. Doorsnede: wat in beide zit. Verschil: wat alleen in a zit.",
        ),
        voorspel(
            """
            s = {1, 2}
            s.add(2)
            s.add(5)
            print(len(s))
            """,
            "2 zat er al in, dus enkel 5 komt erbij: 3 elementen.",
        ),
        keuze(
            "Hoe maak je een **lege set**?",
            ["{}", "set()", "[]", "()"],
            1,
            "`{}` is een lege **dictionary**. Voor een lege set gebruik je `set()`.",
        ),
        keuze(
            "Wat gebeurt er?",
            ["Er gebeurt niets", "Een fout: KeyError", "Het toont {1, 2}", "7 wordt toegevoegd"],
            1,
            "`remove` geeft een KeyError als het element er niet in zit. `discard(7)` zou geen fout geven.",
            code="""
            s = {1, 2}
            s.remove(7)
            print(s)
            """,
        ),
        voorspel(
            """
            print({1, 2}.issubset({1, 2, 3}))
            print({1, 2}.isdisjoint({2, 5}))
            """,
            "{1, 2} zit helemaal in {1, 2, 3}. {1, 2} en {2, 5} hebben 2 gemeen, dus niet disjunct.",
        ),
        schrijf(
            """
            Schrijf een functie `gemeenschappelijk(w1, w2)` die een **set** teruggeeft met alle
            letters die in beide woorden voorkomen. `gemeenschappelijk("een", "peer")` geeft `{"e"}`.
            """,
            """
            def gemeenschappelijk(w1, w2):
                return set(w1) & set(w2)
            """,
            "Zet beide woorden om naar een set en neem de doorsnede. Dubbels verdwijnen vanzelf.",
            tests=[("gemeenschappelijk('een', 'peer')", {"e"}), ("gemeenschappelijk('abc', 'xyz')", set()),
                   ("gemeenschappelijk('banaan', 'ananas')", {"a", "n"})],
            start="def gemeenschappelijk(w1, w2):",
            boek="Opgave in 14.2.9",
        ),
        schrijf(
            """
            Schrijf een functie `aantal_verschillend(lst)` die teruggeeft hoeveel **verschillende**
            waarden er in een list zitten. `aantal_verschillend([1, 2, 2, 3, 1])` geeft 3.
            """,
            """
            def aantal_verschillend(lst):
                return len(set(lst))
            """,
            "Een set bevat elk element maar één keer.",
            tests=[("aantal_verschillend([1, 2, 2, 3, 1])", 3), ("aantal_verschillend([])", 0),
                   ("aantal_verschillend(['a', 'a'])", 1)],
            start="def aantal_verschillend(lst):",
        ),
        schrijf(
            """
            Maak drie sets met de getallen van 1 tot en met 1000 die deelbaar zijn door
            respectievelijk 3, 7 en 11. Toon daarna, gesorteerd, de getallen die in **alle drie**
            de sets zitten (als list, met `sorted`).
            """,
            """
            drie = set()
            zeven = set()
            elf = set()
            for i in range(1, 1001):
                if i % 3 == 0:
                    drie.add(i)
                if i % 7 == 0:
                    zeven.add(i)
                if i % 11 == 0:
                    elf.add(i)
            print(sorted(drie & zeven & elf))
            """,
            """
            Met list comprehensions kan het korter: `drie = set([i for i in range(1, 1001) if i % 3 == 0])`.
            De doorsnede van de drie sets zijn de veelvouden van 3 · 7 · 11 = 231.
            """,
            ptests=[([], "[231, 462, 693, 924]")],
            boek="Opgave 14.2",
        ),
    ],
}
