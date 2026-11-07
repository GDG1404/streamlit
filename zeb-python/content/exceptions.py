from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

NIVEAU = {
    "key": "exceptions",
    "titel": "Exceptions",
    "kort": "try, except, else, finally, raise",
    "hoofdstuk": "17",
    "spiek": ["exceptions"],
    "doel": "Je kan fouten opvangen met try/except, kent de belangrijkste exceptions en kan er zelf een genereren met raise.",
    "uitleg": [
        les(
            "Errors en exceptions",
            """
            Er zijn twee soorten fouten (cursus 17.1):
            - een **syntax error**: Python begrijpt je code niet en voert niets uit
              (een vergeten `:`, een haakje te weinig)
            - een **runtime error** of **exception**: de code is correct geschreven,
              maar tijdens het uitvoeren loopt er iets mis

            De bekendste exceptions:
            - `ValueError`: verkeerde waarde, zoals `int("abc")`
            - `ZeroDivisionError`: delen door nul
            - `IndexError`: een index die niet bestaat
            - `KeyError`: een key die niet in een dictionary zit
            - `TypeError`: verkeerd type, zoals `"a" + 1`
            - `NameError`: een variabele die niet bestaat
            - `FileNotFoundError`: een bestand dat niet bestaat
            """,
        ),
        les(
            "try ... except",
            """
            Code die een exception kan geven, zet je in een `try`-blok. Gebeurt er een
            exception, dan springt Python meteen naar het `except`-blok (cursus 17.2.1).
            De rest van het `try`-blok wordt dan **overgeslagen**.

            Noem altijd de exception die je verwacht (cursus 17.2.2), zodat je geen
            andere fouten verstopt. Je mag meerdere `except`-blokken na elkaar zetten.
            """,
            """
            for tekst in ["12", "abc", "0"]:
                try:
                    getal = int(tekst)
                    print(100 / getal)
                except ValueError:
                    print(tekst, "is geen getal")
                except ZeroDivisionError:
                    print("delen door nul")
            """,
        ),
        les(
            "else en finally",
            """
            (cursus 17.2.3 en 17.2.4)
            - `else:` wordt uitgevoerd als er **geen** exception was
            - `finally:` wordt **altijd** uitgevoerd, met of zonder exception.
              Handig om een bestand zeker te sluiten.
            """,
            """
            try:
                x = 10 / 2
            except ZeroDivisionError:
                print("delen door nul")
            else:
                print("resultaat", x)
            finally:
                print("klaar")
            """,
        ),
        les(
            "Informatie over de exception",
            """
            Met `except ValueError as ex:` krijg je de exception in de variabele `ex`
            (cursus 17.2.5). Print je `ex`, dan zie je de foutmelding.
            """,
            """
            try:
                getal = int("3,5")
            except ValueError as ex:
                print("Fout:", ex)
            """,
        ),
        les(
            "Zelf een exception genereren: raise",
            """
            Met `raise` genereer je zelf een exception (cursus 17.4), bijvoorbeeld als een
            functie een ongeldige waarde krijgt: `raise ValueError("uitleg")`.
            Wie de functie aanroept, kan die exception dan opvangen.

            De functies van **pcinput** (zoals `getInteger()`) werken zo: een
            `while True` met `try`/`except ValueError` die blijft vragen tot het lukt.
            """,
            """
            def wortel(x):
                if x < 0:
                    raise ValueError("geen wortel uit een negatief getal")
                return x ** 0.5

            try:
                print(wortel(16))
                print(wortel(-4))
            except ValueError as ex:
                print("Fout:", ex)
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            try:
                x = int("abc")
                print("gelukt")
            except ValueError:
                print("geen getal")
            print("einde")
            """,
            "`int(\"abc\")` geeft een ValueError. De rest van het try-blok (`gelukt`) wordt overgeslagen.",
        ),
        voorspel(
            """
            try:
                print(10 / 2)
            except ZeroDivisionError:
                print("delen door nul")
            else:
                print("geen fout")
            finally:
                print("klaar")
            """,
            "Geen exception: dus het else-blok, en finally komt altijd.",
        ),
        voorspel(
            """
            try:
                print(10 / 0)
            except ZeroDivisionError:
                print("delen door nul")
            else:
                print("geen fout")
            finally:
                print("klaar")
            """,
            "Nu wel een exception: het except-blok, géén else, en finally komt altijd.",
        ),
        voorspel(
            """
            lst = [1, 2, 3]
            for i in [1, 5, 2]:
                try:
                    print(lst[i])
                except IndexError:
                    print("index", i, "bestaat niet")
            """,
            "Index 5 bestaat niet. De exception wordt opgevangen en de loop gaat gewoon verder.",
        ),
        keuze(
            "Welke exception geeft `[1, 2, 3][3]`?",
            ["ValueError", "KeyError", "IndexError", "TypeError"],
            2,
            "Een list heeft indexen 0, 1 en 2. Index 3 bestaat niet: IndexError. (KeyError is voor dictionaries.)",
        ),
        keuze(
            "Welke exception geeft `int(\"3.5\")`?",
            ["ValueError", "TypeError", "ZeroDivisionError", "Geen: het geeft 3"],
            0,
            "`\"3.5\"` ziet er niet uit als een geheel getal. `float(\"3.5\")` zou wel lukken.",
        ),
        voorspel(
            """
            def wortel(x):
                if x < 0:
                    raise ValueError("negatief getal")
                return x ** 0.5

            try:
                print(wortel(9))
                print(wortel(-4))
                print("na de wortels")
            except ValueError as ex:
                print("Fout:", ex)
            """,
            "wortel(9) geeft 3.0. wortel(-4) genereert een ValueError, dus `na de wortels` wordt overgeslagen.",
        ),
        voorspel(
            """
            while True:
                try:
                    n = int(input("Getal: "))
                    break
                except ValueError:
                    print("probeer opnieuw")
            print(n * 2)
            """,
            "Zo werkt `getInteger()` uit pcinput: `abc` en `2.5` geven een ValueError, pas bij 7 komt de `break`.",
            inputs=["abc", "2.5", "7"],
            vraag="De gebruiker typt **abc**, dan **2.5**, dan **7**. Wat toont `print`? (Schrijf de vraag van input niet mee op.)",
        ),
        aanvullen(
            "Vul aan zodat een ongeldige invoer niet tot een crash leidt.",
            """
            tekst = "twaalf"
            ___:
                getal = int(tekst)
            ___ ValueError:
                getal = 0
            print(getal)
            """,
            [["try"], ["except"]],
            "`try` rond de gevaarlijke regel, `except ValueError` voor wat er dan moet gebeuren.",
        ),
        schrijf(
            """
            Schrijf een functie `veilig_delen(a, b)` die `a / b` teruggeeft, of `None` als b
            gelijk is aan 0. Gebruik `try` en `except` (geen if).
            """,
            """
            def veilig_delen(a, b):
                try:
                    return a / b
                except ZeroDivisionError:
                    return None
            """,
            "Vang precies de ZeroDivisionError op, geen andere fouten.",
            tests=[("veilig_delen(10, 4)", 2.5), ("veilig_delen(1, 0)", None), ("veilig_delen(0, 5)", 0.0)],
            start="def veilig_delen(a, b):",
            verboden=["if "],
        ),
        schrijf(
            """
            Vraag een geheel getal. Typt de gebruiker iets wat geen geheel getal is, toon dan
            `Geen geheel getal -- probeer het opnieuw` en vraag opnieuw. Toon daarna het
            dubbel van het getal. (Dit is wat `getInteger()` van pcinput doet.)
            """,
            """
            while True:
                try:
                    getal = int(input("Getal: "))
                    break
                except ValueError:
                    print("Geen geheel getal -- probeer het opnieuw")
            print(getal * 2)
            """,
            "Een loop-en-een-half met `try`/`except` in de loop.",
            ptests=[(["abc", "3.5", "4"], "Geen geheel getal -- probeer het opnieuw\nGeen geheel getal -- probeer het opnieuw\n8"),
                    (["10"], "20")],
            boek="Bijlage C (pcinput)",
        ),
        schrijf(
            """
            Schrijf een functie `lees_getal(naam)` die het bestand met die naam opent en het
            gehele getal op de eerste regel teruggeeft. Bestaat het bestand niet, of staat er
            geen geheel getal, geef dan `-1` terug.
            (`a.txt` bevat `42`, `b.txt` bevat `hallo`, `c.txt` bestaat niet.)
            """,
            """
            def lees_getal(naam):
                try:
                    fp = open(naam)
                    regel = fp.readline()
                    fp.close()
                    return int(regel)
                except FileNotFoundError:
                    return -1
                except ValueError:
                    return -1
            """,
            "Twee mogelijke exceptions: FileNotFoundError en ValueError. Je mag ze ook samen opvangen: `except (FileNotFoundError, ValueError):`.",
            tests=[("lees_getal('a.txt')", 42), ("lees_getal('b.txt')", -1), ("lees_getal('c.txt')", -1)],
            start="def lees_getal(naam):",
            bestanden={"a.txt": "42\n", "b.txt": "hallo\n"},
            boek="Hoofdstuk 17.3",
            uitdaging=True,
        ),
        schrijf(
            """
            Schrijf een functie `controleer_leeftijd(x)` die x teruggeeft als 0 ≤ x ≤ 130,
            en anders zelf een `ValueError` genereert met `raise`.
            (In de tests geeft `geeft_fout(f, x)` aan welke exception `f(x)` geeft.)
            """,
            """
            def controleer_leeftijd(x):
                if x < 0 or x > 130:
                    raise ValueError("ongeldige leeftijd")
                return x
            """,
            "`raise ValueError(\"uitleg\")` stopt de functie meteen, net als een return, maar met een fout.",
            tests=[("controleer_leeftijd(20)", 20), ("geeft_fout(controleer_leeftijd, -1)", "ValueError"),
                   ("geeft_fout(controleer_leeftijd, 200)", "ValueError"), ("controleer_leeftijd(0)", 0)],
            start="def controleer_leeftijd(x):",
        ),
    ],
}
