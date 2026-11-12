/*
 * CanSat 2027 - Teensy 4.1
 * Gebaseerd op originele Pico/MicroPython code
 *
 * Sensoren:
 *   - BMP390     : druk, temperatuur, hoogte        (I2C)
 *   - BNO055     : oriëntatie, versnelling, gyro    (I2C)
 *   - LSM6DSO    : trillingen aan hoge samplerate   (I2C)
 *   - GPS PA1616D: positie (GLONASS + GPS)          (UART)
 *   - SPH0645    : MEMS microfoon, akoestisch       (I2S)
 *   - RFM95W     : LoRa 868 MHz datalink            (SPI)
 *   - SD kaart   : ingebouwd op Teensy 4.1          (SDIO)
 *
 * Pinout Teensy 4.1:
 *   I2C (Wire):   SDA=18, SCL=19
 *   SPI:          MOSI=11, MISO=12, SCK=13
 *   RFM95W CS:    pin 10
 *   RFM95W RST:   pin 9
 *   RFM95W DIO0:  pin 2   (verplaatst vanaf pin 8 i.v.m. I2S-conflict)
 *   GPS UART:     Serial1 TX=1, RX=0
 *   Buzzer:       pin 14
 *   I2S MEMS:     I2S_IN = pin 8 (data, hardware-vast), LRCLK=20, BCLK=21
 *
 * Libraries:
 *   - Adafruit_BMP3XX
 *   - Adafruit_BNO055
 *   - Adafruit_Sensor
 *   - SparkFun_LSM6DSO (of LSM6DS3 library)
 *   - Adafruit GPS Library
 *   - RadioLib (voor RFM95W LoRa)
 *   - SD (ingebouwd Teensy)
 *   - Audio (Teensy Audio library voor I2S - alleen RMS, geen FFT)
 *   - ArduinoFFT 2.x (alleen voor LSM6DSO trillingen)
 *
 * CSV op SD (34 kolommen, gelijk aan sensortest_fft.ino en de dashboards):
 *   millis,temp_C,press_hPa,alt_m,lat,lon,time_utc,
 *   gyro_x,gyro_y,gyro_z,lacc_x,lacc_y,lacc_z,grav_x,grav_y,grav_z,
 *   heading,roll,pitch,qw,qx,qy,qz,fft_peak_hz,fft_peak_amp,audio_rms,
 *   acc_peak_g,gps_course_deg,gps_speed_ms,
 *   vib_0_10_g,vib_10_30_g,vib_30_60_g,vib_60_120_g,vib_120_208_g
 *   time_utc     = de tijd van de GPS; 00:00:00 = op dit moment GEEN GPS-fix
 *                  (lat en lon zijn dan de laatste bekende positie)
 *   fft_peak_amp = sterkte van de trilling in g
 *   audio_rms    = RMS van alle audio sinds de vorige regel (DC verwijderd)
 *   acc_peak_g   = grootste versnelling (LSM6DSO) sinds de vorige regel, in g
 *   gps_course_deg / gps_speed_ms = bewegingsrichting (0 = noord, 90 = oost)
 *                  en snelheid over de grond volgens de GPS (afdrijven)
 *   vib_*_g      = RMS-trilling per frequentieband in g (uit dezelfde FFT),
 *                  van de drie assen samen (zie FFT_ALL_AXES)
 *
 * LoRa-pakket (1 per seconde, tekst, 19 waarden):
 *   temp,press,alt,lat,lon,lacc_x,lacc_y,lacc_z,heading,roll,pitch,
 *   fft_peak_hz,audio_rms,fft_peak_amp,vib_0_10,vib_10_30,vib_30_60,
 *   vib_60_120,vib_120_208
 *   De eerste 13 zijn dezelfde als vroeger; de FFT-waarden staan achteraan.
 *   Zonder GPS-fix staan in lat en lon de vaste waarden NO_FIX_LAT en
 *   NO_FIX_LON: zo herkent het grondstation "geen fix".
 *
 * Versie 2026-11-12: juist meten
 *   - De I2C-bus loopt nu echt op 400 kHz. De Adafruit-bibliotheken zetten
 *     hem bij het starten terug op 100 kHz; daardoor haalde de LSM6DSO maar
 *     de helft van de 416 metingen per seconde en gaf de FFT ongeveer
 *     dubbel zo hoge frequenties.
 *   - LSM6DSO: de sensor bewaart nu zelf elke meting (FIFO), op zijn eigen
 *     klok. Er gaat geen meting meer verloren als de lus even bezig is, en
 *     de echte meetsnelheid wordt gemeten. Werkt de FIFO niet, dan leest de
 *     Teensy zelf op een rooster van 416 Hz (gemiste metingen ingevuld).
 *   - BMP390: 20 keer per seconde gelezen. Vroeger was elke waarde één
 *     seconde oud en veel te traag gefilterd (hoogste punt te laag).
 *   - GPS: een verloren fix is nu zichtbaar (time_utc = 00:00:00).
 *   - Lancering: pas na 3 seconden bevestiging. Het einde van de vlucht:
 *     pas als de CanSat stil ligt. Na een valse start begint een echte
 *     lancering toch een nieuwe meting.
 *   - De FFT telt de trillingen van de drie assen samen.
 */

// ============================================================
// INCLUDES
// ============================================================
#include <Wire.h>
#include <SPI.h>
#include <SD.h>

#include <Adafruit_BMP3XX.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_Sensor.h>
#include <utility/imumaths.h>

#include <SparkFunLSM6DSO.h>

#include <Adafruit_GPS.h>
#include <RadioLib.h>

#include <Audio.h>
#include <arduinoFFT.h>

// ============================================================
// CONSTANTEN
// ============================================================

#define VERSIE              "2026-11-12"

// LoRa instellingen
#define LORA_FREQUENCY      868.0   // MHz - Europa
#define LORA_BANDWIDTH      125.0   // kHz
#define LORA_SF             7       // Spreading Factor 7-12 — SF7: ~0,25 s on-air voor 19 waarden (SF9 zou ~1 s zijn)
#define LORA_CR             7       // Coding Rate 5-8
#define LORA_SYNC_WORD      0x12    // Privé netwerk
// Zendvermogen in dBm. 14 dBm = 25 mW: het maximum dat in Europa mag op
// 868,0-868,6 MHz. Ruim genoeg voor de test op 100 m. (Was 20 = 100 mW.)
// De ontvanger (Pico: pico/main.py) moet dezelfde frequentie, BW, SF, CR
// en sync word gebruiken; het zendvermogen mag verschillen.
#define LORA_POWER_DBM      14

// Pins
#define RFM95_CS            10
#define RFM95_RST           9
#define RFM95_DIO0          2       // Verplaatst vanaf pin 8 i.v.m. I2S audio-data conflict
#define BUZZER_PIN          14
#define SD_CS               BUILTIN_SDCARD  // Ingebouwd op Teensy 4.1

// Hoogte
#define SEA_LEVEL_PRESSURE  1014.0  // hPa - pas aan voor lanceerlocatie!

// Lancering: de CanSat is LAUNCH_ALT_DIFF meter hoger dan LAUNCH_CHECK_MS
// eerder, en dat LAUNCH_CONFIRM seconden na elkaar. Eén foute drukmeting
// of een korte drukstoot (tot 2 s) start de vlucht dus niet.
#define LAUNCH_ALT_DIFF     50.0    // meter hoogteverschil voor lanceerdetectie
#define LAUNCH_CHECK_MS     5000    // ... ten opzichte van 5 s eerder
#define LAUNCH_CONFIRM      3       // zoveel seconden na elkaar
// Einde van de vlucht: FLIGHT_DURATION_MS na de lancering, EN de CanSat ligt
// stil (10 s lang minder dan LANDED_RANGE_M hoogteverschil). Hangt hij dan
// nog in de lucht, dan loopt de meting door. Na FLIGHT_MAX_MS stopt ze altijd.
#define FLIGHT_DURATION_MS  360000  // 6 minuten vluchtduur
#define LANDED_RANGE_M      5.0     // meter
#define FLIGHT_MAX_MS       1800000 // 30 minuten

// Samplerates
#define I2C_CLOCK_HZ        400000  // I2C-snelheid: gezet NA het starten van de sensoren
#define BMP_INTERVAL_MS     50      // BMP390: 20 Hz (zie readBMP390)
#define BNO_INTERVAL_MS     100     // BNO055: 10 Hz, in 5 kleine stappen
#define LSM_USE_FIFO        1       // 1 = de LSM6DSO bewaart zelf elke meting (FIFO); 0 = zelf pollen
#define LSM_FIFO_SERVICE_US 5000    // FIFO: elke 5 ms leeghalen
#define LSM_FIFO_MAX_WORDS  32      // ... hoogstens zoveel metingen per keer
#define LSM_FIFO_TIMEOUT_MS 300     // zo lang niets uit de FIFO: terug naar pollen
#define LSM_INTERVAL_US     2404    // zonder FIFO: poll exact op 416 Hz (1e6/416 µs)
#define LORA_INTERVAL_MS    1000    // LoRa verzenden + SD-regel: 1 Hz
#define SD_FLUSH_MS         500     // SD flush: elke 500 ms
#define DIAG_INTERVAL_MS    10000   // controleregel op Serial: elke 10 s

// FFT instellingen
#define FFT_SAMPLES         512     // Aantal samples voor FFT
#define LSM_SAMPLE_RATE_HZ  416     // Hz — overeenkomstig met setAccelDataRate(416)
#define LSM_ODR_NOMINAL_HZ  416.7f  // wat de sensor zelf "416 Hz" noemt (6667/16)
#define FFT_ALL_AXES        1       // 1 = trillingen van X, Y en Z samen; 0 = alleen Z (zoals vroeger)
#define LSM_MAX_FILL        40      // hoogstens zoveel gemiste metingen na elkaar invullen (~0,1 s)

// GPS
#define GPS_FIX_MAX_AGE_S   3.0     // een fix ouder dan dit telt niet meer
#define NO_FIX_LAT          50.457303   // "geen fix": Elsenborn (ook in serial_logger.py)
#define NO_FIX_LON          6.221376

// ============================================================
// OBJECTEN
// ============================================================

// Sensoren
Adafruit_BMP3XX bmp;
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
LSM6DSO lsm;
Adafruit_GPS GPS(&Serial1);
// Extra RX-buffer: als de lus even stilstaat (SD) komt er op 9600 baud
// ~1 byte per ms NMEA binnen; de standaardbuffer is maar 64 bytes.
static uint8_t gpsRxBuf[512];

// LoRa via RadioLib
RFM95 radio = new Module(RFM95_CS, RFM95_DIO0, RFM95_RST);

// Audio - I2S microfoon
AudioInputI2S            micInput;
AudioRecordQueue         audioQueue;
AudioConnection          patchCord1(micInput, 0, audioQueue, 0);

// FFT
ArduinoFFT<float> FFT;
float fft_real[FFT_SAMPLES];
float fft_imag[FFT_SAMPLES];
float fft_window[FFT_SAMPLES];          // Hamming-venster, één keer berekend
float fft_window_power = 1;             // gemiddelde van venster² (≈ 0,3966)
float fft_power[FFT_SAMPLES / 2];       // |X|² per frequentie, alle assen samen

// SD
File csvFile;
bool sd_ok = false;                     // SD.begin() gelukt
int sdBufferLines = 0;

// ============================================================
// GLOBALE VARIABELEN
// ============================================================

// Welke onderdelen werken? Een onderdeel dat bij het opstarten niet
// antwoordt, wordt overgeslagen: de rest blijft meten, loggen en zenden.
bool ok_bmp = false, ok_bno = false, ok_lsm = false, ok_lora = false;

// Vluchtstatus
bool isLaunched = false;                // de vlucht is bezig
bool landed = false;                    // de vlucht is voorbij: buzzer, niets meer loggen
unsigned long launchTimer = 0;          // millis() van de lancering
unsigned long landedMs = 0;             // millis() van het einde van de vlucht
int launchHits = 0;                     // zoveel seconden na elkaar "aan het stijgen"

// De hoogte van de laatste seconden, één waarde per seconde:
// altHist[0] = nu, altHist[1] = 1 s geleden, ...
#define ALT_HIST_N 11
float altHist[ALT_HIST_N];
int altCount = 0;

// Timers
unsigned long lastBmpMs = 0;
unsigned long lastBnoMs = 0;
unsigned long lastLsmUs = 0;     // microseconden! (exacte 416 Hz timing)
unsigned long lastLogMs = 0;
unsigned long lastSdFlushMs = 0;
unsigned long lastDiagMs = 0;

// LoRa zonder wachten: startTransmit() geeft het pakket aan de radio en de
// lus gaat meteen verder. checkLoRa() rondt af als DIO0 hoog is.
bool loraBusy = false;
unsigned long loraStartMs = 0;
#define LORA_TX_TIMEOUT_MS  2000    // nooit langer dan dit "bezig"

// Laatste bekende waarden (fallback bij sensoruitval)
float last_temp       = 10.0;
float last_pressure   = 1000.0;
float last_altitude   = 600.0;
bool  bmp_valid       = false;      // er is al een echte meting van de BMP390
float last_lat        = NO_FIX_LAT; // tot de eerste fix
float last_lon        = NO_FIX_LON;
String last_time_utc  = "00:00:00";
bool  gps_fix         = false;      // heeft de GPS NU een fix?
float last_gps_course = 0, last_gps_speed = 0;   // afdrijfrichting en -snelheid

float last_gyro_x = 0, last_gyro_y = 0, last_gyro_z = 0;
float last_lacc_x = 0, last_lacc_y = 0, last_lacc_z = 0;
float last_grav_x = 0, last_grav_y = 0, last_grav_z = 0;
float last_heading = 0, last_roll = 0, last_pitch = 0;
float last_qw = 1, last_qx = 0, last_qy = 0, last_qz = 0;
int bnoStep = 0;                    // 0 = klaar, 1..5 = bezig met een leesronde
Adafruit_BNO055::adafruit_bno055_rev_info_t bno_rev;   // versienummers van de BNO055

// LSM6DSO buffer voor FFT
float lsm_buffer_x[FFT_SAMPLES];
float lsm_buffer_y[FFT_SAMPLES];
float lsm_buffer_z[FFT_SAMPLES];
int lsm_buf_index = 0;
float lsm_g_per_lsb = 0.000488f;    // ±16 g: 0,488 mg per stap (gecontroleerd bij het starten)
float lsm_prev_x = 0, lsm_prev_y = 0, lsm_prev_z = 0;   // de vorige echte meting
bool lsm_have_prev = false;
uint32_t lsm_owed = 0;              // roosterpunten zonder meting (leesfout)
// FIFO: de sensor meet op zijn eigen klok en bewaart elke meting tot wij ze
// ophalen. De echte meetsnelheid (lsm_fs) meten we door te tellen.
bool lsm_fifo = false;              // true = FIFO in gebruik
float lsm_fs = LSM_ODR_NOMINAL_HZ;  // gemeten meetsnelheid van de sensor (Hz)
unsigned long lastFifoUs = 0;
unsigned long fifoLastSampleMs = 0;
uint32_t fifo_consumed = 0;         // zoveel metingen uit de FIFO gehaald
bool fifo_rate_started = false;
uint32_t fifo_rate_us0 = 0, fifo_rate_n0 = 0, fifo_rate_window_us = 2000000UL;
bool fft_ran = false;               // deze lus-doorgang is er al een FFT berekend

// Grootste versnelling (LSM6DSO, ±16 g) sinds de vorige logregel.
// Een schok (uitwerpen, parachute) duurt korter dan 1 s en valt anders
// tussen twee logregels in. Inclusief zwaartekracht: in rust ≈ 1 g.
float acc_peak_g = 0;

// Audio RMS (geen FFT - alleen fasedetectie en snelheidsvalidatie)
float audio_rms = 0;
double audio_sum = 0, audio_sum_sq = 0;   // alle audio sinds vorige regel
uint32_t audio_count = 0;

// Tellers voor de controleregel (elke 10 s op Serial)
uint32_t diag_lsm_real = 0, diag_lsm_filled = 0, diag_lsm_restarts = 0;
uint32_t diag_lsm_errors = 0, diag_bmp = 0, diag_bmp_bad = 0;
bool diag_fifo_fallback = false;    // de FIFO viel uit tijdens het meten
uint32_t lsm_read_us = 0;           // zo lang duurt één LSM6DSO-meting (µs)
uint32_t i2c_hz = I2C_CLOCK_HZ;     // de I2C-snelheid die echt gebruikt wordt

// ---- Trillingsbanden (uit dezelfde FFT) ----
// Band i loopt van BAND_EDGE_HZ[i] tot BAND_EDGE_HZ[i+1] Hz; de laatste band
// loopt tot de Nyquist-frequentie (helft van de samplefrequentie, ~208 Hz).
// Per band: RMS-versnelling in g (stelling van Parseval, venster-gecorrigeerd).
// Gecontroleerd met een testsignaal: 0,5 g sinus bij 25 Hz → 0,354 g in 10–30.
#define N_BANDS        5
const float BAND_EDGE_HZ[N_BANDS] = {0, 10, 30, 60, 120};
float vib_band_g[N_BANDS] = {0, 0, 0, 0, 0};

float fft_peak_hz  = 0;
float fft_peak_amp = 0;

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("CanSat 2027 - Teensy 4.1");
    Serial.println("========================");
    Serial.print("Vluchtcode versie ");
    Serial.println(VERSIE);

    // Buzzer
    pinMode(BUZZER_PIN, OUTPUT);

    // I2C
    Wire.begin();

    // GPS UART: Serial1 wordt gestart in initGPS() (GPS.begin)

    // Audio geheugen — ruim genoeg om een pauze van de lus van ~0,15 s te
    // overbruggen (44.1 kHz / 128 samples ≈ 345 blokken/s → 45 blokken
    // + marge).
    AudioMemory(60);

    // Sensoren initialiseren
    initBMP390();
    initBNO055();
    initLSM6DSO();
    initGPS();
    initLoRa();
    initSD();

    // De I2C-snelheid HIER zetten, na de sensoren. bmp.begin_I2C() en
    // bno.begin() roepen zelf Wire.begin() op, en dat zet een Teensy 4 terug
    // op 100 kHz. Op 100 kHz duurt één LSM6DSO-meting langer dan de 2,4 ms
    // tussen twee metingen.
    Wire.setClock(I2C_CLOCK_HZ);
    // Antwoorden de sensoren ook op deze snelheid? (lange draden, breadboard)
    // Zo niet: terug naar 100 kHz. Met de FIFO gaat er dan nog niets verloren.
    if (!i2cAlive()) {
        i2c_hz = 100000;
        Wire.setClock(i2c_hz);
    }
    initFFT();
    if (ok_lsm) calibrateLSM6DSO();

    Serial.println("\n--- Status ---");
    Serial.print("BMP390 : "); Serial.println(ok_bmp  ? "OK" : "FOUT (geen hoogte, geen lanceerdetectie)");
    Serial.print("BNO055 : "); Serial.println(ok_bno  ? "OK" : "FOUT (geen oriëntatie)");
    Serial.print("LSM6DSO: "); Serial.println(ok_lsm  ? "OK" : "FOUT (geen trillingen, geen acc_peak_g)");
    Serial.print("LoRa   : "); Serial.println(ok_lora ? "OK" : "FOUT (niets naar het grondstation)");
    Serial.print("SD     : "); Serial.println(csvFile ? "OK" : "FOUT (niets op de SD-kaart)");
    Serial.print("# I2C: ");
    Serial.print(i2c_hz / 1000);
    Serial.println(i2c_hz == I2C_CLOCK_HZ ? " kHz" : " kHz (LET OP: de sensoren antwoorden niet op de hoge snelheid)");
    if (ok_lsm) {
        // Eén meting moet ruim korter duren dan 2404 µs (op 400 kHz ~250 µs)
        Serial.print("# LSM6DSO: 1 meting duurt ");
        Serial.print(lsm_read_us);
        Serial.println(lsm_read_us < 1200 ? " us (goed)" : " us (TE TRAAG: de FFT mist metingen)");
        Serial.println(lsm_fifo ? "# LSM6DSO: FIFO aan (de sensor bewaart zelf elke meting)"
                                : "# LSM6DSO: zonder FIFO (de Teensy leest zelf, 416 keer per seconde)");
    }

    // Startbuzzer
    beep(3);

    Serial.println("\nHoofdlus gestart");
    Serial.println("================\n");

    unsigned long now = millis();
    lastSdFlushMs = now;
    lastLogMs = now;
    lastDiagMs = now;

    // Audio queue starten
    audioQueue.begin();

    restartLSM6DSO();
}

// ============================================================
// HOOFDLUS
// ============================================================

void loop() {
    unsigned long now = millis();

    // --- LoRa: klaar met zenden? (zenden zelf wacht niet) ---
    checkLoRa();

    // --- GPS continu uitlezen (niet-blokkerend) ---
    // hele buffer leeglezen, niet 1 teken per loop-doorgang
    while (Serial1.available()) {
        GPS.read();
        if (GPS.newNMEAreceived()) {
            GPS.parse(GPS.lastNMEA());
        }
    }

    // --- Na de vlucht: buzzer, en blijven kijken naar een nieuwe lancering ---
    if (landed) {
        loopLanded(now);
        return;
    }

    // --- LSM6DSO: 416 metingen per seconde + FFT buffer vullen ---
    bool slot = !ok_lsm;        // zonder LSM6DSO is er altijd tijd voor de rest
    fft_ran = false;
    if (ok_lsm && lsm_fifo) {
        // De sensor bewaart zelf elke meting: wij halen ze om de 5 ms op.
        if (micros() - lastFifoUs >= LSM_FIFO_SERVICE_US) {
            lastFifoUs = micros();
            serviceLsmFifo(now);
        }
        slot = true;
    } else if (ok_lsm) {
        // Zonder FIFO: zelf lezen op een vast rooster van 2404 µs. Komt de
        // lus te laat (SD, zenden), dan worden de gemiste roosterpunten
        // ingevuld: de tijd-as van de FFT blijft dus altijd juist.
        uint32_t late = micros() - lastLsmUs;
        if (late >= LSM_INTERVAL_US) {
            uint32_t steps = late / LSM_INTERVAL_US;      // 1 = op tijd
            lastLsmUs += steps * LSM_INTERVAL_US;         // vaste tijdbasis, geen drift
            readLSM6DSO(steps - 1);
            slot = true;
        }
    }

    // --- De andere I2C-sensoren: hoogstens één korte taak, METEEN na een
    // LSM6DSO-meting. Zo is de bus weer vrij voor de volgende meting. ---
    if (slot && !fft_ran) slowJob(now);

    // --- Audio RMS berekenen ---
    processAudio();

    // --- 1 Hz: GPS, vluchtstatus, LoRa verzenden + SD schrijven ---
    if (now - lastLogMs >= LORA_INTERVAL_MS) {
        lastLogMs = now;
        readGPS();
        updateFlightState(now);
        if (!landed) sendAndLog();
    }

    // --- SD flushen ---
    if (now - lastSdFlushMs >= SD_FLUSH_MS) {
        lastSdFlushMs = now;
        flushSD();
    }

    // --- Controleregel: wordt er echt 416 keer per seconde gemeten? ---
    if (now - lastDiagMs >= DIAG_INTERVAL_MS) {
        printDiagnostics(now - lastDiagMs);
        lastDiagMs = now;
    }
}

// Hoogstens één I2C-taak per LSM6DSO-meting: de BMP390 (~1 ms op 400 kHz) of
// één stap van de BNO055 (~0,3 ms). Samen met de LSM6DSO-meting blijft dat
// onder de 2,4 ms tot de volgende meting.
void slowJob(unsigned long now) {
    if (ok_bmp && now - lastBmpMs >= BMP_INTERVAL_MS) {
        lastBmpMs = now;
        readBMP390();
        return;
    }
    if (ok_bno) {
        if (bnoStep == 0 && now - lastBnoMs >= BNO_INTERVAL_MS) {
            lastBnoMs = now;
            bnoStep = 1;
        }
        if (bnoStep > 0) {
            readBNO055Step(bnoStep);
            bnoStep = (bnoStep >= 5) ? 0 : bnoStep + 1;
        }
    }
}

// Na de vlucht: het terugvindsignaal (3 s buzzer, 7 s stil), zonder de lus
// te blokkeren. De BMP390 blijft meten: herkent hij toch nog een lancering
// (de vorige was vals), dan begint een nieuwe meting in een nieuw bestand.
void loopLanded(unsigned long now) {
    digitalWrite(BUZZER_PIN, ((now - landedMs) % 10000UL) < 3000UL ? HIGH : LOW);
    if (ok_bmp && now - lastBmpMs >= BMP_INTERVAL_MS) {
        lastBmpMs = now;
        readBMP390();
    }
    if (now - lastLogMs >= LORA_INTERVAL_MS) {
        lastLogMs = now;
        readGPS();
        updateFlightState(now);
    }
}

// ============================================================
// VLUCHTSTATUS: lancering en einde van de vlucht
// ============================================================

// Elke seconde opgeroepen.
void updateFlightState(unsigned long now) {
    if (!bmp_valid) return;         // zonder hoogte geen lancering

    // de hoogte van deze seconde vooraan in de rij
    for (int i = ALT_HIST_N - 1; i > 0; i--) altHist[i] = altHist[i - 1];
    altHist[0] = last_altitude;
    if (altCount < ALT_HIST_N) altCount++;

    // --- Lanceerdetectie ---
    const int back = LAUNCH_CHECK_MS / 1000;      // 5 s geleden
    bool climbing = altCount > back &&
                    (altHist[0] - altHist[back]) >= LAUNCH_ALT_DIFF;
    launchHits = climbing ? launchHits + 1 : 0;
    if (!isLaunched && launchHits >= LAUNCH_CONFIRM) {
        startFlight(now);
    }

    // --- Einde van de vlucht ---
    if (isLaunched) {
        unsigned long dt = now - launchTimer;
        if (dt >= FLIGHT_DURATION_MS && (altitudeSteady() || dt >= FLIGHT_MAX_MS)) {
            Serial.println(">>> LANDING GEDETECTEERD <<<");
            landingProcedure(now);
        }
    }
}

// Ligt de CanSat stil? De laatste 10 s minder dan LANDED_RANGE_M verschil.
bool altitudeSteady() {
    const int n = 10;
    if (altCount < n) return false;
    float lo = altHist[0], hi = altHist[0];
    for (int i = 1; i < n; i++) {
        if (altHist[i] < lo) lo = altHist[i];
        if (altHist[i] > hi) hi = altHist[i];
    }
    return (hi - lo) < LANDED_RANGE_M;
}

void startFlight(unsigned long now) {
    if (landed) {
        // De vorige "vlucht" was vals (of dit is een tweede vlucht): alles
        // weer aan, in een NIEUW bestand. Het vorige bestand blijft bewaard.
        landed = false;
        digitalWrite(BUZZER_PIN, LOW);
        openNewFile();
        audio_sum = audio_sum_sq = 0;
        audio_count = 0;
        audioQueue.begin();
        acc_peak_g = 0;
        bnoStep = 0;
        restartLSM6DSO();
        lastSdFlushMs = now;
        lastDiagMs = now;
        Serial.println(">>> NIEUWE METING: de vorige vlucht was al afgesloten <<<");
    }
    isLaunched = true;
    launchTimer = now;
    Serial.println(">>> LANCERING GEDETECTEERD <<<");
    // GEEN buzzer tijdens de vlucht: hij zit naast de SPH0645
    // en zou de audio_rms-meting vervuilen. De buzzer komt pas
    // na de landing (terugvindsignaal).
}

// ============================================================
// SENSOR INITIALISATIE
// ============================================================

void initBMP390() {
    Serial.print("BMP390 initialiseren... ");
    for (int i = 0; i < 5; i++) {
        if (bmp.begin_I2C()) {  // default adres 0x77
            bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_8X);
            bmp.setPressureOversampling(BMP3_OVERSAMPLING_4X);
            // Een licht filter (coëfficiënt 1): bij 20 metingen per seconde
            // loopt de hoogte dan hoogstens ~0,1 s achter. (Was 3.)
            bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_1);
            bmp.setOutputDataRate(BMP3_ODR_50_HZ);
            // performReading() start een meting en leest meteen: je krijgt
            // de VORIGE meting. De eerste keer is dat onzin. Daarom een paar
            // keer lezen, met telkens tijd voor de meting (~25 ms).
            for (int k = 0; k < 3; k++) {
                bmp.performReading();
                delay(40);
            }
            ok_bmp = true;
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! BMP390 niet gevonden.");
    errorBeep();
    // Niet stoppen: de rest blijft werken. Zonder BMP390 is er
    // wel geen lanceerdetectie (en dus ook geen landingsbuzzer).
}

void initBNO055() {
    Serial.print("BNO055 initialiseren... ");
    for (int i = 0; i < 5; i++) {
        if (bno.begin()) {
            delay(1000);
            bno.setExtCrystalUse(true);
            // IMU+ : zonder kompas (magnetometer). Het kompas wordt in de
            // raket gestoord door metaal, batterijen en de buzzer en moet
            // gekalibreerd worden. De afdrijfrichting komt van de GPS.
            // Heading is RELATIEF: 0° = de richting bij het opstarten.
            // Zelfde modus als in Drie_sensoren_test.
            bno.setMode(OPERATION_MODE_IMUPLUS);
            delay(25);
            bno.getRevInfo(&bno_rev);       // om later de I2C-snelheid te controleren
            ok_bno = true;
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! BNO055 niet gevonden.");
    errorBeep();
    // Niet stoppen: doorgaan zonder oriëntatie
}

void initGPS() {
    Serial.print("GPS PA1616D initialiseren... ");
    GPS.begin(9600);                                 // doet Serial1.begin()
    Serial1.addMemoryForRead(gpsRxBuf, sizeof(gpsRxBuf));  // na begin()
    GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);   // RMC + GGA zinnen
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);       // 1 Hz update
    GPS.sendCommand(PGCMD_ANTENNA);                  // Antennestatus opvragen
    delay(1000);
    Serial.println("OK");
}

void initLSM6DSO() {
    Serial.print("LSM6DSO initialiseren... ");
    for (int i = 0; i < 5; i++) {
        // initialize(): auto-increment + Block Data Update (geen mix van
        // oude en nieuwe bytes bij uitlezen aan 416 Hz), daarna ±16 g
        if (lsm.begin() && lsm.initialize(BASIC_SETTINGS)) {
            lsm.setAccelRange(16);          // ±16g voor hoge G-krachten
            lsm.setAccelDataRate(416);      // 416 Hz accelerometer
            lsm.setGyroDataRate(416);       // 416 Hz gyroscoop
            ok_lsm = true;
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! LSM6DSO niet gevonden.");
    errorBeep();
    // Niet fataal - doorgaan zonder trillingssensor
}

// Antwoordt elke sensor die bij het starten gevonden werd?
bool i2cAlive() {
    if (ok_lsm) {
        float ax, ay, az;
        if (!readLsmRaw(ax, ay, az)) return false;
    }
    if (ok_bmp && !bmp.performReading()) return false;
    if (ok_bno) {
        // dezelfde versienummers als bij het starten (toen op 100 kHz)?
        Adafruit_BNO055::adafruit_bno055_rev_info_t info;
        bno.getRevInfo(&info);
        if (info.accel_rev != bno_rev.accel_rev || info.gyro_rev != bno_rev.gyro_rev ||
            info.mag_rev != bno_rev.mag_rev || info.sw_rev != bno_rev.sw_rev) return false;
    }
    return true;
}

// Eén keer bij het starten: hoeveel g is één stap van de sensor, en hoe lang
// duurt één meting? De bibliotheek leest bij ELKE readFloatAccel?() ook het
// meetbereik opnieuw uit (6 leesopdrachten per meting). Wij vragen de
// schaal hier één keer en lezen daarna de drie assen in één opdracht.
void calibrateLSM6DSO() {
    float g = lsm.calcAccel(10000) / 10000.0f;      // ±16 g: 0,000488
    if (g > 0.00005f && g < 0.001f) lsm_g_per_lsb = g;
    float ax, ay, az;
    readLsmRaw(ax, ay, az);                         // de eerste keer telt niet
    uint32_t t0 = micros();
    readLsmRaw(ax, ay, az);
    lsm_read_us = micros() - t0;
#if LSM_USE_FIFO
    lsm_fifo = startLsmFifo();
#endif
}

// ---- FIFO van de LSM6DSO ----
// Zonder FIFO vraagt de Teensy 416 keer per seconde "wat is de versnelling
// nu?". De sensor meet op zijn eigen klok, die een paar procent afwijkt: af
// en toe krijg je dus twee keer dezelfde meting, of mis je er één. En is de
// lus even bezig (SD-kaart), dan is er een gat.
// Met de FIFO schrijft de sensor ELKE meting in zijn eigen geheugen (tot
// 512 metingen, ruim 1 seconde). De Teensy haalt ze op wanneer hij tijd
// heeft. Alle metingen liggen dan precies even ver uit elkaar.

// Het aantal metingen dat in de FIFO wacht; overflow = er zijn er verloren.
bool lsmFifoCount(uint16_t &n, bool &overflow) {
    uint8_t s[2];
    if (lsm.readMultipleRegisters(s, FIFO_STATUS1, 2) != IMU_SUCCESS) return false;
    n = s[0] | ((uint16_t)(s[1] & 0x03) << 8);
    overflow = (s[1] & 0x48) != 0;          // FIFO_OVR_IA of FIFO_OVR_LATCHED
    return true;
}

// Eén meting uit de FIFO: 1 byte "soort" + 6 bytes X, Y, Z.
// Geeft false bij een leesfout; isAccel zegt of het een versnelling is.
bool lsmFifoWord(float &ax, float &ay, float &az, bool &isAccel) {
    uint8_t w[7];
    if (lsm.readMultipleRegisters(w, FIFO_DATA_OUT_TAG, 7) != IMU_SUCCESS) return false;
    isAccel = (w[0] >> 3) == ACCELEROMETER_DATA;
    ax = (int16_t)(w[1] | (w[2] << 8)) * lsm_g_per_lsb;
    ay = (int16_t)(w[3] | (w[4] << 8)) * lsm_g_per_lsb;
    az = (int16_t)(w[5] | (w[6] << 8)) * lsm_g_per_lsb;
    return true;
}

// De FIFO leeg en opnieuw aan: alleen de versnelling, 417 keer per seconde.
bool lsmFifoOn() {
    lsm.writeRegister(FIFO_CTRL4, FIFO_MODE_DISABLED);      // leegmaken
    lsm.writeRegister(FIFO_CTRL1, 0);                       // geen drempel
    lsm.writeRegister(FIFO_CTRL2, 0);                       // geen compressie
    if (lsm.writeRegister(FIFO_CTRL3, FIFO_BDR_ACC_417Hz) != IMU_SUCCESS) return false;
    return lsm.writeRegister(FIFO_CTRL4, FIFO_MODE_CONTINUOUS) == IMU_SUCCESS;
}

void lsmFifoOff() {
    lsm.writeRegister(FIFO_CTRL4, FIFO_MODE_DISABLED);
}

// Bij het starten: de FIFO aanzetten en CONTROLEREN of hij doet wat we
// verwachten. Zo niet: uit, en de Teensy leest zelf (zoals vroeger).
bool startLsmFifo() {
    if (!lsmFifoOn()) { lsmFifoOff(); return false; }
    delay(60);                                              // ~25 metingen
    uint16_t n = 0;
    bool overflow = false;
    float fx, fy, fz, dx, dy, dz;
    bool isAccel = false;
    bool ok = lsmFifoCount(n, overflow) && n >= 10 && n <= 60
              && lsmFifoWord(fx, fy, fz, isAccel) && isAccel
              && readLsmRaw(dx, dy, dz);
    if (ok) {
        // dezelfde versnelling als de gewone meting? (0,06 s verschil in tijd)
        float mf = sqrtf(fx * fx + fy * fy + fz * fz);
        float md = sqrtf(dx * dx + dy * dy + dz * dz);
        ok = fabsf(mf - md) < 0.5f;
    }
    if (!ok) lsmFifoOff();
    return ok;
}

// Opnieuw beginnen met meten (einde van setup, of een nieuwe meting).
void restartLSM6DSO() {
    lsm_buf_index = 0;
    lsm_have_prev = false;
    lsm_owed = 0;
    if (ok_lsm && lsm_fifo) {
        lsm_fifo = lsmFifoOn();
        fifo_consumed = 0;
        fifo_rate_started = false;
        fifoLastSampleMs = millis();
        lastFifoUs = micros();
    }
    lastLsmUs = micros();
}

// Om de 5 ms: alle metingen die in de FIFO wachten ophalen.
void serviceLsmFifo(unsigned long now) {
    uint16_t n = 0;
    bool overflow = false;
    if (!lsmFifoCount(n, overflow)) {
        diag_lsm_errors++;
    } else {
        if (overflow) {
            // De FIFO was vol (meer dan 1 s niet opgehaald): er ontbreken
            // metingen. De buffer en de telling beginnen opnieuw.
            lsm_buf_index = 0;
            fifo_rate_started = false;
            diag_lsm_restarts++;
        }
        measureLsmRate(micros(), fifo_consumed + n);
        if (n > LSM_FIFO_MAX_WORDS) n = LSM_FIFO_MAX_WORDS;
        for (uint16_t i = 0; i < n; i++) {
            float ax, ay, az;
            bool isAccel = false;
            if (!lsmFifoWord(ax, ay, az, isAccel)) { diag_lsm_errors++; break; }
            fifo_consumed++;
            if (!isAccel) continue;
            float a = sqrtf(ax * ax + ay * ay + az * az);
            if (a > acc_peak_g) acc_peak_g = a;
            pushSample(ax, ay, az);
            diag_lsm_real++;
            fifoLastSampleMs = now;
        }
    }
    // Komt er niets meer uit de FIFO? Dan terug naar zelf lezen.
    if ((long)(now - fifoLastSampleMs) > (long)LSM_FIFO_TIMEOUT_MS) {
        lsmFifoOff();
        lsm_fifo = false;
        diag_fifo_fallback = true;
        lsm_buf_index = 0;
        lsm_have_prev = false;
        lsm_owed = 0;
        lastLsmUs = micros();
    }
}

// De echte meetsnelheid van de sensor: zoveel metingen gemaakt in zoveel
// tijd (klok van de Teensy). Eerst over 2 s, daarna telkens over 10 s.
void measureLsmRate(uint32_t nowUs, uint32_t made) {
    if (!fifo_rate_started) {
        fifo_rate_started = true;
        fifo_rate_us0 = nowUs;
        fifo_rate_n0 = made;
        return;
    }
    uint32_t dt = nowUs - fifo_rate_us0;
    if (dt >= fifo_rate_window_us) {
        float fs = (float)(made - fifo_rate_n0) * 1e6f / (float)dt;
        if (fs > 0.9f * LSM_ODR_NOMINAL_HZ && fs < 1.1f * LSM_ODR_NOMINAL_HZ) lsm_fs = fs;
        fifo_rate_us0 = nowUs;
        fifo_rate_n0 = made;
        fifo_rate_window_us = 10000000UL;
    }
}

void initLoRa() {
    Serial.print("LoRa RFM95W initialiseren... ");
    int state = radio.begin(LORA_FREQUENCY, LORA_BANDWIDTH,
                            LORA_SF, LORA_CR, LORA_SYNC_WORD);
    if (state == RADIOLIB_ERR_NONE) {
        radio.setOutputPower(LORA_POWER_DBM);   // zie LORA_POWER_DBM
        ok_lora = true;
        Serial.println("OK");
    } else {
        Serial.print("FOUT! Code: ");
        Serial.println(state);
        errorBeep();
        // Niet stoppen: blijven meten en op de SD-kaart schrijven
    }
}

void initSD() {
    Serial.print("SD kaart initialiseren... ");
    if (SD.begin(SD_CS)) {
        sd_ok = true;
        openNewFile();
    } else {
        Serial.println("FOUT! SD kaart niet gevonden.");
        errorBeep();
        // Niet fataal - doorgaan zonder SD
    }
}

// Elke start (en elke nieuwe meting) een NIEUW bestand: cansat27_000.csv,
// cansat27_001.csv, ...
void openNewFile() {
    if (!sd_ok) return;
    char fname[24];
    bool found = false;
    for (int i = 0; i < 1000; i++) {
        snprintf(fname, sizeof(fname), "cansat27_%03d.csv", i);
        if (!SD.exists(fname)) { found = true; break; }
    }
    if (!found) {
        Serial.println("FOUT! Geen vrije bestandsnaam (1000 bestanden).");
        errorBeep();
        return;
    }
    csvFile = SD.open(fname, FILE_WRITE);
    if (csvFile) {
        // CSV header schrijven
        csvFile.println(
            "millis,temp_C,press_hPa,alt_m,"
            "lat,lon,time_utc,"
            "gyro_x,gyro_y,gyro_z,"
            "lacc_x,lacc_y,lacc_z,"
            "grav_x,grav_y,grav_z,"
            "heading,roll,pitch,"
            "qw,qx,qy,qz,"
            "fft_peak_hz,fft_peak_amp,"
            "audio_rms,"
            "acc_peak_g,"
            "gps_course_deg,gps_speed_ms,"
            "vib_0_10_g,vib_10_30_g,vib_30_60_g,vib_60_120_g,vib_120_208_g"
        );
        csvFile.flush();
        sdBufferLines = 0;
        Serial.print("OK → ");
        Serial.println(fname);
    } else {
        Serial.println("FOUT! Kan bestand niet openen.");
        errorBeep();
    }
}

// Het Hamming-venster één keer berekenen (zelfde formule als arduinoFFT),
// en het gemiddelde van venster²: dat is nodig om de sterkte in g te kennen.
void initFFT() {
    double sum = 0;
    for (int i = 0; i < FFT_SAMPLES; i++) {
        float w = 0.54f - 0.46f * cosf(6.2831853f * i / (FFT_SAMPLES - 1));
        fft_window[i] = w;
        sum += (double)w * w;
    }
    fft_window_power = (float)(sum / FFT_SAMPLES);
}

// ============================================================
// SENSOR UITLEZEN
// ============================================================

// BMP390, 20 keer per seconde. De bibliotheek (performReading) start een
// meting en leest METEEN de registers: daarin staat nog de vorige meting.
// Met 1 meting per seconde was elke waarde dus 1 s oud, en het filter van
// de sensor (IIR) werkte dan op 1 meting per seconde: veel te traag voor
// een raket. Nu is een waarde hoogstens 50 ms oud, en het (lichtere) filter
// volgt binnen ~0,1 s.
void readBMP390() {
    if (!bmp.performReading()) { diag_bmp_bad++; return; }
    diag_bmp++;
    float t = bmp.temperature;
    float p = bmp.pressure / 100.0F;        // Pa naar hPa
    // Een onmogelijke waarde (storing op de bus) overslaan
    if (!(p > 300.0f && p < 1100.0f && t > -40.0f && t < 85.0f)) {
        diag_bmp_bad++;
        return;
    }
    last_temp     = t;
    last_pressure = p;
    // Zelfde formule als Adafruit (readAltitude zou een tweede meting starten)
    last_altitude = 44330.0f *
        (1.0f - powf(last_pressure / SEA_LEVEL_PRESSURE, 0.1903f));
    bmp_valid = true;
}

// Elke seconde. Alleen een VERSE fix telt. Zonder fix blijven lat en lon de
// laatste bekende positie, maar gps_fix is false: in de CSV staat dan
// time_utc = 00:00:00, en de radio stuurt NO_FIX_LAT / NO_FIX_LON. Vroeger
// bleef de oude positie staan alsof ze nog klopte.
void readGPS() {
    gps_fix = GPS.fix && GPS.secondsSinceFix() < GPS_FIX_MAX_AGE_S;
    if (gps_fix) {
        last_lat = GPS.latitudeDegrees;   // decimale graden, inclusief N/S teken
        last_lon = GPS.longitudeDegrees;  // decimale graden, inclusief E/W teken
        char buf[12];
        snprintf(buf, sizeof(buf), "%02d:%02d:%02d", GPS.hour, GPS.minute, GPS.seconds);
        last_time_utc = String(buf);
        last_gps_course = GPS.angle;               // graden, 0 = noord
        last_gps_speed  = GPS.speed * 0.514444f;   // knopen → m/s
    }
}

// De BNO055 in 5 kleine stappen (één per LSM6DSO-meting), 10 rondes per
// seconde. Vroeger: alles in één keer, 100 keer per seconde. Dat hield de
// I2C-bus bijna de helft van de tijd bezet, terwijl er maar 1 waarde per
// seconde bewaard wordt.
void readBNO055Step(int step) {
    if (step == 1) {
        // Quaternionen - geen gimbal lock
        imu::Quaternion q = bno.getQuat();
        last_qw = q.w();
        last_qx = q.x();
        last_qy = q.y();
        last_qz = q.z();
    } else if (step == 2) {
        // Euler-hoeken (voor eenvoudige weergave)
        imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
        last_heading = euler.x();
        last_roll    = euler.y();
        last_pitch   = euler.z();
    } else if (step == 3) {
        // Lineaire versnelling (zonder zwaartekracht)
        imu::Vector<3> lacc = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
        last_lacc_x = lacc.x();
        last_lacc_y = lacc.y();
        last_lacc_z = lacc.z();
    } else if (step == 4) {
        // Gyroscoop
        imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
        last_gyro_x = gyro.x();
        last_gyro_y = gyro.y();
        last_gyro_z = gyro.z();
    } else {
        // Zwaartekrachtsvector
        imu::Vector<3> grav = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
        last_grav_x = grav.x();
        last_grav_y = grav.y();
        last_grav_z = grav.z();
    }
}

// De drie assen van de LSM6DSO in ÉÉN leesopdracht (6 bytes), in g.
bool readLsmRaw(float &ax, float &ay, float &az) {
    uint8_t b[6];
    if (lsm.readMultipleRegisters(b, OUTX_L_A, 6) != IMU_SUCCESS) return false;
    ax = (int16_t)(b[0] | (b[1] << 8)) * lsm_g_per_lsb;
    ay = (int16_t)(b[2] | (b[3] << 8)) * lsm_g_per_lsb;
    az = (int16_t)(b[4] | (b[5] << 8)) * lsm_g_per_lsb;
    return true;
}

// Eén meting op het rooster van 416 Hz. missed = het aantal roosterpunten
// dat net gemist werd (de lus was bezig). Die worden ingevuld op een rechte
// lijn tussen de vorige en deze meting: zo blijft elke meting op zijn plaats
// in de tijd en klopt de frequentie van de FFT.
void readLSM6DSO(uint32_t missed) {
    float ax, ay, az;
    if (!readLsmRaw(ax, ay, az)) {
        diag_lsm_errors++;
        lsm_owed += missed + 1;         // ook dit roosterpunt is er niet
        return;
    }
    missed += lsm_owed;
    lsm_owed = 0;

    // Grootste versnelling sinds de vorige logregel (in g)
    float a = sqrtf(ax * ax + ay * ay + az * az);
    if (a > acc_peak_g) acc_peak_g = a;

    if (lsm_have_prev && missed > 0) {
        if (missed > LSM_MAX_FILL) {
            // Te groot gat om in te vullen: de buffer begint opnieuw
            lsm_buf_index = 0;
            diag_lsm_restarts++;
        } else {
            for (uint32_t k = 1; k <= missed; k++) {
                float f = (float)k / (float)(missed + 1);
                pushSample(lsm_prev_x + (ax - lsm_prev_x) * f,
                           lsm_prev_y + (ay - lsm_prev_y) * f,
                           lsm_prev_z + (az - lsm_prev_z) * f);
                diag_lsm_filled++;
            }
        }
    }
    pushSample(ax, ay, az);
    diag_lsm_real++;
    lsm_prev_x = ax;
    lsm_prev_y = ay;
    lsm_prev_z = az;
    lsm_have_prev = true;
}

// Eén meting in de FFT-buffer. Is de buffer vol, dan meteen de FFT.
void pushSample(float ax, float ay, float az) {
    lsm_buffer_x[lsm_buf_index] = ax;
    lsm_buffer_y[lsm_buf_index] = ay;
    lsm_buffer_z[lsm_buf_index] = az;
    lsm_buf_index++;
    if (lsm_buf_index >= FFT_SAMPLES) {
        lsm_buf_index = 0;
        computeFFT();
        fft_ran = true;
    }
}

// De FFT van één as, opgeteld bij fft_power[].
// Eerst het gemiddelde (zwaartekracht ~1 g) aftrekken, anders lekt
// dat naar de laagste frequenties en wint "1 Hz" bijna altijd.
void addAxisPower(const float *buf) {
    float mean = 0;
    for (int i = 0; i < FFT_SAMPLES; i++) mean += buf[i];
    mean /= FFT_SAMPLES;
    for (int i = 0; i < FFT_SAMPLES; i++) {
        fft_real[i] = (buf[i] - mean) * fft_window[i];
        fft_imag[i] = 0;
    }
    FFT.compute(fft_real, fft_imag, FFT_SAMPLES, FFT_FORWARD);
    for (int k = 0; k < FFT_SAMPLES / 2; k++) {
        fft_power[k] += fft_real[k] * fft_real[k] + fft_imag[k] * fft_imag[k];
    }
}

void computeFFT() {
    // De trillingen van de drie assen samen: de som van |X|² van X, Y en Z.
    // Zo telt elke trilling mee, in welke richting ze ook gaat, en maakt het
    // niet uit hoe de sensor in het blik zit. (Vroeger: alleen de Z-as.)
    for (int k = 0; k < FFT_SAMPLES / 2; k++) fft_power[k] = 0;
#if FFT_ALL_AXES
    addAxisPower(lsm_buffer_x);
    addAxisPower(lsm_buffer_y);
#endif
    addAxisPower(lsm_buffer_z);

    // Zelf de piek zoeken (bin 0 = DC overslaan), zodat frequentie en
    // sterkte gegarandeerd bij dezelfde bin horen
    int   peakIdx = 1;
    float peakPow = fft_power[1];
    for (int i = 2; i < FFT_SAMPLES / 2; i++) {
        if (fft_power[i] > peakPow) { peakPow = fft_power[i]; peakIdx = i; }
    }
    // Parabolische interpolatie voor een nauwkeurigere frequentie
    float delta = 0;
    if (peakIdx > 1 && peakIdx < FFT_SAMPLES / 2 - 1) {
        float a = sqrtf(fft_power[peakIdx - 1]), b = sqrtf(peakPow),
              c = sqrtf(fft_power[peakIdx + 1]);
        float denom = a - 2 * b + c;
        if (denom != 0) delta = 0.5f * (a - c) / denom;
    }
    // Met de FIFO: de gemeten meetsnelheid van de sensor. Zonder FIFO liggen
    // de metingen op het rooster van de Teensy (2404 µs, gemiste punten
    // ingevuld): dan de nominale 416 Hz.
    const float fs = lsm_fifo ? lsm_fs : (float)LSM_SAMPLE_RATE_HZ;
    fft_peak_hz = (peakIdx + delta) * fs / FFT_SAMPLES;
    // Sterkte uit de energie van de piek (bins k-2 .. k+2, Parseval, zoals
    // de banden): klopt ook als de frequentie tussen twee bins valt.
    int lo = peakIdx - 2 < 1 ? 1 : peakIdx - 2;
    int hi = peakIdx + 2 > FFT_SAMPLES / 2 - 1 ? FFT_SAMPLES / 2 - 1 : peakIdx + 2;
    float p = 0;
    for (int i = lo; i <= hi; i++) p += fft_power[i];
    float rms = sqrtf(2.0f * p / ((float)FFT_SAMPLES * FFT_SAMPLES * fft_window_power));
    fft_peak_amp = rms * 1.41421356f;          // sinus: piek = RMS · √2

    computeBands(fs);
}

// RMS-versnelling per frequentieband, uit fft_power[] (|X|² per frequentie).
// Parseval: de energie van het signaal = de som van |X_k|² over alle bins.
// Factor 2: elke frequentie komt twee keer voor (positief en negatief).
// Delen door N² · gemiddelde(w²): het venster maakt het signaal zwakker.
void computeBands(float fs) {
    float pow_[N_BANDS] = {0, 0, 0, 0, 0};
    for (int k = 1; k < FFT_SAMPLES / 2; k++) {     // k = 0 is DC: overslaan
        float f = k * fs / FFT_SAMPLES;
        int b = N_BANDS - 1;
        for (int j = 0; j < N_BANDS - 1; j++) {
            if (f < BAND_EDGE_HZ[j + 1]) { b = j; break; }
        }
        pow_[b] += fft_power[k];
    }
    const float norm = (float)FFT_SAMPLES * FFT_SAMPLES * fft_window_power;
    for (int b = 0; b < N_BANDS; b++) {
        vib_band_g[b] = sqrtf(2.0f * pow_[b] / norm);
    }
}

void processAudio() {
    // Alleen RMS berekenen - geen FFT
    // ALLE beschikbare blokken (128 samples, ~2,9 ms) optellen.
    while (audioQueue.available() > 0) {
        int16_t* buf = audioQueue.readBuffer();
        for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
            float s = buf[i] / 32768.0f;
            audio_sum    += s;
            audio_sum_sq += s * s;
        }
        audio_count += AUDIO_BLOCK_SAMPLES;
        audioQueue.freeBuffer();
    }
}

void updateAudioRms() {
    if (audio_count == 0) return;
    // RMS over de hele seconde, zonder DC-offset (SPH0645 heeft een offset)
    double mean = audio_sum / audio_count;
    double var  = audio_sum_sq / audio_count - mean * mean;
    audio_rms = var > 0 ? sqrt(var) : 0;
    audio_sum = audio_sum_sq = 0;
    audio_count = 0;
}

// ============================================================
// VERZENDEN EN LOGGEN
// ============================================================

void sendAndLog() {
    unsigned long now = millis();
    updateAudioRms();

    // CSV regel samenstellen
    String csv = String(now) + "," +
                 String(last_temp, 2) + "," +
                 String(last_pressure, 2) + "," +
                 String(last_altitude, 2) + "," +
                 String(last_lat, 6) + "," +
                 String(last_lon, 6) + "," +
                 (gps_fix ? last_time_utc : String("00:00:00")) + "," +
                 String(last_gyro_x, 3) + "," +
                 String(last_gyro_y, 3) + "," +
                 String(last_gyro_z, 3) + "," +
                 String(last_lacc_x, 3) + "," +
                 String(last_lacc_y, 3) + "," +
                 String(last_lacc_z, 3) + "," +
                 String(last_grav_x, 3) + "," +
                 String(last_grav_y, 3) + "," +
                 String(last_grav_z, 3) + "," +
                 String(last_heading, 2) + "," +
                 String(last_roll, 2) + "," +
                 String(last_pitch, 2) + "," +
                 String(last_qw, 4) + "," +
                 String(last_qx, 4) + "," +
                 String(last_qy, 4) + "," +
                 String(last_qz, 4) + "," +
                 String(fft_peak_hz, 1) + "," +
                 String(fft_peak_amp, 3) + "," +
                 String(audio_rms, 4) + "," +
                 String(acc_peak_g, 2) + "," +
                 String(last_gps_course, 1) + "," +
                 String(last_gps_speed, 2) + "," +
                 String(vib_band_g[0], 4) + "," +
                 String(vib_band_g[1], 4) + "," +
                 String(vib_band_g[2], 4) + "," +
                 String(vib_band_g[3], 4) + "," +
                 String(vib_band_g[4], 4);
    acc_peak_g = 0;   // nieuw interval: opnieuw de grootste zoeken

    // SD kaart schrijven
    if (csvFile) {
        csvFile.println(csv);
        sdBufferLines++;
    }

    // LoRa pakket verzenden (compacte versie, 19 waarden)
    // temp, press, alt, lat, lon, lacc_xyz, heading, roll, pitch, fft_peak_hz,
    // audio_rms, en daarna de FFT: fft_peak_amp en de 5 trillingsbanden (g)
    // Zonder fix: de vaste "geen fix"-positie (zie NO_FIX_LAT)
    String loraPacket = String(last_temp, 1) + "," +
                        String(last_pressure, 1) + "," +
                        String(last_altitude, 1) + "," +
                        String(gps_fix ? last_lat : (float)NO_FIX_LAT, 5) + "," +
                        String(gps_fix ? last_lon : (float)NO_FIX_LON, 5) + "," +
                        String(last_lacc_x, 2) + "," +
                        String(last_lacc_y, 2) + "," +
                        String(last_lacc_z, 2) + "," +
                        String(last_heading, 1) + "," +
                        String(last_roll, 1) + "," +
                        String(last_pitch, 1) + "," +
                        String(fft_peak_hz, 0) + "," +
                        String(audio_rms, 3) + "," +
                        String(fft_peak_amp, 3) + "," +
                        String(vib_band_g[0], 4) + "," +
                        String(vib_band_g[1], 4) + "," +
                        String(vib_band_g[2], 4) + "," +
                        String(vib_band_g[3], 4) + "," +
                        String(vib_band_g[4], 4);

    if (ok_lora) {
        if (loraBusy) {
            // Kan normaal niet (een pakket duurt ~0,25 s): niet wachten
            Serial.println("LoRa: vorig pakket nog bezig, dit pakket overgeslagen");
        } else {
            // geeft het pakket aan de radio en keert meteen terug
            int state = radio.startTransmit(loraPacket);
            if (state == RADIOLIB_ERR_NONE) {
                loraBusy = true;
                loraStartMs = millis();
            } else {
                Serial.print("LoRa fout: ");
                Serial.println(state);
            }
        }
    }

    // Debug output
    Serial.println(csv);
}

// Het pakket is weg als DIO0 hoog wordt: radio terug naar standby.
// Wordt elke lus-doorgang opgeroepen; kost bijna niets.
void checkLoRa() {
    if (!loraBusy) return;
    if (digitalRead(RFM95_DIO0) == HIGH ||
        millis() - loraStartMs > LORA_TX_TIMEOUT_MS) {
        radio.finishTransmit();
        loraBusy = false;
    }
}

void flushSD() {
    if (csvFile && sdBufferLines > 0) {
        csvFile.flush();
        sdBufferLines = 0;
    }
}

// Elke 10 s één regel die met # begint (alleen op Serial, niet op de
// SD-kaart en niet via de radio). Zo zie je in de Serial Monitor of er
// echt 416 keer per seconde gemeten wordt:
//   # Controle 10 s: LSM6DSO 4155 echt + 5 ingevuld (moet samen ~4160) ...
// Met de FIFO staat er het aantal metingen en de gemeten meetsnelheid.
// Zonder FIFO: "echt" moet bijna alles zijn; veel "ingevuld" = lus te traag.
void printDiagnostics(unsigned long ms) {
    Serial.print("# Controle ");
    Serial.print(ms / 1000);
    Serial.print(" s: LSM6DSO ");
    Serial.print(diag_lsm_real);
    if (lsm_fifo) {
        Serial.print(" metingen via FIFO (");
        Serial.print(lsm_fs, 1);
        Serial.print(" per seconde");
    } else {
        Serial.print(" echt + ");
        Serial.print(diag_lsm_filled);
        Serial.print(" ingevuld (moet samen ~");
        Serial.print((unsigned long)(ms * (unsigned long)LSM_SAMPLE_RATE_HZ / 1000UL));
    }
    Serial.print("), BMP390 ");
    Serial.print(diag_bmp);
    Serial.print(" (moet ~");
    Serial.print(ms / BMP_INTERVAL_MS);
    Serial.print(")");
    if (diag_lsm_restarts || diag_lsm_errors || diag_bmp_bad) {
        Serial.print(", buffer opnieuw ");
        Serial.print(diag_lsm_restarts);
        Serial.print(", leesfouten LSM6DSO ");
        Serial.print(diag_lsm_errors);
        Serial.print(", BMP390 ");
        Serial.print(diag_bmp_bad);
    }
    if (ok_lsm && diag_lsm_filled * 20 > diag_lsm_real) {
        Serial.print("  LET OP: meer dan 5 % ingevuld");
    }
    if (diag_fifo_fallback) {
        Serial.print("  LET OP: de FIFO viel uit, de Teensy leest nu zelf");
        diag_fifo_fallback = false;
    }
    Serial.println();
    diag_lsm_real = diag_lsm_filled = diag_lsm_restarts = 0;
    diag_lsm_errors = diag_bmp = diag_bmp_bad = 0;
}

// ============================================================
// LANDINGSPROCEDURE
// ============================================================

void landingProcedure(unsigned long now) {
    Serial.println("\n=======================");
    Serial.println("== Landingsprocedure ==");
    Serial.println("=======================\n");

    // Laatste SD flush
    if (csvFile) {
        csvFile.flush();
        csvFile.close();
        Serial.println("SD kaart afgesloten.");
    }

    // Audio queue stoppen
    audioQueue.end();

    // Vanaf nu: loopLanded() — buzzer, en wachten op een nieuwe lancering
    landed = true;
    isLaunched = false;
    landedMs = now;
    launchHits = 0;

    Serial.println("Landingsprocedure voltooid.");
    Serial.println("Buzzer aan voor terugvinden...");
}

// ============================================================
// HULPFUNCTIES
// ============================================================

void beep(int times) {
    for (int i = 0; i < times; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
        delay(100);
    }
}

void errorBeep() {
    for (int i = 0; i < 3; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(500);
        digitalWrite(BUZZER_PIN, LOW);
        delay(200);
    }
}
