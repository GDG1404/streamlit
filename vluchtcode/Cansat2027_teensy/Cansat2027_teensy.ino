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
 *   - ArduinoFFT (alleen voor LSM6DSO trillingen)
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

// LoRa instellingen
#define LORA_FREQUENCY      868.0   // MHz - Europa
#define LORA_BANDWIDTH      125.0   // kHz
#define LORA_SF             7       // Spreading Factor 7-12 — SF7: ~130ms on-air (SF9 was ~800ms en blokkeerde de sensorloop)
#define LORA_CR             7       // Coding Rate 5-8
#define LORA_SYNC_WORD      0x12    // Privé netwerk

// Pins
#define RFM95_CS            10
#define RFM95_RST           9
#define RFM95_DIO0          2       // Verplaatst vanaf pin 8 i.v.m. I2S audio-data conflict
#define BUZZER_PIN          14
#define SD_CS               BUILTIN_SDCARD  // Ingebouwd op Teensy 4.1

// Drempelwaarden
#define SEA_LEVEL_PRESSURE  1014.0  // hPa - pas aan voor lanceerlocatie!
#define LAUNCH_ALT_DIFF     50.0    // meter hoogteverschil voor lanceerdetectie
#define LAUNCH_CHECK_MS     5000    // elke 5s checken
#define FLIGHT_DURATION_MS  360000  // 6 minuten vluchtduur

// Samplerates
#define BMP_INTERVAL_MS     1000    // BMP390: 1 Hz
#define GPS_INTERVAL_MS     1000    // GPS: 1 Hz
#define BNO_INTERVAL_MS     10      // BNO055: 100 Hz
#define LSM_INTERVAL_US     2404    // LSM6DSO: poll exact op 416 Hz (1e6/416 µs)
#define LORA_INTERVAL_MS    1000    // LoRa verzenden: 1 Hz
#define SD_FLUSH_MS         500     // SD flush: elke 500 ms

// FFT instellingen
#define FFT_SAMPLES         512     // Aantal samples voor FFT
#define LSM_SAMPLE_RATE_HZ  416     // Hz — overeenkomstig met setAccelDataRate(416)

// ============================================================
// OBJECTEN
// ============================================================

// Sensoren
Adafruit_BMP3XX bmp;
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
LSM6DSO lsm;
Adafruit_GPS GPS(&Serial1);
// Extra RX-buffer: tijdens radio.transmit() (~130 ms blokkerend) komt er
// op 9600 baud ~125 bytes NMEA binnen; de standaardbuffer is maar 64 bytes
// en zou elke seconde GPS-zinnen corrumperen.
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

// SD
File csvFile;
String sdBuffer = "";
int sdBufferLines = 0;

// ============================================================
// GLOBALE VARIABELEN
// ============================================================

// Vluchtstatusus
bool isLaunched = false;
unsigned long launchCheckTimer = 0;
unsigned long launchTimer = 0;
float launchCheckAltitude = 0;

// Timers
unsigned long lastBmpMs = 0;
unsigned long lastGpsMs = 0;
unsigned long lastBnoMs = 0;
unsigned long lastLsmUs = 0;     // microseconden! (exacte 416 Hz timing)
unsigned long lastLoraMs = 0;
unsigned long lastSdFlushMs = 0;

// Laatste bekende waarden (fallback bij sensoruitval)
float last_temp       = 10.0;
float last_pressure   = 1000.0;
float last_altitude   = 600.0;
float last_lat        = 50.457303;  // Elsenborn
float last_lon        = 6.221376;
String last_time_utc  = "00:00:00";

float last_gyro_x = 0, last_gyro_y = 0, last_gyro_z = 0;
float last_lacc_x = 0, last_lacc_y = 0, last_lacc_z = 0;
float last_grav_x = 0, last_grav_y = 0, last_grav_z = 0;
float last_heading = 0, last_roll = 0, last_pitch = 0;
float last_qw = 1, last_qx = 0, last_qy = 0, last_qz = 0;

// LSM6DSO buffer voor FFT
float lsm_buffer_x[FFT_SAMPLES];
float lsm_buffer_y[FFT_SAMPLES];
float lsm_buffer_z[FFT_SAMPLES];
int lsm_buf_index = 0;
bool lsm_buf_ready = false;

// Audio RMS (geen FFT - alleen fasedetectie en snelheidsvalidatie)
float audio_rms = 0;

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("CanSat 2027 - Teensy 4.1");
    Serial.println("========================");

    // Buzzer
    pinMode(BUZZER_PIN, OUTPUT);

    // I2C
    Wire.begin();
    Wire.setClock(400000);

    // GPS UART
    Serial1.begin(9600);
    Serial1.addMemoryForRead(gpsRxBuf, sizeof(gpsRxBuf));

    // Audio geheugen — ruim genoeg om de ~130 ms blokkerende
    // radio.transmit() te overbruggen (44.1 kHz / 128 samples
    // ≈ 345 blokken/s → 45 blokken per transmit + marge)
    AudioMemory(60);

    // Sensoren initialiseren
    initBMP390();
    initBNO055();
    initLSM6DSO();
    initGPS();
    initLoRa();
    initSD();

    // Startbuzzer
    beep(3);

    Serial.println("\nHoofdlus gestart");
    Serial.println("================\n");

    launchCheckTimer = millis();
    lastSdFlushMs = millis();

    // Audio queue starten
    audioQueue.begin();
}

// ============================================================
// HOOFDLUS
// ============================================================

void loop() {
    unsigned long now = millis();

    // --- GPS continu uitlezen (niet-blokkerend) ---
    // hele buffer leeglezen, niet 1 teken per loop-doorgang
    while (Serial1.available()) {
        GPS.read();
        if (GPS.newNMEAreceived()) {
            GPS.parse(GPS.lastNMEA());
        }
    }

    // --- BMP390 uitlezen: 1 Hz ---
    if (now - lastBmpMs >= BMP_INTERVAL_MS) {
        lastBmpMs = now;
        readBMP390();
    }

    // --- GPS data ophalen: 1 Hz ---
    if (now - lastGpsMs >= GPS_INTERVAL_MS) {
        lastGpsMs = now;
        readGPS();
    }

    // --- BNO055 uitlezen: 100 Hz ---
    if (now - lastBnoMs >= BNO_INTERVAL_MS) {
        lastBnoMs = now;
        readBNO055();
    }

    // --- LSM6DSO uitlezen: exact 416 Hz + FFT buffer vullen ---
    // µs-timer: op 2 ms (500 Hz) pollen van een 416 Hz-sensor gaf
    // ~17% dubbele samples en dus een scheve FFT-frequentie-as.
    if (micros() - lastLsmUs >= LSM_INTERVAL_US) {
        lastLsmUs = micros();
        readLSM6DSO();
    }

    // --- Audio RMS berekenen ---
    processAudio();

    // --- FFT berekenen als buffer vol is ---
    if (lsm_buf_ready) {
        computeFFT();
        lsm_buf_ready = false;
    }

    // --- LoRa verzenden + SD schrijven: 1 Hz ---
    if (now - lastLoraMs >= LORA_INTERVAL_MS) {
        lastLoraMs = now;
        sendAndLog();
    }

    // --- SD flushen ---
    if (now - lastSdFlushMs >= SD_FLUSH_MS) {
        lastSdFlushMs = now;
        flushSD();
    }


    // --- Lanceerdetectie ---
    if (!isLaunched && last_pressure != 1000.0 &&
        now - launchCheckTimer >= LAUNCH_CHECK_MS) {
        if (launchCheckAltitude != 0 &&
            abs(last_altitude - launchCheckAltitude) >= LAUNCH_ALT_DIFF) {
            isLaunched = true;
            launchTimer = now;
            Serial.println(">>> LANCERING GEDETECTEERD <<<");
            // GEEN buzzer tijdens de vlucht: hij zit naast de SPH0645
            // en zou de audio_rms-meting vervuilen. De buzzer komt pas
            // na de landing (terugvindsignaal).
        }
        launchCheckTimer = now;
        launchCheckAltitude = last_altitude;
    }

    // --- Landingsdetectie na 6 minuten ---
    if (isLaunched && now - launchTimer >= FLIGHT_DURATION_MS) {
        Serial.println(">>> LANDING GEDETECTEERD <<<");
        landingProcedure();
        // Terugvindsignaal: elke 10 s een buzz van 3 s.
        // Blokkerend is hier prima — loggen en zenden zijn gestopt.
        while (true) {
            digitalWrite(BUZZER_PIN, HIGH);
            delay(3000);
            digitalWrite(BUZZER_PIN, LOW);
            delay(7000);
        }
    }
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
            bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
            bmp.setOutputDataRate(BMP3_ODR_50_HZ);
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! BMP390 niet gevonden.");
    errorBeep();
    while (true); // Stop bij kritieke sensorfout
}

void initBNO055() {
    Serial.print("BNO055 initialiseren... ");
    for (int i = 0; i < 5; i++) {
        if (bno.begin()) {
            delay(1000);
            bno.setExtCrystalUse(true);
            // Zet in IMU-modus voor hogere updaterate (geen magnetometer)
            // bno.setMode(OPERATION_MODE_IMUPLUS);
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! BNO055 niet gevonden.");
    errorBeep();
    while (true);
}

void initGPS() {
    Serial.print("GPS PA1616D initialiseren... ");
    GPS.begin(9600);
    GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);   // RMC + GGA zinnen
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);       // 1 Hz update
    GPS.sendCommand(PGCMD_ANTENNA);                  // Antennestatus opvragen
    delay(1000);
    Serial.println("OK");
}

void initLSM6DSO() {
    Serial.print("LSM6DSO initialiseren... ");
    for (int i = 0; i < 5; i++) {
        if (lsm.begin()) {
            lsm.setAccelRange(16);          // ±16g voor hoge G-krachten
            lsm.setAccelDataRate(416);      // 416 Hz accelerometer
            lsm.setGyroDataRate(416);       // 416 Hz gyroscoop
            // setAccelFIFO niet beschikbaar in SparkFun LSM6DSO library — polling via timer
            Serial.println("OK");
            return;
        }
        delay(200);
    }
    Serial.println("FOUT! LSM6DSO niet gevonden.");
    errorBeep();
    // Niet fataal - doorgaan zonder trillingssensor
}

void initLoRa() {
    Serial.print("LoRa RFM95W initialiseren... ");
    int state = radio.begin(LORA_FREQUENCY, LORA_BANDWIDTH,
                            LORA_SF, LORA_CR, LORA_SYNC_WORD);
    if (state == RADIOLIB_ERR_NONE) {
        radio.setOutputPower(20); // Maximaal zendvermogen
        Serial.println("OK");
    } else {
        Serial.print("FOUT! Code: ");
        Serial.println(state);
        errorBeep();
        while (true);
    }
}

void initSD() {
    Serial.print("SD kaart initialiseren... ");
    if (SD.begin(SD_CS)) {
        csvFile = SD.open("cansat27.csv", FILE_WRITE);
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
                "audio_rms"
            );
            Serial.println("OK");
        } else {
            Serial.println("FOUT! Kan bestand niet openen.");
        }
    } else {
        Serial.println("FOUT! SD kaart niet gevonden.");
        errorBeep();
        // Niet fataal - doorgaan zonder SD
    }
}

// ============================================================
// SENSOR UITLEZEN
// ============================================================

void readBMP390() {
    if (bmp.performReading()) {
        last_temp     = bmp.temperature;
        last_pressure = bmp.pressure / 100.0F; // Pa naar hPa
        last_altitude = bmp.readAltitude(SEA_LEVEL_PRESSURE);
    }
}

void readGPS() {
    if (GPS.fix) {
        last_lat = GPS.latitudeDegrees;   // decimale graden, inclusief N/S teken
        last_lon = GPS.longitudeDegrees;  // decimale graden, inclusief E/W teken
        char buf[12];
        sprintf(buf, "%02d:%02d:%02d", GPS.hour, GPS.minute, GPS.seconds);
        last_time_utc = String(buf);
    }
}

void readBNO055() {
    // Quaternionen - geen gimbal lock
    imu::Quaternion q = bno.getQuat();
    last_qw = q.w();
    last_qx = q.x();
    last_qy = q.y();
    last_qz = q.z();

    // Euler-hoeken (voor eenvoudige weergave)
    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
    last_heading = euler.x();
    last_roll    = euler.y();
    last_pitch   = euler.z();

    // Lineaire versnelling (zonder zwaartekracht)
    imu::Vector<3> lacc = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    last_lacc_x = lacc.x();
    last_lacc_y = lacc.y();
    last_lacc_z = lacc.z();

    // Gyroscoop
    imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
    last_gyro_x = gyro.x();
    last_gyro_y = gyro.y();
    last_gyro_z = gyro.z();

    // Zwaartekrachtsvector
    imu::Vector<3> grav = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
    last_grav_x = grav.x();
    last_grav_y = grav.y();
    last_grav_z = grav.z();
}

// FFT resultaatvariabelen (globaal voor gebruik in sendAndLog)
float fft_peak_hz  = 0;
float fft_peak_amp = 0;

void readLSM6DSO() {
    // Polling via timer in loop() — geen checkStatus nodig in SparkFun library

    // Ruwe accelerometerdata uitlezen
    float ax = lsm.readFloatAccelX();
    float ay = lsm.readFloatAccelY();
    float az = lsm.readFloatAccelZ();

    // Buffer vullen voor FFT
    if (lsm_buf_index < FFT_SAMPLES) {
        // Magnitude van de drie assen
        lsm_buffer_x[lsm_buf_index] = ax;
        lsm_buffer_y[lsm_buf_index] = ay;
        lsm_buffer_z[lsm_buf_index] = az;
        lsm_buf_index++;
    } else {
        lsm_buf_ready = true;
        lsm_buf_index = 0;
    }
}

void computeFFT() {
    // FFT op Z-as (verticale valrichting)
    for (int i = 0; i < FFT_SAMPLES; i++) {
        fft_real[i] = lsm_buffer_z[i];
        fft_imag[i] = 0;
    }

    FFT.windowing(fft_real, FFT_SAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
    FFT.compute(fft_real, fft_imag, FFT_SAMPLES, FFT_FORWARD);
    FFT.complexToMagnitude(fft_real, fft_imag, FFT_SAMPLES);

    // Dominante frequentie vinden
    fft_peak_hz  = FFT.majorPeak(fft_real, FFT_SAMPLES, LSM_SAMPLE_RATE_HZ);
    int peakIdx  = constrain((int)(fft_peak_hz * FFT_SAMPLES / LSM_SAMPLE_RATE_HZ), 0, FFT_SAMPLES / 2 - 1);
    fft_peak_amp = fft_real[peakIdx];
}

void processAudio() {
    if (audioQueue.available() < 2) return;

    // Alleen RMS berekenen - geen FFT
    // RMS is evenredig met v² → bruikbaar voor fasedetectie en snelheidsvalidatie
    int16_t* buf = audioQueue.readBuffer();
    float sum = 0;
    int n = 128; // Teensy audio buffer grootte

    for (int i = 0; i < n; i++) {
        float s = buf[i] / 32768.0;
        sum += s * s;
    }
    audioQueue.freeBuffer();

    audio_rms = sqrt(sum / n);
}

// ============================================================
// VERZENDEN EN LOGGEN
// ============================================================

void sendAndLog() {
    unsigned long now = millis();

    // CSV regel samenstellen
    String csv = String(now) + "," +
                 String(last_temp, 2) + "," +
                 String(last_pressure, 2) + "," +
                 String(last_altitude, 2) + "," +
                 String(last_lat, 6) + "," +
                 String(last_lon, 6) + "," +
                 last_time_utc + "," +
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
                 String(audio_rms, 4);

    // SD kaart schrijven
    if (csvFile) {
        csvFile.println(csv);
        sdBufferLines++;
    }

    // LoRa pakket verzenden (compacte versie)
    // Pakket: temp, press, alt, lat, lon, lacc_xyz, heading, roll, pitch, fft_peak, audio_rms
    String loraPacket = String(last_temp, 1) + "," +
                        String(last_pressure, 1) + "," +
                        String(last_altitude, 1) + "," +
                        String(last_lat, 5) + "," +
                        String(last_lon, 5) + "," +
                        String(last_lacc_x, 2) + "," +
                        String(last_lacc_y, 2) + "," +
                        String(last_lacc_z, 2) + "," +
                        String(last_heading, 1) + "," +
                        String(last_roll, 1) + "," +
                        String(last_pitch, 1) + "," +
                        String(fft_peak_hz, 0) + "," +
                        String(audio_rms, 3);

    int state = radio.transmit(loraPacket);
    if (state != RADIOLIB_ERR_NONE) {
        Serial.print("LoRa fout: ");
        Serial.println(state);
    }

    // Debug output
    Serial.println(csv);
}

void flushSD() {
    if (csvFile && sdBufferLines > 0) {
        csvFile.flush();
        sdBufferLines = 0;
    }
}

// ============================================================
// LANDINGSPROCEDURE
// ============================================================

void landingProcedure() {
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