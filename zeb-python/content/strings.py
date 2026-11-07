from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

BARBARA = ("Barbara had een bar, waar ze rabarbar verkocht, en die daarom "
           "de rabarbarbarbarabar werd genoemd.")

NIVEAU = {
    "key": "strings",
    "titel": "Strings",
    "kort": "index, slices, methodes",
    "hoofdstuk": "10",
    "spiek": ["indexing", "string-ops", "base-types"],
    "doel": "Je kan met indexen en slices stukken uit een string halen, een string teken per teken doorlopen en de belangrijkste string methodes gebruiken.",
    "uitleg": [
        les(
            "Herhaling en speciale tekens",
            """
            Een string is tekst tussen aanhalingstekens. Je kent al `len()`, `+`, `*`
            en `in`. Sommige tekens schrijf je met een **backslash** (cursus 10.3):
            - `\\n` een nieuwe regel
            - `\\t` een tab
            - `\\"` en `\\'` een aanhalingsteken in de string
            - `\\\\` een echte backslash

            Een string over meerdere regels zet je tussen drie aanhalingstekens:
            `\"\"\"...\"\"\"` (cursus 10.2).
            """,
            """
            print("Ze zei: \\"hoi\\"\\nen ging weg.")
            print("a\\tb")
            print(len("a\\nb"))
            """,
            papier="`\\n` is één teken: de string `\"a\\nb\"` heeft lengte 3.",
        ),
        les(
            "Tekens in een string: index",
            """
            Elk teken heeft een **index**, net als bij lists: het eerste teken heeft
            index **0**, het laatste `len(s) - 1` (cursus 10.4.1).
            Negatieve indexen tellen van achteren: `s[-1]` is het laatste teken.
            """,
            """
            s = "Python"
            print(s[0], s[1], s[-1])
            print(s[len(s) - 1])
            """,
        ),
        les(
            "Slices: een stuk van een string",
            """
            `s[start:einde]` geeft het stuk van index start tot (niet met) einde.
            Met een derde getal kies je de **stap** (cursus 10.4.3):
            - `s[:3]` de eerste drie tekens
            - `s[3:]` alles vanaf index 3
            - `s[::2]` elk tweede teken
            - `s[::-1]` de string achterstevoren
            """,
            """
            s = "programmeren"
            print(s[0:3], s[3:7])
            print(s[:4], s[8:])
            print(s[::2])
            print(s[::-1])
            """,
        ),
        les(
            "Een string doorlopen",
            """
            Twee manieren (cursus 10.4.2):
            - `for c in s:` als je alleen de tekens nodig hebt
            - `for i in range(len(s)):` of een while loop als je ook de **index**
              nodig hebt, bijvoorbeeld om twee strings te vergelijken
            """,
            """
            s = "banaan"
            for i in range(len(s)):
                if s[i] in "aeiou":
                    print(i, s[i])
            """,
        ),
        les(
            "Strings zijn onveranderbaar",
            """
            Je kan geen teken in een string vervangen: `s[0] = "H"` geeft een
            **TypeError** (cursus 10.5). Je maakt altijd een **nieuwe** string,
            bijvoorbeeld met slices en `+`.
            """,
            """
            s = "hallo"
            s = "H" + s[1:]
            print(s)
            """,
        ),
        les(
            "String methodes",
            """
            Methodes roep je aan met een punt: `s.upper()`. Ze geven een **nieuwe**
            string terug (cursus 10.6):
            - `strip()` haalt spaties vooraan en achteraan weg
            - `upper()`, `lower()` alles in hoofdletters of kleine letters
            - `find(x)` de index waar x begint, of **-1** als x er niet in zit
            - `replace(oud, nieuw)` vervangt **alle** keren oud door nieuw
            - `split()` knipt de string in een list van woorden
            - `"-".join(lst)` plakt een list van strings aan elkaar, met `-` ertussen
            """,
            """
            t = "  Hallo Wereld  "
            print(t.strip().upper())
            print("Hallo".find("l"), "Hallo".find("z"))
            print("1,4,8".split(","))
            print("-".join(["a", "b", "c"]))
            """,
        ),
        les(
            "Tekens zijn getallen: ord en chr",
            """
            Elk teken heeft een code (cursus 10.7, ASCII en UTF-8).
            `ord("A")` geeft de code (65), `chr(66)` geeft het teken (`"B"`).
            De letters van het alfabet hebben opeenvolgende codes, dus
            `chr(ord("a") + 1)` is `"b"`.
            """,
            """
            print(ord("A"), ord("a"))
            print(chr(66), chr(ord("a") + 2))
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            s = "Python"
            print(s[0], s[-1], s[1:4])
            """,
            "Index 0 is `P`, -1 is `n`. `s[1:4]` geeft index 1, 2 en 3: `yth`.",
        ),
        voorspel(
            """
            s = "programmeren"
            print(s[:3], s[3:6])
            print(s[::-1])
            """,
            "De eerste drie tekens, dan index 3 tot 5. `[::-1]` draait de string om.",
        ),
        voorspel(
            """
            t = "  Hallo Wereld  "
            print(t.strip())
            print(t.strip().lower())
            print("Hallo".find("l"), "Hallo".find("z"))
            """,
            "`find` geeft de **eerste** index (2). Zit het er niet in, dan -1.",
        ),
        voorspel(
            """
            zin = "ik heb zo'n honger"
            woorden = zin.split()
            print(len(woorden))
            print("-".join(woorden))
            """,
            "`split()` knipt op spaties: 4 woorden. `join` plakt ze terug, met `-` ertussen.",
        ),
        voorspel(
            """
            print("rabarbar".replace("bar", "ber"))
            """,
            """
            `replace` vervangt **alle** keren `bar`: ra-**bar**-**bar** wordt ra-**ber**-**ber**.
            Dus `raberber`, niet `rabarber`!
            """,
        ),
        voorspel(
            """
            s = "banaan"
            for i in range(len(s)):
                if s[i] in "aeiou":
                    print(i, end=" ")
            """,
            "De klinkers staan op index 1, 3 en 4.",
            boek="Opgave in 10.4.2",
        ),
        voorspel(
            """
            print(ord("A"), chr(ord("A") + 2))
            print("A" < "a", "Zeb" < "an")
            """,
            """
            `ord("A")` is 65, plus 2 geeft 67, dat is `C`. Hoofdletters hebben **kleinere** codes
            dan kleine letters, daarom is `"Zeb" < "an"` waar.
            """,
        ),
        fout(
            "Dit programma moet `Hallo` tonen. Op welke regel loopt het mis?",
            """
            s = "hallo"
            s[0] = "H"
            print(s)
            """,
            2,
            """
            s = "hallo"
            s = "H" + s[1:]
            print(s)
            """,
            "Strings zijn **onveranderbaar**: je kan geen teken vervangen (TypeError). Maak een nieuwe string.",
        ),
        aanvullen(
            "Vul aan zodat de tekst getoond wordt tot (niet met) het hekje `#`.",
            """
            tekst = "Niemand verwacht de Spaanse Inquisitie!# In feite..."
            print(tekst[:tekst.___("#")])
            """,
            [["find", "index"]],
            "`find(\"#\")` geeft de index van het hekje. De slice stopt net ervoor.",
            boek="Opgave in 10.6.7",
        ),
        schrijf(
            """
            In de variabele `tekst` is het woord "rabarber" verkeerd gespeld als "rabarbar".
            Verbeter alle keren met `replace()` en toon de verbeterde tekst.
            """,
            f"""
            tekst = "{BARBARA}"
            print(tekst.replace("rabarbar", "rabarber"))
            """,
            "`replace` vervangt alle keren dat `rabarbar` voorkomt, ook midden in een lang woord.",
            ptests=[([], BARBARA.replace("rabarbar", "rabarber"))],
            start=f'tekst = "{BARBARA}"',
            boek="Opgave in 10.6.7",
        ),
        schrijf(
            """
            Schrijf een functie `tel_klinkers(s)` die teruggeeft hoeveel klinkers (a, e, i, o, u)
            er in s staan. Hoofdletters tellen ook: `tel_klinkers("Appel")` geeft 2.
            """,
            """
            def tel_klinkers(s):
                aantal = 0
                for c in s.lower():
                    if c in "aeiou":
                        aantal += 1
                return aantal
            """,
            "Met `lower()` hoef je maar op kleine letters te testen.",
            tests=[("tel_klinkers('Appel')", 2), ("tel_klinkers('xyz')", 0), ("tel_klinkers('AEIOU aeiou')", 10)],
            start="def tel_klinkers(s):",
            boek="Opgave 10.1",
        ),
        schrijf(
            """
            Schrijf een functie `alleen_letters(s)` die een **nieuwe** string teruggeeft waarin
            elk teken dat geen letter is, vervangen is door een spatie.
            `alleen_letters("ph@t l00t")` geeft `"ph t l  t"`.
            """,
            """
            def alleen_letters(s):
                nieuw = ""
                for c in s:
                    if c.isalpha():
                        nieuw += c
                    else:
                        nieuw += " "
                return nieuw
            """,
            """
            Je bouwt een nieuwe string op met `+=`. `c.isalpha()` is True voor een letter;
            zonder die methode kan het ook met `"a" <= c.lower() <= "z"`.
            """,
            tests=[("alleen_letters('ph@t l00t')", "ph t l  t"), ("alleen_letters('abc')", "abc"),
                   ("alleen_letters('1+1')", "   ")],
            start="def alleen_letters(s):",
            boek="Opgave in 10.4.2",
        ),
        schrijf(
            """
            Schrijf een functie `is_palindroom(s)` die True teruggeeft als s hetzelfde is van voor
            naar achter als van achter naar voor. Hoofdletters tellen niet mee:
            `is_palindroom("Lepel")` geeft True.
            """,
            """
            def is_palindroom(s):
                s = s.lower()
                return s == s[::-1]
            """,
            "Met `[::-1]` draai je de string om. Kan ook met een loop die de tekens van voor en achter vergelijkt.",
            tests=[("is_palindroom('Lepel')", True), ("is_palindroom('kayak')", True),
                   ("is_palindroom('python')", False), ("is_palindroom('')", True)],
            start="def is_palindroom(s):",
        ),
        schrijf(
            """
            Twee strings, `a = "The Holy Grail"` en `b = "Life of Brian"`. Toon voor elke index
            waar **beide** strings hetzelfde teken hebben, de index en het teken (bv. `11 a`).
            Pas op dat je niet voorbij het einde van de kortste string gaat.
            """,
            """
            a = "The Holy Grail"
            b = "Life of Brian"
            for i in range(min(len(a), len(b))):
                if a[i] == b[i]:
                    print(i, a[i])
            """,
            "Loop tot de lengte van de **kortste** string, anders krijg je een IndexError.",
            ptests=[([], "\n".join(f"{i} {x}" for i, (x, y) in enumerate(zip("The Holy Grail", "Life of Brian")) if x == y))],
            start='a = "The Holy Grail"\nb = "Life of Brian"',
            boek="Opgave in 10.4.2",
            uitdaging=True,
        ),
    ],
}
