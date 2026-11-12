#ifndef BIGINT_HPP
#define BIGINT_HPP

#include <iostream>
#include <string>

class bigint
{
	std::string _digits;  // most significant first, "0" for zero, no leading zeros

	static unsigned int	_count(const bigint &n);

public:
	bigint();
	bigint(unsigned int n);
	bigint(const bigint &other);
	bigint	&operator=(const bigint &other);
	~bigint();

	bigint	operator+(const bigint &other) const;
	bigint	&operator+=(const bigint &other);
	bigint	&operator++();
	bigint	operator++(int);

	bigint	operator<<(unsigned int n) const;
	bigint	operator>>(unsigned int n) const;
	bigint	&operator<<=(unsigned int n);
	bigint	&operator>>=(unsigned int n);
	bigint	operator<<(const bigint &n) const;
	bigint	operator>>(const bigint &n) const;
	bigint	&operator<<=(const bigint &n);
	bigint	&operator>>=(const bigint &n);

	bool	operator==(const bigint &other) const;
	bool	operator!=(const bigint &other) const;
	bool	operator<(const bigint &other) const;
	bool	operator<=(const bigint &other) const;
	bool	operator>(const bigint &other) const;
	bool	operator>=(const bigint &other) const;

	const std::string	&str() const;
};

std::ostream	&operator<<(std::ostream &os, const bigint &n);

#endif
