// digit shifts and comparisons
#include "bigint.hpp"
#include <iostream>

static void compare(const bigint &x, const bigint &y)
{
	std::cout << x << " vs " << y << ": "
		<< (x < y) << (x <= y) << (x > y) << (x >= y) << (x == y) << (x != y) << std::endl;
}

int main()
{
	const bigint a(42);
	std::cout << "42 << 3 = " << (a << 3) << std::endl;
	std::cout << "42 << 0 = " << (a << 0) << std::endl;
	std::cout << "1337 >> 2 = " << (bigint(1337) >> 2) << std::endl;
	std::cout << "1337 >> 4 = " << (bigint(1337) >> 4) << std::endl;
	std::cout << "1337 >> 10 = " << (bigint(1337) >> 10) << std::endl;
	std::cout << "0 << 5 = " << (bigint() << 5) << std::endl;
	std::cout << "0 >> 5 = " << (bigint() >> 5) << std::endl;

	bigint d(7);
	d <<= 30;
	std::cout << "7 <<= 30: " << d << std::endl;
	d >>= (const bigint)29;
	std::cout << ">>= 29: " << d << std::endl;
	d >>= (const bigint)5;
	std::cout << ">>= 5: " << d << std::endl;
	bigint big(1);
	big <<= 50;
	std::cout << "10^50 + 1 = " << big + 1 << std::endl;
	std::cout << "(10^50 << 10) >> 10 == 10^50: " << (((big << 10) >> 10) == big) << std::endl;

	compare(bigint(41), bigint(42));
	compare(bigint(42), bigint(42));
	compare(bigint(100), bigint(99));
	compare(bigint(9), bigint(10));
	compare(bigint(), bigint(0));
	compare(big, big + 1);
	compare(big << 1, big);
	compare(bigint(1000), bigint(999));
	return 0;
}
