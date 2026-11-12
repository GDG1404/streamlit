// The REAL arduinoFFT, with the time it takes on the Teensy added.
#pragma once
#include "Arduino.h"
#undef abs
#define ArduinoFFT ArduinoFFT_real
#include "arduinoFFT_src/arduinoFFT.h"      // the real library (see build.py)
#undef ArduinoFFT
#undef abs
#define abs(x) ({ __typeof__(x) _x = (x); (_x > 0) ? _x : -_x; })
template <class T> class ArduinoFFT {
    ArduinoFFT_real<T> r;
public:
    void windowing(T *d, uint_fast16_t n, FFTWindow w, FFTDirection dir) { sim.advance(150); r.windowing(d, n, w, dir); }
    void compute(T *re, T *im, uint_fast16_t n, FFTDirection dir) { sim.advance(400); r.compute(re, im, n, dir); }
    void complexToMagnitude(T *re, T *im, uint_fast16_t n) { sim.advance(60); r.complexToMagnitude(re, im, n); }
};
