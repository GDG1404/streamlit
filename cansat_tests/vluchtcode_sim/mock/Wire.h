#pragma once
#include "Arduino.h"
class TwoWire {
public:
    void begin() { sim.wireClock = 100000; }        // Teensy 4: begin() resets the speed
    void setClock(uint32_t f) { sim.wireClock = f; }
};
extern TwoWire Wire;
