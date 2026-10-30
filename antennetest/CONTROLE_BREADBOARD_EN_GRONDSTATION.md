# CanSat 2027 — Werkt de radio? Controle van het breadboard en het grondstation

Werkt de meting via de radio niet? Test dan de twee helften apart: eerst het breadboard
(de zender), dan het grondstation (de ontvanger). Zo weet je meteen aan welke kant de
fout zit.

## Eerst: staat de juiste code op de Teensy?

**De sensortest (`sensortest_fft.ino`) zendt niets via de radio.** Voor de antenne heb je
de vluchtcode nodig: `Cansat2027_teensy.ino`.

---

## Deel 1 – Het breadboard, in de Serial Monitor van Arduino

1. Stop `START_METING` en sluit de dashboards.
2. Steek de Teensy met de USB-kabel in de laptop. De antenne zit op de radio.
3. Open de Arduino IDE en de **Serial Monitor** op 115200 baud.
4. Trek de USB-kabel even uit en steek hem terug. Nu zie je het begin.

Zo hoort het eruit te zien:

```
CanSat 2027 - Teensy 4.1
...
--- Status ---
BMP390 : OK
BNO055 : OK
LSM6DSO: OK
LoRa   : OK
SD     : FOUT (niets op de SD-kaart)
```

Daarna komt er elke seconde een lange regel met getallen. Het lampje op de Teensy flikkert
elke seconde even: dan zendt de radio.

| Wat je ziet | Wat betekent het? |
|---|---|
| `=== CanSat 2027 — Sensortest ===` en geen regel `LoRa` | De sensortest staat erop: er wordt niets gezonden. Zet de vluchtcode erop. |
| `LoRa : FOUT` | De Teensy vindt de radio niet. Kijk de 8 draden na: 3.3V, GND, 13, 12, 11, 10, 9 en 2. |
| `LoRa : OK` | Het breadboard zendt elke seconde een pakket. Deze helft is in orde. |
| een sensor met `FOUT` | Kijk de vier draden van die sensor na. Dit stoort de radio niet. |
| `SD : FOUT` | Er zit geen SD-kaart in. Dat mag. |

---

## Deel 2 – Het grondstation, in Thonny

1. Steek de Pico in de laptop.
2. Open Thonny. Kies **rechtsonder** `MicroPython (Raspberry Pi Pico)`.
3. Klik op de rode **Stop**-knop. Open `main.py` van de Pico
   (**File → Open… → Raspberry Pi Pico**) en druk op **F5**.

Zo hoort het eruit te zien:

```
# CanSat 2027 - ontvanger (Raspberry Pi Pico) start
# Instellingen: 868.0 MHz, BW 125.0 kHz, SF7, CR 4/7, sync word 0x12
# Radio OK. Wacht op pakketten van de CanSat ...
```

Het lampje van de Pico flitst om de 2 seconden. Staat het breadboard aan met de
vluchtcode? Dan komt er elke seconde een regel met getallen bij: 19 waarden, gevolgd door
de RSSI en de SNR.

| Wat je ziet | Wat betekent het? |
|---|---|
| `# FOUT: Radio niet gevonden ... 0x00` of `0xFF` | De Pico vindt zijn radio niet. Kijk de draden na: MISO, CS, SCK, 3.3V en GND. Kloppen de pinnen bovenaan `main.py`? |
| `# FOUT: deze pinnen horen niet bij SPI0` | `SPI_BUS` past niet bij de pinnen bovenaan `main.py`. |
| `# Radio OK` en daarna `# Al 10 s geen pakket` | De ontvanger werkt, maar hoort niets. Zendt het breadboard wel (deel 1)? Staan beide antennes erop? |
| `# Onbekend pakket genegeerd` | Er komt iets aan, maar niet van onze vluchtcode. Zet de vluchtcode opnieuw op de Teensy. |
| `# Beschadigd pakket (CRC-fout)` | Er komt iets aan, maar met fouten. Zet de antennes recht. Zelden is normaal. |
| elke seconde een regel met getallen | Alles werkt! |

---

## Deel 3 – Allebei tegelijk kijken

Dat kan op dezelfde laptop: de Serial Monitor kijkt naar de Teensy, Thonny naar de Pico.
Elke seconde verschijnt er een regel in de Serial Monitor, en meteen daarna een regel in
Thonny. Dan weet je zeker dat de verbinding werkt.

**Werkt de radio maar komt er toch niets aan?** Vergelijk dan de instellingen. De regel
`# Instellingen` van de Pico moet overeenkomen met de vluchtcode: 868.0 MHz, BW 125, SF7,
CR 4/7 en sync word 0x12.

---

## Na de controle, voor het dashboard

1. Sluit de Arduino IDE helemaal.
2. Klik in Thonny op **Stop** en kies rechtsonder `Local Python 3`, of sluit Thonny.
3. Trek de Pico uit en steek hem terug.
4. Start `START_METING.bat` en kies `← Pico (ontvanger)`.
