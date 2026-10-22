# CanSat 2027 — Handleiding sensortest

Met deze handleiding test je alle sensoren van de CanSat tegelijk. Je ziet de
metingen **live** in een dashboard op de laptop. Je hebt nog nooit met Arduino
gewerkt? Geen probleem: elke stap staat erin, ook waar je klikt en wat je typt.

> **Zo werkt het in het kort**
>
> ```
> sensoren ──► Teensy ──USB-kabel──► laptop: serial_logger ──► C:\CanSat\metingen\test_01.csv ──► dashboard
> ```
>
> De Teensy (een kleine computer in de CanSat) leest elke seconde alle sensoren
> uit en stuurt de metingen als één regel tekst via de USB-kabel naar de laptop.
> Een klein programma op de laptop (`serial_logger`) schrijft die regels in een
> bestand. Het dashboard leest dat bestand terwijl het groeit en tekent grafieken.

**Inhoud**

- [Deel A — Eenmalig klaarzetten](#deel-a--eenmalig-klaarzetten) (± 45 minuten, één keer per laptop)
- [Deel B — Een test uitvoeren](#deel-b--een-test-uitvoeren) (elke keer)
- [Deel C — Hoe werkt het?](#deel-c--hoe-werkt-het) (uitleg en vragen)
- [Deel D — Het lukt niet](#deel-d--het-lukt-niet)
- [Deel E — Naslag](#deel-e--naslag): aansluitingen, CSV-kolommen, normale waarden, woordenlijst, alle commando's
- [Deel F — Na de vlucht: de krachten op de CanSat](#deel-f--na-de-vlucht-de-krachten-op-de-cansat) (Cd van de parachute, controle, zones)

Deze handleiding gaat uit van een **Windows**-laptop.

---

## Deel A — Eenmalig klaarzetten

Deze stappen doe je **één keer per laptop**. Vink ze af:

- [ ] A1. De map `C:\CanSat` maken met alle bestanden
- [ ] A2. Arduino IDE installeren
- [ ] A3. Teensy toevoegen aan de Arduino IDE
- [ ] A4. De bibliotheken installeren
- [ ] A5. Python installeren
- [ ] A6. De Python-pakketten installeren
- [ ] A7. Proefdraaien zonder Teensy

### A1. De map `C:\CanSat` maken

Alles voor dit project komt in één map: **`C:\CanSat`**. Zo hoef je maar één plek te
onthouden.

1. Download `CanSat.zip` (je krijgt die van je leerkracht).
2. Ga in de **Verkenner** naar je map *Downloads*.
3. Klik met de **rechtermuisknop** op `CanSat.zip` → **Alles uitpakken…**
4. In het venster staat een pad, bv. `C:\Users\jouwnaam\Downloads\CanSat`.
   Wis dat pad en typ: **`C:\CanSat`**
5. Klik op **Uitpakken**.

> **Heb je al een map `C:\CanSat` van vroeger?** Pak de nieuwe `CanSat.zip` op
> dezelfde manier uit naar `C:\CanSat`. Windows vraagt dan of het bestanden mag
> vervangen. Kies **De bestanden in de doelmap vervangen**. Je map `metingen`
> blijft gewoon staan. Vervang altijd alle bestanden samen, niet één bestand apart:
> de programma's gebruiken stukjes van elkaar.

Kijk nu in `C:\CanSat`. Je moet dit zien:

```
C:\CanSat\
├── README.md                    ← deze handleiding
├── start_meting.py              ← meting starten met één knop (bv. in Thonny)
├── sensortest_fft\
│   └── sensortest_fft.ino       ← het programma voor de Teensy
├── pico\
│   └── main.py                  ← ontvanger voor de radio (Raspberry Pi Pico)
├── dashboard\
│   ├── dashboard_scherm1.py     ← dashboard: grafieken
│   ├── dashboard_scherm2.py     ← dashboard: 3D-baan, kaart en oriëntatie
│   ├── krachten.py              ← gegevens van jullie CanSat + het krachtenmodel
│   └── requirements.txt         ← lijst met Python-pakketten
└── tools\
    ├── serial_logger.py         ← schrijft de metingen van de Teensy naar een bestand
    ├── check_csv.py             ← controleert een meetbestand
    ├── gen_test_csv.py          ← maakt nep-metingen om te oefenen (ook een oefenvlucht)
    └── krachten_analyse.py      ← na de vlucht: Cd, controle en krachten per zone
```

De map `metingen` bestaat nog niet. Die wordt vanzelf gemaakt bij je eerste test.

> **Let op:** hernoem de map `sensortest_fft` niet. Arduino eist dat een `.ino`-bestand
> in een map staat met **precies dezelfde naam** als het bestand. Anders weigert de
> Arduino IDE het te openen.

> **Mag je niets maken op `C:\`?** Op sommige schoolcomputers is dat geblokkeerd.
> Gebruik dan `Documenten\CanSat` en lees overal in deze handleiding die map in plaats
> van `C:\CanSat`.

### A2. Arduino IDE installeren

De **Arduino IDE** is het programma waarmee je code schrijft en naar de Teensy stuurt.

1. Ga naar **https://www.arduino.cc/en/software**
2. Download **Arduino IDE 2** voor Windows en installeer het (alles op standaard laten).
3. Start de Arduino IDE.

### A3. Teensy toevoegen aan de Arduino IDE

De Arduino IDE kent de Teensy nog niet. Dat los je zo op:

1. Menu **File → Preferences** (Nederlands: *Bestand → Voorkeuren*).
2. Onderaan, bij **Additional boards manager URLs**, plak je:
   ```
   https://www.pjrc.com/teensy/package_teensy_index.json
   ```
3. Klik **OK**.
4. Klik links op het icoon van de **Boards Manager** (het tweede icoon, een printplaatje).
5. Typ `teensy` in het zoekveld en klik bij **Teensy (for Arduino IDE 2.0.4 or later)**
   op **Install**. Dit duurt een paar minuten.

### A4. De bibliotheken installeren

Een **bibliotheek** is code die iemand anders al geschreven heeft, bv. om een sensor
uit te lezen. Zo hoef jij niet zelf uit te zoeken hoe elke chip werkt.

1. Klik links op het icoon van de **Library Manager** (het derde icoon, boekjes).
2. Zoek en installeer deze bibliotheken één voor één. Vraagt de IDE of hij ook
   "dependencies" mag installeren, klik dan op **Install All**.

| Zoek op | Installeer | Voor |
|---|---|---|
| `BMP3XX` | **Adafruit BMP3XX Library** | luchtdruksensor |
| `BNO055` | **Adafruit BNO055** | oriëntatiesensor |
| `Adafruit Unified Sensor` | **Adafruit Unified Sensor** | nodig voor de twee vorige |
| `Adafruit GPS` | **Adafruit GPS Library** | GPS |
| `arduinoFFT` | **arduinoFFT** van Enrique Condes, **versie 2.x** | trillingen analyseren |

3. De **LSM6DSO**-bibliotheek installeer je anders, via een zip (zoals in de StartGids):
   1. Ga naar **https://github.com/sparkfun/SparkFun_Qwiic_6DoF_LSM6DSO_Arduino_Library**
   2. Klik op de groene knop **Code → Download ZIP**.
   3. In de Arduino IDE: **Sketch → Include Library → Add .ZIP Library…** en kies het
      gedownloade zip-bestand.

   > **Let op:** neem de versie **zonder X**. De LSM6DSO**X** is een andere chip.

De bibliotheken voor de microfoon (`Audio`), de SD-kaart (`SD`) en de
verbindingen (`Wire`, `SPI`) zitten al in Teensy. Die hoef je niet te installeren.

### A5. Python installeren

De dashboards zijn geschreven in **Python**, een andere programmeertaal. Python draait
op de laptop, niet op de Teensy.

1. Ga naar **https://www.python.org/downloads/** en klik op de gele knop **Download Python 3.x**.
2. Start het installatiebestand.
3. **Belangrijk:** vink onderaan **"Add python.exe to PATH"** aan.
4. Klik **Install Now**.

### A6. De Python-pakketten installeren

Ook Python gebruikt bibliotheken; daar heten ze **pakketten**. Je installeert ze met een
commando in de **opdrachtprompt**.

**Een opdrachtprompt openen in de juiste map** (dit heb je nog vaak nodig):

1. Open in de Verkenner de map `C:\CanSat`.
2. Klik bovenaan in de **adresbalk** (waar `C:\CanSat` staat).
3. Typ `cmd` en druk op **Enter**.

Er opent een zwart venster dat begint met `C:\CanSat>`. Dat betekent: dit venster
"staat" in de map `C:\CanSat`.

Typ nu dit commando en druk op Enter:

```
py -m pip install -r dashboard\requirements.txt
```

Er rollen veel regels voorbij. Wacht tot je weer `C:\CanSat>` ziet. Staat er
onderaan `Successfully installed ...`, dan is het gelukt.

> **Waarom `py` en niet `python`?** Op veel Windows-computers opent `python` de
> Microsoft Store. `py` start altijd de Python die je net installeerde.

### A7. Proefdraaien zonder Teensy

Test of de dashboards werken, nog zonder hardware. Typ in de opdrachtprompt
(in `C:\CanSat`):

```
py tools\gen_test_csv.py metingen\oefen.csv
py dashboard\dashboard_scherm1.py --replay metingen\oefen.csv
```

Het eerste commando maakt een bestand met **nep-metingen** van een bureautest van
2 minuten. Het tweede speelt dat bestand af in het dashboard. Na een paar seconden
opent een venster met grafieken. Kijk wat er gebeurt:

| Tijd | Wat gebeurde er (nep)? | Wat zie je? |
|---|---|---|
| 0–25 s | GPS zoekt nog satellieten | geen positie |
| 35 s | iemand tikt met de CanSat op de tafel | ACCELERATION: de witte stippellijn springt omhoog. Linksboven staat `largest shock`. |
| 40–55 s | CanSat wordt geschud | pieken in ACCELERATION en GYROSCOPE. In VIBRATION PER BAND wordt alleen het balkje **0–10** groot. |
| 60 s | iemand klapt in de handen | piek in AUDIO RMS |
| 70–90 s | iemand loopt een trap op | ALTITUDE stijgt ongeveer 6 m |

Sluit het venster en probeer ook scherm 2:

```
py dashboard\dashboard_scherm2.py --replay metingen\oefen.csv
```

**Deel A is klaar.** ✔

---

## Deel B — Een test uitvoeren

Dit doe je **bij elke test**.

### Wat heb je nodig?

- de CanSat met de Teensy en alle sensoren (bedrading: zie de StartGids en [E1](#e1-aansluitingen))
- een **USB-kabel die data doorgeeft** (sommige goedkope kabels kunnen alleen opladen)
- de laptop met deel A klaar

Een SD-kaart is **niet** nodig.

### B1. Het programma op de Teensy zetten

Dit hoef je alleen opnieuw te doen als de code veranderd is.

1. Sluit de Teensy met de USB-kabel aan op de laptop.
2. Open de Arduino IDE → **File → Open…** → `C:\CanSat\sensortest_fft\sensortest_fft.ino`
3. Kies het board: **Tools → Board → Teensy → Teensy 4.1**.
4. Kies de poort: **Tools → Port**, onder *teensy ports*.
5. Klik op het **vinkje** ✓ (linksboven, *Verify*). De IDE **compileert** de code: hij
   vertaalt ze naar instructies die de Teensy begrijpt. Onderaan verschijnt na een
   tijdje *Done compiling*. Krijg je rode foutmeldingen, kijk dan in [deel D](#deel-d--het-lukt-niet).
6. Klik op de **pijl** → (*Upload*). Er opent een klein venster, de **Teensy Loader**.
   Onderaan in de IDE staat na een paar seconden dat de upload gelukt is.

> **Tip:** start de upload niet, druk dan één keer op het **witte knopje** op de Teensy.

### B2. Controleren of alle sensoren werken

1. Klik in de Arduino IDE rechtsboven op het **vergrootglas** (*Serial Monitor*).
2. Kies onderaan rechts **115200 baud**.
3. Druk één keer op het witte knopje van de Teensy om opnieuw te starten.

Je ziet dit:

```
=== CanSat 2027 — Sensortest + FFT + CSV ===
BMP390 ... OK
BNO055 ... OK
LSM6DSO ... OK
GPS PA1616D ... OK
SD kaart ... FOUT

--- Sensorstatus ---
BMP390 : OK
...
--- logging gestart ---
millis,temp_C,press_hPa,alt_m,lat,lon,time_utc,...
5212,21.43,942.10,612.31,50.457303,6.221376,00:00:00,...
6212,21.44,942.11,612.29,50.457303,6.221376,00:00:00,...
```

- Bij elke sensor moet **OK** staan. `SD kaart ... FOUT` is normaal: er zit geen kaart in.
- Staat er bij GPS `nog geen data (wordt verder gevolgd)`? Geen paniek, de GPS start
  soms trager op. De sketch blijft hem volgen.
- Elke seconde komt er een nieuwe regel met getallen bij.
- Het **oranje lampje** op de Teensy knippert: het programma draait.

**Sluit nu de Arduino IDE helemaal** (het hele programma, niet alleen het tabblad
*Serial Monitor*). De Teensy blijft gewoon werken: het programma staat erop.

> **Waarom sluiten?** De USB-poort kan maar door **één** programma tegelijk gebruikt
> worden. In de volgende stap heeft `serial_logger` hem nodig. De Arduino IDE houdt de
> poort soms vast, ook als de Serial Monitor dicht is.

### Snelle weg: alles met één knop (`start_meting.py`, met of zonder Thonny)

Werk je liever in **Thonny**, of wil je niet drie vensters openen? Dan doet
`start_meting.py` stap B3 en B4 in één keer.

**Eén keer klaarzetten in Thonny:**
1. Kijk **rechtsonder** in Thonny: daar moet **Local Python 3** staan. Staat er
   *MicroPython*? Klik erop en kies *Local Python 3*. Anders houdt Thonny zelf de
   USB-poort bezet.
2. **Tools → Manage packages** → installeer `pyserial`, `matplotlib`, `numpy` en `pillow`.
   (Thonny heeft zijn eigen Python. Wat je in A6 installeerde, kent Thonny niet.)

**Elke meting:**
1. Steek de Teensy met de USB-kabel in de laptop. Staat de sketch er al op (B1)?
   Dan heb je de Arduino IDE niet nodig. Staat ze toch open? Sluit **alle**
   Arduino-vensters met het kruisje rechtsboven.
2. Open `C:\CanSat\start_meting.py` in Thonny en druk op de groene **Run**-knop (F5).
3. Beantwoord de vier vragen onderaan in de Shell. Druk je gewoon op **Enter**, dan
   neemt het programma het voorstel tussen [haakjes].
   ```
   1) Op welke poort zit de Teensy (USB-kabel) of de Pico (radio)?
      1. COM3     Intel(R) Active Management Technology
      2. COM9     USB Serial Device (COM9)   ← Teensy
      Poort [COM9]:                          ← Enter, of typ 2, of COM9

   2) Hoe heet je meting? Bv. schudtest, buiten_gps, test_03
      Naam [test_02]: schudtest

   3) Welk dashboard wil je zien?
      1 = scherm 1 (grafieken)
      2 = scherm 2 (3D-baan, kaart en oriëntatie)
      3 = allebei
      0 = geen (alleen opslaan)
      Keuze [3]:

   4) Wat is vandaag de luchtdruk op zeeniveau, in hPa?
      Luchtdruk [1013]:                      ← Enter, of typ bv. 1021,5
   ```

**De luchtdruk op zeeniveau** krijg je op de lanceerdag. De dashboards berekenen er de
hoogte mee. Ken je hem niet, druk dan op Enter: dan nemen ze 1013 hPa. Het getal komt
ook in een klein bestand naast de meting, bv. `schudtest_luchtdruk.txt`. Een replay
van die meting gebruikt later vanzelf hetzelfde getal. Typ de luchtdruk **op zeeniveau**,
niet de luchtdruk die je op de lanceerplaats meet.

Het programma bewaart de metingen in `C:\CanSat\metingen\schudtest.csv` en opent de
dashboards die je koos, met LIVE data. Komen de metingen via de radio binnen (de
Pico-ontvanger met `pico\main.py`)? Kies dan de poort met `← Pico (ontvanger)`. De
dashboards tonen dan ook de RSSI, en `not in radio packet` bij wat niet in het
radiopakket zit. Bestaat de naam al, dan vraagt het een andere
naam: een oude meting wordt nooit overschreven. Spaties in de naam worden `_`.

**Stoppen:** klik op de rode **Stop**-knop in Thonny. Staan de dashboards daarna nog
open? Sluit ze dan zelf.

**Geen Thonny?** Dan gebruik je de Python uit A5. De pakketten uit A6 zijn genoeg:
je hoeft niets extra te installeren.
1. Open een opdrachtprompt in `C:\CanSat` (adresbalk → `cmd` → Enter).
2. Typ `py start_meting.py` en druk op Enter.
3. Beantwoord de vier vragen, net zoals hierboven.
4. Stoppen: druk op **Ctrl + C** in het zwarte venster en daarna op **Enter**.

Je kan ook dubbelklikken op `start_meting.py` in de Verkenner. Opent het bestand in
Kladblok of in een ander programma in plaats van een zwart venster? Gebruik dan de
opdrachtprompt.

> **Lukt het niet?**
> - *Geen "← Teensy" in de lijst*: kijk de USB-kabel na (een datakabel, geen
>   laadkabel). Steek hem in en typ `r` om opnieuw te zoeken.
> - *"is gestopt met een fout"*: open het `.log`-bestand dat erbij staat (in
>   `metingen\`). Daar staat wat er misliep.
> - Wil je het liever met de opdrachtprompt doen? Volg dan gewoon B3 en B4 hieronder.

### B3. De metingen opslaan op de laptop

1. Open een opdrachtprompt in `C:\CanSat` (adresbalk → `cmd` → Enter).
2. Zoek op welke **COM-poort** de Teensy zit:
   ```
   py tools\serial_logger.py --list
   ```
   Je krijgt een lijstje, bv.:
   ```
   COM3            Intel(R) Active Management Technology - SOL (COM3)
   COM5            USB Serial Device (COM5)
   ```
   De Teensy is meestal de lijn met **USB**. Twijfel je? Trek de USB-kabel uit, typ het
   commando opnieuw en kijk welke lijn verdwenen is.
3. Start het loggen. Vervang `COM5` door jouw poort, en geef het bestand een naam:
   ```
   py tools\serial_logger.py COM5 metingen\test_01.csv
   ```
   Je ziet:
   ```
   Lezen van COM5 → metingen\test_01.csv  (Ctrl+C om te stoppen)
   12 rijen gelogd
   ```
   Het getal loopt elke seconde op. **Laat dit venster open** tijdens de hele test.

> **Bestandsnamen:** gebruik voor **elke test een nieuwe naam**: `test_01.csv`,
> `test_02.csv`, … of iets dat zegt wat je deed: `schudtest.csv`, `buiten_gps.csv`.
> Gebruik geen spaties. Bestaat het bestand al, dan worden de nieuwe metingen er
> **achteraan bijgeschreven**.

Je metingen komen in **`C:\CanSat\metingen\`**.

### B4. Het dashboard starten

Open een **tweede** opdrachtprompt in `C:\CanSat` (adresbalk → `cmd` → Enter) en typ,
met **dezelfde bestandsnaam** als in B3:

```
py dashboard\dashboard_scherm1.py --live metingen\test_01.csv
```

Wil je ook scherm 2? Open een **derde** opdrachtprompt:

```
py dashboard\dashboard_scherm2.py --live metingen\test_01.csv
```

Bovenaan in het dashboard moet **LIVE: tailing CSV** staan.

> **Staat er `SIMULATED TEST DATA`?** Dan vond het dashboard je bestand niet en toont
> het een simulatie. Meestal komt dat doordat B3 niet draait, of door een tikfout in de
> bestandsnaam. Sluit het dashboard, controleer B3 en start opnieuw.

Je hebt nu dit op je scherm:

| Venster | Wat doet het? | Mag je het sluiten? |
|---|---|---|
| opdrachtprompt 1 | `serial_logger`: schrijft de metingen weg | **Nee**, pas na de test |
| opdrachtprompt 2 (en 3) | start het dashboard | Ja, het dashboard haalt bij een herstart alles weer in |
| dashboardvenster(s) | grafieken | Ja |

### B5. De testen

Doe deze testen en kijk telkens in het dashboard wat er gebeurt. Noteer in je
logboek telkens de **tijd** die rechtsboven in het dashboard staat.

| # | Test | Wat doe je? | Waar kijk je? |
|---|---|---|---|
| 1 | **Rust** | 30 s niets: CanSat stil op tafel | Alle grafieken ongeveer vlak. Dit is je **nulmeting**. |
| 2 | **Schudden** | 15 s stevig schudden met de hand | Scherm 1: ACCELERATION, GYROSCOPE en VIBRATION PER BAND. Scherm 2: het blikje kleurt onderaan wat geler. Schudden is maar 2 à 3 g; rood is pas 20 g. |
| 2b | **Schok** | zet de CanSat met een stevige tik op de tafel | Scherm 1: ACCELERATION. De witte stippellijn springt omhoog. Linksboven staat `largest shock` met de grootte en het tijdstip. Scherm 2: de bodem kleurt geel tot oranje. |
| 3 | **Klap** | één keer hard in de handen klappen naast de CanSat | Scherm 1: AUDIO RMS. Let op de getallen naast de grafiek: de schaal past zich aan. In een stil lokaal is de lijn ongeveer 0,003. Na een klap gaat de schaal omhoog. |
| 4 | **Draaien** | CanSat langzaam een kwartslag draaien rond de verticale as | Scherm 2: het blik rechts draait mee, *Heading* verandert |
| 5 | **Kantelen** | CanSat schuin houden, naar voren en opzij | Scherm 2: *Roll* en *Pitch* |
| 6 | **Hoogte** | trap op en weer af, laptop mee | Scherm 1: ALTITUDE. De grafiek zoomt in, dus je ziet de trap goed. Onder het getal staat `highest`: het hoogste punt. |
| 7 | **GPS** | naar buiten, vrij zicht op de lucht, enkele minuten wachten | Scherm 2: LATITUDE/LONGITUDE, toets **M** voor de kaart |
| 8 | **Wandelen** | met GPS-fix een stukje rechtdoor wandelen, laptop mee | Scherm 2: DRIFT toont je snelheid (ongeveer 1–1,5 m/s) en je richting, bv. `towards NE` |

> **Hoogte op de grond:** zolang de CanSat nooit hoger dan 50 m kwam, zoomt de grafiek
> ALTITUDE in. Rechtsboven staat dan `below 50 m: zoomed in`. Het getal ALTITUDE heeft
> dan één cijfer na de komma, bv. `3.2`. Onder de beginhoogte is het negatief. Tijdens de
> vlucht (hoger dan 50 m) gaat de as van 0 tot 1100 m, zoals altijd.
> PRESSURE heeft twee cijfers na de komma, bv. `1007.95`. Til je de CanSat 1 m op, dan
> zakt de luchtdruk met ongeveer 0,12 hPa: dat zie je meteen. Via de radio komt de
> luchtdruk met maar één cijfer na de komma binnen.

> **De tijd:** de klok rechtsboven begint bij `00:00` bij de eerste meting. Ziet het
> dashboard een lancering, dan telt de klok vanaf de lancering: `T+00:42`. De grafieken
> van scherm 1 tonen dan de vlucht: van 30 s voor de lancering tot 1 minuut na de landing.
> Op scherm 2 telt FLIGHT TIME vanaf de lancering en stopt hij bij de landing.

> **Op scherm 2:** druk op **M** om te wisselen tussen de 3D-vluchtbaan en een kaart. De
> kaart toont de plek waar je staat (zodra de GPS een positie heeft) en zoomt vanzelf uit
> als de CanSat ver afdrijft. De kaart wordt van internet gehaald en daarna bewaard; zie
> [deel D](#deel-d--het-lukt-niet) als ze donker blijft.

### B6. Stoppen

1. Klik in opdrachtprompt 1 en druk op **Ctrl+C**. Je ziet `Gestopt: 312 rijen in metingen\test_01.csv`.
2. Sluit de dashboardvensters.

### B7. Je meting controleren

Typ in een opdrachtprompt in `C:\CanSat`:

```
py tools\check_csv.py metingen\test_01.csv
```

Je krijgt een samenvatting:

```
Bestand : metingen\test_01.csv
Rijen   : 312 geldig van 312
Duur    : 311 s  →  1.00 rijen/s
GPS-fix : 0/312 rijen  (geen fix: buiten testen, antenne vrij zicht)

Kolom          min        max      (controleer of dit logisch is)
  temp_C          21.360     21.440
  press_hPa     1012.100   1012.900
  ...

OK: het dashboard kan dit bestand lezen.
```

- **min** en **max** zijn de kleinste en grootste waarde tijdens je test. Vergelijk ze met
  de tabel [normale waarden](#e3-normale-waarden).
- Staat er **LET OP: deze kolommen veranderen nooit**? Dan werkte die sensor
  waarschijnlijk niet: de waarde bleef de hele tijd gelijk.

### B8. Achteraf opnieuw bekijken

Een opgeslagen test kan je opnieuw afspelen, zo vaak je wil:

```
py dashboard\dashboard_scherm1.py --replay metingen\test_01.csv
py dashboard\dashboard_scherm2.py --replay metingen\test_01.csv --speed 4
```

`--speed 4` speelt 4 keer sneller af. Een replay gebruikt vanzelf de luchtdruk op
zeeniveau die je bij de start ingaf (uit `test_01_luchtdruk.txt`). Een meting zonder dat
bestand, bv. van de SD-kaart? Geef de luchtdruk dan zelf mee: `--sea-level 1021.5`.

---

## Deel C — Hoe werkt het?

### C1. De Teensy: een kleine computer

De **Teensy 4.1** is een **microcontroller**: een volledige computer op een plaatje zo
groot als een kauwgomstrip. Hij heeft geen scherm en geen toetsenbord, maar wel pinnen
waarop je sensoren aansluit.

Een Arduino-programma (een **sketch**) heeft altijd twee delen:

```cpp
void setup() {   // wordt ÉÉN keer uitgevoerd, bij het opstarten
    ...          // hier zetten we de sensoren klaar
}

void loop() {    // wordt daarna EINDELOOS herhaald, duizenden keren per seconde
    ...          // hier lezen we de sensoren uit
}
```

In `sensortest_fft.ino` kijkt `loop()` telkens op de klok (`millis()`, het aantal
milliseconden sinds het opstarten) of het tijd is voor de volgende meting. Zo meet elke
sensor in zijn eigen ritme:

| Sensor | Hoe vaak? |
|---|---|
| LSM6DSO (versnelling) | 416 keer per seconde |
| BNO055 (oriëntatie) | 100 keer per seconde |
| BMP390 (luchtdruk) | 1 keer per seconde |
| GPS | 1 keer per seconde |
| Een regel naar de laptop sturen | 1 keer per seconde |

### C2. I²C: drie sensoren op twee draadjes

De BMP390, BNO055 en LSM6DSO hangen alle drie aan **dezelfde twee draadjes**: SDA (data)
en SCL (klok). Dat heet een **I²C-bus**. Hoe weet de Teensy welke sensor antwoordt?
Elke sensor heeft een eigen **adres**, zoals een huisnummer in een straat:

| Sensor | Adres |
|---|---|
| BMP390 | `0x77` |
| BNO055 | `0x28` |
| LSM6DSO | `0x6B` |

`0x` betekent dat het getal **hexadecimaal** geschreven is: een talstelsel met 16 cijfers
(0–9 en A–F). `0x28` is 40 in ons gewone talstelsel.

### C3. De sensoren

**BMP390 — luchtdruk → hoogte.** Boven je hoofd hangt een kolom lucht die op je drukt.
Hoe hoger je komt, hoe minder lucht er boven je is, en hoe lager de druk. Vlak bij de
grond daalt de druk ongeveer **1 hPa per 8 meter**. Uit de druk rekent de sketch zo de
hoogte uit. Omdat de luchtdruk ook verandert met het weer, kijkt het dashboard naar het
**verschil** met de hoogte bij de start.

**BNO055 — oriëntatie.** Deze chip bevat een versnellingsmeter en een gyroscoop
(draaisnelheid), en een eigen processor die die metingen combineert. Dat heet
**sensorfusie**. Hij geeft:
- *Heading, Roll, Pitch*: hoe de CanSat gedraaid staat (in graden);
- de **zwaartekracht** apart (wijst altijd naar beneden, ongeveer 9,8 m/s²);
- de **lineaire versnelling**: de versnelling **zonder** zwaartekracht, dus alleen
  door bewegen.

We gebruiken de modus **IMU+**, zonder kompas. Heading is daarom **relatief**:
0° is de richting waarin de CanSat stond bij het opstarten.

Waarom geen kompas? Een kompas meet het magnetisch veld van de aarde. Dat is zwak.
Metaal, batterijen en de buzzer in de buurt verstoren het. In een raket gebeurt dat
zeker. Zonder kompas is de oriëntatie stabieler.

**LSM6DSO — snelle versnellingsmeter.** Meet de versnelling 416 keer per seconde. Dat is
snel genoeg om **trillingen** te zien, zoals van een raketmotor.

**GPS PA1616D — positie en tijd.** De GPS ontvangt signalen van satellieten op ongeveer
20 000 km hoogte. Uit het tijdsverschil tussen de signalen van minstens 4 satellieten
berekent hij waar hij is. Daarvoor moet hij de lucht kunnen "zien": binnen lukt het
meestal niet. Tot er een positie is (een **fix**), schrijft de sketch `00:00:00` als tijd.

De GPS meet ook hoe snel en in welke **richting** de CanSat over de grond beweegt.
Hangt de CanSat aan de parachute, dan is dat de richting waarin de **wind** hem
meeneemt. Scherm 2 toont dat bij **DRIFT**.

Let op: dat is iets anders dan de kant waar de CanSat naar **wijst**. Onder een
parachute draait een CanSat vaak rond zijn as. Hij wijst dan telkens een andere
kant op, maar hij drijft wel in één richting af.

**SPH0645 — digitale microfoon.** De microfoon zet geluid meteen om naar getallen en
stuurt die via **I²S** (een verbinding speciaal voor audio) naar de Teensy: ongeveer
44 000 getallen per seconde.

### C4. Van duizenden getallen naar één getal

De laptop krijgt maar **één regel per seconde**. Hoe vat je 44 000 geluidsmetingen of
416 trillingsmetingen samen in één getal?

**Geluid → RMS.** Geluid is lucht die heen en weer trilt. Het gemiddelde van de
metingen is dus ongeveer 0: plus en min heffen elkaar op. Daarom gebruiken we het
**RMS** (*root mean square*):

1. kwadrateer elke meting (dan is alles positief),
2. neem het gemiddelde,
3. trek er de vierkantswortel uit.

Hoe luider het geluid, hoe groter de RMS.

**Trillingen → FFT.** Een **FFT** (*Fast Fourier Transform*) zoekt uit welke
**frequenties** (trillingen per seconde, in Hz) in een signaal zitten. Je kent het van de
springende balkjes van een equalizer in een muziekapp. De sketch verzamelt 512 metingen
(ongeveer 1,2 s), doet er een FFT op en bewaart de **sterkste** frequentie
(`fft_peak_hz`) en hoe sterk ze is (`fft_peak_amp`, in g).

Waarom gaat het maar tot **208 Hz**? Om een trilling te herkennen, moet je ze
minstens 2 keer per periode meten. Met 416 metingen per seconde kan je dus trillingen
tot 416 ÷ 2 = 208 Hz zien. Dat heet de **Nyquist-frequentie**.

**Trillingen per frequentieband.** In het dashboard zie je de grafiek **VIBRATION PER
BAND**. Ze heeft 5 balkjes. Elk balkje is een **frequentieband**: een groep van
frequenties. Het balkje toont hoe sterk de CanSat trilt in die band, in **g**.

| Band | Voorbeelden van wat je daar kan zien |
|---|---|
| 0–10 Hz | bewegen, schudden met de hand, slingeren aan de parachute |
| 10–30 Hz | trillingen van het blikje en van de constructie |
| 30–60 Hz | snellere trillingen van de constructie |
| 60–120 Hz | snelle trillingen, bv. van een motor |
| 120–208 Hz | zeer snelle trillingen, bv. door luchtstroming |

De voorbeelden zijn geen vaste regels. Wat waar zit, ontdekken jullie met de metingen.

Het grijze streepje boven een balkje is de **hoogste** waarde van die band tijdens de
hele test. Rechtsboven staat de sterkste frequentie (bv. `strongest 5 Hz · 0.81 g`).

*Wat gebeurt er op de Teensy?*

1. De Teensy verzamelt 512 metingen van de LSM6DSO (ongeveer 1,2 s).
2. Hij trekt de zwaartekracht (het gemiddelde) eraf. Die is geen trilling.
3. Hij vermenigvuldigt de metingen met een **venster**: een vorm die aan het begin en het
   einde naar nul gaat. Zonder venster "lekt" een trilling naar andere frequenties.
4. De FFT zet de 512 metingen om naar 256 frequenties, telkens 0,8 Hz uit elkaar.
5. De Teensy telt de frequenties per band op en rekent dat om naar één getal per band:
   de **RMS-versnelling in g**.

*Waarom deze keuze?*

- **Het volledige spectrum** zou 256 getallen zijn, elke 1,2 seconde. Dat is te veel om
  later via de radio te sturen. Voor een mens is het ook niet te lezen.
- **Alleen de sterkste frequentie** is maar één getal. Dan mis je alles wat daarnaast
  trilt, bv. als je schudt terwijl er ook een motor draait.
- **5 banden** zijn 5 getallen. Dat is klein genoeg om later via de radio te sturen, en
  je ziet nog altijd **waar** de trillingen zitten. Dat is het evenwicht dat we kozen.
- De banden worden **breder naarmate de frequentie stijgt** (10, 20, 30, 60, 88 Hz).
  Bij lage frequenties zijn kleine verschillen belangrijker.
- De waarde is in **g**, een echte natuurkundige eenheid. Zo kan je ze vergelijken met
  `acc_peak_g` en met andere metingen.

*Hoe weten we dat het klopt?*

- De berekening gebruikt de **stelling van Parseval**: de energie van een signaal is
  even groot of je ze nu in de tijd telt of over alle frequenties.
- Het venster maakt het signaal zwakker. Daarvoor wordt gecorrigeerd: de Teensy deelt
  door het gemiddelde van het kwadraat van het venster (0,397).
- We hebben de berekening getest met een gekend signaal: een trilling van 0,5 g bij
  25 Hz. Een sinus van 0,5 g heeft een RMS van 0,5 ÷ √2 = **0,354 g**. De Teensy-code
  gaf **0,3535 g** in de band 10–30 Hz, en bijna niets in de andere banden. Staat de
  Teensy even stil (bv. om naar de SD-kaart te schrijven), dan klopt de frequentie
  toch: de metingen volgen een vast ritme van 416 per seconde.

*Grenzen: waar moet je op letten?*

- **Banden zijn gemaakt voor aanhoudende trillingen.** Bij een korte schok hangt de
  waarde af van **wanneer** in de 1,2 s de schok valt: soms te hoog, soms te laag. Gebruik
  voor schokken `acc_peak_g`.
- **Een brede band verzamelt meer ruis.** Vergelijk een band daarom met **zichzelf**
  (in rust en tijdens het schudden), niet de banden met elkaar.
- **Trager dan ongeveer 1 Hz** kan je niet goed meten: de frequenties liggen 0,8 Hz uit
  elkaar.
- **Sneller dan 208 Hz** zie je niet (Nyquist). Zo'n snelle trilling kan zelfs als
  "spook" in een lagere band verschijnen (**aliasing**). De sensor heeft zelf een filter
  dat dit grotendeels tegenhoudt.
- Elke 1,2 s is er een nieuw resultaat. Bij één regel per seconde staat dezelfde waarde
  dus soms twee keer in de CSV.

Het dashboard toont alleen wat de Teensy echt gemeten heeft.

**Schokken → grootste versnelling.** Een schok duurt heel kort, bijvoorbeeld als de
CanSat uit de raket wordt geworpen of als de parachute opengaat. Veel korter dan een
seconde. De Teensy stuurt maar één regel per seconde. Een gewone meting valt dan
bijna altijd **naast** de schok.

Daarom houdt de Teensy elke seconde de **grootste** versnelling bij. Hij meet daarvoor
416 keer per seconde met de LSM6DSO. Die grootste waarde komt in de kolom
`acc_peak_g`. Zo mis je geen enkele schok.

De zwaartekracht zit er ook in. Ligt de CanSat stil, dan is `acc_peak_g` dus ongeveer
**1 g**. Een tik op de tafel geeft al snel 3 tot 8 g.

**Het gekleurde blikje op scherm 2 toont de kracht per zone.** Het is een model: het
rekent met de gemeten g en de massa (`dashboard\krachten.py`). Er zit geen sensor die
de kracht in het blik zelf meet.

- Op de grond, bij de lancering en bij de landing komt de kracht **onderaan** binnen.
  Als de parachute trekt, komt ze **bovenaan** binnen.
- Hoe dichter bij die plaats, hoe meer het blik moet dragen.
- Groen is weinig. Rood (100 %) is 20 g op de bodem: zoveel moet een CanSat volgens
  ESA kunnen verdragen.
- De kleur blijft staan op de hoogste waarde. Na de vlucht zie je zo welke zones het
  meest moesten dragen. Meer uitleg staat in [Deel F](#deel-f--na-de-vlucht-de-krachten-op-de-cansat).

### C5. Een CSV-bestand

Elke regel die de Teensy stuurt, is één rij van een tabel. De getallen staan gescheiden
door **komma's**: **CSV** = *comma-separated values*. De eerste rij, de **header**,
geeft de namen van de kolommen:

```
millis,temp_C,press_hPa,alt_m,...
5212,21.43,942.10,612.31,...
```

Je kan een CSV-bestand ook openen in Excel of Google Sheets en er zelf grafieken van maken.

> **Excel met Belgische instellingen** verwacht `;` tussen de waarden en een komma als
> decimaalteken. Dubbelklik je op het bestand, dan staat alles in één kolom. Gebruik
> daarom **Gegevens → Van tekst/CSV**, kies als scheidingsteken **Komma**, en controleer
> of de getallen met een punt (`21.43`) goed overkomen.

### C6. Van de Teensy naar het dashboard

1. De Teensy stuurt elke regel over de USB-kabel. Dat heet **seriële communicatie**:
   de tekens gaan één voor één, achter elkaar. Windows geeft de verbinding een naam,
   bv. **COM5**.
2. `serial_logger.py` luistert naar COM5 en schrijft elke regel achteraan in je
   CSV-bestand. Meldingen die geen meting zijn ("BMP390 ... OK") laat hij weg.
3. Het dashboard kijkt 10 keer per seconde of het bestand gegroeid is, leest de nieuwe
   regels en tekent ze. Dat heet **live** (`--live`). Afspelen achteraf heet
   **replay** (`--replay`).

Omdat alles eerst in een bestand komt, gaat er niets verloren als het dashboard even
hapert of opnieuw opgestart wordt.

### C7. Vragen om over na te denken

1. Je meet de druk op het gelijkvloers en op de eerste verdieping. Hoeveel hPa verschil
   verwacht je bij 4 m hoogteverschil? Klopt dat met je meting?
2. Waarom is `lacc_z` (lineaire versnelling) ongeveer 0 als de CanSat stil ligt, terwijl
   `grav_z` ongeveer 9,8 is?
3. Bij het schudden vindt de FFT een frequentie van een paar Hz. Hoe vaak per seconde
   schudde je dus heen en weer? Kan je sneller?
4. Een klap duurt maar een fractie van een seconde. Waarom is de RMS van een klap in het
   dashboard kleiner dan wanneer je 2 seconden lang roept?
5. De raket stoot de CanSat uit op ongeveer 1000 m hoogte. Is de luchtdruk daar dan
   ongeveer 125 hPa lager (1 hPa per 8 m)? Zoek op waarom de echte waarde wat kleiner is.
6. Waarom heeft de GPS binnen geen fix, en de luchtdruksensor geen enkel probleem?
7. Bij schudden wordt alleen het balkje 0–10 Hz groot. Bij een tik op de tafel worden
   alle balkjes tegelijk groter. Hoe komt dat? (Tip: hoe ziet een korte tik eruit, en
   welke frequenties heb je nodig om zo'n scherpe piek te maken?)

---

## Deel D — Het lukt niet

| Probleem | Wat doe je? |
|---|---|
| Compileren geeft `arduinoFFT.h: No such file or directory` (of een andere `.h`) | De bibliotheek ontbreekt. Doe A4 opnieuw voor die bibliotheek. |
| Compileren geeft een fout bij `ArduinoFFT<float> FFT;` | Je hebt arduinoFFT versie 1.x. Installeer versie **2.x** in de Library Manager. |
| Compileren geeft een fout over `LSM6DSO` | Je hebt de LSM6DSO**X**-bibliotheek. Installeer de versie zonder X (A4, stap 3). |
| Geen poort onder *teensy ports* | Probeer een andere USB-kabel (een die data doorgeeft). Druk op het witte knopje van de Teensy. |
| Upload start niet | Druk één keer op het witte knopje van de Teensy. |
| `BMP390 ... FOUT` (of een andere sensor) | Controleer 3,3 V, GND, SDA (pin 18) en SCL (pin 19). Draai `Drie_sensoren_test` uit de StartGids: die toont welke adressen antwoorden. |
| `GPS PA1616D ... nog geen data` en `time_utc` blijft `00:00:00`, ook buiten | TX en RX omgewisseld? GPS-TX moet naar pin 0. Werkt `GPS_test.ino` wel? |
| `audio_rms` blijft 0 | Controleer pin 8, 20 en 21, en of SEL aan GND hangt. Werkt `SPH0645_test.ino` wel? |
| `'py' is not recognized as an internal or external command` | Python is niet (goed) geïnstalleerd. Doe A5 opnieuw. |
| `No module named 'matplotlib'` (of `numpy`, `serial`, `PIL`) | Doe A6 opnieuw, in een opdrachtprompt in `C:\CanSat`. |
| `can't open file ... No such file or directory` | De opdrachtprompt staat niet in `C:\CanSat`. Open hem opnieuw via de adresbalk (`cmd`). |
| `serial_logger`: *COM9 is bezet door een ander programma* (of `Toegang geweigerd`, `Access is denied`) | Sluit de **Arduino IDE helemaal**. Stop `serial_logger` in andere vensters met Ctrl+C. Lukt het nog niet: USB-kabel uit, 5 s wachten, terug in. |
| `serial_logger`: *al 5 s niets ontvangen* | Je koos waarschijnlijk de verkeerde poort. Kijk met `--list`: de Teensy is meestal `USB Serial Device`. Trek de kabel uit en kijk welke poort verdwijnt. |
| `serial_logger` meldt: *de Teensy stuurt 26 (of 27, 29) kolommen in plaats van 34* | Op de Teensy staat nog een oude versie van de sketch. Doe B1 opnieuw. |
| `serial_logger`: het aantal rijen blijft 0 | Draait de sketch? Knippert het lampje? Druk op het witte knopje van de Teensy. |
| Dashboard toont `SIMULATED TEST DATA` | Het bestand werd niet gevonden. Start eerst `serial_logger` (B3), controleer de bestandsnaam, en start dan het dashboard opnieuw. |
| Scherm 2: de kaart (toets M) is donker, zonder straten | De kaart werd niet gedownload (geen internet). De kaart hangt af van de plaats: open scherm 2 één keer **met internet** op die plaats en druk op M. De kaart wordt dan bewaard in `C:\CanSat\dashboard\osm_cache` en werkt daarna ook zonder internet. |
| Scherm 2 reageert traag of lijkt bevroren | Scherm 2 is zwaar voor de laptop (3D-beelden en kaart). Het tekent daarom alleen opnieuw als er een nieuwe meting is: ongeveer 1 keer per seconde. Het blik en de camera bewegen dus in kleine sprongetjes. Dat is normaal. Nog te traag? Sluit andere programma's. Gebruik de 2D-kaart (toets **M**): die is lichter dan de 3D-vluchtbaan. |
| Scherm 2: de vluchtbaan staat stil op het startpunt | Normaal zolang de GPS geen fix heeft. |
| Scherm 2: DRIFT toont "—" | Normaal zolang de GPS geen fix heeft (`no GPS fix`). Bij een oud meetbestand staat er `not in this file`. |
| `check_csv.py`: "millis loopt niet op" of "herhaalde header" | De Teensy is herstart tijdens de test, of je gebruikte twee keer dezelfde bestandsnaam. Gebruik per test een nieuwe naam. |

---

## Deel E — Naslag

### E1. Aansluitingen

Alle sensoren werken op **3,3 V**. Sluit ze **nooit** aan op 5 V.

| Sensor | Pin op de sensor → pin op de Teensy 4.1 |
|---|---|
| BMP390 | SDA → 18, SCL → 19 |
| BNO055 | SDA → 18, SCL → 19 |
| LSM6DSO | SDA → 18, SCL → 19 |
| GPS PA1616D | TX → 0 (RX1), RX → 1 (TX1) |
| SPH0645 | BCLK → 21, LRCL → 20, DOUT → 8, SEL → GND |

Plus bij elke sensor: **3,3 V** en **GND**.

### E2. De CSV-kolommen

Elke rij heeft 34 kolommen, altijd in deze volgorde.

| Kolom | Eenheid | Sensor | Betekenis |
|---|---|---|---|
| `millis` | ms | Teensy | tijd sinds het opstarten van de Teensy |
| `temp_C` | °C | BMP390 | temperatuur |
| `press_hPa` | hPa | BMP390 | luchtdruk |
| `alt_m` | m | BMP390 | hoogte, uitgerekend uit de luchtdruk |
| `lat`, `lon` | ° | GPS | breedtegraad en lengtegraad. Zonder fix: een vaste nep-waarde. |
| `time_utc` | uu:mm:ss | GPS | wereldtijd (UTC). `00:00:00` = nog geen fix |
| `gyro_x/y/z` | °/s | BNO055 | draaisnelheid rond elke as |
| `lacc_x/y/z` | m/s² | BNO055 | versnelling door bewegen (zonder zwaartekracht) |
| `grav_x/y/z` | m/s² | BNO055 | zwaartekracht, verdeeld over de drie assen |
| `heading`, `roll`, `pitch` | ° | BNO055 | hoe de CanSat gedraaid staat |
| `qw`, `qx`, `qy`, `qz` | — | BNO055 | dezelfde draaiing als *quaternion*: een wiskundige notatie zonder de problemen van hoeken |
| `fft_peak_hz` | Hz | LSM6DSO | sterkste trilling |
| `fft_peak_amp` | g | LSM6DSO | hoe sterk die trilling is (1 g = 9,81 m/s²) |
| `audio_rms` | — (0–1) | SPH0645 | geluidsniveau van de afgelopen seconde |
| `acc_peak_g` | g | LSM6DSO | grootste versnelling van de afgelopen seconde, met de zwaartekracht erbij |
| `gps_course_deg` | ° | GPS | richting waarin de CanSat over de grond beweegt: 0 = noord, 90 = oost, 180 = zuid, 270 = west |
| `gps_speed_ms` | m/s | GPS | snelheid over de grond |
| `vib_0_10_g` … `vib_120_208_g` | g | LSM6DSO | trilling (RMS) in elk van de 5 frequentiebanden: 0–10, 10–30, 30–60, 60–120, 120–208 Hz |

### E3. Normale waarden

| Kolom | CanSat stil op tafel | Opmerking |
|---|---|---|
| `temp_C` | kamertemperatuur | Stijgt een paar graden als de elektronica opwarmt. |
| `press_hPa` | 950–1030 | Hangt af van het weer en de hoogte van je school. |
| `alt_m` | ongeveer de hoogte van je school boven zeeniveau | Verandert ook met het weer. Het dashboard toont het verschil met de start. |
| `lacc_x/y/z` | ongeveer 0 (±0,2) | |
| `grav_z` | ongeveer 9,8 | als de CanSat rechtop staat |
| `gyro_x/y/z` | ongeveer 0 (±1) | |
| `fft_peak_hz` | willekeurig | In rust is er geen echte trilling, dus de "piek" is toeval. |
| `fft_peak_amp` | kleiner dan 0,01 g | Hard schudden: 0,3–1 g. |
| `acc_peak_g` | ongeveer 1,0 | Dat is de zwaartekracht. Een tik op de tafel: 3–8 g. Schudden: 2–4 g. |
| `vib_..._g` | 0,0002–0,002 per band | Dat is de ruis van de sensor. Brede banden geven iets meer ruis. Schudden: de band 0–10 Hz stijgt naar 0,2–0,6 g. |
| `gps_speed_ms` | 0 (zonder fix) of bijna 0 | Wandelen: 1–1,5 m/s. Stilstaand springt `gps_course_deg` willekeurig rond: dat is normaal. |
| `audio_rms` | 0,001–0,005 | Zelfde als in `SPH0645_test`. Een korte klap geeft hier een **lagere** waarde dan in die test: de sketch middelt over 1 s, de test over 0,1 s. Aanhoudend geluid geeft ongeveer hetzelfde. |

> In VIBRATION PER BAND verschijnt de sterkste frequentie pas als `fft_peak_amp` groter
> is dan 0,3 g. Anders staat er `no strong vibration`. De lijst `most frequent` met de 5
> vaakste trillingen verschijnt pas na 20 zulke metingen. Dat is ongeveer 20 s stevig
> schudden.

### E4. Woordenlijst

| Woord | Betekenis |
|---|---|
| **Arduino IDE** | programma om code te schrijven en naar de microcontroller te sturen |
| **baud** | snelheid van een seriële verbinding in bits per seconde. 115 200 baud is ongeveer 11 500 tekens per seconde. |
| **bibliotheek / pakket** | code die iemand anders geschreven heeft en die jij kan gebruiken |
| **COM-poort** | de naam die Windows geeft aan een seriële verbinding, bv. COM5 |
| **Cd** | luchtweerstandscoëfficiënt: een getal dat zegt hoe goed de parachute de lucht tegenhoudt |
| **compileren** | code vertalen naar instructies die de microcontroller begrijpt |
| **CSV** | tekstbestand met een tabel; de waarden staan gescheiden door komma's |
| **FFT** | rekenmethode die uitzoekt welke frequenties in een signaal zitten |
| **fix** | de GPS heeft genoeg satellieten gevonden om zijn positie te berekenen |
| **g** | versnelling uitgedrukt in de zwaartekracht: 1 g = 9,81 m/s² |
| **hPa** | hectopascal, eenheid van luchtdruk (ongeveer 1013 hPa op zeeniveau) |
| **Hz** | hertz: aantal keer per seconde |
| **I²C** | verbinding met 2 draden waarop meerdere sensoren kunnen hangen, elk met een eigen adres |
| **I²S** | verbinding speciaal voor digitale audio |
| **luchtdichtheid (ρ)** | hoeveel kilogram lucht er in 1 m³ zit. Hoger in de lucht is het minder. |
| **microcontroller** | kleine computer op één chip, gemaakt om dingen te meten en aan te sturen |
| **model** | een berekening die de werkelijkheid nabootst, met formules en gemeten getallen |
| **opdrachtprompt** | venster waarin je commando's typt (`cmd`) |
| **RMS** | soort gemiddelde dat aangeeft hoe groot een trilling of geluid is |
| **sensorfusie** | metingen van meerdere sensoren combineren tot één betere meting |
| **sketch** | een Arduino-programma (bestand `.ino`) |
| **upload** | het gecompileerde programma naar de microcontroller sturen |

### E5. Alle commando's op een rij

Altijd in een opdrachtprompt in `C:\CanSat`:

```
py -m pip install -r dashboard\requirements.txt           (eenmalig)

py tools\serial_logger.py --list                          COM-poort zoeken
py tools\serial_logger.py COM5 metingen\test_01.csv       metingen opslaan (stoppen: Ctrl+C)

py dashboard\dashboard_scherm1.py --live metingen\test_01.csv
py dashboard\dashboard_scherm2.py --live metingen\test_01.csv
py dashboard\dashboard_scherm1.py --replay metingen\test_01.csv
py dashboard\dashboard_scherm1.py --replay metingen\test_01.csv --speed 4
py dashboard\dashboard_scherm1.py --sim                   vluchtsimulator

py tools\check_csv.py metingen\test_01.csv                meting controleren
py tools\gen_test_csv.py metingen\oefen.csv               nep-metingen maken
py tools\gen_test_csv.py metingen\oefen.csv --live        nep-metingen, 1 per seconde
py tools\gen_test_csv.py metingen\oefenvlucht.csv --vlucht   een oefenvlucht (Cd 0,50)
py tools\krachten_analyse.py metingen\vlucht.csv          na de vlucht: Cd en krachten
py start_meting.py                                         logger + 2 dashboards in één keer
```

---

## Deel F — Na de vlucht: de krachten op de CanSat

Na de vlucht kan je uitrekenen welke krachten op de CanSat werkten, en **waar**. Dat
doet `tools\krachten_analyse.py`. Je hebt alleen het meetbestand nodig.

### F1. Wat het programma uitrekent

1. **De vlucht in stukken:** lancering, hoogste punt, parachute open, landing.
2. **De Cd van de parachute.** In de rustige daling valt de CanSat even snel. Dan is
   de luchtweerstand even groot als het gewicht:

   ```
   ½ · ρ · v² · Cd · A = m · g      dus      Cd = 2 · m · g / (ρ · v² · A)
   ```

   - v = de daalsnelheid, uit de hoogtemeter
   - ρ = de luchtdichtheid, uit jullie **eigen** druk en temperatuur: ρ = p / (287 · T),
     met p in pascal en T in kelvin
   - m = de massa van de CanSat, A = de oppervlakte van de parachute
3. **De controle.** Met die Cd rekent het programma voor elke seconde uit hoe hard de
   parachute trekt. Dat zet het naast wat de sensor mat. Komt het overeen? Dan klopt
   het model. Een tweede controle: de Cd moet op elke hoogte ongeveer gelijk zijn. Hoog
   in de lucht is de lucht dunner. Daar valt de CanSat dus sneller, maar de Cd blijft
   dezelfde.
4. **De kracht op elke hoogte in het blik**, voor elk moment van de vlucht.
5. **De zones:** waar het blik het meest en waar het het minst moest dragen.
6. **De energie**, uit de hoogtemeter:
   - hoogte-energie = m · g · h, bewegingsenergie = ½ · m · v²;
   - na de motor blijft de som bijna gelijk: beweging wordt hoogte;
   - onder de parachute verdwijnt elke seconde m · g · v. De parachute zet die energie
     om in warmte en wervelingen in de lucht. Voor de oefenvlucht is dat ongeveer
     27 W: zoveel als een kleine lamp.

### F2. Het idee: waar komt de kracht binnen?

- De sensor meet hoeveel g de CanSat voelt. Bij 10 g duwt of trekt elk onderdeel met
  10 keer zijn eigen gewicht: **F = m · n · g**.
- De kracht komt op één plaats binnen:
  - **onderaan** bij de lancering (de raket duwt) en bij de landing (de grond duwt).
    Het blik wordt dan **samengedrukt**.
  - **bovenaan** als de parachute trekt. Het blik wordt dan **uitgerekt**.
- Een plek in het blik moet alles dragen wat verder van die plaats ligt. Hoe dichter bij
  de plaats waar de kracht binnenkomt, hoe groter de kracht.

**Voorbeeld:** bij de lancering met 10 g draagt de bodem de hele CanSat:
0,330 kg × 10 × 9,81 m/s² = 32 N. Halverwege draagt het blik alleen de bovenste helft:
16 N. Het deksel draagt bijna niets. Hangt de CanSat aan de parachute, dan is het net
andersom.

### F3. De gegevens van jullie CanSat invullen

Open `dashboard\krachten.py`, bijvoorbeeld in Thonny. Bovenaan staat:

```
MASS_KG = 0.330               # de hele CanSat MET parachute (gewogen)
PARACHUTE_MASS_KG = 0.0       # de parachute alleen (0 = nog niet gewogen)
PARACHUTE_DIAMETER_M = 0.45   # diameter van de parachute, plat uitgelegd
HEAVY_PARTS = [ ... ]         # zware onderdelen: naam, massa, hoogte
```

- Weeg en meet, en vul in. Gebruik een **punt**, geen komma: `0.330`.
- Zware onderdelen (bijvoorbeeld de batterij) mag je apart invullen, met de hoogte van
  hun midden boven de bodem. Dan wordt het model nauwkeuriger. Laat je de lijst leeg,
  dan is de massa gelijk verdeeld over de hoogte.
- De dashboards gebruiken dezelfde gegevens.

### F4. Oefenen zonder vlucht

Op tafel kan je dit niet testen: daar is geen vlucht. Maak daarom een oefenvlucht:

```
py tools\gen_test_csv.py metingen\oefenvlucht.csv --vlucht
py tools\krachten_analyse.py metingen\oefenvlucht.csv
```

De oefenvlucht is berekend met de natuurkunde: een lancering met 10 g, een hoogste punt
op ongeveer 950 m, een parachute en een landing. De Cd van de parachute is daarin
**0,50**. Vindt het programma 0,50? Dan werkt de methode.

Je kan de oefenvlucht ook in de dashboards afspelen:

```
py dashboard\dashboard_scherm2.py --replay metingen\oefenvlucht.csv --speed 4
```

### F5. Na de echte vlucht

1. Kopieer het bestand van de SD-kaart naar `C:\CanSat\metingen\`, bijvoorbeeld als
   `vlucht.csv`.
2. Typ in een opdrachtprompt in `C:\CanSat`:
   ```
   py tools\krachten_analyse.py metingen\vlucht.csv
   ```
3. Lees het verslag in het venster. De figuren staan in `metingen\vlucht_krachten\`.

Gebruik het bestand van de **SD-kaart**. Daarin staat elke seconde de grootste
versnelling (`acc_peak_g`). In het radiobestand zit die niet. Dan kent het programma
de lancering en de landing niet, en zegt het dat ook.

### F6. De figuren

| Bestand | Wat zie je? |
|---|---|
| `1_vlucht.png` | de hoogte en de grootste versnelling per seconde, met de lancering, de parachute en de landing |
| `2_parachute_cd.png` | links de daalsnelheid op elke hoogte, rechts de Cd van elke seconde |
| `3_controle.png` | de kracht volgens het parachutemodel naast de kracht volgens de sensor |
| `4_kracht_per_hoogte.png` | de kracht door het blik op elke hoogte, voor elk moment |
| `5_zones.png` | het blik in kleuren: groen is weinig, rood is 20 g op de bodem (de ESA-eis) |
| `6_energie.png` | boven de hoogte-energie, de bewegingsenergie en de som; onder het vermogen van de parachute |
| `krachten_per_seconde.csv` | alle getallen per seconde, om zelf grafieken te maken |

De tekst in de figuren is in het Engels, net als in de dashboards.

### F7. Wat het programma níet kan

- **Het is een model.** Geen enkele sensor meet de kracht in het blik zelf. Het
  programma rekent met de gemeten g en de massa. Ingenieurs doen het ook zo. Zeg dat
  eerlijk in je presentatie.
- **De sensor meet tot 16 g.** Een grotere schok wordt afgeknipt. Het verslag zegt dan
  "≥ 16 g": minstens 16 g. Bij de landing kan dat gebeuren.
- **Eén hoogte per seconde.** De daalsnelheid is daardoor een gemiddelde over
  2 seconden. Bij het openen van de parachute verandert de snelheid heel snel. Daarom
  schat het model die kracht te laag.
- **Uitwerpen en parachute vallen samen.** Ze liggen maar enkele seconden uit elkaar.
  Het programma neemt de grootste piek van die seconden.
- **Alleen krachten langs het blik.** Zijwaartse krachten (buigen) rekent het niet. Het
  controleert met de BNO055 of ze klein zijn.

### F8. Vragen om over na te denken

1. Waarom valt de CanSat hoog in de lucht iets sneller dan vlak bij de grond?
2. Jullie temperatuursensor zit binnen in het blik. Stel dat hij 10 °C te warm meet.
   Hoeveel procent verandert de Cd dan? Reken het uit.
3. Bij het openen van de parachute geeft het model minder g dan de sensor. Bedenk twee
   redenen.
4. Waar is het blik het minst belast? Kan je daar materiaal en dus massa besparen?
5. Waar zou jij de batterij zetten: onderaan of bovenaan? Vul ze in bij `HEAVY_PARTS`
   en vergelijk.
6. Na de motor blijft de totale energie bijna gelijk. Bij een echte vlucht daalt ze
   een beetje. Waar gaat die energie naartoe?

---

## Voor de leerkracht

- **Nieuwe kolommen:** `acc_peak_g` is de grootste versnelling per logregel (LSM6DSO,
  ±16 g). De BNO055 meet standaard maar tot 4 g en zou een schok afkappen.
  `gps_course_deg` en `gps_speed_ms` zijn de afdrijfrichting en -snelheid volgens de GPS.
  De vluchtcode (`Cansat2027_teensy.ino`) schrijft dezelfde 34 kolommen naar de
  SD-kaart. Via LoRa gaan 19 waarden, ook de FFT (piek en 5 banden). De dashboards
  lezen ook oude bestanden met 26, 27 of 29 kolommen.
- **Trillingsbanden, technisch:** per band
  RMS = √( 2 · Σ|X_k|² / (N² · ⟨w²⟩) ), met N = 512, X_k de FFT-bins in de band (DC-bin
  uitgesloten), en ⟨w²⟩ = 0,39664 voor het symmetrische 512-punts Hamming-venster van
  arduinoFFT. De binfrequenties gebruiken de vaste 416 Hz van de timer: een pauze van
  de loop is een gat in de metingen, geen tragere meting. De sterkte van de piek
  (`fft_peak_amp`) komt uit de energie in de bins k−2 … k+2 (ook Parseval), en klopt dus
  ook als de frequentie tussen twee bins valt. De berekening
  is vergeleken met een referentie in Python én met de C++-code van de sketch zelf, met
  dezelfde uitkomst (0,3535 g voor een sinus van 0,5 g bij 25 Hz). De Teensy leest de
  sensor met een eigen timer van 416 Hz, los van de klok van de sensor. Door het kleine
  verschil wordt af en toe een sample dubbel gelezen of overgeslagen. Dat geeft een
  kleine vervorming; een FIFO-uitlezing zou dat oplossen.

- **SD-kaart (optioneel):** zit er een microSD-kaart (FAT32) in de Teensy, dan schrijft
  de sketch dezelfde regels ook naar `test_000.csv`, `test_001.csv`, … op de kaart (elke
  opstart een nieuw bestand). Voor de live-test is dat niet nodig.
- **Sneller loggen:** zet `LOG_INTERVAL_MS` bovenaan in de sketch op `100` voor 10 regels
  per seconde. De dashboards werken daar ook mee.
- **FFT:** de Teensy leest de sensor op een vast ritme van 416 keer per seconde. Staat de
  loop even stil (BMP390-meting, schrijven naar de SD-kaart), dan is dat een klein gat
  in de metingen; de frequentie klopt toch. Een nieuw FFT-resultaat is er elke 1,2 s;
  bij 1 regel per seconde staat dezelfde waarde dus soms twee keer in de CSV.
- **Hoogte-as:** `GROUND_TEST_M = 50` bovenaan in `dashboard_scherm1.py`. Was de
  hoogste hoogte (ten opzichte van de eerste 10 rijen) nooit meer dan 50 m, dan is het
  een grondtest: de grafiek past zich aan de metingen aan (minstens 5 m hoog, 0 altijd
  zichtbaar). Daarboven de vaste as van 0 tot 1100 m. Bij een herstart van de CanSat
  begint het opnieuw.
- **Tijdas:** de Teensy telt vanaf het aanzetten (`millis`). Op de lanceerplaats kan hij
  lang aan staan voor de lancering. Daarom tellen de dashboards vanaf de eerste meting, en
  na de lancering vanaf de lancering (de laatste meting op de grond voor de klim). De
  grafieken van scherm 1 lopen dan van `LAUNCH_LEAD_S = 30` s voor de lancering tot
  `AFTER_LANDING_S = 60` s na de landing (bovenaan in `dashboard_scherm1.py`).
- **Luchtdruk op zeeniveau:** de sketches rekenen de hoogte met een vaste waarde
  (`SEA_LEVEL_PRESSURE` = 1014 hPa). De dashboards rekenen die hoogte om naar de
  luchtdruk op zeeniveau die je bij de start ingeeft (`--sea-level`, standaard 1013 hPa).
  Ze vertrekken van de hoogte van de Teensy en niet van de luchtdruk: in het radiopakket
  staat de luchtdruk met maar 1 cijfer na de komma (±0,4 m). De hoogte boven de start
  verandert daardoor bijna niet (minder dan 0,5 %). De hoogte boven zeeniveau wel: 8 m
  per hPa. Scherm 1 toont die van de startplaats (`start … m ASL`). Vergelijk ze met de
  echte hoogte van de lanceerplaats. Pas je `SEA_LEVEL_PRESSURE` in de sketch toch aan,
  dan ziet het dashboard dat aan de metingen en rekent het mee. De Serial Monitor toont
  de hoogte van de Teensy zelf.
- **Kaart in scherm 2:** gecentreerd op de eerste GPS-fix. Open scherm 2 vooraf met
  internet op de lanceerplaats (bv. een replay van een korte test daar), zodat de
  kaarttegels bewaard worden voor gebruik zonder internet.
- **Krachtenmodel (`dashboard\krachten.py`):** alleen axiale krachten. De normaalkracht
  op hoogte z is N(z) = n · g · m_ver(z): de massa aan de andere kant van de doorsnede,
  gezien vanaf het steunpunt. Steunpunt onderaan op het platform, bij de lancering en
  bij de landing (een schok > 2,5 g onder 25 m tijdens de daling geldt als landing);
  bovenaan bij APOGEE en DESCENT. n is `acc_peak_g` (LSM6DSO); zonder die kolom de
  BNO055 (|lacc + grav|, of 1 + |lacc|/g in het radiobestand, een bovengrens). De kleur
  is N(z) gedeeld door 20 g · g · m. De parachute zit tijdens de lancering verpakt
  bovenaan en hoort dan bij de massa; aan de parachute niet meer.
- **Cd:** scherm 1 en `krachten_analyse.py` gebruiken ρ = p / (R · T) uit de eigen
  druk en temperatuur (R = 287,05 J/(kg·K)). Scherm 1 toont de mediaan over de
  daalfase. Het analyseprogramma neemt alleen de rustige daling: binnen 20 % van de
  gewone daalsnelheid, versnelling < 0,6 m/s². Op de oefenvlucht (`--vlucht`, Cd 0,50)
  vindt het 0,50 terug (0,48 tot 0,52).
- **Energie:** E_h = m·g·h en E_b = ½·m·v² met v de verticale snelheid uit de
  hoogtemeter (centrale differentie over 2 s); horizontaal (wind) telt niet mee. Het
  vermogen van de parachute is −dE/dt, van het openen tot de laatste rij boven de
  grond; in de rustige daling is dat m·g·v.
- **Python-versie:** 3.9 of nieuwer.
