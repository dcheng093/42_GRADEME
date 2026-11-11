#ifndef VECT2_HPP
#define VECT2_HPP

#include <iostream>

class vect2
{
	int	_c[2];

public:
	vect2();
	vect2(int x, int y);
	vect2(const vect2 &other);
	vect2	&operator=(const vect2 &other);
	~vect2();

	int			&operator[](int i);
	const int	&operator[](int i) const;

	vect2	&operator++();
	vect2	operator++(int);
	vect2	&operator--();
	vect2	operator--(int);

	vect2	&operator+=(const vect2 &other);
	vect2	&operator-=(const vect2 &other);
	vect2	&operator*=(int k);

	vect2	operator+(const vect2 &other) const;
	vect2	operator-(const vect2 &other) const;
	vect2	operator*(int k) const;
	vect2	operator-() const;

	bool	operator==(const vect2 &other) const;
	bool	operator!=(const vect2 &other) const;
};

vect2			operator*(int k, const vect2 &v);
std::ostream	&operator<<(std::ostream &os, const vect2 &v);

#endif
