/*
 * CanSat 2027 — LoRa-ontvanger voor de livestream
 * ================================================
 *
 * Een extra ontvanger die alleen luistert naar de CanSat en elk pakket
 * via USB naar de laptop stuurt. Daar toont stream_dashboard.py het.
 *
 * Een extra ontvanger stoort niets: LoRa werkt zoals een radio. Elke
 * ontvanger met dezelfde instellingen hoort hetzelfde pakket.
 *
 * Hardware: een microcontroller met een RFM95W (868 MHz), bedraad zoals
 * in de CanSat. Een ander bord? Pas dan de pinnen hieronder aan.
 *
 * Bibliotheek: RadioLib (Library Manager), versie 6 of nieuwer.
 *
 * De radio-instellingen MOETEN gelijk zijn aan de vluchtcode:
 *   868.0 MHz, bandbreedte 125 kHz, SF7, coding rate 4/7, sync word 0x12
 *
 * Uitvoer (115200 baud), één regel per pakket:
 *   <pakket van de CanSat: 13 waarden>,<RSSI in dBm>,<SNR in dB>
 * Regels die met # beginnen zijn meldingen, geen metingen.
 */

#include <RadioLib.h>

// ── Pinnen (zelfde als in de CanSat) ──
#define RFM95_CS    10
#define RFM95_RST    9
#define RFM95_DIO0   2

// ── Radio-instellingen (zelfde als in de vluchtcode!) ──
#define LORA_FREQUENCY  868.0   // MHz
#define LORA_BANDWIDTH  125.0   // kHz
#define LORA_SF         7
#define LORA_CR         7
#define LORA_SYNC_WORD  0x12

RFM95 radio = new Module(RFM95_CS, RFM95_DIO0, RFM95_RST);

// wordt true zodra er een volledig pakket binnen is
volatile bool pakketBinnen = false;

// Wordt opgeroepen door de radio (interrupt): kort houden!
#if defined(ESP8266) || defined(ESP32)
  ICACHE_RAM_ATTR
#endif
void zetVlag(void) {
    pakketBinnen = true;
}

void setup() {
    Serial.begin(115200);
    delay(1500);                         // tijd om de seriële poort te openen
    Serial.println("# CanSat 2027 stream-ontvanger");

    int state = radio.begin(LORA_FREQUENCY, LORA_BANDWIDTH, LORA_SF,
                            LORA_CR, LORA_SYNC_WORD);
    if (state != RADIOLIB_ERR_NONE) {
        Serial.print("# FOUT: de radio start niet (code ");
        Serial.print(state);
        Serial.println("). Kijk de bedrading en de pinnen na.");
        while (true) {
            delay(1000);
        }
    }

    radio.setPacketReceivedAction(zetVlag);
    state = radio.startReceive();        // blijft luisteren
    if (state != RADIOLIB_ERR_NONE) {
        Serial.print("# FOUT: luisteren lukt niet (code ");
        Serial.print(state);
        Serial.println(")");
        while (true) {
            delay(1000);
        }
    }
    Serial.println("# Klaar: wacht op pakketten van de CanSat");
}

void loop() {
    if (!pakketBinnen) {
        return;
    }
    pakketBinnen = false;

    String pakket;
    int state = radio.readData(pakket);
    if (state == RADIOLIB_ERR_NONE) {
        Serial.print(pakket);
        Serial.print(',');
        Serial.print(radio.getRSSI(), 1);
        Serial.print(',');
        Serial.println(radio.getSNR(), 1);
    } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
        Serial.println("# pakket beschadigd (CRC-fout), overgeslagen");
    } else {
        Serial.print("# fout bij het lezen (code ");
        Serial.print(state);
        Serial.println(")");
    }
}
