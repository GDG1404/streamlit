# Python op papier

Een oefenapp voor het vak *computationeel denken* (eerste jaar industrieel
ingenieur). Het examen is op papier, dus de app traint vooral:

- **code lezen**: wat print dit, wat doet dit programma, waar zit de fout;
- **code schrijven op papier**: eerst op papier, dan overtypen en laten controleren;
- **de spiekbrief gebruiken**: elk vak van de *Python 3 Mémento* (Laurent Pointal)
  uitgelegd in gewone taal, met wat je moet kennen en wat je mag overslaan.

De niveaus volgen het cursusboek **De Programmeursleerling: Leren coderen met
Python 3** van Pieter Spronck, met dezelfde volgorde en dezelfde woorden
(loop, list, conditie, retourwaarde, ...).

## Inhoud

| Niveau | Onderwerp | Cursus |
|---|---|---|
| 0 | Expressies en variabelen: `print`, data types, `=`, commentaar | H3–4 |
| 1 | Rekenen: `+ - * / // % **`, floats, `math` | H3–5 |
| 2 | Eenvoudige functies: type casting, `input`, `len`, `max`, `format`, `random`, pcinput | H5 |
| 3 | Condities: `if`, `elif`, `else`, `and`, `or`, `in`, geneste condities | H6 |
| 4 | `while` loop, eindeloze loops, de loop-en-een-half | H7.1, 7.5 |
| 5 | `for` loop, `range`, `break`, `continue`, `else`, geneste loops, algoritmes | H7.2–7.7 |
| 6 | Functies: `def`, `return`, default waardes, meerdere retourwaardes, scope, `lambda` | H8 |
| 7 | Recursie | H9 |
| 8 | Strings: index, slices, methodes, `ord`/`chr` | H10 |
| 9 | Tuples | H11 |
| 10 | Lists: methodes, alias, geneste lists, list comprehensions | H12 |
| 11 | Dictionaries | H13 |
| 12 | Sets | H14 |
| 13 | Tekstbestanden: `open`, `read`, `readline`, `write`, `with` | H15–16 |
| 14 | Exceptions: `try`, `except`, `else`, `finally`, `raise` | H17 |
| later | Binaire bestanden en bits, objecten en klassen, iteratoren, extra modules, examentraining | H18–27 |

Per niveau: uitlegkaarten met voorbeelden en oefeningen van zes soorten
(wat print dit, meerkeuze, wat doet dit programma, zoek de fout, vul aan,
schrijf op papier). Oefeningen die uit het boek komen, tonen het nummer van
de opgave ("uit je cursus: Opgave 7.10"). Elk stuk code kan je **stap voor
stap** volgen, ook als variabelentabel zoals je die op papier maakt, en bij
recursie zie je elke aanroep apart.

## Hoe het gebouwd is

```
content/     de inhoud: één Python-bestand per niveau, plus spiekbrief en instaptest
template/    de app (HTML, CSS, JavaScript), runner.py (draait in de browser)
             en nepbestanden.py (tekstbestanden in het geheugen)
build.py     voert alle code uit met echte Python en maakt dist/
dist/        het resultaat: één HTML-bestand
```

`python3 build.py` doet het volgende:

1. Het voert elk voorbeeld en elke oefening uit met echte Python. Zo zijn de
   uitvoer en de stap-voor-stap-weergave altijd juist.
2. Het controleert dat elke modeloplossing slaagt voor haar tests, dat elke
   *vul aan* met het eerste antwoord werkt, en dat meerkeuze-antwoorden over
   uitvoer kloppen. Is er iets mis, dan stopt het met een foutmelding.
3. Het schrijft `dist/python-op-papier.html` (voor de Claude-artifactpagina) en
   `dist/index.html` (een volledig HTML-bestand dat je ook gewoon kan openen).

In de browser draait Python via [Brython](https://brython.info) in een Web
Worker (voor het kladblok en het controleren van schrijfopdrachten). Een
eindeloze loop wordt na 5 seconden afgebroken. Werkt Python niet op een toestel,
dan blijft de rest van de app werken: alle antwoorden en stappen zitten al in
de pagina.

Oefeningen met tekstbestanden gebruiken bestanden die alleen in het geheugen
bestaan (`template/nepbestanden.py`). Dezelfde code draait in de build en in
de browser, zodat `open()`, `read()`, `readline()`, `write()` en `with` overal
hetzelfde werken.

## Voortgang

De voortgang wordt in de browser bewaard. Op de Claude-artifactpagina wordt ze
ook gedeeld bewaard: dan kan de eigenaar van de pagina onder **Voortgang** zien
hoe ver iedereen staat. Op elk toestel kan je onder **Voortgang** een
tekstoverzicht kopiëren om door te sturen.

Een oefening heeft als id `<niveau>-<nummer>` (bijvoorbeeld `lists-3`). Voeg
nieuwe oefeningen daarom **achteraan** een niveau toe, dan blijft de voortgang
van de bestaande oefeningen kloppen. `content/oude_ids.json` zet de voortgang
van de eerste versie van de app (ids `0-1` tot `7-15`) om.

## Een oefening toevoegen

Open het juiste bestand in `content/` en voeg achteraan een oefening toe, bijvoorbeeld:

```python
voorspel(
    """
    x = 3
    print(x * 2)
    """,
    "Uitleg die na het antwoord verschijnt.",
    boek="Opgave 3.1",          # optioneel: verwijzing naar het cursusboek
),
```

Draai daarna `python3 build.py`. De juiste uitvoer berekent het script zelf.

## Bronnen

- *De Programmeursleerling: Leren coderen met Python 3*, Pieter Spronck, versie 1.0.16
  (2017), gepubliceerd onder Creative Commons BY-NC 3.0. Een aantal opgaves en
  de tekst van `pc_rose.txt` zijn daaruit overgenomen of aangepast.
- *Python 3 Cheat Sheet (Mémento)*, Laurent Pointal, Creative Commons BY 4.0.
