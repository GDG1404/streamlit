// Host simulation of the Teensy: a virtual clock, the cost of I2C traffic and
// the outside world (altitude, acceleration, GPS) as a function of time.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <map>
#include <string>
#include <utility>
#include <vector>

struct SimEnd {};

struct Scenario {                       // the world; t = seconds since power-on
    virtual double altitude(double) { return 265.0; }           // m above sea level
    virtual double temperature(double) { return 16.5; }
    virtual void accel(double, double a[3]) { a[0] = 0; a[1] = 0; a[2] = 1; }   // g
    virtual bool gpsFix(double t) { return t > 20; }
    virtual bool gpsSpeaking(double) { return true; }
    virtual void gpsPos(double, double &lat, double &lon) { lat = 50.45831; lon = 6.22192; }
    virtual double bmpGlitchHpa(double) { return 0; }
    virtual double sdFlushUs(double) { return 4000; }
    virtual ~Scenario() {}
};

struct Sim {
    uint64_t us = 0, end_us = 0;
    Scenario *sc = nullptr;
    uint32_t wireClock = 100000;
    uint64_t i2c_us = 0;
    long i2c_tx = 0, lsm_reads = 0, bmp_reads = 0, bno_reads = 0;
    bool bmp_present = true, bno_present = true, lsm_present = true, sd_present = true;
    bool bmp_iir_persist = true;
    bool fast_i2c_broken = false;   // the sensors do not answer above 100 kHz
    bool i2c_bad() const { return fast_i2c_broken && wireClock > 100000; }
    int lsm_fifo_fault = 0;      // 1 = stays empty, 2 = wrong tag, 3 = stops after 50 s, 4 = not there (old chip)
    double lsm_odr = 416.6875 * 1.013;          // the sensor's own clock: 1.3 % fast
    std::vector<std::pair<double, std::string>> packets, serial;
    std::vector<std::pair<double, int>> buzzer;
    std::map<std::string, std::string> files;
    std::vector<std::string> file_order;
    std::map<std::string, double> file_closed_at;
    bool radio_tx = false;
    uint64_t radio_done_us = 0;
    int buzzer_state = 0;
    unsigned rng = 12345;
    double t() const { return us / 1e6; }
    void advance(uint64_t d) {
        us += d;
        if (end_us && us > end_us) throw SimEnd();
    }
    // one I2C transaction with `bytes` bytes on the wire (address bytes included)
    void i2c(int bytes, int extra_us = 0) {
        uint64_t d = (uint64_t)(bytes * 9 + 3) * 1000000ull / wireClock + 12 + extra_us;
        i2c_us += d;
        i2c_tx++;
        advance(d);
    }
    double noise() {                     // uniform in -1..1
        rng = rng * 1664525u + 1013904223u;
        return ((rng >> 8) & 0xFFFF) / 32768.0 - 1.0;
    }
};
extern Sim sim;
