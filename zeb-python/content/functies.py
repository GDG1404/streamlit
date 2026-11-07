from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "functies",
    "titel": "Functies",
    "kort": "def, parameters, return",
    "hoofdstuk": "8",
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
               `def aantal_delers(n):`
            2. **Wat moet eruit komen?** Een getal, een tekst, True/False?
            3. **Reken een voorbeeld met de hand.** 6 is deelbaar door 1, 2, 3 en 6: er moet 4 uitkomen.
            4. **Schrijf de code.** Meestal: beginwaarde, loop, return.
            5. **Test op papier** met je voorbeeld en een variabelentabel.
            """,
            """
            def aantal_delers(n):
                aantal = 0
                for d in range(1, n + 1):
                    if n % d == 0:
                        aantal += 1
                return aantal

            print(aantal_delers(6))
            """,
        ),
        les(
            "Default parameter waardes",
            """
            Een parameter kan een **standaardwaarde** krijgen (cursus 8.2.4).
            Geef je bij het aanroepen geen argument mee, dan gebruikt Python die
            waarde. Parameters met een standaardwaarde staan altijd **achteraan**.
            """,
            """
            def groet(naam, begroeting="Dag"):
                print(begroeting, naam)

            groet("Zeb")
            groet("Lies", "Hallo")
            """,
        ),
        les(
            "Meerdere retourwaardes",
            """
            Een functie kan **meerdere waarden** tegelijk teruggeven, gescheiden door
            komma's (cursus 8.2.8). Bij het aanroepen vang je ze op in evenveel variabelen.
            """,
            """
            def deel(a, b):
                return a // b, a % b

            quotient, rest = deel(17, 5)
            print(quotient, rest)
            """,
        ),
        les(
            "Functies roepen functies aan",
            """
            Een functie mag een andere functie aanroepen (cursus 8.2.9). Zo bouw je
            grote problemen op uit kleine stukjes die je al getest hebt. Het boek
            gebruikt namen zoals `isEven()`: een functie die True of False teruggeeft,
            begint vaak met `is`.
            """,
            """
            def isEven(n):
                return n % 2 == 0

            def isOneven(n):
                return not isEven(n)

            print(isEven(4), isOneven(4))
            """,
        ),
        les(
            "Globale variabelen",
            """
            Een variabele die je **buiten** elke functie maakt, is **globaal**. Een
            functie kan ze lezen. Maar zodra je in een functie een **toekenning** doet
            met dezelfde naam, maakt Python een nieuwe, **lokale** variabele.

            Met `global x` kan een functie toch de globale x aanpassen (cursus 8.3.2).
            Het boek raadt dat af: geef waarden liever mee als parameter en gebruik `return`.
            """,
            """
            x = 1

            def f():
                x = 5
                print("in f:", x)

            f()
            print("buiten f:", x)
            """,
        ),
        les(
            "Anonieme functies: lambda",
            """
            Met `lambda` maak je een kleine functie zonder naam, in één regel
            (cursus 8.6): `lambda parameters: uitkomst`. Je kan ze in een variabele
            steken. Het boek zegt zelf dat je ze eigenlijk nooit nodig hebt; je moet
            ze vooral kunnen **lezen**.
            """,
            """
            kwadraat = lambda x: x * x
            print(kwadraat(4))
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

        voorspel(
            """
            def groet(naam, begroeting="Dag"):
                print(begroeting, naam)

            groet("Zeb")
            groet("Lies", "Hallo")
            """,
            "Zonder tweede argument wordt de standaardwaarde `Dag` gebruikt.",
        ),
        voorspel(
            """
            def deel(a, b):
                return a // b, a % b

            q, r = deel(17, 5)
            print(q, r)
            print(deel(9, 2))
            """,
            """
            17 // 5 = 3 en 17 % 5 = 2. Druk je het resultaat rechtstreeks af, dan zie je
            een **tuple**: `(4, 1)`. Tuples komen terug in hoofdstuk 11.
            """,
        ),
        voorspel(
            """
            x = 1

            def f():
                x = 5
                print(x)

            f()
            print(x)
            """,
            "In f is x een **lokale** variabele (5). De globale x buiten de functie blijft 1.",
        ),
        voorspel(
            """
            kwadraat = lambda x: x * x
            plus = lambda a, b: a + b
            print(kwadraat(3), plus(2, 5))
            """,
            "`lambda x: x * x` is een functie die x² teruggeeft. Dus 9 en 7.",
        ),
        fout(
            "Het programma moet de totale oppervlakte van twee driehoeken tonen. Het geeft een fout. Welke regel moet anders?",
            """
            def oppervlakte_driehoek(basis, hoogte):
                opp = 0.5 * basis * hoogte
                print(opp)

            totaal = oppervlakte_driehoek(4, 5) + oppervlakte_driehoek(2, 3)
            print(totaal)
            """,
            3,
            """
            def oppervlakte_driehoek(basis, hoogte):
                opp = 0.5 * basis * hoogte
                return opp

            totaal = oppervlakte_driehoek(4, 5) + oppervlakte_driehoek(2, 3)
            print(totaal)
            """,
            """
            De functie **print** het resultaat in plaats van het terug te geven. Ze geeft
            dus `None` terug, en `None + None` geeft een TypeError. Vervang `print` door `return`.
            """,
            boek="Opgave 8.7",
        ),
        schrijf(
            """
            Schrijf de functie `isEven(n)` die `True` teruggeeft als n even is, en anders `False`.
            Schrijf daarna `isOneven(n)` die `isEven()` **aanroept** en het resultaat omdraait.
            """,
            """
            def isEven(n):
                return n % 2 == 0

            def isOneven(n):
                return not isEven(n)
            """,
            "`n % 2 == 0` is zelf al True of False. Met `not` draai je het om.",
            tests=[("isEven(4)", True), ("isEven(7)", False), ("isEven(0)", True),
                   ("isOneven(7)", True), ("isOneven(10)", False)],
            start="def isEven(n):",
            boek="Opgaves in 8.2.10",
        ),
        schrijf(
            """
            Schrijf een functie `tafel(n)` die de tafel van vermenigvuldiging van n toont,
            van 1 tot en met 10, in de vorm `1 * 7 = 7`. Roep ze daarna aan met `tafel(7)`.
            """,
            """
            def tafel(n):
                for i in range(1, 11):
                    print(i, "*", n, "=", i * n)

            tafel(7)
            """,
            "De functie **toont** iets, dus hier is `print` wel juist. Ze heeft geen return nodig.",
            ptests=[([], "\n".join(f"{i} * 7 = {i * 7}" for i in range(1, 11)))],
            boek="Opgave 8.1",
        ),
        schrijf(
            """
            Schrijf een functie `binomiaal(n, k)` die "n boven k" teruggeeft:
            n! / (k! · (n−k)!). Schrijf eerst een functie `faculteit(n)` en gebruik die.
            `binomiaal(5, 2)` geeft 10.
            """,
            """
            def faculteit(n):
                resultaat = 1
                for i in range(2, n + 1):
                    resultaat *= i
                return resultaat

            def binomiaal(n, k):
                return faculteit(n) // (faculteit(k) * faculteit(n - k))
            """,
            """
            Met `//` krijg je een geheel getal; met `/` krijg je 10.0, wat ook goed is.
            Het idee: kleine functie eerst, dan de grote erop bouwen.
            """,
            tests=[("binomiaal(5, 2)", 10), ("binomiaal(10, 3)", 120), ("binomiaal(4, 0)", 1),
                   ("binomiaal(6, 6)", 1)],
            boek="Opgave 8.6",
            uitdaging=True,
        ),
    ],
}
