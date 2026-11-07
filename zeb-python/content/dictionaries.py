from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "dictionaries",
    "titel": "Dictionaries",
    "kort": "sleutel → waarde",
    "hoofdstuk": "13",
    "spiek": ["dict-ops", "container-types"],
    "doel": "Je kan een dictionary maken, aanpassen en doorlopen, en ermee tellen.",
    "uitleg": [
        les(
            "Dictionary basis",
            """
            Een **dictionary** koppelt **keys** (sleutels) aan **waardes** (cursus 13.1),
            zoals een woordenboek een woord aan zijn uitleg koppelt:
            `{"appel": 3, "peer": 5}`.

            - `d["appel"]` zoekt de waarde bij een key op
            - `d["kers"] = 2` voegt een key toe, of past de waarde aan als hij al bestaat
            - `del d["peer"]` verwijdert een key
            - `"appel" in d` test of een **key** bestaat
            - `len(d)` is het aantal keys

            Een key die niet bestaat opzoeken geeft een **KeyError**.
            """,
            """
            voorraad = {"appel": 3, "peer": 5}
            voorraad["kers"] = 2
            voorraad["appel"] += 10
            del voorraad["peer"]
            print(voorraad)
            print(len(voorraad), "peer" in voorraad)
            """,
        ),
        les(
            "Een dictionary doorlopen",
            """
            `for k in d:` loopt over de **keys**. Met de methodes (cursus 13.2.2):
            - `d.keys()` alle keys
            - `d.values()` alle waardes
            - `d.items()` alle paren (key, waarde): `for k, v in d.items():`
            """,
            """
            punten = {"Zeb": 14, "Lies": 16, "Tom": 12}
            for naam, p in punten.items():
                print(naam, p)
            print(sum(punten.values()))
            """,
        ),
        les(
            "get(): opzoeken zonder fout",
            """
            `d.get(key, standaard)` geeft de waarde bij key, of de standaardwaarde als
            de key niet bestaat (cursus 13.2.3). Zo vermijd je een KeyError.
            """,
            """
            punten = {"Zeb": 14}
            print(punten.get("Zeb", 0))
            print(punten.get("An", 0))
            """,
        ),
        les(
            "Tellen met een dictionary",
            """
            Het bekendste gebruik: **tellen** hoe vaak iets voorkomt. Elke key is
            een woord, de waarde is de teller. Is het woord nieuw, dan begint de
            teller bij 1; anders tel je er 1 bij.
            """,
            """
            woorden = ["kat", "hond", "kat", "vis", "kat"]
            teller = {}
            for w in woorden:
                if w in teller:
                    teller[w] += 1
                else:
                    teller[w] = 1
            print(teller)
            """,
            papier="Korter, met get(): `teller[w] = teller.get(w, 0) + 1`.",
        ),
        les(
            "Keys, waardes en kopieën",
            """
            - **Keys** moeten onveranderbaar zijn: strings, getallen of tuples. Een
              list kan geen key zijn (cursus 13.3).
            - **Waardes** mogen alles zijn, ook lists of andere dictionaries (cursus 13.4).
            - `b = a` maakt een **alias**, net als bij lists. Een kopie maak je met
              `a.copy()` (cursus 13.2.1).
            """,
            """
            scores = {"Film A": [8, 7, 9], "Film B": [6, 5]}
            scores["Film B"].append(7)
            print(scores["Film B"])
            plaats = {(2, 3): "schat"}
            print(plaats[(2, 3)])
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            d = {"appel": 3, "peer": 5}
            d["kers"] = 2
            d["appel"] += 1
            print(d["appel"], len(d))
            """,
            "`kers` wordt toegevoegd (3 keys). De waarde van `appel` wordt 4.",
        ),
        voorspel(
            """
            for k, v in {"a": 1, "b": 2}.items():
                print(k, v)
            """,
            "`items()` geeft de paren (key, waarde), die je uitpakt in k en v.",
        ),
        voorspel(
            """
            d = {"x": 1}
            print(d.get("x", 0), d.get("y", 0))
            print("y" in d, 1 in d)
            """,
            "`get` geeft 0 als de key niet bestaat. `in` kijkt naar de **keys**, niet naar de waardes: 1 is geen key.",
        ),
        keuze(
            "Wat gebeurt er?",
            ["Het toont None", "Het toont 0", "Een fout: KeyError", "Het toont y"],
            2,
            "De key `y` bestaat niet. Gebruik `d.get(\"y\")` of test eerst met `if \"y\" in d`.",
            code="""
            d = {"x": 1}
            print(d["y"])
            """,
        ),
        voorspel(
            """
            woorden = ["kat", "hond", "kat", "vis", "kat"]
            teller = {}
            for w in woorden:
                teller[w] = teller.get(w, 0) + 1
            print(teller)
            """,
            "Elk woord krijgt een teller. `kat` komt 3 keer voor.",
        ),
        keuze(
            "Welke van deze kan **geen** key van een dictionary zijn?",
            ['"tekst"', "42", "(1, 2)", "[1, 2]"],
            3,
            "Keys moeten onveranderbaar zijn. Een list kan veranderen, een tuple niet.",
        ),
        voorspel(
            """
            a = {"x": 1}
            b = a
            c = a.copy()
            b["x"] = 5
            print(a["x"], c["x"])
            """,
            "`b = a` is een alias, dus a verandert mee. `c` is een echte kopie en blijft 1.",
        ),
        fout(
            "Dit programma moet tellen hoe vaak elk woord voorkomt. Op welke regel loopt het mis?",
            """
            woorden = ["kat", "hond", "kat"]
            teller = {}
            for w in woorden:
                teller[w] += 1
            print(teller)
            """,
            4,
            """
            woorden = ["kat", "hond", "kat"]
            teller = {}
            for w in woorden:
                teller[w] = teller.get(w, 0) + 1
            print(teller)
            """,
            "De eerste keer bestaat de key nog niet, dus `teller[w] += 1` geeft een KeyError. Start bij 0 met `get`, of test met `in`.",
        ),
        schrijf(
            """
            Schrijf een functie `tel_woorden(lst)` die een dictionary teruggeeft met elk woord
            uit de list als key en het aantal keer dat het voorkomt als waarde.
            """,
            """
            def tel_woorden(lst):
                teller = {}
                for w in lst:
                    if w in teller:
                        teller[w] += 1
                    else:
                        teller[w] = 1
                return teller
            """,
            "Het tel-patroon: nieuwe key op 1 zetten, bestaande key verhogen.",
            tests=[("tel_woorden(['a', 'b', 'a'])", {"a": 2, "b": 1}), ("tel_woorden([])", {}),
                   ("tel_woorden(['x', 'x', 'x'])", {"x": 3})],
            start="def tel_woorden(lst):",
            boek="Opgave in 13.2.4",
        ),
        schrijf(
            """
            Schrijf een functie `vertaal(zin, woordenboek)` die een zin woord voor woord vertaalt.
            Een woord dat niet in het woordenboek staat, blijft gewoon staan.
            `vertaal("the cat sleeps", {"the": "de", "cat": "kat"})` geeft `"de kat sleeps"`.
            """,
            """
            def vertaal(zin, woordenboek):
                nieuw = []
                for w in zin.split():
                    nieuw.append(woordenboek.get(w, w))
                return " ".join(nieuw)
            """,
            "`get(w, w)` geeft de vertaling, of het woord zelf als er geen vertaling is.",
            tests=[("vertaal('the cat sleeps', {'the': 'de', 'cat': 'kat'})", "de kat sleeps"),
                   ("vertaal('hello', {})", "hello")],
            start="def vertaal(zin, woordenboek):",
            boek="Opgave in 13.2.4",
        ),
        schrijf(
            """
            Een dictionary bevat per film een list met scores:
            `{"Film A": [8, 7, 9], "Film B": [6, 5]}`. Schrijf een functie `gemiddelden(d)` die een
            **nieuwe** dictionary teruggeeft met per film het gemiddelde, afgerond op 1 decimaal.
            """,
            """
            def gemiddelden(d):
                resultaat = {}
                for film, scores in d.items():
                    resultaat[film] = round(sum(scores) / len(scores), 1)
                return resultaat
            """,
            "Loop met `items()` over de films, en bewaar het gemiddelde onder dezelfde key.",
            tests=[("gemiddelden({'Film A': [8, 7, 9], 'Film B': [6, 5]})", {"Film A": 8.0, "Film B": 5.5}),
                   ("gemiddelden({})", {})],
            start="def gemiddelden(d):",
            boek="Opgave 13.2",
        ),
        schrijf(
            """
            Schrijf een functie `tel_letters(s)` die een dictionary teruggeeft met hoe vaak elke
            **letter** voorkomt. Hoofdletters tellen als kleine letters; tekens die geen letter
            zijn, sla je over. `tel_letters("Aap!")` geeft `{"a": 2, "p": 1}`.
            """,
            """
            def tel_letters(s):
                teller = {}
                for c in s.lower():
                    if c.isalpha():
                        teller[c] = teller.get(c, 0) + 1
                return teller
            """,
            "`lower()` eerst, `isalpha()` om enkel letters te tellen.",
            tests=[("tel_letters('Aap!')", {"a": 2, "p": 1}), ("tel_letters('123')", {})],
            start="def tel_letters(s):",
            boek="Opgave 13.1 (vereenvoudigd)",
            uitdaging=True,
        ),
    ],
}
