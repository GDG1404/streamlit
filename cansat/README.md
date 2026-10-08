# CanSat 2027 — Sensortest & Dashboard

Handleiding voor de sensortest van de CanSat. De Teensy leest alle sensoren uit
en stuurt elke seconde een CSV-regel via USB naar de laptop. Daar schrijft
`serial_logger.py` die regels naar een CSV-bestand op de C-schijf, en het
dashboard leest dat bestand **live** mee.

```
Teensy ──USB──► serial_logger.py ──► C:\CanSat\cansat27_live.csv ──► dashboard --live
```

> **Kort samengevat:** sketch uploaden → Seriële Monitor controleren en sluiten →
> `serial_logger.py` starten → dashboard starten met `--live` → testen.

---

## 1. Inhoud van deze map

| Bestand | Wat doet het? |
|---|---|
| `sensortest_fft/sensortest_fft.ino` | Arduino-sketch voor de Teensy 4.1: leest alle sensoren, berekent de FFT en stuurt 1× per seconde een CSV-regel via USB naar de laptop (en naar de SD-kaart als die erin zit). |
| `dashboard/dashboard_scherm1.py` | Dashboard (scherm 1): hoogte, versnelling, gyroscoop, FFT, audio, vluchtfase en Cd. |
| `dashboard/dashboard_scherm2.py` | Dashboard (scherm 2): 3D-vluchtbaan, kaart, oriëntatie van het blik met belasting, radioverbinding. Heeft `dashboard_scherm1.py` in dezelfde map nodig. |
| `dashboard/requirements.txt` | Python-pakketten die je nodig hebt. |
| `tools/check_csv.py` | Controleert of een CSV correct is en toont een samenvatting van de metingen. |
| `tools/gen_test_csv.py` | Maakt een test-CSV **zonder hardware**, handig om het dashboard te leren kennen. |
| `tools/serial_logger.py` | Schrijft de CSV-regels die de Teensy via USB stuurt naar een bestand op de laptop (bv. op de C-schijf). Het dashboard leest dat bestand live. |

---

## 2. Wat heb je nodig?

### Hardware

| Onderdeel | Functie | Aansluiting op de Teensy 4.1 |
|---|---|---|
| BMP390 | luchtdruk, temperatuur, hoogte | I²C: SDA → pin 18, SCL → pin 19 (adres 0x77) |
| BNO055 | oriëntatie, lineaire versnelling, gyroscoop, zwaartekracht | I²C: SDA → pin 18, SCL → pin 19 (adres 0x28) |
| LSM6DSO | snelle versnellingsmeter (416 Hz) voor de FFT | I²C: SDA → pin 18, SCL → pin 19 (adres 0x6B) |
| GPS PA1616D | positie en UTC-tijd | Serial1: GPS-TX → pin 0 (RX1), GPS-RX → pin 1 (TX1) |
| SPH0645 | microfoon (I²S) | BCLK → pin 21, LRCL → pin 20, DOUT → pin 8, SEL → GND |
| microSD-kaart *(optioneel)* | extra kopie op de CanSat | ingebouwde SD-sleuf van de Teensy 4.1 (FAT32). Nu nog niet nodig. |

Alle sensoren werken op **3,3 V**. Sluit ze nooit aan op 5 V.

### Software op de computer

1. **Arduino IDE 2** met **Teensyduino**. Ga naar *Bestand → Voorkeuren → Additional
   boards manager URLs*, voeg `https://www.pjrc.com/teensy/package_teensy_index.json`
   toe en installeer daarna "Teensy" in de Boards Manager.
2. **Arduino-bibliotheken** (*Tools → Manage Libraries*):
   - Adafruit BMP3XX Library
   - Adafruit BNO055
   - Adafruit Unified Sensor
   - Adafruit GPS Library
   - SparkFun LSM6DSO: de versie **zonder X** (niet de LSM6DSOX), te installeren via de GitHub-zip zoals in de StartGids (*Sketch → Include Library → Add .ZIP Library*)
   - arduinoFFT (van Enrique Condes, versie 2.x)

   `Audio`, `SD`, `Wire` en `SPI` worden al met Teensyduino geïnstalleerd.
3. **Python 3.9 of nieuwer**, met de pakketten uit `requirements.txt`:
   ```
   cd dashboard
   pip install -r requirements.txt
   ```
   Op Linux heb je ook Tkinter nodig: `sudo apt install python3-tk`.

---

## 3. Eerst zonder hardware: het dashboard leren kennen

Je kan het dashboard al uitproberen zonder Teensy:

```
cd tools
python gen_test_csv.py test_000.csv
python ../dashboard/dashboard_scherm1.py --replay test_000.csv
```

De test-CSV beschrijft een bureautest van 2 minuten. Dit zou je moeten zien:

| Tijd | Wat gebeurt er? | Wat zie je in het dashboard? |
|---|---|---|
| 0–25 s | GPS heeft nog geen fix | `time_utc` = `00:00:00` |
| 40–55 s | CanSat wordt geschud | pieken in de versnellings- en gyroscoopgrafiek, FFT-piek rond 4–5 Hz |
| 60 s | handklap | piek in de AUDIO RMS-grafiek |
| 70–90 s | trap op gelopen | hoogte stijgt ongeveer 6 m. De fase blijft **PRELAUNCH**: een trap is geen lancering. |

Scherm 2 open je op dezelfde manier, eventueel tegelijk in een tweede venster:

```
python ../dashboard/dashboard_scherm2.py --replay test_000.csv
```

Andere opties (gelden voor beide schermen):

```
python dashboard_scherm1.py --sim                 # ingebouwde vluchtsimulator
python dashboard_scherm1.py --replay x.csv --speed 4   # 4× sneller afspelen
python dashboard_scherm1.py --help
```

---

## 4. De sensortest met de Teensy

### Stap 1 — Sketch uploaden

1. Open `sensortest_fft/sensortest_fft.ino` in de Arduino IDE.
2. Kies *Tools → Board → Teensy 4.1* en de juiste poort.
3. Klik op **Upload**.

Een SD-kaart is niet nodig. Zonder kaart meldt de sketch `SD kaart ... FOUT` en
gaat gewoon verder via USB.

### Stap 2 — Seriële Monitor controleren

Open de Seriële Monitor (115200 baud). Na een paar seconden zie je:

```
=== CanSat 2027 — Sensortest + FFT + CSV ===
BMP390 ... OK
BNO055 ... OK
LSM6DSO ... OK
GPS PA1616D ... OK
SD kaart ... FOUT

--- Sensorstatus ---
...
--- logging gestart ---
millis,temp_C,press_hPa,alt_m,...
5212,21.43,942.10,612.31,...
```

- Elke seconde verschijnt er een nieuwe regel.
- De LED op de Teensy knippert elke seconde: dan draait het programma.
- `SD kaart ... FOUT` is normaal zonder SD-kaart.

**Sluit daarna de Seriële Monitor.** Maar één programma tegelijk kan de USB-poort
gebruiken, en in de volgende stap heeft `serial_logger.py` die nodig.

### Stap 3 — Live loggen naar de C-schijf en het dashboard starten

Open twee (of drie) terminalvensters in de map van dit pakket. Start ze **in deze
volgorde**: het dashboard heeft het bestand nodig dat de logger aanmaakt.

```
# venster 1: poort opzoeken, daarna loggen naar de C-schijf
python tools/serial_logger.py --list
python tools/serial_logger.py COM5 C:\CanSat\test_01.csv

# venster 2: dashboard scherm 1, leest hetzelfde bestand live
python dashboard/dashboard_scherm1.py --live C:\CanSat\test_01.csv

# venster 3 (optioneel): scherm 2
python dashboard/dashboard_scherm2.py --live C:\CanSat\test_01.csv
```

- Vervang `COM5` door de poort die `--list` toont bij de Teensy.
- De map `C:\CanSat` wordt vanzelf aangemaakt.
- Gebruik **per test een nieuwe bestandsnaam** (`test_01.csv`, `test_02.csv`, …).
  Bestaat het bestand al, dan schrijft de logger er achteraan bij.
- Venster 1 telt de gelogde rijen. Meldingen van de Teensy die geen CSV zijn,
  verschijnen daar met `[Teensy]` ervoor en komen niet in het bestand.
- Sluit je het dashboard af en start je het opnieuw, dan haalt het alle rijen die
  al in het bestand stonden meteen in. Zolang venster 1 draait, gaat er niets verloren.
- Stoppen: **Ctrl+C** in venster 1, en sluit de dashboardvensters.

> Start je het dashboard vóór de logger, dan vindt het het bestand niet en toont
> het de simulator ("SIMULATED TEST DATA"). Sluit het dan en start het opnieuw.

### Stap 4 — Testen uitvoeren

Voer deze testen uit en kijk meteen in het dashboard wat er gebeurt:

1. **In rust** (30 s): CanSat stil op tafel.
2. **Schudden** (15 s): schud de CanSat stevig met de hand.
3. **Klap** naast de microfoon.
4. **Draaien**: draai de CanSat langzaam rond de verticale as. Op scherm 2 moet
   het blik rechts in dezelfde richting meedraaien.
5. **Hoogte**: loop een trap op en weer af (laptop mee, of een lange USB-kabel).
6. **GPS**: ga naar buiten met vrij zicht op de lucht en wacht tot `time_utc`
   niet meer `00:00:00` is. De eerste fix kan enkele minuten duren.

Op scherm 2:
- Na het schudden kleurt het blik oranje tot rood. De kleur blijft staan ("peak hold"):
  zo zie je achteraf waar de belasting het grootst was.
- Druk op **M** om te wisselen tussen de 3D-baan en de 2D-kaart. De kaart toont de
  plaats waar je staat: ze wordt gecentreerd op de **eerste GPS-fix** en de titel
  toont die coördinaten. Zonder fix staat er `WAITING FOR GPS FIX`. Drijft de
  CanSat verder af dan de kaart reikt (±1 km), dan zoomt de kaart vanzelf uit,
  tot ongeveer ±15 km. Alleen de simulator (`--sim`) toont Elsenborn.

### Stap 5 — CSV controleren

Na de test (of tussendoor, terwijl de logger draait):

```
python tools/check_csv.py C:\CanSat\test_01.csv
```

Je krijgt een samenvatting:

```
Rijen   : 312 geldig van 312
Duur    : 311 s  →  1.00 rijen/s
GPS-fix : 0/312 rijen  (geen fix: buiten testen, antenne vrij zicht)

Kolom          min        max      (controleer of dit logisch is)
  temp_C          21.360     21.440
  ...
OK: het dashboard kan dit bestand lezen.
```

Controleer of de waarden logisch zijn (zie §6). Staat er **LET OP: deze kolommen
veranderen nooit**? Dan werd die sensor waarschijnlijk niet gevonden. Kijk dan in
venster 1 of de Seriële Monitor of hij `FOUT` meldt.

### Stap 6 — Achteraf opnieuw bekijken (replay)

Een opgeslagen test speel je opnieuw af met `--replay`:

```
python dashboard/dashboard_scherm1.py --replay C:\CanSat\test_01.csv
python dashboard/dashboard_scherm2.py --replay C:\CanSat\test_01.csv --speed 4
```

Zonder Teensy kan je de live-modus ook testen. In venster 1 schrijft dit 1 regel
per seconde, net zoals de logger:
```
python tools/gen_test_csv.py C:\CanSat\oefen.csv --live
```

### Optioneel — SD-kaart

Steek je een microSD-kaart (FAT32) in de Teensy, dan schrijft de sketch dezelfde
regels ook naar `test_000.csv`, `test_001.csv`, … op de kaart (elke opstart een
nieuw bestand). Dat is een reservekopie. Voor de live-test is ze niet nodig.

---

## 5. De CSV-kolommen

Er zijn 26 kolommen, altijd in deze volgorde. Wijzig je de sketch, verander dan
de kolommen **niet**: het dashboard verwacht ze precies zo.

| Kolom | Eenheid | Sensor | Betekenis |
|---|---|---|---|
| `millis` | ms | Teensy | tijd sinds het opstarten |
| `temp_C` | °C | BMP390 | temperatuur |
| `press_hPa` | hPa | BMP390 | luchtdruk |
| `alt_m` | m | BMP390 | hoogte boven zeeniveau, berekend uit de druk (referentie 1014 hPa) |
| `lat`, `lon` | ° | GPS | positie. Zonder fix staan hier vaste plaatshouder-waarden. |
| `time_utc` | hh:mm:ss | GPS | UTC-tijd; `00:00:00` = nog geen fix |
| `gyro_x/y/z` | °/s | BNO055 | draaisnelheid |
| `lacc_x/y/z` | m/s² | BNO055 | lineaire versnelling, zonder zwaartekracht |
| `grav_x/y/z` | m/s² | BNO055 | richting van de zwaartekracht (samen ongeveer 9,8) |
| `heading`, `roll`, `pitch` | ° | BNO055 | oriëntatie (Euler-hoeken) |
| `qw`, `qx`, `qy`, `qz` | — | BNO055 | oriëntatie als quaternion |
| `fft_peak_hz` | Hz | LSM6DSO | sterkste trillingsfrequentie (0–208 Hz) |
| `fft_peak_amp` | g | LSM6DSO | amplitude van die trilling |
| `audio_rms` | — (0–1) | SPH0645 | geluidsniveau van de afgelopen seconde |

---

## 6. Welke waarden zijn normaal?

| Kolom | In rust op tafel | Opmerking |
|---|---|---|
| `temp_C` | kamertemperatuur | Stijgt een paar graden als de printplaat opwarmt. |
| `press_hPa` | 950–1030 | Hangt af van het weer en de hoogte. |
| `alt_m` | ongeveer de hoogte van je school | Varieert met het weer: de referentie 1014 hPa is vast. Het dashboard gebruikt de hoogte t.o.v. de start. |
| `lacc_x/y/z` | ongeveer 0 (±0,2) | |
| `grav_z` | ongeveer 9,8 | als de CanSat rechtop staat |
| `gyro_x/y/z` | ongeveer 0 (±1) | |
| `fft_peak_hz` | willekeurig | In rust is er geen echte trilling; de "piek" is ruis. |
| `fft_peak_amp` | < 0,01 g | Schudden met de hand: 0,3–1 g. |
| `audio_rms` | 0,001–0,005 | Zelfde als in `SPH0645_test`. Een korte klap geeft hier een **lagere** waarde dan in die test: de sketch middelt over 1 s, de test over 0,1 s. Aanhoudend geluid (roepen, muziek) geeft wel ongeveer dezelfde waarde. |

> **Let op:** het dashboard toont een FFT-piek pas als `fft_peak_amp > 0,3`.
> De lijnen met de top-5-frequenties verschijnen pas na 20 zulke regels, dus
> ongeveer 20 s stevig schudden bij 1 meting per seconde.

---

## 7. Problemen oplossen

| Probleem | Oplossing |
|---|---|
| `BMP390 ... FOUT` (of een andere sensor) | Controleer 3,3 V, GND, SDA (18) en SCL (19). Maak een I²C-scan met het voorbeeld *Wire → Scanner*. |
| `SD kaart ... FOUT` | Normaal zonder SD-kaart. Met kaart: goed ingestoken? Geformatteerd als FAT32? |
| `GPS PA1616D ... nog geen data` en `time_utc` blijft `00:00:00`, ook buiten | De sketch blijft de GPS volgen, maar er komt niets binnen: TX/RX omgedraaid? GPS-TX moet naar pin 0. Werkt `GPS_test.ino` wel? |
| GPS geeft nooit een fix | Ga naar buiten met vrij zicht op de lucht. De eerste fix duurt soms 1–5 min. |
| `audio_rms` blijft 0 | Controleer pin 8, 20 en 21 en of SEL aan GND hangt. |
| `serial_logger.py`: poort bezet | Sluit de Seriële Monitor van de Arduino IDE. |
| Dashboard toont "SIMULATED TEST DATA" | Het CSV-bestand werd niet gevonden: controleer het pad achter `--replay` / `--live`. |
| `check_csv.py`: "herhaalde header" | De Teensy is herstart terwijl hij naar hetzelfde bestand schreef. Verwijder die regel. |
| Dashboard start niet: `No module named 'tkinter'` | Linux: `sudo apt install python3-tk`. |
| Scherm 2: kaart (M) is donker, zonder straten | Er was geen internet om de kaarttegels te downloaden. De kaart hangt af van de plaats, dus de tegels moeten **per locatie** één keer gedownload worden. Open vooraf, met internet, scherm 2 met een replay van een korte test op die plaats en druk op M. De tegels worden bewaard in `dashboard/osm_cache` en werken daarna offline. |
| Scherm 2: vluchtbaan staat stil op het startpunt | Normaal zolang er geen GPS-fix is: de positie blijft dan op de laatst bekende plaats staan. |
| Scherm 2: GPS FIX toont "—" | De sketch stuurt het aantal satellieten niet mee. Of er een fix is, zie je onder LATITUDE. |

---

## 8. Tips

- **Bewaar elke CSV** met een duidelijke naam, bv. `2027-03-14_schudtest.csv`.
- **Loggen naar 10 Hz:** zet `LOG_INTERVAL_MS` in de sketch op `100`. Het dashboard
  werkt daar ook mee.
- Scherm 2 rekent de positie uit ten opzichte van de **eerste GPS-fix**. Rijen
  zonder fix tellen niet mee.
- De FFT gebruikt 512 metingen aan 416 Hz, dus elke 1,23 s is er een nieuw resultaat.
  Bij loggen aan 1 Hz staat dezelfde FFT-waarde daardoor soms twee keer in de CSV.
  Dat is normaal.
