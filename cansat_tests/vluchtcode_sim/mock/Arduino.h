#pragma once
#include "sim.h"
#include <algorithm>
#include <string>

typedef uint8_t byte;
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define BUILTIN_SDCARD 254
#define F(x) x

inline unsigned long millis() { return (unsigned long)(uint32_t)(sim.us / 1000); }
inline unsigned long micros() { return (unsigned long)(uint32_t)(sim.us); }
inline void delay(unsigned long ms) { sim.advance((uint64_t)ms * 1000); }
inline void delayMicroseconds(unsigned long us) { sim.advance(us); }
inline void pinMode(int, int) {}
#define SIM_BUZZER_PIN 14
#define SIM_DIO0_PIN 2
inline void digitalWrite(int pin, int v) {
    if (pin == SIM_BUZZER_PIN && v != sim.buzzer_state) {
        sim.buzzer_state = v;
        sim.buzzer.push_back({sim.t(), v});
    }
}
inline int digitalRead(int pin) {
    if (pin == SIM_DIO0_PIN) return sim.radio_tx && sim.us >= sim.radio_done_us;
    return 0;
}

class String {
public:
    std::string s;
    String() {}
    String(const char *c) : s(c ? c : "") {}
    String(const std::string &x) : s(x) {}
    String(char c) : s(1, c) {}
    String(int v) : s(std::to_string(v)) {}
    String(unsigned int v) : s(std::to_string(v)) {}
    String(long v) : s(std::to_string(v)) {}
    String(unsigned long v) : s(std::to_string(v)) {}
    String(float v, int dec = 2) { char b[64]; snprintf(b, sizeof b, "%.*f", dec, (double)v); s = b; }
    String(double v, int dec = 2) { char b[64]; snprintf(b, sizeof b, "%.*f", dec, v); s = b; }
    String operator+(const String &o) const { return String(s + o.s); }
    String &operator+=(const String &o) { s += o.s; return *this; }
    bool operator==(const String &o) const { return s == o.s; }
    const char *c_str() const { return s.c_str(); }
    unsigned int length() const { return s.size(); }
};
inline String operator+(const char *a, const String &b) { return String(std::string(a) + b.s); }

class SimSerial {
    std::string line;
public:
    void begin(long) {}
    operator bool() const { return true; }
    void print(const char *c) { line += c; }
    void print(const String &x) { line += x.s; }
    void print(char c) { line += c; }
    void print(int v) { line += std::to_string(v); }
    void print(unsigned int v) { line += std::to_string(v); }
    void print(long v) { line += std::to_string(v); }
    void print(unsigned long v) { line += std::to_string(v); }
    void print(double v, int dec = 2) { line += String(v, dec).s; }
    void println() { sim.serial.push_back({sim.t(), line}); line.clear(); sim.advance(25); }
    template <class T> void println(const T &x) { print(x); println(); }
    void println(double v, int dec) { print(v, dec); println(); }
};
extern SimSerial Serial;

class HardwareSerial {
public:
    void begin(long) {}
    int available() { return 0; }
    int read() { return -1; }
    void addMemoryForRead(void *, size_t) {}
};
extern HardwareSerial Serial1;

// like Arduino: abs() works on floats too
#undef abs
#define abs(x) ({ __typeof__(x) _x = (x); (_x > 0) ? _x : -_x; })
