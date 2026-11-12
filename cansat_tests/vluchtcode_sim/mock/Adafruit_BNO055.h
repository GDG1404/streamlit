#pragma once
#include "Wire.h"
#include "utility/imumaths.h"
#define OPERATION_MODE_IMUPLUS 8
#define OPERATION_MODE_NDOF 12
class Adafruit_BNO055 {
public:
    enum adafruit_vector_type_t { VECTOR_EULER, VECTOR_LINEARACCEL, VECTOR_GYROSCOPE, VECTOR_GRAVITY };
    typedef struct { uint8_t accel_rev, mag_rev, gyro_rev; uint16_t sw_rev; uint8_t bl_rev; } adafruit_bno055_rev_info_t;
    Adafruit_BNO055(int, uint8_t) {}
    void getRevInfo(adafruit_bno055_rev_info_t *i) {
        for (int k = 0; k < 5; k++) sim.i2c(4);
        bool ok = sim.bno_present && !sim.i2c_bad();
        i->accel_rev = ok ? 0xFB : 0; i->mag_rev = ok ? 0x32 : 0; i->gyro_rev = ok ? 0x0F : 0; i->sw_rev = 0; i->bl_rev = 0;
    }
    bool begin(int = OPERATION_MODE_NDOF) {
        Wire.begin();
        sim.i2c(3);
        if (!sim.bno_present) return false;
        sim.advance(700000);
        return true;
    }
    void setExtCrystalUse(bool) { sim.advance(40000); }
    void setMode(int) { sim.advance(30000); }
    imu::Quaternion getQuat() { sim.bno_reads++; sim.i2c(11, 150); return imu::Quaternion(); }   // + clock stretching
    imu::Vector<3> getVector(adafruit_vector_type_t type) {
        sim.i2c(9, 150);
        imu::Vector<3> v;
        double a[3];
        sim.sc->accel(sim.t(), a);
        if (type == VECTOR_GRAVITY) { v[2] = 9.81; }
        if (type == VECTOR_LINEARACCEL) {
            for (int i = 0; i < 3; i++) {
                double g = a[i] - (i == 2 ? 1.0 : 0.0);
                g = std::max(-4.0, std::min(4.0, g));     // fusion mode: +-4 g
                v[i] = g * 9.81;
            }
        }
        return v;
    }
};
