# 家計簿 Kakebo — het huishoudboekje van Geert & Mart

Een Kakebo-budgetplanner die draait op **Google Sheets**, met een eigen **app voor de telefoon**.
Alles in het Nederlands en in euro. Jullie gegevens blijven in jullie eigen Google Drive.

## Wat krijg je?

**In de Google Sheet** (alles wordt automatisch opgebouwd):

| Tabblad | Wat staat erin |
|---|---|
| **Overzicht** | Dashboard per maand, opgebouwd rond de vier Kakebo-vragen: inkomen, sparen, uitgaven en resultaat. Met een voortgangsbalk van het budget, totalen per categorie, per week (met grafiek) en per persoon, en jullie reflectie. Kies bovenaan een andere maand. |
| **Uitgaven** | Het logboek: datum, wie, categorie, omschrijving en bedrag, met keuzelijstjes en kleuren. |
| **Maanden** | Per maand: inkomen van Geert, inkomen van Mart, overig inkomen, vaste lasten en spaardoel. Daaruit volgen het budget, wat uitgegeven is en wat gespaard is. Plus de reflectie. |
| **Vaste lasten** | Huur, energie, verzekeringen enzovoort. Het totaal telt vanzelf mee in de lopende maand. |
| **Instellingen** | Jullie namen, de link naar de app en een korte uitleg van de methode. |

**De app** (op je telefoon, of in de sheet via het menu *家計簿 Kakebo › Uitgave toevoegen*):

- **Nieuw**: bedrag, categorie (Overleven, Optioneel, Cultuur, Extra), omschrijving, datum en wie betaalde.
- **Overzicht**: hoeveel er nog te besteden is, ongeveer hoeveel per dag, per categorie, per week en per persoon, en de lijst met uitgaven (tik erop om te bewerken of te verwijderen).
- **Maand**: aan het begin van de maand plannen (inkomen, vaste lasten, spaardoel) en aan het einde terugblikken met de vier vragen.

> **Eerst even proberen?** Open `test/demo.html` in je browser. Dat is de echte app met voorbeeldgegevens, zonder Google-account.

---

## Installeren (eenmalig, ongeveer 10 minuten)

Doe dit op een computer. Geert installeert, Mart hoeft alleen de gedeelde sheet en de link te openen.

### 1. Maak een nieuwe Google Sheet
Ga naar [sheets.new](https://sheets.new) en noem het bestand bijvoorbeeld **Kakebo**.

### 2. Plak het script
1. Kies in de sheet **Extensies › Apps Script**.
2. Je ziet een bestand `Code.gs` met een paar regels code. Selecteer alles (Ctrl+A of Cmd+A) en verwijder het.
3. Open [`Kakebo.gs`](Kakebo.gs) (op GitHub: knop **Copy raw file**), kopieer **alles** en plak het in `Code.gs`.
4. Klik op het diskette-icoon (**Opslaan**). Geef het project gerust de naam *Kakebo*.

### 3. Voer "installeren" uit
1. Kies bovenaan in de lijst met functies **installeren** (die staat er normaal al) en klik op **▶ Uitvoeren**.
2. Google vraagt om toestemming: **Rechten controleren** › kies je account.
3. Je ziet *"Google heeft deze app niet geverifieerd"*. Dat is normaal: het is jullie eigen script.
   Klik op **Geavanceerd** › **Ga naar Kakebo (niet veilig)** › **Toestaan**.
4. Wacht tot onderaan *"Uitvoering voltooid"* staat (ongeveer een halve minuut).
5. Ga terug naar de sheet en **herlaad de pagina**. Het menu **家計簿 Kakebo** verschijnt nu bovenaan.

### 4. Vul de eerste maand in
Open **家計簿 Kakebo › Uitgave toevoegen** en ga in de app naar **Maand**. Vul jullie inkomens, de vaste lasten en
het spaardoel in en klik op **Maand opslaan**. Wat overblijft is jullie budget.

### 5. Maak de app voor de telefoon
1. Ga terug naar **Extensies › Apps Script**.
2. Klik rechtsboven op **Implementeren › Nieuwe implementatie**.
3. Klik op het tandwiel naast *Type selecteren* en kies **Web-app**.
4. Vul in:
   - Beschrijving: *Kakebo*
   - **Uitvoeren als: Gebruiker die de web-app opent** (Engels: *User accessing the web app*)
   - **Wie heeft toegang: Iedereen met een Google-account** (Engels: *Anyone with Google account*)
5. Klik op **Implementeren**, geef opnieuw toestemming en kopieer de **URL van de web-app**.

> Waarom deze instellingen? Zo werkt de app met de rechten van wie hem opent. Alleen wie de sheet mag
> bewerken (jij en Mart) kan er gegevens in zien of toevoegen. Iemand anders met de link ziet een foutmelding.

### 6. Deel met Mart
1. Klik in de sheet op **Delen**, vul het e-mailadres van Mart in en kies **Bewerker**.
2. Stuur Mart de link van de web-app. Of kies in de sheet **家計簿 Kakebo › App op je telefoon**: daar staat een
   QR-code die je met de camera van je telefoon kunt scannen.
3. Mart opent de link één keer, geeft toestemming (zelfde scherm als in stap 3) en kiest in de app **Mart**.

### 7. Op het beginscherm van je telefoon
- **iPhone (Safari)**: open de link › deelknop (vierkantje met pijl) › **Zet op beginscherm**.
- **Android (Chrome)**: open de link › menu (⋮) › **Toevoegen aan startscherm**.

Klaar! Vanaf nu: uitgave doen, app openen, bedrag + categorie, **Bewaren**.

---

## Zo werkt Kakebo

1. **Begin van de maand**: hoeveel geld hebben we, hoeveel gaat er vast uit, hoeveel willen we sparen?
   Wat overblijft is het budget. Een nieuwe maand neemt automatisch de bedragen van de vorige maand over.
2. **Elke dag**: schrijf elke uitgave op en kies een categorie.
   - **Overleven**: boodschappen, vervoer, gezondheid, verzorging
   - **Optioneel**: uit eten, kleding, hobby's, iets leuks voor jezelf
   - **Cultuur**: boeken, film, concerten, musea, cursussen
   - **Extra**: onverwachte kosten zoals reparaties en cadeaus
3. **Elke week**: kijk samen naar *Per week* in het overzicht.
4. **Einde van de maand**: beantwoord in de app (scherm **Maand**) de vierde vraag: *hoe kunnen we het beter doen?*

---

## Vragen en problemen

**Ik zie het menu 家計簿 Kakebo niet.** Herlaad de sheet. Nog steeds niet? Voer in Apps Script opnieuw
*installeren* uit.

**De opmaak is per ongeluk aangepast.** Kies **家計簿 Kakebo › Installeren / opmaak herstellen**. Jullie gegevens
blijven bewaard.

**Namen aanpassen?** Op het tabblad **Instellingen** (cellen C5 en C6). Ze veranderen dan overal mee.

**Kunnen we tegelijk invoeren?** Ja. Het script zorgt ervoor dat er niets door elkaar loopt.

**Een vaste last verandert.** Pas hem aan in de app (scherm *Maand*) of op het tabblad *Vaste lasten*. Dat geldt
voor deze en de volgende maanden. Afgelopen maanden blijven zoals ze waren.

**Ik heb een nieuwe versie van het script geplakt.** Ga in Apps Script naar **Implementeren › Implementaties
beheren**, klik op het potlood, kies bij *Versie* **Nieuwe versie** en klik **Implementeren**. De link blijft
dezelfde.

**Wat ziet het script?** Bij de toestemming vraagt Google om toegang tot je spreadsheets. Het script gebruikt
alleen deze Kakebo-sheet. Er gaat niets naar buiten: alles blijft in jullie Google-account.

---

## Voor wie verder wil knutselen

| Bestand | Inhoud |
|---|---|
| `Kakebo.gs` | Het bestand om te plakken (gebouwd uit `src/`) |
| `src/Code.js` | De serverkant: tabbladen opbouwen, gegevens lezen en schrijven, berekeningen |
| `src/app.html` | De app: opmaak, schermen en logica |
| `build.mjs` | `node kakebo/build.mjs` bouwt `Kakebo.gs` opnieuw |
| `test/` | Een nagebootste Google-omgeving en tests: `node --test kakebo/test/*.test.mjs` |
| `test/maak-demo.mjs` | `node kakebo/test/maak-demo.mjs` maakt `test/demo.html` |
