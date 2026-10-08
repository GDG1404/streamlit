/*
 * CanSat 2027 - Teensy 4.1 - SENSORTEST + FFT + CSV
 * Zelfstandige testsketch — zelfde CSV-formaat als de vluchtcode.
 *
 * Sensoren: BMP390, BNO055, LSM6DSO, GPS PA1616D, SPH0645 (I2S)
 *
 * CSV-kolommen (identiek aan vluchtcode):
 *   millis,temp_C,press_hPa,alt_m,lat,lon,time_utc,
 *   gyro_x,gyro_y,gyro_z,lacc_x,lacc_y,lacc_z,grav_x,grav_y,grav_z,
 *   heading,roll,pitch,qw,qx,qy,qz,fft_peak_hz,fft_peak_amp,audio_rms
 *
 * fft_peak_amp = amplitude van de piek in g (DC verwijderd, venster-gecorrigeerd)
 * audio_rms    = RMS van alle audio sinds de vorige logregel (DC verwijderd)
 */

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_BMP3XX.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_Sensor.h>
#include <utility/imumaths.h>
#include <SparkFunLSM6DSO.h>
#include <Adafruit_GPS.h>
#include <Audio.h>
#include <arduinoFFT.h>

// ---------------- CONSTANTEN ----------------
#define SEA_LEVEL_PRESSURE  1014.0
#define SD_CS               BUILTIN_SDCARD
#define LOG_INTERVAL_MS     1000     // 1 Hz loggen; zet op 100 voor snelle test
#define FFT_SAMPLES         512
#define LSM_SAMPLE_RATE_HZ  416
#define LSM_INTERVAL_US     2404     // 1e6 / 416
#define HAMMING_GAIN        0.54f    // coherente versterking Hamming-venster

// ---------------- OBJECTEN ----------------
Adafruit_BMP3XX bmp;
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
LSM6DSO         lsm;
Adafruit_GPS    GPS(&Serial1);

static uint8_t gpsRxBuf[512];

AudioInputI2S     micInput;
AudioRecordQueue  audioQueue;
AudioConnection   patchCord1(micInput, 0, audioQueue, 0);

ArduinoFFT<float> FFT;
float fft_real[FFT_SAMPLES];
float fft_imag[FFT_SAMPLES];

// Moet identiek blijven aan CSV_COLUMNS in dashboard_scherm1.py
const char CSV_HEADER[] =
    "millis,temp_C,press_hPa,alt_m,"
    "lat,lon,time_utc,"
    "gyro_x,gyro_y,gyro_z,"
    "lacc_x,lacc_y,lacc_z,"
    "grav_x,grav_y,grav_z,"
    "heading,roll,pitch,"
    "qw,qx,qy,qz,"
    "fft_peak_hz,fft_peak_amp,"
    "audio_rms";

File csvFile;
int  sdBufferLines = 0;

// ---------------- STATUS ----------------
bool ok_bmp = false, ok_bno = false, ok_lsm = false, ok_gps = false, ok_sd = false;

// ---------------- LAATSTE WAARDEN ----------------
float last_temp = 10.0, last_pressure = 1000.0, last_altitude = 600.0;
float last_lat = 50.457303, last_lon = 6.221376;
String last_time_utc = "00:00:00";

float last_gyro_x=0, last_gyro_y=0, last_gyro_z=0;
float last_lacc_x=0, last_lacc_y=0, last_lacc_z=0;
float last_grav_x=0, last_grav_y=0, last_grav_z=0;
float last_heading=0, last_roll=0, last_pitch=0;
float last_qw=1, last_qx=0, last_qy=0, last_qz=0;

float fft_peak_hz = 0, fft_peak_amp = 0;
float audio_rms = 0;

// Audio-accumulatie tussen twee logregels
double   audio_sum = 0, audio_sum_sq = 0;
uint32_t audio_count = 0;

// LSM buffer
float lsm_buffer_z[FFT_SAMPLES];
int   lsm_buf_index = 0;
bool  lsm_buf_ready = false;
unsigned long lsmBufStartUs = 0;     // start van huidige buffer
float lsm_measured_fs = LSM_SAMPLE_RATE_HZ;  // werkelijke samplefrequentie

// Timers
unsigned long lastBmpMs=0, lastGpsMs=0, lastBnoMs=0, lastLsmUs=0;
unsigned long lastLogMs=0, lastFlushMs=0, lastHeartbeatMs=0;

// ============================================================
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000);

    pinMode(LED_BUILTIN, OUTPUT);

    Serial.println("\n=== CanSat 2027 — Sensortest + FFT + CSV ===");

    Wire.begin();
    Wire.setClock(400000);

    AudioMemory(60);

    ok_bmp = initBMP390();
    ok_bno = initBNO055();
    ok_lsm = initLSM6DSO();
    ok_gps = initGPS();
    ok_sd  = initSD();

    printStatus();
    audioQueue.begin();

    lastLogMs = millis();
    lastLsmUs = micros();
    lsmBufStartUs = lastLsmUs;
    Serial.println("--- logging gestart ---");
    // Header ook op Serial: een live-capture (CsvLive in het dashboard)
    // slaat alles over tot de regel die met "millis" begint
    Serial.println(CSV_HEADER);
}

// ============================================================
void loop() {
    unsigned long now = millis();

    // GPS continu leeglezen (niet-blokkerend)
    while (Serial1.available()) {
        GPS.read();
        if (GPS.newNMEAreceived()) GPS.parse(GPS.lastNMEA());
    }

    // LSM6DSO @ 416 Hz — vaste tijdbasis (+=) zodat er geen drift ontstaat
    if (ok_lsm && (micros() - lastLsmUs >= LSM_INTERVAL_US)) {
        lastLsmUs += LSM_INTERVAL_US;
        // Na een lange blokkering (BMP/SD) niet proberen in te halen
        if (micros() - lastLsmUs >= LSM_INTERVAL_US) lastLsmUs = micros();
        readLSM6DSO();
    }

    // BMP390 @ 1 Hz (performReading blokkeert ~20-30 ms!)
    if (now - lastBmpMs >= 1000) {
        lastBmpMs = now;
        if (ok_bmp) readBMP390();
    }

    // GPS data ophalen @ 1 Hz
    if (now - lastGpsMs >= 1000) {
        lastGpsMs = now;
        if (ok_gps) readGPS();
    }

    // BNO055 @ 100 Hz
    if (now - lastBnoMs >= 10) {
        lastBnoMs = now;
        if (ok_bno) readBNO055();
    }

    // Audio: alle beschikbare blokken verwerken
    processAudio();

    // FFT zodra buffer vol
    if (lsm_buf_ready) {
        computeFFT();
        lsm_buf_ready = false;
    }

    // Log @ 1 Hz
    if (now - lastLogMs >= LOG_INTERVAL_MS) {
        lastLogMs = now;
        writeCSV();
    }

    // SD flush
    if (now - lastFlushMs >= 500) {
        lastFlushMs = now;
        if (csvFile && sdBufferLines > 0) {
            csvFile.flush();
            sdBufferLines = 0;
        }
    }

    // Heartbeat LED (pin 13) — laat zien dat loop draait
    if (now - lastHeartbeatMs >= 1000) {
        lastHeartbeatMs = now;
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    }
}

// ============================================================
// INITIALISATIE
// ============================================================

bool initBMP390() {
    Serial.print("BMP390 ... ");
    if (bmp.begin_I2C()) {
        bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_8X);
        bmp.setPressureOversampling(BMP3_OVERSAMPLING_4X);
        bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
        bmp.setOutputDataRate(BMP3_ODR_50_HZ);
        // Eerste meting na het instellen is onbetrouwbaar: weggooien
        // (zelfde oplossing als in Drie_sensoren_test)
        bmp.performReading();
        delay(100);
        Serial.println("OK");
        return true;
    }
    Serial.println("FOUT");
    return false;
}

bool initBNO055() {
    Serial.print("BNO055 ... ");
    if (bno.begin()) {
        delay(1000);
        bno.setExtCrystalUse(true);
        // Zelfde modus als in de vlucht: IMU+ (zonder magnetometer).
        // Heading is dus RELATIEF: 0° = de richting bij het opstarten.
        bno.setMode(OPERATION_MODE_IMUPLUS);
        delay(25);
        Serial.println("OK");
        return true;
    }
    Serial.println("FOUT");
    return false;
}

bool initLSM6DSO() {
    Serial.print("LSM6DSO ... ");
    // initialize(): auto-increment + Block Data Update (geen mix van
    // oude en nieuwe bytes bij uitlezen aan 416 Hz), daarna ±16 g
    if (lsm.begin() && lsm.initialize(BASIC_SETTINGS)) {
        lsm.setAccelRange(16);
        lsm.setAccelDataRate(416);
        lsm.setGyroDataRate(416);
        Serial.println("OK");
        return true;
    }
    Serial.println("FOUT");
    return false;
}

bool initGPS() {
    Serial.print("GPS PA1616D ... ");
    GPS.begin(9600);                                     // doet Serial1.begin()
    Serial1.addMemoryForRead(gpsRxBuf, sizeof(gpsRxBuf)); // na begin()
    GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);
    GPS.sendCommand(PGCMD_ANTENNA);
    delay(1000);
    // Controleren of de module echt iets stuurt
    bool gotData = Serial1.available() > 0;
    Serial.println(gotData ? "OK" : "GEEN DATA");
    return gotData;
}

bool initSD() {
    Serial.print("SD kaart ... ");
    if (!SD.begin(SD_CS)) { Serial.println("FOUT"); return false; }

    // Uniek bestand per boot → geen overschrijven
    char fname[32];
    bool found = false;
    for (int i = 0; i < 1000; i++) {
        snprintf(fname, sizeof(fname), "test_%03d.csv", i);
        if (!SD.exists(fname)) { found = true; break; }
    }
    if (!found) { Serial.println("FOUT: geen vrije bestandsnaam"); return false; }

    csvFile = SD.open(fname, FILE_WRITE);
    if (!csvFile) { Serial.println("FOUT bij openen"); return false; }

    csvFile.println(CSV_HEADER);
    csvFile.flush();
    Serial.print("OK → ");
    Serial.println(fname);
    return true;
}

void printStatus() {
    Serial.println("\n--- Sensorstatus ---");
    Serial.print("BMP390 : "); Serial.println(ok_bmp ? "OK" : "FAIL");
    Serial.print("BNO055 : "); Serial.println(ok_bno ? "OK" : "FAIL");
    Serial.print("LSM6DSO: "); Serial.println(ok_lsm ? "OK" : "FAIL");
    Serial.print("GPS    : "); Serial.println(ok_gps ? "OK" : "FAIL");
    Serial.print("SD     : "); Serial.println(ok_sd  ? "OK" : "FAIL");
    Serial.println("--------------------\n");
}

// ============================================================
// SENSOREN
// ============================================================

void readBMP390() {
    if (bmp.performReading()) {
        last_temp     = bmp.temperature;
        last_pressure = bmp.pressure / 100.0F;
        // Hoogte uit DEZE meting berekenen. bmp.readAltitude() start
        // intern een tweede meting (blokkeert de loop opnieuw ~25 ms en
        // hoort bij een ander moment dan last_pressure). Zelfde formule.
        last_altitude = 44330.0f *
            (1.0f - powf(last_pressure / SEA_LEVEL_PRESSURE, 0.1903f));
    }
}

void readGPS() {
    if (GPS.fix) {
        last_lat = GPS.latitudeDegrees;
        last_lon = GPS.longitudeDegrees;
        char buf[12];
        snprintf(buf, sizeof(buf), "%02d:%02d:%02d",
                 GPS.hour, GPS.minute, GPS.seconds);
        last_time_utc = String(buf);
    }
}

void readBNO055() {
    imu::Quaternion q = bno.getQuat();
    last_qw = q.w(); last_qx = q.x(); last_qy = q.y(); last_qz = q.z();

    imu::Vector<3> e = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
    last_heading = e.x(); last_roll = e.y(); last_pitch = e.z();

    imu::Vector<3> l = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    last_lacc_x = l.x(); last_lacc_y = l.y(); last_lacc_z = l.z();

    imu::Vector<3> g = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
    last_gyro_x = g.x(); last_gyro_y = g.y(); last_gyro_z = g.z();

    imu::Vector<3> gr = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
    last_grav_x = gr.x(); last_grav_y = gr.y(); last_grav_z = gr.z();
}

void readLSM6DSO() {
    // Eerst opslaan, dan pas controleren → geen sample verloren
    lsm_buffer_z[lsm_buf_index++] = lsm.readFloatAccelZ();

    if (lsm_buf_index >= FFT_SAMPLES) {
        // Werkelijke samplefrequentie meten (loop kan blokkeren)
        unsigned long t = micros();
        unsigned long dt = t - lsmBufStartUs;
        if (dt > 0) lsm_measured_fs = FFT_SAMPLES * 1e6f / dt;
        lsmBufStartUs = t;

        // Kopiëren vóór de buffer opnieuw gevuld wordt
        for (int i = 0; i < FFT_SAMPLES; i++) fft_real[i] = lsm_buffer_z[i];
        lsm_buf_ready = true;
        lsm_buf_index = 0;
    }
}

void computeFFT() {
    // DC (zwaartekracht ~1 g) verwijderen, anders lekt die naar de laagste bins
    float mean = 0;
    for (int i = 0; i < FFT_SAMPLES; i++) mean += fft_real[i];
    mean /= FFT_SAMPLES;
    for (int i = 0; i < FFT_SAMPLES; i++) {
        fft_real[i] -= mean;
        fft_imag[i] = 0;
    }

    FFT.windowing(fft_real, FFT_SAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
    FFT.compute(fft_real, fft_imag, FFT_SAMPLES, FFT_FORWARD);
    FFT.complexToMagnitude(fft_real, fft_imag, FFT_SAMPLES);

    // Zelf de piek zoeken (bin 0 = DC overslaan) zodat freq en amplitude
    // gegarandeerd bij dezelfde bin horen
    int   peakIdx = 1;
    float peakMag = fft_real[1];
    for (int i = 2; i < FFT_SAMPLES / 2; i++) {
        if (fft_real[i] > peakMag) { peakMag = fft_real[i]; peakIdx = i; }
    }

    // Parabolische interpolatie voor nauwkeurigere frequentie
    float delta = 0;
    if (peakIdx > 1 && peakIdx < FFT_SAMPLES / 2 - 1) {
        float a = fft_real[peakIdx - 1], b = peakMag, c = fft_real[peakIdx + 1];
        float denom = a - 2 * b + c;
        if (denom != 0) delta = 0.5f * (a - c) / denom;
    }

    fft_peak_hz  = (peakIdx + delta) * lsm_measured_fs / FFT_SAMPLES;
    // Omrekenen naar amplitude in g: /(N/2) en corrigeren voor venster
    fft_peak_amp = peakMag / (FFT_SAMPLES / 2.0f) / HAMMING_GAIN;
}

void processAudio() {
    // Alle beschikbare blokken (128 samples, ~2.9 ms) verwerken
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
    // RMS zonder DC-offset (SPH0645 heeft een flinke offset)
    double mean = audio_sum / audio_count;
    double var  = audio_sum_sq / audio_count - mean * mean;
    audio_rms = var > 0 ? sqrt(var) : 0;
    audio_sum = audio_sum_sq = 0;
    audio_count = 0;
}

// ============================================================
// CSV SCHRIJVEN
// ============================================================

void writeCSV() {
    updateAudioRms();

    String csv = String(millis()) + "," +
        String(last_temp, 2)     + "," + String(last_pressure, 2) + "," +
        String(last_altitude, 2) + "," + String(last_lat, 6) + "," +
        String(last_lon, 6)      + "," + last_time_utc + "," +
        String(last_gyro_x, 3)   + "," + String(last_gyro_y, 3) + "," +
        String(last_gyro_z, 3)   + "," +
        String(last_lacc_x, 3)   + "," + String(last_lacc_y, 3) + "," +
        String(last_lacc_z, 3)   + "," +
        String(last_grav_x, 3)   + "," + String(last_grav_y, 3) + "," +
        String(last_grav_z, 3)   + "," +
        String(last_heading, 2)  + "," + String(last_roll, 2) + "," +
        String(last_pitch, 2)    + "," +
        String(last_qw, 4) + "," + String(last_qx, 4) + "," +
        String(last_qy, 4) + "," + String(last_qz, 4) + "," +
        String(fft_peak_hz, 1)   + "," + String(fft_peak_amp, 3) + "," +
        String(audio_rms, 4);

    if (csvFile) {
        csvFile.println(csv);
        sdBufferLines++;
    }
    Serial.println(csv);
}
