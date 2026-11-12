#include "vect2.hpp"

vect2::vect2() { _c[0] = 0; _c[1] = 0; }
vect2::vect2(int x, int y) { _c[0] = x; _c[1] = y; }
vect2::vect2(const vect2 &other) { _c[0] = other._c[0]; _c[1] = other._c[1]; }

vect2 &vect2::operator=(const vect2 &other)
{
	_c[0] = other._c[0];
	_c[1] = other._c[1];
	return *this;
}

vect2::~vect2() {}

int &vect2::operator[](int i) { return _c[i]; }
const int &vect2::operator[](int i) const { return _c[i]; }

vect2 &vect2::operator++() { ++_c[0]; ++_c[1]; return *this; }
vect2 vect2::operator++(int) { vect2 old(*this); ++*this; return old; }
vect2 &vect2::operator--() { --_c[0]; --_c[1]; return *this; }
vect2 vect2::operator--(int) { vect2 old(*this); --*this; return old; }

vect2 &vect2::operator+=(const vect2 &o) { _c[0] += o._c[0]; _c[1] += o._c[1]; return *this; }
vect2 &vect2::operator-=(const vect2 &o) { _c[0] -= o._c[0]; _c[1] -= o._c[1]; return *this; }
vect2 &vect2::operator*=(int k) { _c[0] *= k; _c[1] *= k; return *this; }

vect2 vect2::operator+(const vect2 &o) const { vect2 r(*this); return r += o; }
vect2 vect2::operator-(const vect2 &o) const { vect2 r(*this); return r -= o; }
vect2 vect2::operator*(int k) const { vect2 r(*this); return r *= k; }
vect2 vect2::operator-() const { return vect2(-_c[0], -_c[1]); }

bool vect2::operator==(const vect2 &o) const { return _c[0] == o._c[0] && _c[1] == o._c[1]; }
bool vect2::operator!=(const vect2 &o) const { return !(*this == o); }

vect2 operator*(int k, const vect2 &v) { return v * k; }

std::ostream &operator<<(std::ostream &os, const vect2 &v)
{
	return os << "{" << v[0] << ", " << v[1] << "}";
}
