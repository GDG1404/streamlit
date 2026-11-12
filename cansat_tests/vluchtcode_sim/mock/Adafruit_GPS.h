#pragma once
#include "Arduino.h"
#define PMTK_SET_NMEA_OUTPUT_RMCGGA "x"
#define PMTK_SET_NMEA_UPDATE_1HZ "x"
#define PGCMD_ANTENNA "x"
class Adafruit_GPS;
extern Adafruit_GPS *sim_gps;
class Adafruit_GPS {
    double last_update = -1;
public:
    bool fix = false;
    float latitudeDegrees = 0, longitudeDegrees = 0, angle = 0, speed = 0;
    uint8_t hour = 0, minute = 0, seconds = 0;
    uint32_t lastFix = 2000000000UL;
    Adafruit_GPS(HardwareSerial *) { sim_gps = this; }
    bool begin(long) { return true; }
    void sendCommand(const char *) {}
    char read() { return 0; }
    bool newNMEAreceived() { return false; }
    char *lastNMEA() { return nullptr; }
    bool parse(char *) { return true; }
    float secondsSinceFix() { return (millis() - lastFix) / 1000.0f; }
    void simulate() {                         // called by the driver: one sentence pair per second
        double t = sim.t();
        if (t - last_update < 1.0) return;
        last_update = t;
        if (!sim.sc->gpsSpeaking(t)) return;
        fix = sim.sc->gpsFix(t);
        if (fix) {
            double la, lo;
            sim.sc->gpsPos(t, la, lo);
            latitudeDegrees = la; longitudeDegrees = lo;
            int s = 12 * 3600 + (int)t;
            hour = s / 3600 % 24; minute = s / 60 % 60; seconds = s % 60;
            angle = 65.0; speed = 9.7;
            lastFix = millis();
        }
    }
};
