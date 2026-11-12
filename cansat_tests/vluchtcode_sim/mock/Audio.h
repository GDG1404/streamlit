#pragma once
#include "Arduino.h"
#define AUDIO_BLOCK_SAMPLES 128
inline void AudioMemory(int) {}
class AudioStream {};
class AudioInputI2S : public AudioStream {};
class AudioRecordQueue : public AudioStream {
    bool on = false;
    uint64_t last_us = 0;
    int16_t buf[AUDIO_BLOCK_SAMPLES];
public:
    void begin() { on = true; last_us = sim.us; }
    void end() { on = false; }
    int available() { return on ? (int)std::min<uint64_t>(60, (sim.us - last_us) / 2902) : 0; }
    int16_t *readBuffer() {                      // a 1 kHz tone, RMS 0.02, with a DC offset
        for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
            double t = (last_us + i * 22.68) / 1e6;
            buf[i] = (int16_t)(32768 * (0.05 + 0.02 * 1.41421356 * sin(2 * M_PI * 1000 * t)));
        }
        return buf;
    }
    void freeBuffer() { last_us += 2902; }
};
class AudioConnection { public: AudioConnection(AudioStream &, int, AudioStream &, int) {} };
