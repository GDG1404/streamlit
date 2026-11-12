#pragma once
#include "Arduino.h"
#define FILE_WRITE 1
class File {
public:
    std::string name;
    bool is_open = false;
    operator bool() const { return is_open; }
    void println(const String &x) { if (is_open) { sim.files[name] += x.s + "\r\n"; sim.advance(60); } }
    void println(const char *x) { println(String(x)); }
    void print(const String &x) { if (is_open) sim.files[name] += x.s; }
    void flush() { if (is_open) sim.advance((uint64_t)sim.sc->sdFlushUs(sim.t())); }
    void close() { if (is_open) { is_open = false; sim.file_closed_at[name] = sim.t(); } }
};
class SDClass {
public:
    bool begin(int) { sim.advance(20000); return sim.sd_present; }
    bool exists(const char *n) { return sim.files.count(n) > 0; }
    File open(const char *n, int) {
        File f;
        f.name = n;
        f.is_open = sim.sd_present;
        if (f.is_open && !sim.files.count(n)) { sim.files[n] = ""; sim.file_order.push_back(n); }
        return f;
    }
};
extern SDClass SD;
