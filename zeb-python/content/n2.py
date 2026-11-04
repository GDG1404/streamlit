from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "nr": 2,
    "titel": "Tekst en invoer",
    "kort": "str, input en omzetten",
    "spiek": ["base-types", "input", "conversions", "display"],
    "doel": "Je kent het verschil tussen `\"5\"` en `5`, en je kan invoer vragen en omzetten naar een getal.",
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
    ],
}
