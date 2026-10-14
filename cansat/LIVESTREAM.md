# CanSat 2027 — Livestream op YouTube

Met een **extra LoRa-ontvanger**, het **streamdashboard** en het gratis programma
**OBS Studio** zet je de vlucht live op YouTube: grote cijfers, een grafiek van de
hoogte, en het beeld van een camera.

```
CanSat ──LoRa──► extra ontvanger ──USB──► laptop: stream_dashboard.py ─┐
                                                                        ├─► OBS ─► YouTube
                                          camera (gsm of webcam) ───────┘
```

Een extra ontvanger stoort niets. LoRa werkt zoals een radio: elke ontvanger met
dezelfde instellingen hoort hetzelfde pakket.

## Wat heb je nodig?

| Wat | Kost |
|---|---|
| Microcontroller + RFM95W (868 MHz), zoals in de CanSat | ± €20–40 |
| Laptop (mag een andere zijn dan die van het grondstation) | — |
| OBS Studio (obsproject.com) | gratis |
| YouTube-kanaal | gratis |
| Camera: gsm met een webcam-app, of een USB-webcam | €0–30 |
| Internet: hotspot van een gsm (4G is genoeg; ± 1,5 GB per uur) | je databundel |

## Stap 1 — De ontvanger klaarmaken (één keer)

1. Bedraad de RFM95W zoals in de CanSat: CS = pin 10, RST = pin 9, DIO0 = pin 2.
   Een ander bord? Pas de pinnen bovenaan in `ontvanger_stream.ino` aan.
2. Installeer **RadioLib** via de Library Manager van de Arduino IDE.
3. Open `ontvanger_stream\ontvanger_stream.ino` en klik op **Upload**.
4. Open de Serial Monitor (115200 baud). Je ziet:
   `# Klaar: wacht op pakketten van de CanSat`.
   Zet de CanSat aan: er verschijnt elke seconde een regel met getallen.
5. **Sluit de Arduino IDE helemaal.** Anders blijft de USB-poort bezet.

## Stap 2 — Het dashboard proberen zonder hardware

```
py dashboard\stream_dashboard.py --demo
```

Je ziet een nagebootste vlucht. Bovenaan staat duidelijk
**DEMO — simulated flight, not real data**. Zo kan je OBS al instellen.

## Stap 3 — Met de echte ontvanger

```
py dashboard\stream_dashboard.py
```

Kies de poort van de ontvanger in de lijst. Start het dashboard **vóór de lancering**,
als de CanSat nog op de grond staat: de eerste 5 pakketten zijn het nulpunt van de
hoogte. Elk pakket wordt ook bewaard in `metingen\stream_<datum>_<uur>.csv`.
Druk op **F** voor volledig scherm.

## Stap 4 — OBS en YouTube

1. **YouTube:** zet livestreamen aan voor je kanaal, minstens **een dag vooraf**
   (de eerste keer duurt het tot 24 uur).
2. Installeer **OBS Studio** en maak een scène met:
   - **Window Capture** → het venster *CanSat 2027 — Stream*
   - **Video Capture Device** → de camera
3. **Settings → Stream** → kies YouTube en koppel je account.
4. **Settings → Output** → kies een hardware-encoder als die er is
   (QuickSync, NVENC of AMF). Dat spaart de laptop.
5. Klik op **Start Streaming** én **Start Recording**. Zo heb je ook een opname
   als het internet even wegvalt.

> **Tip:** maak in OBS twee scènes, *Camera* en *Dashboard*. Tijdens de vlucht toon
> je het dashboard, daarvoor en daarna de camera. Wisselen is één klik.

## Let op

- **Gsm-hotspot een paar meter van de ontvangers.** Gsm's zenden op frequenties
  dicht bij 868 MHz en kunnen de ontvangst van de CanSat storen.
- **Test het internet op de lanceerplaats.** Vraag ook of er wifi is.
- **Privacy:** komen leerlingen herkenbaar in beeld? Volg de regels van de school.
  Of kies op YouTube **Verborgen** en deel de link alleen met de ouders.
- Het radiopakket bevat 13 waarden. De trillingsbanden zitten er niet in; die staan
  alleen op de SD-kaart. Het streamdashboard toont dus hoogte, snelheid, temperatuur,
  luchtdruk en de radio-ontvangst.
