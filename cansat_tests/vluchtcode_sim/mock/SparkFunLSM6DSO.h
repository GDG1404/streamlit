// Model of the SparkFun LSM6DSO library: every readFloatAccel?() is two
// transactions (the value, then the range register in calcAccel()).
#pragma once
#include "Wire.h"
#define BASIC_SETTINGS 0
typedef int status_t;
#define IMU_SUCCESS 0
#define IMU_HW_ERROR 1
enum { FIFO_CTRL1 = 0x07, FIFO_CTRL2 = 0x08, FIFO_CTRL3 = 0x09, FIFO_CTRL4 = 0x0A,
       OUTX_L_A = 0x28, FIFO_STATUS1 = 0x3A, FIFO_DATA_OUT_TAG = 0x78 };
enum { FIFO_MODE_DISABLED = 0x00, FIFO_MODE_CONTINUOUS = 0x06 };
enum { FIFO_BDR_ACC_417Hz = 0x06 };
enum { GYROSCOPE_DATA = 0x01, ACCELEROMETER_DATA };
class LSM6DSO {
    int range = 8;
    // FIFO: the sensor stores every sample of its own clock (up to 512)
    bool fifo_on = false, fifo_ovr = false;
    uint8_t bdr = 0;
    double fifo_t0 = 0;
    long fifo_read = 0;
    long fifoMade() {
        if (!fifo_on || (bdr & 0x0F) != FIFO_BDR_ACC_417Hz || sim.lsm_fifo_fault == 1) return 0;
        double t = sim.t();
        if (sim.lsm_fifo_fault == 3 && t > 50) t = 50;                // stops during the measurement
        long made = (long)floor((t - fifo_t0) * sim.lsm_odr);
        if (made - fifo_read > 512) { fifo_read = made - 512; fifo_ovr = true; }
        return made;
    }
    int16_t raw(int axis, double at = -1) {
        double tick = at >= 0 ? at : floor(sim.t() * sim.lsm_odr) / sim.lsm_odr;     // the sensor's last sample
        double a[3];
        sim.sc->accel(tick, a);
        double g = a[axis] + 0.0006 * sim.noise();
        double lsb = (range == 16) ? 0.000488 : 0.000244;
        double r = round(g / lsb);
        return (int16_t)std::max(-32768.0, std::min(32767.0, r));
    }
public:
    bool begin() { sim.i2c(2); sim.i2c(2); return sim.lsm_present; }
    bool initialize(int) { for (int i = 0; i < 6; i++) sim.i2c(3); return true; }
    bool setAccelRange(int r) { range = r; sim.i2c(3); return true; }
    bool setAccelDataRate(int) { sim.i2c(3); return true; }
    bool setGyroDataRate(int) { sim.i2c(3); return true; }
    status_t writeRegister(uint8_t address, uint8_t v) {
        sim.i2c(3);
        if (!sim.lsm_present) return IMU_HW_ERROR;
        if (address == FIFO_CTRL3) bdr = v;
        if (address == FIFO_CTRL4) {
            bool on = (v & 0x07) == FIFO_MODE_CONTINUOUS;
            if (on && !fifo_on) { fifo_t0 = sim.t(); fifo_read = 0; fifo_ovr = false; }
            fifo_on = on;
        }
        return IMU_SUCCESS;
    }
    float calcAccel(int16_t v) {
        sim.i2c(2); sim.i2c(2);                                       // reads CTRL1_XL every time
        return v * ((range == 16) ? 0.000488f : 0.000244f);
    }
    float readFloatAccelX() { sim.lsm_reads++; sim.i2c(5); return calcAccel(raw(0)); }
    float readFloatAccelY() { sim.i2c(5); return calcAccel(raw(1)); }
    float readFloatAccelZ() { sim.i2c(5); return calcAccel(raw(2)); }
    status_t readMultipleRegisters(uint8_t *out, uint8_t address, uint8_t n) {
        if (!sim.lsm_present || sim.i2c_bad()) { sim.i2c(2); return IMU_HW_ERROR; }
        sim.i2c(3 + n);
        if (address == FIFO_STATUS1 && n == 2) {
            long c = fifoMade() - fifo_read;
            out[0] = c & 0xFF;
            out[1] = ((c >> 8) & 0x03) | (fifo_ovr ? 0x48 : 0);
            fifo_ovr = false;
        } else if (address == FIFO_DATA_OUT_TAG && n == 7) {
            long made = fifoMade();
            if (fifo_read >= made) { memset(out, 0, 7); return IMU_SUCCESS; }
            double at = fifo_t0 + (fifo_read + 1) / sim.lsm_odr;
            fifo_read++;
            sim.lsm_reads++;
            out[0] = (sim.lsm_fifo_fault == 2 ? 0x03 : ACCELEROMETER_DATA) << 3;
            for (int i = 0; i < 3; i++) { int16_t r = raw(i, at); out[1 + 2 * i] = r & 0xFF; out[2 + 2 * i] = (r >> 8) & 0xFF; }
        } else if (address == OUTX_L_A && n == 6) {
            sim.lsm_reads++;
            for (int i = 0; i < 3; i++) { int16_t r = raw(i); out[2 * i] = r & 0xFF; out[2 * i + 1] = (r >> 8) & 0xFF; }
        } else {
            memset(out, 0, n);
        }
        return IMU_SUCCESS;
    }
};
