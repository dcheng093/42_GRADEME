#include "bigint.hpp"

bigint::bigint() : _digits("0") {}

bigint::bigint(unsigned int n) : _digits()
{
	if (n == 0)
		_digits = "0";
	while (n)
	{
		_digits.insert(_digits.begin(), static_cast<char>('0' + n % 10));
		n /= 10;
	}
}

bigint::bigint(const bigint &other) : _digits(other._digits) {}

bigint &bigint::operator=(const bigint &other)
{
	if (this != &other)
		_digits = other._digits;
	return *this;
}

bigint::~bigint() {}

bigint bigint::operator+(const bigint &other) const
{
	bigint result(*this);
	result += other;
	return result;
}

bigint &bigint::operator+=(const bigint &other)
{
	std::string	sum;
	int			i = static_cast<int>(_digits.size()) - 1;
	int			j = static_cast<int>(other._digits.size()) - 1;
	int			carry = 0;

	while (i >= 0 || j >= 0 || carry)
	{
		int d = carry;
		if (i >= 0)
			d += _digits[i--] - '0';
		if (j >= 0)
			d += other._digits[j--] - '0';
		sum.insert(sum.begin(), static_cast<char>('0' + d % 10));
		carry = d / 10;
	}
	_digits = sum;
	return *this;
}

bigint &bigint::operator++()
{
	*this += bigint(1);
	return *this;
}

bigint bigint::operator++(int)
{
	bigint old(*this);
	*this += bigint(1);
	return old;
}

bigint bigint::operator<<(unsigned int n) const
{
	bigint result(*this);
	result <<= n;
	return result;
}

bigint bigint::operator>>(unsigned int n) const
{
	bigint result(*this);
	result >>= n;
	return result;
}

bigint &bigint::operator<<=(unsigned int n)
{
	if (_digits != "0")
		_digits.append(n, '0');
	return *this;
}

bigint &bigint::operator>>=(unsigned int n)
{
	if (n >= _digits.size())
		_digits = "0";
	else
		_digits.erase(_digits.size() - n);
	return *this;
}

// a shift amount too big for an unsigned int saturates
unsigned int bigint::_count(const bigint &n)
{
	unsigned long	value = 0;

	for (size_t i = 0; i < n._digits.size(); i++)
	{
		value = value * 10 + (n._digits[i] - '0');
		if (value > 4000000000UL)
			return 4000000000U;
	}
	return static_cast<unsigned int>(value);
}

bigint bigint::operator<<(const bigint &n) const { return *this << _count(n); }
bigint bigint::operator>>(const bigint &n) const { return *this >> _count(n); }
bigint &bigint::operator<<=(const bigint &n) { return *this <<= _count(n); }
bigint &bigint::operator>>=(const bigint &n) { return *this >>= _count(n); }

bool bigint::operator==(const bigint &other) const { return _digits == other._digits; }
bool bigint::operator!=(const bigint &other) const { return !(*this == other); }

bool bigint::operator<(const bigint &other) const
{
	if (_digits.size() != other._digits.size())
		return _digits.size() < other._digits.size();
	return _digits < other._digits;
}

bool bigint::operator<=(const bigint &other) const { return !(other < *this); }
bool bigint::operator>(const bigint &other) const { return other < *this; }
bool bigint::operator>=(const bigint &other) const { return !(*this < other); }

const std::string &bigint::str() const { return _digits; }

std::ostream &operator<<(std::ostream &os, const bigint &n)
{
	return os << n.str();
}
