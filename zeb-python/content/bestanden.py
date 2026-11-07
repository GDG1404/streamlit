from helpers import les, voorspel, keuze, fout, aanvullen, schrijf

# Uit bijlage E van het cursusboek (pc_rose.txt, eerste regels).
ROSE = (
    "Het is slechts je naam die mijn vijand is;\n"
    "Jij bent wie je bent, jezelf, niet een Montague.\n"
    "Wat is een Montague? Is het een hand, een voet,\n"
    "een arm, een gezicht, of enig ander deel\n"
    "behorend aan een man? O, had je maar een andere naam!\n"
    "Wat betekent een naam? Dat wat wij een roos noemen\n"
)
GETALLEN = "3\n8\n5\n"
KORT = "een\ntwee\n"
ROSE_BESTAND = {"pc_rose.txt": ROSE}

NIVEAU = {
    "key": "bestanden",
    "titel": "Tekstbestanden",
    "kort": "open, read, readline, write",
    "hoofdstuk": "15 en 16",
    "spiek": ["files"],
    "doel": "Je kan een tekstbestand openen, lezen (alles, per regel), schrijven en sluiten.",
    "uitleg": [
        les(
            "Een bestand openen, lezen en sluiten",
            """
            Werken met een tekstbestand gebeurt altijd in drie stappen (cursus 16.2):
            1. **openen**: `fp = open("pc_rose.txt")` geeft een *handle* (hier `fp`)
            2. **lezen** of **schrijven** via die handle
            3. **sluiten**: `fp.close()`

            `fp.read()` leest het **hele** bestand in één string.
            Bestaat het bestand niet, dan krijg je een **FileNotFoundError**.

            In deze app bestaan de bestanden alleen in het geheugen. Bij elke
            oefening zie je wat erin staat.
            """,
            """
            fp = open("pc_rose.txt")
            inhoud = fp.read()
            fp.close()
            print(inhoud)
            """,
            bestanden=ROSE_BESTAND,
        ),
        les(
            "Regel per regel lezen",
            """
            Drie manieren om per regel te lezen (cursus 16.2.5 en 16.2.6):
            - `fp.readline()` leest **één** regel; aan het einde van het bestand
              geeft het een lege string `""`
            - `fp.readlines()` geeft een **list** met alle regels
            - `for regel in fp:` loopt over de regels

            **Let op:** elke regel eindigt met een `\\n`. Print je de regel, dan
            komt er nog een nieuwe regel bij. Daarom gebruik je vaak `regel.strip()`.
            """,
            """
            fp = open("pc_rose.txt")
            while True:
                regel = fp.readline()
                if regel == "":
                    break
                print(regel.strip())
            fp.close()
            """,
            bestanden=ROSE_BESTAND,
        ),
        les(
            "with: automatisch sluiten",
            """
            Met `with open(...) as fp:` wordt het bestand **vanzelf gesloten** aan het
            einde van het blok, ook als er een fout gebeurt (cursus 16.2.1).
            Dit staat ook op je spiekbrief, onderaan rechts.
            """,
            """
            aantal = 0
            with open("pc_rose.txt") as fp:
                for regel in fp:
                    if "naam" in regel:
                        aantal += 1
            print(aantal, "regels met 'naam'")
            """,
            bestanden=ROSE_BESTAND,
        ),
        les(
            "Schrijven en toevoegen",
            """
            Om te schrijven open je met een **mode** (cursus 16.3 en 16.4):
            - `open("uit.txt", "w")`: schrijven. Een bestaand bestand wordt **leeggemaakt**!
            - `open("uit.txt", "a")`: toevoegen (*append*) aan het einde

            `fp.write(tekst)` schrijft tekst, maar **geen** nieuwe regel: die moet je
            zelf toevoegen met `\\n`. `fp.writelines(lst)` schrijft een list van strings.
            """,
            """
            fp = open("uit.txt", "w")
            fp.write("eerste regel\\n")
            fp.write("tweede ")
            fp.write("regel\\n")
            fp.close()
            fp = open("uit.txt", "a")
            fp.write("derde regel\\n")
            fp.close()
            fp = open("uit.txt")
            print(fp.read())
            fp.close()
            """,
        ),
        les(
            "Mappen en os.path",
            """
            Hoofdstuk 15 en 16.5 van je cursus gaan over het **bestandssysteem**:
            mappen (*directories*), paden en de module `os.path`:
            - `os.path.exists(pad)`: bestaat het bestand of de map?
            - `os.path.isfile(pad)`, `os.path.isdir(pad)`
            - `os.path.join("map", "bestand.txt")`: een pad samenstellen
            - `os.path.getsize(pad)`: de grootte in bytes

            Op papier moet je die vooral **herkennen**. In deze app oefen je enkel
            met bestanden, niet met mappen.
            """,
        ),
    ],
    "oefeningen": [
        voorspel(
            """
            fp = open("getallen.txt")
            totaal = 0
            for regel in fp:
                totaal += int(regel)
            fp.close()
            print(totaal)
            """,
            "Elke regel is een string zoals `\"3\\n\"`. `int()` negeert de `\\n` en zet ze om. 3 + 8 + 5 = 16.",
            bestanden={"getallen.txt": GETALLEN},
        ),
        voorspel(
            """
            fp = open("pc_rose.txt")
            r1 = fp.readline()
            r2 = fp.readline()
            fp.close()
            print(r2.strip())
            """,
            "Elke `readline()` leest de **volgende** regel. r2 is dus de tweede regel.",
            bestanden=ROSE_BESTAND,
        ),
        keuze(
            "Waarom staat er een **lege regel** na elk woord in de uitvoer?",
            [
                "Het bestand bevat lege regels",
                "Elke regel eindigt met \\n, en print voegt nog een nieuwe regel toe",
                "readline() voegt een spatie toe",
                "Dat is een fout in Python",
            ],
            1,
            "De regel `\"een\\n\"` eindigt al met een nieuwe regel, en `print` zet er nog één achter. Met `print(regel.strip())` of `print(regel, end=\"\")` verdwijnen de lege regels.",
            code="""
            fp = open("kort.txt")
            for regel in fp:
                print(regel)
            fp.close()
            """,
            bestanden={"kort.txt": KORT},
        ),
        voorspel(
            """
            fp = open("test.txt", "w")
            fp.write("hallo")
            fp.write("wereld\\n")
            fp.write("tot ziens\\n")
            fp.close()
            fp = open("test.txt")
            print(fp.read())
            fp.close()
            """,
            "`write` zet geen nieuwe regel achter de tekst: `hallo` en `wereld` komen dus aan elkaar.",
        ),
        voorspel(
            """
            fp = open("log.txt", "w")
            fp.write("A\\n")
            fp.close()
            fp = open("log.txt", "a")
            fp.write("B\\n")
            fp.close()
            fp = open("log.txt", "w")
            fp.write("C\\n")
            fp.close()
            fp = open("log.txt")
            print(fp.read())
            fp.close()
            """,
            "Mode `\"a\"` voegt B toe na A. Maar daarna opent mode `\"w\"` het bestand opnieuw: het wordt **leeggemaakt**, en enkel C blijft over.",
        ),
        keuze(
            "Het bestand `cijfers.txt` bestaat niet. Wat gebeurt er?",
            ["Er wordt een leeg bestand gemaakt", "Een fout: FileNotFoundError", "Het toont een lege string",
             "Het toont None"],
            1,
            "In leesmode moet het bestand bestaan. (In schrijfmode `\"w\"` wordt het wel aangemaakt.)",
            code="""
            fp = open("cijfers.txt")
            print(fp.read())
            """,
        ),
        fout(
            "Dit programma moet de som van de getallen in het bestand tonen. Op welke regel loopt het mis?",
            """
            fp = open("getallen.txt")
            totaal = 0
            for regel in fp:
                totaal += regel
            fp.close()
            print(totaal)
            """,
            4,
            """
            fp = open("getallen.txt")
            totaal = 0
            for regel in fp:
                totaal += int(regel)
            fp.close()
            print(totaal)
            """,
            "Uit een tekstbestand lees je altijd **strings**. Zet ze om met `int()` voor je optelt.",
            bestanden={"getallen.txt": GETALLEN},
        ),
        aanvullen(
            "Vul aan zodat het bestand automatisch gesloten wordt.",
            """
            ___ open("pc_rose.txt") ___ fp:
                print(fp.readline().strip())
            """,
            [["with"], ["as"]],
            "`with open(...) as fp:` sluit het bestand vanzelf aan het einde van het blok.",
            bestanden=ROSE_BESTAND,
        ),
        schrijf(
            """
            Toon van het bestand `pc_rose.txt` enkel de regels die het woord `naam` bevatten,
            zonder lege regels ertussen.
            """,
            """
            fp = open("pc_rose.txt")
            for regel in fp:
                if "naam" in regel:
                    print(regel.strip())
            fp.close()
            """,
            "`in` test of het woord in de regel staat. `strip()` haalt de `\\n` weg.",
            ptests=[([], "\n".join(r for r in ROSE.splitlines() if "naam" in r))],
            bestanden=ROSE_BESTAND,
            boek="Opgave in 16.2.5",
        ),
        schrijf(
            """
            Schrijf een functie `som_bestand(naam)` die het bestand met die naam opent, op elke
            regel één geheel getal leest, en de som teruggeeft.
            Het bestand `getallen.txt` bevat 3, 8 en 5 (elk op een regel).
            """,
            """
            def som_bestand(naam):
                totaal = 0
                fp = open(naam)
                for regel in fp:
                    totaal += int(regel)
                fp.close()
                return totaal
            """,
            "Openen, lezen in een loop, sluiten, en dan pas `return`.",
            tests=[("som_bestand('getallen.txt')", 16), ("som_bestand('leeg.txt')", 0)],
            start="def som_bestand(naam):",
            bestanden={"getallen.txt": GETALLEN, "leeg.txt": ""},
        ),
        schrijf(
            """
            Lees `pc_rose.txt`, zet elke regel **achterstevoren** en schrijf de omgekeerde regels
            naar het bestand `omgekeerd.txt` (elk op een eigen regel). Open daarna `omgekeerd.txt`
            en toon de inhoud.
            """,
            """
            fp = open("pc_rose.txt")
            regels = fp.readlines()
            fp.close()
            uit = open("omgekeerd.txt", "w")
            for regel in regels:
                uit.write(regel.strip()[::-1] + "\\n")
            uit.close()
            fp = open("omgekeerd.txt")
            print(fp.read())
            fp.close()
            """,
            """
            Haal eerst de `\\n` weg met `strip()`, draai dan om met `[::-1]`, en zet er zelf
            een nieuwe `\\n` achter bij het schrijven.
            """,
            ptests=[([], "\n".join(r[::-1] for r in ROSE.splitlines()))],
            bestanden=ROSE_BESTAND,
            boek="Opgave in 16.3.4",
            uitdaging=True,
        ),
    ],
}
