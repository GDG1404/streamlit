#pragma once
namespace imu {
class Quaternion {
public:
    double _w = 1, _x = 0, _y = 0, _z = 0;
    double w() const { return _w; }
    double x() const { return _x; }
    double y() const { return _y; }
    double z() const { return _z; }
};
template <int N> class Vector {
public:
    double v[N] = {};
    double &operator[](int i) { return v[i]; }
    double x() const { return v[0]; }
    double y() const { return v[1]; }
    double z() const { return v[2]; }
};
}
