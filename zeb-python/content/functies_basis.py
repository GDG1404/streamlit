from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "functies-basis",
    "titel": "Eenvoudige functies",
    "kort": "type casting, input, len, max, format",
    "hoofdstuk": "5",
    "spiek": ["input", "conversions", "display", "formatting"],
    "doel": "Je kent het verschil tussen `\"5\"` en `5`, je kan invoer vragen en omzetten (type casting), en je gebruikt functies zoals `len`, `max`, `round` en `format`.",
    "uitleg": [
        les(
            "Tekst is een str",
            """
            Tekst (een *string*, kort `str`) staat tussen `"..."` of `'...'`.
            Beide mogen, als begin en einde maar hetzelfde zijn.

            Met tekst kan je ook "rekenen":
            - `+` plakt tekst aan elkaar
            - `*` herhaalt tekst
            - `len(...)` geeft het aantal tekens
            """,
            """
            naam = "Zeb"
            print("Dag " + naam)
            print("ha" * 3)
            print(len(naam))
            """,
        ),
        les(
            "input vraagt iets aan de gebruiker",
            """
            `input("vraag")` toont de vraag, wacht tot de gebruiker iets intypt
            en Enter drukt, en geeft dat terug.

            **Belangrijk:** `input` geeft **altijd tekst** terug, ook als je een
            getal intypt. Je spiekbrief zegt het ook: *input always returns a string*.
            """,
            """
            antwoord = input("Hoe oud ben je? ")
            print(antwoord * 2)
            """,
            inputs=["18"],
            papier="Hier typte de gebruiker 18. Tekst maal 2 is de tekst twee keer: 1818.",
        ),
        les(
            "Omzetten: int, float, str",
            """
            Om met invoer te rekenen, zet je de tekst om naar een getal
            (spiekbrief: *Conversions*):
            - `int("15")` geeft `15`
            - `float("2.5")` geeft `2.5`
            - `str(15)` geeft `"15"`
            - `int(15.56)` geeft `15`: de komma wordt gewoon **afgekapt**, niet afgerond

            Het vaste patroon voor een getal vragen is:
            `getal = int(input("Geef een getal: "))`
            """,
            """
            leeftijd = int(input("Hoe oud ben je? "))
            print(leeftijd + 1)
            print(int(15.56))
            """,
            inputs=["18"],
        ),
        les(
            "Tekst en getallen mengen",
            """
            `"Ik ben " + 18` geeft een **fout** (TypeError): je kan geen tekst
            en getal optellen. Twee oplossingen:
            - zet het getal om: `"Ik ben " + str(18)`
            - of gebruik komma's in `print`: `print("Ik ben", 18)`
            """,
            """
            leeftijd = 18
            print("Ik ben " + str(leeftijd) + " jaar")
            print("Ik ben", leeftijd, "jaar")
            """,
        ),
        les(
            "print-opties: sep en end",
            """
            Normaal zet `print` een spatie tussen de stukken en springt het
            daarna naar een nieuwe regel. Dat kan je veranderen (spiekbrief: *Display*):
            - `sep="-"` verandert wat er tussen de stukken komt
            - `end=""` zorgt dat de volgende print op dezelfde regel verdergaat
            """,
            """
            print("a", "b", "c")
            print("a", "b", "c", sep="-")
            print("x", end="")
            print("y")
            """,
        ),

        les(
            "Een functie aanroepen",
            """
            Een functie (cursus hoofdstuk 5) heeft:
            - een **naam**, zoals `len` of `max`
            - **parameters** tussen haakjes: wat je meegeeft
            - een **retourwaarde**: wat eruit komt

            Je hoeft niet te weten hoe de functie vanbinnen werkt: het is een
            **zwarte doos**. Je moet wel weten wat erin gaat en wat eruit komt.
            """,
            """
            lengte = len("mango")
            print(lengte)
            print(max(3, 8, 1), min(3, 8, 1))
            print(abs(-4), pow(2, 5), round(3.14159, 2))
            """,
        ),
        les(
            "Mooie uitvoer met format()",
            """
            Met `format()` maak je een string waarin waarden op de plaats van `{}`
            komen (cursus 5.2.6). `format()` is eigenlijk een **methode**: je roept
            hem aan op een string, met een punt ertussen.

            - `{}` wordt vervangen door de volgende waarde
            - `{:.2f}` toont een getal met **2 cijfers na de komma**
            - `{:5}` gebruikt minstens 5 posities (handig om uit te lijnen)
            """,
            """
            print("{} kost {} euro".format("appel", 2))
            print("{:.3f}".format(7 / 11))
            print("{:.2f} gedeeld door {:.2f} is {:.2f}".format(1, 2, 1 / 2))
            """,
        ),
        les(
            "Toevalsgetallen met random",
            """
            De module `random` maakt (pseudo-)toevalsgetallen (cursus 5.3.2):
            - `random()` geeft een float van 0.0 tot (niet met) 1.0
            - `randint(a, b)` geeft een geheel getal van a **tot en met** b

            Let op: bij `randint` zit het einde **wel** in, bij `range` niet!
            """,
            """
            from random import randint, seed
            seed(1)
            print(randint(1, 6))
            print(randint(1, 6))
            """,
            papier="Door `seed(1)` krijg je elke keer dezelfde 'toevalsgetallen'. Handig om te testen.",
        ),
        les(
            "pcinput: getInteger() en getFloat()",
            """
            In je cursus gebruikt het boek vaak de module **pcinput** (bijlage C):
            - `getInteger("Geef een getal: ")` vraagt een geheel getal
            - `getFloat("Geef een getal: ")` vraagt een kommagetal
            - `getString(...)` vraagt een tekst (zonder spaties vooraan en achteraan)

            Ze werken zoals `int(input(...))` en `float(input(...))`, maar vragen
            opnieuw als de gebruiker iets verkeerds intypt. In deze app gebruiken
            we gewoon `int(input(...))`: dat werkt altijd, ook zonder pcinput.
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            print("ab" + "cd")
            print("ab" * 3)
            """,
            "`+` plakt aan elkaar, `*` herhaalt.",
        ),
        voorspel(
            """
            print("5" + "3")
            print(5 + 3)
            """,
            "Tekst + tekst wordt aan elkaar geplakt: `53`. Getal + getal wordt opgeteld: `8`.",
        ),
        voorspel(
            """
            naam = "Zeb"
            print(len(naam))
            print("Dag " + naam + "!")
            """,
            "`len` telt de tekens: Z, e, b = 3. Let op de spatie na `Dag`.",
        ),
        keuze(
            "De gebruiker typt `42` in bij `x = input()`. Wat zit er dan in x?",
            ["Het getal 42 (int)", 'De tekst "42" (str)', "Het kommagetal 42.0 (float)", "Niets"],
            1,
            "`input` geeft altijd tekst. Wil je een getal, dan schrijf je `int(input())`.",
        ),
        voorspel(
            """
            getal = input("Geef een getal: ")
            print(getal * 2)
            """,
            """
            `getal` is de **tekst** `"7"`. Tekst maal 2 herhaalt de tekst: `77`.
            Dit is een klassieke examenvraag.
            """,
            inputs=["7"],
            vraag="De gebruiker typt **7** in. Wat toont `print`? (Schrijf de vraag van input niet mee op.)",
        ),
        voorspel(
            """
            getal = int(input("Geef een getal: "))
            print(getal * 2)
            """,
            "Nu wordt de tekst eerst omgezet naar het getal 7. 7 maal 2 is 14.",
            inputs=["7"],
            vraag="De gebruiker typt **7** in. Wat toont `print`?",
        ),
        fout(
            "Dit programma moet `Je bent 18 jaar` tonen. Op welke regel loopt het mis?",
            """
            leeftijd = 18
            print("Je bent " + leeftijd + " jaar")
            """,
            2,
            """
            leeftijd = 18
            print("Je bent " + str(leeftijd) + " jaar")
            """,
            "Je kan geen tekst en getal optellen (TypeError). Zet het getal om met `str(...)` of gebruik komma's.",
        ),
        voorspel(
            """
            print(int("15") + 1)
            print(int(9.99))
            print(float("2.5") * 2)
            """,
            "`int(9.99)` kapt af: 9, niet 10! `float(\"2.5\") * 2` is 5.0.",
        ),
        voorspel(
            """
            print("a", "b", "c")
            print("a", "b", "c", sep="-")
            print("x", end="")
            print("y")
            """,
            "Met `sep=\"-\"` komt er een streepje tussen in plaats van een spatie. Met `end=\"\"` gaat de volgende print verder op dezelfde regel.",
        ),
        aanvullen(
            "Vul aan zodat het programma de **som** van twee ingetypte getallen toont (bij 3 en 4: `7`).",
            """
            a = ___(input("a? "))
            b = ___(input("b? "))
            print(a + b)
            """,
            [["int", "float"], ["int", "float"]],
            "Zonder omzetting plakt `+` de teksten aan elkaar: `34` in plaats van 7.",
            inputs=["3", "4"],
        ),
        voorspel(
            """
            woord = "py"
            zin = woord + "thon"
            print(zin * 2, len(zin))
            """,
            "`zin` is `python` (6 tekens). Twee keer achter elkaar: `pythonpython`, dan een spatie en 6.",
        ),
        schrijf(
            """
            Schrijf een programma dat met `input` de naam van de gebruiker vraagt en daarna
            `Hallo <naam>!` toont. Typt de gebruiker `Zeb`, dan verschijnt: `Hallo Zeb!`
            """,
            """
            naam = input("Wat is je naam? ")
            print("Hallo " + naam + "!")
            """,
            """
            Let op de spaties: `print("Hallo", naam, "!")` geeft `Hallo Zeb !`
            (met een spatie voor het uitroepteken). Met `+` heb je zelf de controle.
            """,
            ptests=[(["Zeb"], "Hallo Zeb!"), (["An"], "Hallo An!")],
        ),
        schrijf(
            """
            Vraag een aantal minuten (een geheel getal) en toon hoeveel uur en minuten dat is,
            in de vorm `2 u 15 min`. Bij 135 verschijnt dus `2 u 15 min`.
            """,
            """
            totaal = int(input("Aantal minuten: "))
            print(totaal // 60, "u", totaal % 60, "min")
            """,
            "Vergeet `int(...)` niet rond `input`, anders kan je niet rekenen.",
            ptests=[(["135"], "2 u 15 min"), (["59"], "0 u 59 min"), (["60"], "1 u 0 min")],
        ),

        voorspel(
            """
            print(len("man"))
            print(len("mango"))
            print(len(""))
            """,
            "`len` telt de tekens. Een lege string `\"\"` heeft lengte 0.",
            boek="Opgave in 5.2.3",
        ),
        voorspel(
            """
            print(max(3, 8, 1), min(3, 8, 1))
            print(abs(-7.5), round(2.675, 1))
            print(pow(2, 3) + len("abc"))
            """,
            "max 8, min 1. `abs(-7.5)` is 7.5. `round(2.675, 1)` is 2.7. Dan 8 + 3 = 11.",
        ),
        keuze(
            "Wat gebeurt er bij `print(10 * int(\"100,000,000\"))`?",
            [
                "Het toont 1000000000",
                "Het toont 100,000,0000",
                "Een runtime error (ValueError): \"100,000,000\" is geen geheel getal",
                "Het toont 100000000",
            ],
            2,
            """
            `int()` kan alleen tekst omzetten die er echt uitziet als een geheel getal.
            Komma's mogen niet. Haal je de twee komma's weg, dan werkt het: 1000000000.
            """,
            boek="Opgave in 5.2.1",
        ),
        voorspel(
            """
            print("{} kost {} euro".format("appel", 2))
            print("{:.2f}".format(2 / 3))
            print("{:.1f} en {}".format(3.14159, 7))
            """,
            "`{}` vult de volgende waarde in. `{:.2f}` rondt af op 2 cijfers na de komma: 0.67.",
        ),
        keuze(
            "Welke getallen kan `randint(1, 6)` teruggeven?",
            ["1, 2, 3, 4, 5", "1, 2, 3, 4, 5, 6", "0, 1, 2, 3, 4, 5", "0 tot 6, ook kommagetallen"],
            1,
            "Bij `randint` zit het einde **wel** in, net als bij een dobbelsteen. Bij `range` niet.",
        ),
        schrijf(
            """
            Vraag drie gehele getallen. Toon daarna, elk op een eigen regel: het **grootste**,
            het **kleinste** en het **gemiddelde** afgerond op twee decimalen.
            Bij 3, 8 en 2 verschijnt: `8`, `2` en `4.33`.
            """,
            """
            a = int(input("Getal 1: "))
            b = int(input("Getal 2: "))
            c = int(input("Getal 3: "))
            print(max(a, b, c))
            print(min(a, b, c))
            print(round((a + b + c) / 3, 2))
            """,
            "Met `max`, `min` en `round` heb je geen if nodig.",
            ptests=[(["3", "8", "2"], "8\n2\n4.33"), (["5", "5", "5"], "5\n5\n5.0")],
            boek="Opgave 5.3",
        ),
        schrijf(
            """
            Vraag de lengtes van de twee rechte zijden van een rechthoekige driehoek
            (kommagetallen). Bereken met Pythagoras de schuine zijde en toon die.
            Bij 3 en 4 verschijnt `5.0`.
            """,
            """
            from math import sqrt
            a = float(input("Zijde a: "))
            b = float(input("Zijde b: "))
            c = sqrt(a * a + b * b)
            print(c)
            """,
            "`sqrt` komt uit de module `math`. Vergeet de import niet.",
            ptests=[(["3", "4"], "5.0"), (["5", "12"], "13.0")],
            boek="Opgave 5.2",
        ),
    ],
}
