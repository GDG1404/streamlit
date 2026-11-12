// Runs a flight sketch (setup/loop) in the simulated world and writes what it
// produced: the SD files, the radio packets, the serial lines, the buzzer.
//   sim <scenario> <out dir> <seconds>
#include "Arduino.h"
#include "Wire.h"
#include "SD.h"
#include "Adafruit_GPS.h"
#include <sys/stat.h>

Sim sim;
SimSerial Serial;
HardwareSerial Serial1;
TwoWire Wire;
SDClass SD;
Adafruit_GPS *sim_gps = nullptr;
void setup();
void loop();

struct Tone { int axis; double f, amp, t0, t1; };

struct World : Scenario {
    std::vector<double> launches;          // times of launch (s since power-on)
    double H = 955, v_desc = 8.5, ground = 265;
    std::vector<Tone> tones;
    double fix_from = 20, fix_lost_from = 1e18, fix_back = 1e18;
    double gps_silent_from = 1e18;
    double glitch_period = 0, glitch_len = 0, glitch_hpa = 0, glitch_from = 40;
    double lift_at = 1e18, lift_m = 0, lift_s = 4;      // carried up (no flight)
    int stall_every = 0; long flushes = 0;
    static constexpr double A_BOOST = 150.0, T_BOOST = 1.5;
    double h1() const { return 0.5 * A_BOOST * T_BOOST * T_BOOST; }
    double v1() const { return A_BOOST * T_BOOST; }
    double dcoast() const { return v1() * v1() / (2 * (H - h1())); }
    double t_apogee() const { return T_BOOST + v1() / dcoast(); }
    double t_land() const { return t_apogee() + H / v_desc; }
    double flightH(double tau) const {
        if (tau <= 0) return 0;
        if (tau < T_BOOST) return 0.5 * A_BOOST * tau * tau;
        if (tau < t_apogee()) { double u = tau - T_BOOST; return h1() + v1() * u - 0.5 * dcoast() * u * u; }
        return std::max(0.0, H - v_desc * (tau - t_apogee()));
    }
    double altitude(double t) override {
        double h = ground;
        for (double tl : launches) h += flightH(t - tl);
        if (t > lift_at) h += lift_m * std::min(1.0, (t - lift_at) / lift_s);
        return h;
    }
    double temperature(double t) override { return 16.5 - 0.0065 * (altitude(t) - ground); }
    void accel(double t, double a[3]) override {
        a[0] = 0; a[1] = 0; a[2] = 1;
        for (double tl : launches) {
            double tau = t - tl;
            if (tau < 0 || tau > t_land() + 600) continue;
            if (tau < T_BOOST) {                                    // motor
                a[2] = 1 + A_BOOST / 9.81;
                a[2] += 0.30 * sin(2 * M_PI * 140 * t);
                a[0] += 0.20 * sin(2 * M_PI * 85 * t);
            } else if (tau < t_apogee()) {
                a[2] = 1 - dcoast() / 9.81;
                a[2] += 0.10 * sin(2 * M_PI * 140 * t);
            } else if (tau < t_apogee() + 0.03) {
                a[2] = 9.0;                                         // parachute opens
            } else if (tau < t_land()) {
                a[2] = 1 + 0.02 * sin(2 * M_PI * 6 * t);
                a[0] = 0.05 * sin(2 * M_PI * 1.5 * t);              // swinging
            } else if (tau < t_land() + 0.02) {
                a[2] = 22.0;                                        // touchdown
            } else {
                a[0] = 1; a[2] = 0;                                 // on its side
            }
        }
        for (auto &k : tones)
            if (t >= k.t0 && t < k.t1) a[k.axis] += k.amp * sin(2 * M_PI * k.f * t);
    }
    bool gpsFix(double t) override { return t > fix_from && !(t >= fix_lost_from && t < fix_back); }
    bool gpsSpeaking(double t) override { return t < gps_silent_from; }
    void gpsPos(double t, double &lat, double &lon) override {
        double d = 0;
        for (double tl : launches) { double tau = t - tl; if (tau > t_apogee()) d += 4.2 * (std::min(tau, t_land()) - t_apogee()); }
        lat = 50.45831 + d * 0.9063 * 0.42 / 111320.0;
        lon = 6.22192 + d * 0.9063 / (111320.0 * 0.6366);
    }
    double bmpGlitchHpa(double t) override {
        if (glitch_period <= 0 || t < glitch_from) return 0;
        return fmod(t - glitch_from, glitch_period) < glitch_len ? glitch_hpa : 0;
    }
    double sdFlushUs(double) override {
        flushes++;
        return (stall_every && flushes % stall_every == 0) ? 60000 : 4000;
    }
};

int main(int argc, char **argv) {
    std::string name = argc > 1 ? argv[1] : "tone";
    std::string out = argc > 2 ? argv[2] : ".";
    double seconds = argc > 3 ? atof(argv[3]) : 40;
    World w;
    if (name == "tone" || name == "sdstall") {
        w.tones.push_back({2, 37.0, 0.5, 8, 1e18});
        w.tones.push_back({0, 90.0, 0.2, 8, 1e18});
        if (name == "sdstall") w.stall_every = 7;
    } else if (name == "sweep") {                    // 20 s per frequency, on Z
        double fs[] = {5, 12, 25, 37, 60, 85, 110, 140, 170, 195};
        for (int i = 0; i < 10; i++) w.tones.push_back({2, fs[i], 0.5, 10.0 + 20 * i, 30.0 + 20 * i});
    } else if (name == "flight") {
        w.launches.push_back(90);
    } else if (name == "spike") {                    // one bad conversion every 7.3 s
        w.glitch_period = 7.3; w.glitch_len = 0.04; w.glitch_hpa = -25;
    } else if (name == "spike1s") {                  // a pressure dip of 1.2 s every 7.3 s
        w.glitch_period = 7.3; w.glitch_len = 1.2; w.glitch_hpa = -25;
    } else if (name == "false_then_real") {          // carried up 60 m, real flight much later
        w.lift_at = 60; w.lift_m = 60; w.lift_s = 4;
        w.launches.push_back(900);
    } else if (name == "slow") {
        w.launches.push_back(90); w.v_desc = 2.2;
    } else if (name == "gpsloss") {
        w.launches.push_back(90); w.fix_lost_from = 91;
    } else if (name == "gpsback") {
        w.launches.push_back(90); w.fix_lost_from = 91; w.fix_back = 130;
    } else if (name == "gpssilent") {
        w.launches.push_back(90); w.gps_silent_from = 91;
    } else if (name == "nobmp") {
        sim.bmp_present = false; w.launches.push_back(90);
    } else if (name == "nolsm") {
        sim.lsm_present = false; w.launches.push_back(90);
    } else if (name == "nosd") {
        sim.sd_present = false; w.launches.push_back(90);
    } else if (name == "nofilter") {                 // if the BMP390 filter does not persist
        sim.bmp_iir_persist = false; w.launches.push_back(90);
    } else if (name == "fifo_empty" || name == "fifo_tag" || name == "fifo_stops") {
        sim.lsm_fifo_fault = name == "fifo_empty" ? 1 : name == "fifo_tag" ? 2 : 3;
        w.tones.push_back({2, 37.0, 0.5, 8, 1e18});
        w.tones.push_back({0, 90.0, 0.2, 8, 1e18});
    } else if (name == "slowbus" || name == "slowbus_nofifo") {      // only 100 kHz works
        sim.fast_i2c_broken = true;
        if (name == "slowbus_nofifo") sim.lsm_fifo_fault = 1;
        w.tones.push_back({2, 37.0, 0.5, 8, 1e18});
        w.tones.push_back({0, 90.0, 0.2, 8, 1e18});
    } else if (name != "rest") {
        fprintf(stderr, "unknown scenario %s\n", name.c_str());
        return 2;
    }
    sim.sc = &w;
    sim.end_us = (uint64_t)(seconds * 1e6);
    long passes = 0;
    long reads_a = 0, reads_b = 0;
    uint64_t i2c_a = 0, i2c_b = 0;
    try {
        setup();
        for (;;) {
            if (sim_gps) sim_gps->simulate();
            double t0 = sim.t();
            loop();
            passes++;
            sim.advance(12);                                   // the rest of a loop pass
            if (t0 < 20 && sim.t() >= 20) { reads_a = sim.lsm_reads; i2c_a = sim.i2c_us; }
            if (t0 < 30 && sim.t() >= 30) { reads_b = sim.lsm_reads; i2c_b = sim.i2c_us; }
        }
    } catch (SimEnd &) {}
    mkdir(out.c_str(), 0755);
    for (auto &f : sim.files) {
        FILE *fh = fopen((out + "/sd_" + f.first).c_str(), "w");
        fwrite(f.second.data(), 1, f.second.size(), fh);
        fclose(fh);
    }
    FILE *fh = fopen((out + "/packets.csv").c_str(), "w");
    for (auto &p : sim.packets) fprintf(fh, "%.3f;%s\n", p.first, p.second.c_str());
    fclose(fh);
    fh = fopen((out + "/serial.txt").c_str(), "w");
    for (auto &p : sim.serial) fprintf(fh, "%.3f;%s\n", p.first, p.second.c_str());
    fclose(fh);
    fh = fopen((out + "/buzzer.txt").c_str(), "w");
    for (auto &p : sim.buzzer) fprintf(fh, "%.3f;%d\n", p.first, p.second);
    fclose(fh);
    fh = fopen((out + "/stats.txt").c_str(), "w");
    fprintf(fh, "scenario=%s\nseconds=%.1f\nwire_clock=%u\n", name.c_str(), seconds, sim.wireClock);
    fprintf(fh, "lsm_reads_per_s=%.1f\ni2c_share=%.3f\n", (reads_b - reads_a) / 10.0, (i2c_b - i2c_a) / 1e7);
    fprintf(fh, "bmp_reads=%ld\nbno_reads=%ld\npackets=%zu\nfiles=", sim.bmp_reads, sim.bno_reads, sim.packets.size());
    for (auto &n : sim.file_order)
        fprintf(fh, "%s(%s) ", n.c_str(), sim.file_closed_at.count(n) ? ("closed@" + std::to_string((int)sim.file_closed_at[n])).c_str() : "open");
    fprintf(fh, "\nt_launch_world=%s\nt_apogee=%.2f\nt_land=%.2f\n",
            w.launches.empty() ? "none" : std::to_string(w.launches[0]).c_str(),
            w.launches.empty() ? 0 : w.launches[0] + w.t_apogee(), w.launches.empty() ? 0 : w.launches[0] + w.t_land());
    fclose(fh);
    return 0;
}
