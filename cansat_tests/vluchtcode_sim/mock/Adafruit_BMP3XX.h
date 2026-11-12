// Model of Adafruit_BMP3XX 2.1.6: performReading() starts a forced conversion
// and reads the data registers AT ONCE, so it returns the previous conversion.
#pragma once
#include "Wire.h"
#define BMP3_OVERSAMPLING_8X 3
#define BMP3_OVERSAMPLING_4X 2
#define BMP3_IIR_FILTER_COEFF_1 1
#define BMP3_IIR_FILTER_COEFF_3 2
#define BMP3_IIR_FILTER_DISABLE 0
#define BMP3_ODR_50_HZ 2
class Adafruit_BMP3XX {
    bool pending = false, have = false;
    uint64_t done_us = 0;
    double pend_p = 0, pend_t = 0, reg_p = 80000 * 0.9, reg_t = 23.0, filt_p = 0;   // junk after reset
    int iir = 0;
    void finish() {
        if (pending && sim.us >= done_us) {
            pending = false;
            if (iir && have && sim.bmp_iir_persist) { double c = (1 << iir) - 1; filt_p = (filt_p * c + pend_p) / (c + 1); }
            else filt_p = pend_p;
            have = true;
            reg_p = filt_p;
            reg_t = pend_t;
        }
    }
public:
    double temperature = 0, pressure = 0;
    bool begin_I2C() {
        Wire.begin();
        sim.i2c(3);
        if (!sim.bmp_present) return false;
        sim.advance(4000);
        for (int i = 0; i < 4; i++) sim.i2c(8);
        return true;
    }
    void setTemperatureOversampling(int) {}
    void setPressureOversampling(int) {}
    void setIIRFilterCoeff(int c) { iir = c; }
    void setOutputDataRate(int) {}
    bool performReading() {
        if (!sim.bmp_present || sim.i2c_bad()) { sim.i2c(3); return false; }
        sim.bmp_reads++;
        for (int i = 0; i < 4; i++) sim.i2c(6);         // settings: read and write back
        sim.i2c(4);                                      // get_op_mode
        finish();
        if (pending) {                                   // still converting: sleep first
            pending = false;
            sim.i2c(4);
            sim.advance(5000);
        }
        sim.i2c(4); sim.i2c(3);                          // write_power_mode: forced
        double t = sim.t();
        double alt = sim.sc->altitude(t);
        pend_p = 101325.0 * pow(1.0 - alt / 44330.0, 5.255) + 100.0 * sim.sc->bmpGlitchHpa(t)
                 + 1.5 * sim.noise();                    // Pa
        pend_t = sim.sc->temperature(t) + 0.01 * sim.noise();
        pending = true;
        done_us = sim.us + 25000;                        // 8x temperature, 4x pressure
        sim.i2c(9);                                      // data registers: the OLD result
        temperature = reg_t;
        pressure = reg_p;
        return true;
    }
    float readAltitude(float sea) { performReading(); return 44330.0 * (1.0 - pow(pressure / 100.0 / sea, 0.1903)); }
};
