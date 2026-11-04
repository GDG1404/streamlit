from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "nr": 7,
    "titel": "Functies",
    "kort": "def, parameters, return",
    "spiek": ["def", "call"],
    "doel": "Je kan een functie schrijven die een resultaat **teruggeeft** en kent het verschil tussen return en print.",
    "uitleg": [
        les(
            "Een functie is een stukje code met een naam",
            """
            Met `def` maak je een functie: een stuk code dat je later zo vaak kan
            gebruiken als je wil. Je spiekbrief noemt het een **zwarte doos**
            (*black box*): er gaat iets in (de parameters), er komt iets uit
            (de return-waarde).

            **Belangrijk:** de code in een functie wordt pas uitgevoerd als je de
            functie **aanroept**. Alleen `def` schrijven doet nog niets.
            """,
            """
            def groet(naam):
                print("Dag", naam)

            groet("Zeb")
            groet("Lies")
            """,
        ),
        les(
            "return geeft een resultaat terug",
            """
            `return waarde` stuurt het resultaat terug naar de plek waar de
            functie werd aangeroepen. Daar kan je het in een variabele steken of
            ermee verder rekenen.
            """,
            """
            def kwadraat(x):
                return x * x

            a = kwadraat(4)
            print(a)
            print(kwadraat(3) + kwadraat(2))
            """,
        ),
        les(
            "return of print: het grote verschil",
            """
            - `print` zet iets op het **scherm**. Het programma kan er daarna niets meer mee doen.
            - `return` geeft een **waarde terug**. Daar kan je mee verder rekenen.

            Een functie zonder return geeft `None` terug (spiekbrief: *if no
            computed result to return: return None*).

            Op het examen staat bijna altijd: *"Schrijf een functie die ...
            **teruggeeft**"*. Dan moet je `return` gebruiken, geen `print`!
            """,
            """
            def met_print(x):
                print(x * 2)

            def met_return(x):
                return x * 2

            a = met_print(5)
            b = met_return(5)
            print("a is", a)
            print("b is", b)
            """,
        ),
        les(
            "return stopt de functie",
            """
            Zodra Python een `return` uitvoert, is de functie **meteen gedaan**.
            Code die daarna komt in de functie wordt niet meer uitgevoerd.
            Dat kan je slim gebruiken:
            """,
            """
            def maximum(a, b):
                if a > b:
                    return a
                return b

            print(maximum(3, 7))
            print(maximum(9, 2))
            """,
        ),
        les(
            "Lokale variabelen",
            """
            Variabelen die je **in** een functie maakt (ook de parameters), bestaan
            alleen **tijdens** die functie. Daarbuiten kan je ze niet gebruiken.
            Je spiekbrief: *parameters and all variables of this block exist only
            in the block and during the function call*.
            """,
            """
            def som_tot(n):
                s = 0
                for i in range(1, n + 1):
                    s = s + i
                return s

            print(som_tot(4))
            print(som_tot(10))
            """,
        ),
        les(
            "Een functie schrijven op papier: stappenplan",
            """
            1. **Kopregel**: hoe heet de functie en welke parameters krijgt ze?
               `def aantal_even(lst):`
            2. **Wat moet eruit komen?** Een getal, een lijst, True/False?
            3. **Reken een voorbeeld met de hand.** Voor `[1, 2, 3, 4]` moet er 2 uitkomen.
            4. **Schrijf de code.** Meestal: beginwaarde, lus, return.
            5. **Test op papier** met je voorbeeld en een variabelentabel.
            """,
            """
            def aantal_even(lst):
                aantal = 0
                for x in lst:
                    if x % 2 == 0:
                        aantal += 1
                return aantal

            print(aantal_even([1, 2, 3, 4]))
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            def dubbel(x):
                return 2 * x

            print(dubbel(5))
            print(dubbel(1) + 1)
            """,
            "`dubbel(5)` geeft 10. `dubbel(1)` geeft 2, plus 1 is 3.",
        ),
        voorspel(
            """
            def groet(naam):
                print("Dag", naam)

            groet("Zeb")
            groet("Lies")
            """,
            "De functie wordt twee keer aangeroepen, telkens met een andere naam.",
        ),
        voorspel(
            """
            def f(x):
                print(x + 1)

            resultaat = f(3)
            print(resultaat)
            """,
            """
            `f(3)` **toont** 4, maar heeft geen return. Dus geeft ze `None` terug, en dat
            komt in `resultaat`. Dit is een van de belangrijkste examenvragen!
            """,
        ),
        keuze(
            "Wat is het verschil tussen `return` en `print` in een functie?",
            [
                "Er is geen verschil",
                "return toont iets op het scherm, print geeft een waarde terug",
                "print toont iets op het scherm, return geeft een waarde terug aan wie de functie aanriep",
                "return mag je alleen gebruiken met getallen",
            ],
            2,
            "Met return kan het programma verder rekenen met het resultaat. Met print alleen kijken.",
        ),
        voorspel(
            """
            def maximum(a, b):
                if a > b:
                    return a
                return b

            print(maximum(3, 7))
            print(maximum(9, 2))
            """,
            "Bij (3, 7) is a > b onwaar, dus `return b` = 7. Bij (9, 2) wordt meteen 9 teruggegeven.",
        ),
        voorspel(
            """
            def f(n):
                return n * 2
                print("hier")

            print(f(4))
            """,
            "Na `return` is de functie gedaan: `hier` wordt **nooit** getoond.",
        ),
        voorspel(
            """
            def som_tot(n):
                s = 0
                for i in range(1, n + 1):
                    s += i
                return s

            print(som_tot(4))
            """,
            "`range(1, 5)` geeft 1, 2, 3, 4. De som is 10.",
        ),
        keuze(
            "Wat gebeurt er als je dit programma uitvoert?",
            [
                "Het toont 5",
                "Het toont None",
                "Een fout (NameError): y bestaat niet buiten de functie",
                "Het toont niets",
            ],
            2,
            "`y` is een **lokale** variabele van f. Buiten de functie bestaat y niet.",
            code="""
            def f():
                y = 5

            f()
            print(y)
            """,
        ),
        fout(
            "Deze functie moet de oppervlakte van een rechthoek **teruggeven** (bij 3 en 4: 12). Na welke regel ontbreekt er iets?",
            """
            def oppervlakte(l, b):
                opp = l * b

            print(oppervlakte(3, 4))
            """,
            2,
            """
            def oppervlakte(l, b):
                opp = l * b
                return opp

            print(oppervlakte(3, 4))
            """,
            "Zonder `return` geeft de functie `None` terug. Na regel 2 moet `return opp` komen.",
        ),
        aanvullen(
            "Vul aan zodat de functie True teruggeeft als n even is.",
            """
            def is_even(n):
                ___ n % 2 == 0

            print(is_even(4))
            """,
            [["return"]],
            "`n % 2 == 0` is zelf al True of False. Dat kan je meteen teruggeven.",
        ),
        voorspel(
            """
            def f(a, b):
                a = a + b
                return a * b

            x = 2
            y = f(x, 3)
            print(x, y)
            """,
            "In f wordt de lokale a 2 + 3 = 5, en de functie geeft 5 · 3 = 15 terug. De x buiten de functie blijft 2.",
            tip="Hou in je tabel de variabelen van f apart van die van het hoofdprogramma.",
        ),
        schrijf(
            """
            Schrijf een functie `oppervlakte_cirkel(r)` die de oppervlakte van een cirkel
            met straal r **teruggeeft** (π · r²). Gebruik `from math import pi`.
            """,
            """
            from math import pi

            def oppervlakte_cirkel(r):
                return pi * r ** 2
            """,
            "`r ** 2` is r in het kwadraat. Geen print in de functie: het resultaat wordt teruggegeven.",
            tests=[("round(oppervlakte_cirkel(1), 4)", 3.1416), ("round(oppervlakte_cirkel(2), 4)", 12.5664),
                   ("oppervlakte_cirkel(0)", 0.0)],
            start="from math import pi\n\ndef oppervlakte_cirkel(r):",
        ),
        schrijf(
            """
            Schrijf een functie `aantal_even(lst)` die **teruggeeft** hoeveel even getallen
            er in de lijst zitten. `aantal_even([1, 2, 3, 4])` geeft `2`.
            """,
            """
            def aantal_even(lst):
                aantal = 0
                for x in lst:
                    if x % 2 == 0:
                        aantal += 1
                return aantal
            """,
            "Teller op 0 vóór de lus, +1 als het getal even is, return **na** de lus (niet erin!).",
            tests=[("aantal_even([1, 2, 3, 4])", 2), ("aantal_even([])", 0), ("aantal_even([7, 9])", 0),
                   ("aantal_even([2, 2, 8])", 3)],
            start="def aantal_even(lst):",
        ),
        schrijf(
            """
            Schrijf een functie `faculteit(n)` die n! teruggeeft: 1 · 2 · 3 · ... · n.
            Afspraak: `faculteit(0)` is 1. `faculteit(5)` is 120.
            """,
            """
            def faculteit(n):
                resultaat = 1
                for i in range(1, n + 1):
                    resultaat = resultaat * i
                return resultaat
            """,
            "Bij vermenigvuldigen begin je met **1** (niet 0, want dan blijft alles 0).",
            tests=[("faculteit(0)", 1), ("faculteit(1)", 1), ("faculteit(5)", 120), ("faculteit(10)", 3628800)],
            start="def faculteit(n):",
        ),
        schrijf(
            """
            Schrijf een functie `grootste(lst)` die het grootste getal uit een (niet-lege)
            lijst teruggeeft, **zonder** `max` te gebruiken.
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
            bij een lijst met enkel negatieve getallen zou 0 anders fout zijn.
            """,
            tests=[("grootste([3, 9, 2])", 9), ("grootste([-5, -2, -9])", -2), ("grootste([7])", 7)],
            start="def grootste(lst):",
            verboden=["max("],
            uitdaging=True,
        ),
    ],
}
