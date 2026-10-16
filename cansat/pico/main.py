# CanSat 2027 - LoRa-ontvanger op de Raspberry Pi Pico (MicroPython)
# ===================================================================
#
# Wat doet dit programma?
#   Het luistert naar de radiopakketten van de CanSat (Teensy + RFM95W)
#   en stuurt elk pakket via de USB-kabel naar de laptop, als een regel:
#
#     19 waarden van de CanSat , RSSI (dBm) , SNR (dB)
#     (13 metingen + 6 van de FFT; een oudere vluchtcode stuurt er 13)
#
#   Meldingen beginnen met '#'. De laptop toont ze, maar slaat ze niet op.
#
# Gebruik (meer uitleg in de handleiding):
#   1. Open dit bestand in Thonny. Rechtsonder: MicroPython (Raspberry Pi Pico).
#   2. Bestand > Opslaan als... > Raspberry Pi Pico > naam: main.py
#   3. Druk op F5. Je ziet "# Radio OK". Stoppen: rode Stop-knop.
#   4. Sluit Thonny. Trek de USB-kabel uit en steek hem terug: main.py start
#      dan vanzelf. Start daarna start_meting.py op de laptop.
#
# Het lampje op de Pico:
#   - kort flitsje om de 2 s : het programma draait en wacht
#   - flits bij elk pakket   : er komt iets binnen
#   - snel knipperen         : fout (radio niet gevonden)
#
# Een sleutel (versleuteling) is er niet: iedereen met dezelfde instellingen
# kan meeluisteren. Dat is geen probleem, de metingen zijn niet geheim.

from machine import Pin, SPI
import time

# -------------------------------------------------------------------
# 1. PINNEN: pas aan als jullie radio op andere pinnen zit
#    (GP-nummers, niet de nummers van de pootjes)
# -------------------------------------------------------------------
SPI_BUS = 0      # SPI0. Bij SPI0 horen GP16 (MISO), GP18 (SCK), GP19 (MOSI)
PIN_MISO = 16    # RFM95W: MISO
PIN_CS = 17      # RFM95W: CS   (op sommige bordjes: NSS)
PIN_SCK = 18     # RFM95W: SCK
PIN_MOSI = 19    # RFM95W: MOSI
PIN_RST = 20     # RFM95W: RST  (op sommige bordjes: RESET). Niet aangesloten? Zet None
# G0 / DIO0 is niet nodig: dit programma vraagt de radio zelf af.

# -------------------------------------------------------------------
# 2. RADIO: moet PRECIES gelijk zijn aan de vluchtcode op de Teensy
#    (Cansat2027_teensy.ino: LORA_FREQUENCY, LORA_BANDWIDTH, LORA_SF,
#    LORA_CR en LORA_SYNC_WORD). Anders komt er niets door.
# -------------------------------------------------------------------
FREQ_MHZ = 868.0
BW_KHZ = 125.0
SF = 7           # spreading factor
CR = 7           # coding rate 4/7
SYNC_WORD = 0x12
PREAMBLE = 8     # standaard van RadioLib (de bibliotheek op de Teensy)

AANTAL_WAARDEN = (13, 19)   # zoveel getallen stuurt de CanSat per pakket
                            # (19 = met de FFT; 13 = oudere vluchtcode)

# -------------------------------------------------------------------
# Hieronder hoef je niets te veranderen.
# -------------------------------------------------------------------

# Registers van de SX1276, de radiochip in de RFM95W (datasheet, LoRa-modus)
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_RX_CURRENT = 0x10
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_PKT_SNR = 0x19
REG_PKT_RSSI = 0x1A
REG_HOP_CHANNEL = 0x1C
REG_VERSION = 0x42

LORA = 0x88              # LoRa-modus (zelfde bits als RadioLib op de Teensy)
SLEEP = 0x00
STANDBY = 0x01
RX_CONTINU = 0x05

IRQ_RX_DONE = 0x40
IRQ_CRC_FOUT = 0x20
CRC_IN_HEADER = 0x40

BANDBREEDTES = ((7.8, 0), (10.4, 1), (15.6, 2), (20.8, 3), (31.25, 4),
                (41.7, 5), (62.5, 6), (125.0, 7), (250.0, 8), (500.0, 9))


def instellingen():
    """Alle registers die de radio-instellingen bepalen: (register, waarde)."""
    frf = int(FREQ_MHZ * 524288 / 32)          # stappen van 32 MHz / 2^19
    bw = None
    for khz, code in BANDBREEDTES:
        if abs(khz - BW_KHZ) < 0.05:
            bw = code
    if bw is None:
        raise ValueError("BW_KHZ %s bestaat niet" % BW_KHZ)
    # lange symbolen (>= 16 ms): 'low data rate optimize' aan, zoals RadioLib
    ldro = 0x08 if (2 ** SF) / BW_KHZ >= 16.0 else 0x00
    return (
        (0x06, (frf >> 16) & 0xFF),            # frequentie
        (0x07, (frf >> 8) & 0xFF),
        (0x08, frf & 0xFF),
        (0x0B, 0x23),                          # stroombegrenzing 60 mA
        (0x0C, 0x23),                          # ontvanger: maximale versterking
        (0x0E, 0x80),                          # FIFO: begin zendbuffer
        (0x0F, 0x00),                          # FIFO: begin ontvangbuffer
        (0x1D, (bw << 4) | ((CR - 4) << 1)),   # bandbreedte, coding rate, header
        (0x1E, (SF << 4) | 0x04),              # spreading factor, CRC aan
        (0x1F, 0x64),
        (0x20, (PREAMBLE >> 8) & 0xFF),        # lengte van de aanloop
        (0x21, PREAMBLE & 0xFF),
        (0x23, 0xFF),                          # langste pakket: 255 bytes
        (0x24, 0x00),                          # geen frequency hopping
        (0x26, ldro | 0x04),                   # automatische versterking aan
        (0x2F, 0x20),
        (0x30, 0x00),
        (0x31, 0xC3),                          # detectie voor SF7 tot SF12
        (0x37, 0x0A),
        (0x33, 0x27),                          # IQ normaal (niet omgekeerd)
        (0x3B, 0x1D),
        (0x39, SYNC_WORD),
        (0x40, 0x00),                          # DIO0 = pakket ontvangen
    )


class Radio:
    """De RFM95W (SX1276), aangestuurd via SPI."""

    def __init__(self):
        self.cs = Pin(PIN_CS, Pin.OUT, value=1)
        self.rst = None
        if PIN_RST is not None:
            self.rst = Pin(PIN_RST, Pin.OUT, value=1)
        # ValueError als de pinnen niet bij deze SPI-bus horen
        self.spi = SPI(SPI_BUS, baudrate=1000000, polarity=0, phase=0,
                       sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

    def lees(self, reg):
        self.cs.value(0)
        try:
            self.spi.write(bytes([reg & 0x7F]))
            waarde = self.spi.read(1)[0]
        finally:
            self.cs.value(1)
        return waarde

    def schrijf(self, reg, waarde):
        self.cs.value(0)
        try:
            self.spi.write(bytes([reg | 0x80, waarde & 0xFF]))
        finally:
            self.cs.value(1)

    def lees_fifo(self, aantal):
        self.cs.value(0)
        try:
            self.spi.write(bytes([REG_FIFO]))
            data = self.spi.read(aantal)
        finally:
            self.cs.value(1)
        return data

    def start(self):
        """Radio zoeken, instellen en laten luisteren.
        Geeft None als alles goed is, anders een foutmelding."""
        if self.rst is not None:            # radio herstarten
            self.rst.value(0)
            time.sleep_ms(1)
            self.rst.value(1)
        time.sleep_ms(10)
        versie = self.lees(REG_VERSION)
        if versie != 0x12:
            return ("Radio niet gevonden: de chip antwoordt 0x%02X in plaats "
                    "van 0x12." % versie)
        # LoRa aanzetten kan alleen in slaapstand: eerst slapen, dan LoRa
        self.schrijf(REG_OP_MODE, LORA | SLEEP)
        time.sleep_ms(10)
        self.schrijf(REG_OP_MODE, LORA | SLEEP)
        time.sleep_ms(10)
        self.schrijf(REG_OP_MODE, LORA | STANDBY)
        time.sleep_ms(2)
        if not self.lees(REG_OP_MODE) & 0x80:
            return "De radio wil niet in LoRa-modus. Zit de MOSI-draad goed?"
        regs = instellingen()
        for reg, waarde in regs:
            self.schrijf(reg, waarde)
        for reg, waarde in regs:                    # alles goed aangekomen?
            if self.lees(reg) != waarde:
                return ("De radio onthoudt zijn instellingen niet (register "
                        "0x%02X). Zit de MOSI-draad goed?" % reg)
        self.schrijf(REG_IRQ_FLAGS, 0xFF)
        self.schrijf(REG_FIFO_ADDR_PTR, 0x00)
        self.schrijf(REG_OP_MODE, LORA | RX_CONTINU)
        return None

    def pakket(self):
        """Een ontvangen pakket als (data, goed, rssi, snr), of None."""
        vlaggen = self.lees(REG_IRQ_FLAGS)
        if not vlaggen & IRQ_RX_DONE:
            return None
        lengte = self.lees(REG_RX_NB_BYTES)
        self.schrijf(REG_FIFO_ADDR_PTR, self.lees(REG_FIFO_RX_CURRENT))
        data = self.lees_fifo(lengte) if lengte else b""
        crc_in_header = self.lees(REG_HOP_CHANNEL) & CRC_IN_HEADER
        snr = self.lees(REG_PKT_SNR)
        if snr > 127:
            snr -= 256
        snr = snr / 4
        # signaalsterkte in dBm, zelfde formule als RadioLib op de Teensy
        rssi = (-157 if FREQ_MHZ > 525 else -164) + self.lees(REG_PKT_RSSI)
        if snr < 0:
            rssi += snr
        self.schrijf(REG_IRQ_FLAGS, 0xFF)           # klaar voor het volgende
        goed = not (vlaggen & IRQ_CRC_FOUT) and crc_in_header
        return data, goed, rssi, snr


def maak_regel(data):
    """Pakket -> tekstregel met de getallen, of None als het geen
    CanSat-pakket is (bv. een pakket van een ander toestel)."""
    try:
        tekst = data.decode().strip()
    except Exception:
        return None
    delen = tekst.split(",")
    if len(delen) not in AANTAL_WAARDEN:
        return None
    for i in range(len(delen)):
        d = delen[i].strip()
        if d in ("nan", "-nan", "inf", "-inf", "ovf"):   # Arduino: geen getal
            d = "nan"
        else:
            try:
                float(d)
            except ValueError:
                return None
        delen[i] = d
    return ",".join(delen)


def maak_led():
    try:
        return Pin("LED", Pin.OUT)      # Pico en Pico W
    except Exception:
        return Pin(25, Pin.OUT)         # oudere MicroPython op de Pico


def flits(led, ms):
    led.value(1)
    time.sleep_ms(ms)
    led.value(0)


def knipper_fout(led):
    for _ in range(10):
        flits(led, 50)
        time.sleep_ms(50)


def luister(radio, led, rondes=None):
    """Pakketten ontvangen en doorsturen. rondes=None: voor altijd."""
    goed = beschadigd = vreemd = 0
    nu = time.ticks_ms()
    laatste_pakket = laatste_melding = laatste_herstart = laatste_flits = nu
    while rondes is None or rondes > 0:
        if rondes is not None:
            rondes -= 1
        p = radio.pakket()
        nu = time.ticks_ms()
        if p is None:
            stil = time.ticks_diff(nu, laatste_pakket)
            if stil >= 10000 and time.ticks_diff(nu, laatste_melding) >= 10000:
                print("# Al %d s geen pakket. Tot nu: %d goed, %d beschadigd."
                      % (stil // 1000, goed, beschadigd))
                laatste_melding = nu
            if stil >= 60000 and time.ticks_diff(nu, laatste_herstart) >= 60000:
                # een minuut stil: radio opnieuw instellen (voor de zekerheid)
                fout = radio.start()
                print("# Radio opnieuw ingesteld." if fout is None
                      else "# FOUT: " + fout)
                laatste_herstart = nu
            if time.ticks_diff(nu, laatste_flits) >= 2000:
                flits(led, 20)                      # teken van leven
                laatste_flits = nu
            time.sleep_ms(5)
            continue

        data, ok, rssi, snr = p
        laatste_pakket = laatste_herstart = nu
        if not ok:
            beschadigd += 1
            print("# Beschadigd pakket (CRC-fout). RSSI %d dBm, SNR %.1f dB"
                  % (round(rssi), snr))
            continue
        regel = maak_regel(data)
        if regel is None:
            vreemd += 1
            print("# Onbekend pakket genegeerd (%d bytes). Niet van onze CanSat?"
                  % len(data))
            continue
        goed += 1
        print("%s,%d,%.1f" % (regel, round(rssi), snr))
        flits(led, 50)
        laatste_flits = nu


def main():
    led = maak_led()
    print("# CanSat 2027 - ontvanger (Raspberry Pi Pico) start")
    print("# Instellingen: %.1f MHz, BW %.1f kHz, SF%d, CR 4/%d, sync word 0x%02X"
          % (FREQ_MHZ, BW_KHZ, SF, CR, SYNC_WORD))
    try:
        radio = Radio()
    except ValueError as e:
        while True:     # verkeerde pinnen: blijven melden
            print("# FOUT: deze pinnen horen niet bij SPI%d (%s). "
                  "Pas bovenaan main.py SPI_BUS of de pinnen aan." % (SPI_BUS, e))
            knipper_fout(led)
            time.sleep(5)
    while True:
        fout = radio.start()
        if fout is None:
            break
        print("# FOUT: " + fout)
        rst = "GP%d" % PIN_RST if PIN_RST is not None else "niet gebruikt"
        print("# Kijk de draden na: MISO=GP%d, CS=GP%d, SCK=GP%d, MOSI=GP%d, "
              "RST=%s, 3V3 en GND." % (PIN_MISO, PIN_CS, PIN_SCK, PIN_MOSI, rst))
        knipper_fout(led)
        time.sleep(2)
    print("# Radio OK. Wacht op pakketten van de CanSat ...")
    luister(radio, led)


if __name__ == "__main__":
    main()
