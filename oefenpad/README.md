# Oefenpad met Google Sheets en Apps Script

Eén spreadsheet met de gegevens, één Apps Script-project met de logica en de pagina's. Geen server, geen database, geen installatie.

**Status:** de code is geschreven maar nog niet getest. Test eerst met een kopie van het bestand, niet met echte leerlingen.

## Bestanden

| Bestand | Wat het doet |
|---|---|
| `Code.gs` | Server: inloggen, voortgang, controle, beheer, jaarwissel |
| `Modules.gs` | Oefeningen van de modules (tweedegraad en topvorm, met theorie en een voorbeeld) en de controle van antwoorden |
| `Oefenpad.html` | Eén pagina voor leerlingen en leerkrachten, met de keuze "Ik ben leerling" of "Ik ben leerkracht" |
| `appsscript.json` | Instellingen: tijdzone Brussel, webapp voor iedereen met de link |

## Instellen (eenmalig)

1. **Maak een spreadsheet** aan in de Google-account van de leerkracht (of de schoolaccount). Noem hem bv. "Oefenpad hoofdstuk 2".
2. **Open Extensies > Apps Script.** Verwijder de standaardcode in `Code.gs`.
3. **Maak de bestanden aan** in het Apps Script-project: `Code.gs` en `Modules.gs` als script-bestanden, `Oefenpad.html` als HTML-bestand met de naam `Oefenpad` (zonder `.html`). Verwijder eventuele oude `Leerling`- en `Leerkracht`-bestanden. Plak de inhoud erin. Bij `appsscript.json`: open Project-instellingen en zet "Toon het manifestbestand" aan, en vervang de inhoud.
4. **Maak de tabbladen aan.** Kies in de editor de functie `setupSheets` en klik op Uitvoeren. Keur de rechten goed. Heb je deze spreadsheet al eerder met een oudere versie gebruikt? Verwijder dan de tabbladen eerst, want de kolommen zijn veranderd.
5. **Maak de leerkrachten aan (beheerder).** Open in `Code.gs` de functie `voorbeeldLeerkracht`, pas de gebruikersnaam en een tijdelijk wachtwoord van minstens 8 tekens aan, kies de functie in de editor en klik op Uitvoeren. Verwijder daarna het wachtwoord uit de code. Herhaal dit voor elke leerkracht met `voegLeerkrachtToe_('juf.els', 'tijdelijk-wachtwoord')` in een nieuwe functie. Bij de eerste login moet de leerkracht zelf een wachtwoord kiezen. Elke leerkracht ziet alleen eigen klassen.
   - **Wachtwoord vergeten:** de leerkracht vraagt het bij jou (de beheerder). Jij voert dan `herstelWachtwoord_('juf.els', 'nieuw-tijdelijk-wachtwoord')` uit in de editor, met een nieuw tijdelijk wachtwoord. Bij de volgende login moet ze weer een eigen wachtwoord kiezen.
   - Het tijdelijke wachtwoord is zichtbaar in de editor-geschiedenis. Geef het alleen persoonlijk door en gebruik het niet twee keer.
6. **Zet de jaarwissel aan.** Kies `installeerJaarwissel` en klik op Uitvoeren. Dat maakt een dagelijkse controle die alleen op 1 september alle leerlinggegevens wist. De leerkrachtaccounts blijven bestaan.
7. **Publiceer als webapp.** Klik op Implementeren > Nieuwe implementatie > Type: Webapp. Kies:
   - Uitvoeren als: **Ik** (de leerkracht)
   - Wie heeft toegang: **Iedereen**
   Kopieer de URL. Dat is de ene link voor iedereen. Leerlingen kiezen "Ik ben leerling", leerkrachten kiezen "Ik ben leerkracht".

## Testen (vóór gebruik)

- Open de link en kies "Ik ben leerkracht". Log in met je gebruikersnaam en wachtwoord, voeg een klas toe, voeg een leerling toe.
- Maak een tweede leerkracht aan en controleer dat die de klassen van de eerste niet ziet.
- Open de link en kies "Ik ben leerling". Log in als leerling. Los de eerste stap op. Controleer dat de volgende stap pas daarna opent.
- Doe een foute poging. Controleer dat de hint verschijnt.
- Vul vijf foute codes in: de zesde keer moet geweigerd worden.
- Voeg een leerling toe. Log in als die leerling: er verschijnt een herhaalveld. Kies een code, herhaal hem, en controleer dat de aanmelding lukt. Log daarna uit en probeer met een andere code: dat moet geweigerd worden.
- Probeer in te loggen met de naam van een klasgenoot en de code van de eerste leerling: dat moet geweigerd worden.
- Zet in het dashboard de code van een leerling terug met "Code resetten". Controleer dat de pincode-status "nog geen" wordt en dat de leerling opnieuw een code kiest.
- Controleer in het dashboard de voortgang, de tijd, en de veelgemaakte fouten.
- Oefen een stap met twee velden (topvorm, nulpunten) met één goed en één fout antwoord: de pagina moet "deels juist" tonen, en het dashboard moet die stap als deels juist (oranje) zetten.
- Laat de leerling een paar minuten actief oefenen: de weekbalk moet stijgen. Laat de pagina twee minuten stil staan en controleer dat de tijd daarna niet verder oploopt.
- Test de jaarwissel: zet in de editor tijdelijk de datum-controle in `jaarwissel` uit (of voer `wisAlles_` uit) en controleer dat de gegevens verdwijnen. Herstel daarna de controle.

## Werking (afgestemd op de werkwoordentrainer)

- **Actieve tijd:** de pagina telt alleen de seconden waarin de leerling iets doet (toetsen, klikken). Na een minuut stilte telt het niet meer. Dat maakt de minuten in het dashboard eerlijk. Het weekdoel staat in `WEEKDOEL_MIN` in `Code.gs` (standaard 30 minuten).
- **Deels juist:** bij een stap met meerdere velden krijgt de leerling 0,5 als een deel klopt. Die poging staat als "deels juist" in het dashboard. De leerling moet de stap volledig juist maken om verder te gaan.
- **Oefeningen:** komen uit "H2 lln van Geert". Tweedegraad: 15 oefeningen (2.2, 2.4 en 2.6, zonder de eerstegraadsvragen). Topvorm: 15 oefeningen. De eerste 9 komen uit de PDF (voorbeeld en 2.3, 2.5, 2.7). De laatste 6 (p10 t/m p15) staan niet in het boek; ze zijn extra toegevoegd in dezelfde stijl. Bij een tweedegraadsoefening zonder oplossing wordt de stap "oplossingen" overgeslagen. Bij de topvorm wordt de stap "nulpunten" overgeslagen als die er niet zijn.
- **Testdata:** deze oefeningen hebben andere codes dan de vorige versie. Wis daarom eerst de testdata met "Alles wissen", voordat je de link aan leerlingen geeft.
- **Tempo:** na een juist antwoord kiest de leerling zelf "Volgende stap" of drukt op Enter. Er gaat niets vanzelf verder.
- **Dashboard:** de stippen per leerling tonen per stap of die klaar is, deels juist, fout of nog niet begonnen. Het tabblad "Veelgemaakte fouten" toont de meest gegeven foute antwoorden per stap.

## Let op

- **Gratis Google-account:** Apps Script heeft dagelijkse quota, bv. voor het aantal verzoeken en de looptijd. Voor één klas is dat in de praktijk ruim genoeg, maar controleer het als het traag wordt.
- **Pincodes:** elke leerling kiest zelf een code van 4 cijfers bij de eerste aanmelding (twee keer typen). De code wordt gehasht met SHA-256 en een willekeurig zout, en de leerkracht kent hem niet. Daardoor kan een leerling niet onder de naam van een klasgenoot oefenen, zonder diens code. Let op: wie als eerste inlogt op een nieuwe naam, stelt de code in. Laat de eerste aanmelding daarom in de klas gebeuren, onder toezicht. Met "Code resetten" zet je de code terug naar leeg. Met 10.000 mogelijke codes kan iemand met toegang tot de spreadsheet de hashes toch proberen te kraken. Houd de spreadsheet daarom privé.
- **Spreadsheet is gevoelig:** iedereen die de spreadsheet kan openen, ziet namen en resultaten. Deel hem niet. De webapp zelf toont die gegevens niet.
- **Wachtwoorden:** leerkrachtwachtwoorden worden gehasht opgeslagen, net als de codes. Verwijder het wachtwoord uit `voorbeeldLeerkracht` zodra het is uitgevoerd. Gebruik sterke wachtwoorden.
- **Nieuwe leerkracht:** alleen jij als eigenaar van het project kunt leerkrachten toevoegen, via de editor. Er is geen zelfregistratie.
- **Wissen door een leerkracht:** de wisknop van een leerkracht verwijdert alleen haar eigen klassen. Alleen de jaarwissel wist alles.
- **Gegevens en privacy:** dezelfde regels gelden als bij het eerdere platform. Vraag de ICT-coördinator of de DPO na of Google Workspace hiervoor is goedgekeurd.
- **Nieuwe module:** voeg de oefeningen toe aan `MODULES` in `Modules.gs`, en voeg een keuze toe aan de fouten-selectie in `Leerkracht.html`.
