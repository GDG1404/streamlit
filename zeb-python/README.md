# Python op papier

Een oefenapp voor het vak *computationeel denken* (eerste jaar industrieel
ingenieur). Het examen is op papier, dus de app traint vooral:

- **code lezen**: wat print dit, wat doet dit programma, waar zit de fout;
- **code schrijven op papier**: eerst op papier, dan overtypen en laten controleren;
- **de spiekbrief gebruiken**: elk vak van de *Python 3 Mémento* (Laurent Pointal)
  uitgelegd in gewone taal, met wat je moet kennen en wat je mag overslaan.

## Inhoud

| Niveau | Onderwerp | Spiekbrief |
|---|---|---|
| 0 | Eerste stappen: variabelen en print | Base Types, Variables assignment, Display, Identifiers |
| 1 | Rekenen: `+ - * / // % **`, math | Maths |
| 2 | Tekst en invoer: `str`, `input`, omzetten | Input, Conversions |
| 3 | Beslissen: `if`, `elif`, `else`, `and`, `or` | Boolean Logic, Conditional Statement, Statements Blocks |
| 4 | Herhalen met `while` | Conditional Loop Statement |
| 5 | Herhalen met `for` en `range` | Iterative Loop Statement, Integer Sequences, Loop Control |
| 6 | Lijsten: index, `append`, slices | Sequence Containers Indexing, Operations on Lists, Generic Operations |
| 7 | Functies: `def`, `return` | Function Definition, Function Call |
| 8–12 | Algoritmen, tekst bewerken, dict, bestanden, examentraining | *komt later* |

Per niveau: uitlegkaarten met voorbeelden en oefeningen van zes soorten
(wat print dit, meerkeuze, wat doet dit programma, zoek de fout, vul aan,
schrijf op papier). Elk stuk code kan je **stap voor stap** volgen, ook als
variabelentabel zoals je die op papier maakt.

## Hoe het gebouwd is

```
content/     de inhoud (Python-bestanden, één per niveau + spiekbrief + instaptest)
template/    de app (HTML, CSS, JavaScript) en runner.py (draait in de browser)
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
oneindige lus wordt na 5 seconden afgebroken. Werkt Python niet op een toestel,
dan blijft de rest van de app werken: alle antwoorden en stappen zitten al in
de pagina.

## Voortgang

De voortgang wordt in de browser bewaard. Op de Claude-artifactpagina wordt ze
ook gedeeld bewaard: dan kan de eigenaar van de pagina onder **Voortgang** zien
hoe ver iedereen staat. Op elk toestel kan je onder **Voortgang** een
tekstoverzicht kopiëren om door te sturen.

## Een oefening toevoegen

Open het juiste bestand in `content/` en voeg een regel toe, bijvoorbeeld:

```python
voorspel(
    """
    x = 3
    print(x * 2)
    """,
    "Uitleg die na het antwoord verschijnt.",
),
```

Draai daarna `python3 build.py`. De juiste uitvoer berekent het script zelf.
