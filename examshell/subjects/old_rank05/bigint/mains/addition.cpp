// addition, carries, increments, copies: only what the subject main uses
#include "bigint.hpp"
#include <iostream>

int main()
{
	bigint zero;
	bigint nines(999999999);
	std::cout << "zero = " << zero << std::endl;
	std::cout << "bigint(0) = " << bigint(0) << std::endl;
	std::cout << "nines + 1 = " << nines + 1 << std::endl;
	std::cout << "1 + nines = " << bigint(1) + nines << std::endl;
	std::cout << "zero + zero = " << zero + zero << std::endl;
	std::cout << "4294967295 + 4294967295 = " << bigint(4294967295U) + bigint(4294967295U) << std::endl;

	bigint x(1);
	for (int i = 0; i < 200; i++)
		x = x + x;
	std::cout << "2^200 = " << x << std::endl;
	bigint y(x);
	y += x;
	std::cout << "2^201 = " << y << std::endl;
	std::cout << "x unchanged = " << x << std::endl;

	bigint n(9);
	std::cout << "++9 = " << ++n << std::endl;
	std::cout << "10++ = " << n++ << std::endl;
	std::cout << "now = " << n << std::endl;
	bigint m(99999);
	++(++m);
	std::cout << "++(++99999) = " << m << std::endl;

	bigint chain;
	(chain += 5) += 7;
	std::cout << "(0 += 5) += 7 = " << chain << std::endl;
	chain = chain;
	std::cout << "self-assigned = " << chain << std::endl;
	bigint a(1), b(2), c(3);
	a = b = c;
	std::cout << "a = b = c: " << a << " " << b << " " << c << std::endl;

	const bigint k(123456789);
	std::cout << "const k + k = " << k + k << std::endl;
	return 0;
}
