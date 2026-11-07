from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "start",
    "titel": "Expressies en variabelen",
    "kort": "print, data types, variabelen",
    "hoofdstuk": "3 en 4",
    "spiek": ["base-types", "assignment", "display", "identifiers"],
    "doel": "Je weet wat een variabele is, wat `=` doet en wat `print` op het scherm zet.",
    "uitleg": [
        les(
            "Een programma is een lijstje opdrachten",
            """
            Python leest je programma **van boven naar onder** en voert de regels
            één voor één uit. Pas als een regel klaar is, komt de volgende.

            Dat is het belangrijkste idee van heel het vak: als jij op papier
            precies doet wat Python doet, regel per regel, dan weet je ook wat
            er gebeurt.
            """,
            """
            print("Goeiemorgen")
            print("Tijd voor Python")
            """,
        ),
        les(
            "print zet iets op het scherm",
            """
            Tekst tussen aanhalingstekens wordt **letterlijk** getoond. Zonder
            aanhalingstekens rekent Python eerst uit wat er staat.

            Zet je meerdere dingen in `print`, gescheiden door komma's, dan
            komt er automatisch **één spatie** tussen.
            """,
            """
            print("3 + 4")
            print(3 + 4)
            print("Som:", 3 + 4)
            """,
        ),
        les(
            "Een variabele is een doosje met een naam",
            """
            `x = 5` betekent: **steek 5 in het doosje met naam x**. Het is
            geen wiskundige gelijkheid, het is een opdracht.

            Python werkt altijd zo:
            - eerst wordt **rechts** van `=` uitgerekend,
            - dan gaat het resultaat in de variabele **links**.

            Daarom kan `x = x + 1` gewoon: neem de oude x, tel 1 op, en steek
            het resultaat terug in x. De oude waarde is dan weg.
            """,
            """
            x = 5
            print(x)
            x = x + 1
            print(x)
            """,
            papier="""
            Op papier: teken een tabel met een kolom per variabele. Schrijf bij
            elke toekenning de nieuwe waarde onder de vorige en streep de oude door.
            """,
        ),
        les(
            "Soorten waarden",
            """
            Elke waarde heeft een **type**. Op je spiekbrief staat dat bij
            *Base Types*:
            - `int`: een geheel getal, zoals `783`, `0` of `-192`
            - `float`: een kommagetal, met een **punt**: `9.23`, `0.0`
            - `str`: tekst, tussen aanhalingstekens: `"Zeb"`, `'hallo'`
            - `bool`: waar of onwaar: `True` of `False`

            Let op: `"5"` is tekst en `5` is een getal. Dat verschil komt nog
            vaak terug.
            """,
            """
            print(type(5))
            print(type(5.0))
            print(type("5"))
            print(type(True))
            """,
        ),
        les(
            "Namen kiezen",
            """
            Een variabelenaam:
            - bestaat uit letters, cijfers en `_`
            - begint **niet** met een cijfer
            - heeft geen spaties
            - is geen Python-woord zoals `if`, `for` of `and`

            Hoofdletters tellen: `Naam` en `naam` zijn twee verschillende variabelen.
            Op je spiekbrief (*Identifiers*) staan goede voorbeelden (`a`, `toto`,
            `x7`, `y_max`) en foute (`8y`, `and`, `for`).
            """,
        ),
        les(
            "Twee waarden wisselen",
            """
            Op je spiekbrief staat `a, b = b, a` (*values swap*). Python rekent
            eerst **beide** waarden rechts uit en steekt ze dan tegelijk in a en b.
            """,
            """
            a = 3
            b = 8
            a, b = b, a
            print(a, b)
            """,
        ),

        les(
            "Commentaar",
            """
            Alles na een `#` op een regel is **commentaar**: Python slaat het over.
            Je schrijft het voor mensen, om uit te leggen wat je code doet
            (cursus 4.6).

            Op papier mag je ook commentaar schrijven. Een korte zin boven een
            moeilijk stuk helpt de prof (en jezelf) om je bedoeling te volgen.

            Namen van **constanten**, waarden die nooit veranderen, schrijf je
            volgens de gewoonte in hoofdletters: `PI = 3.14159` (cursus 4.2.3).
            """,
            """
            # Oppervlakte van een cirkel
            PI = 3.14159
            straal = 2
            opp = PI * straal * straal   # straal keer straal keer pi
            print(opp)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            print("Hallo Zeb")
            print("Welkom")
            """,
            "Elke `print` zet zijn tekst op een **nieuwe regel**.",
        ),
        voorspel(
            """
            x = 4
            y = x + 3
            print(y)
            """,
            "Eerst krijgt x de waarde 4. Dan rekent Python `x + 3` uit, dus 7, en dat gaat in y.",
        ),
        voorspel(
            """
            a = 10
            a = a + 5
            print(a)
            """,
            "Rechts eerst: `a + 5` is `10 + 5`, dus 15. Dat gaat terug in a. De oude 10 is weg.",
        ),
        keuze(
            "Wat betekent `x = 7` in Python?",
            [
                "x is gelijk aan 7 (een vergelijking)",
                "Steek de waarde 7 in de variabele x",
                "Toon 7 op het scherm",
                "Controleer of x gelijk is aan 7",
            ],
            1,
            """
            Eén `=` is een **toekenning**: de waarde rechts gaat in de variabele links.
            Om te vergelijken gebruik je `==` (twee isgelijktekens). Dat zie je in niveau 3.
            """,
        ),
        voorspel(
            """
            print("3 + 4")
            print(3 + 4)
            """,
            "Tussen aanhalingstekens is het tekst, dus letterlijk `3 + 4`. Zonder aanhalingstekens rekent Python: 7.",
        ),
        voorspel(
            """
            a = 2
            b = a
            a = 5
            print(a, b)
            """,
            """
            `b = a` kopieert de **waarde** die a op dat moment heeft (2) naar b.
            Als a daarna verandert, blijft b gewoon 2.
            """,
            tip="Maak een tabel met een kolom a en een kolom b.",
        ),
        keuze(
            "Welke naam is **geen** geldige variabelenaam?",
            ["aantal_2", "2de_getal", "_x", "Totaal"],
            1,
            "Een naam mag niet met een cijfer beginnen. `tweede_getal` of `getal2` mag wel.",
        ),
        voorspel(
            """
            x = 1
            x = x + 1
            x = x * 3
            print("x is", x)
            """,
            "x wordt 1, dan 2, dan 6. `print` met een komma zet er een spatie tussen: `x is 6`.",
        ),
        fout(
            "Dit programma moet de som van 3 en 4 tonen. Op welke regel zit de fout?",
            """
            getal1 = 3
            getal2 = 4
            som = getal1 + getal2
            print(Som)
            """,
            4,
            """
            getal1 = 3
            getal2 = 4
            som = getal1 + getal2
            print(som)
            """,
            "`Som` met een hoofdletter bestaat niet: de variabele heet `som`. Python geeft dan een **NameError**.",
        ),
        aanvullen(
            "Vul aan zodat het programma `Ik ben 18 jaar` toont.",
            """
            leeftijd = 18
            print("Ik ben", ___, "jaar")
            """,
            [["leeftijd", "18"]],
            "Je zet de variabele `leeftijd` tussen de twee stukken tekst. De komma's zorgen voor de spaties.",
        ),
        voorspel(
            """
            a = 3
            b = 8
            a, b = b, a
            print(a, b)
            """,
            "Dit is de *values swap* van je spiekbrief: a en b wisselen van waarde.",
        ),
        voorspel(
            """
            x = 5
            y = x
            x = x + y
            y = x - y
            print(x, y)
            """,
            "Stap voor stap: x=5, y=5, dan x=10, dan y=10-5=5. Volg het met een tabel.",
            tip="Schrijf na elke regel de waarde van x én y op.",
        ),
        schrijf(
            """
            Schrijf een programma dat:
            - in de variabele `prijs` de waarde 12 steekt,
            - in de variabele `aantal` de waarde 3 steekt,
            - en dan `Totaal: 36` toont, waarbij 36 **berekend** wordt.
            """,
            """
            prijs = 12
            aantal = 3
            print("Totaal:", prijs * aantal)
            """,
            "Door `prijs * aantal` te schrijven in plaats van 36 werkt je programma ook als de prijs verandert.",
            ptests=[([], "Totaal: 36")],
        ),

        voorspel(
            """
            print(1,000,000,000)
            """,
            """
            Python leest dit niet als één miljard, maar als **vier getallen**
            gescheiden door komma's: 1, 000, 000 en 000. Dus `print` toont 1 0 0 0.
            Daarom schrijf je grote getallen zonder scheidingstekens: `1000000000`.
            """,
            boek="Opgave in 3.2.2",
        ),
        keuze(
            "Wat toont dit programma?",
            ["Hallo", "Niets, maar ook geen foutmelding", "Een foutmelding", "# Hallo"],
            1,
            "De regel begint met `#`: het is commentaar. Python slaat hem over.",
            code="""
            # print("Hallo")
            """,
            draai=False,
        ),
        schrijf(
            """
            Schrijf een programma dat het aantal **seconden in een week** berekent
            en in een variabele `seconden` steekt. Toon daarna die variabele.
            Laat Python rekenen: typ niet zelf de uitkomst.
            """,
            """
            seconden = 7 * 24 * 60 * 60
            print(seconden)
            """,
            "7 dagen × 24 uur × 60 minuten × 60 seconden.",
            ptests=[([], "604800")],
            boek="Opgave in 3.3.2 en 4.1",
        ),
        schrijf(
            """
            Gebruik een variabele `straal` met waarde 5 en een variabele `pi`
            met waarde 3.14159. Bereken de oppervlakte van de cirkel
            (straal keer straal keer pi) en toon:
            `De oppervlakte van een cirkel met straal 5 is 78.53975`
            """,
            """
            straal = 5
            pi = 3.14159
            opp = straal * straal * pi
            print("De oppervlakte van een cirkel met straal", straal, "is", opp)
            """,
            "Met komma's in `print` komen de spaties vanzelf.",
            ptests=[([], "De oppervlakte van een cirkel met straal 5 is 78.53975")],
            boek="Opgave 4.2",
        ),
    ],
}
