#pragma once
#include "Arduino.h"
#define RADIOLIB_ERR_NONE 0
class Module { public: Module(int, int, int) {} };
class RFM95 {
public:
    RFM95(Module *) {}
    int16_t begin(float, float, int, int, int) { sim.advance(30000); return RADIOLIB_ERR_NONE; }
    int16_t setOutputPower(int) { return 0; }
    int16_t startTransmit(String &p) {
        sim.advance(1500);
        sim.packets.push_back({sim.t(), p.s});
        sim.radio_tx = true;
        sim.radio_done_us = sim.us + 20000 + (uint64_t)p.s.size() * 2100;   // ~0.29 s for 130 bytes (SF7)
        return 0;
    }
    int16_t transmit(String &p) {
        startTransmit(p);
        sim.advance(sim.radio_done_us - sim.us);
        return finishTransmit();
    }
    int16_t finishTransmit() { sim.advance(900); sim.radio_tx = false; return 0; }
};
