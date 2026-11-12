// every operator again, with negatives, zero and chaining
#include "vect2.hpp"
#include <iostream>

int main()
{
	vect2 a(-3, 7);
	const vect2 b(2, -5);
	std::cout << "a + b = " << a + b << std::endl;
	std::cout << "a - b = " << a - b << std::endl;
	std::cout << "b - a = " << b - a << std::endl;
	std::cout << "a * -2 = " << a * -2 << std::endl;
	std::cout << "-2 * a = " << -2 * a << std::endl;
	std::cout << "b * 0 = " << b * 0 << std::endl;
	std::cout << "-b = " << -b << std::endl;
	std::cout << "--b (as -(-b)) = " << -(-b) << std::endl;
	std::cout << "vect2(2,2) * 2 == vect2(4,4): " << (vect2(2, 2) * 2 == vect2(4, 4)) << std::endl;

	vect2 c(a);
	c += b;
	std::cout << "c += b: " << c << "  a unchanged: " << a << std::endl;
	(c -= b) -= b;
	std::cout << "(c -= b) -= b: " << c << std::endl;
	(c *= 3) *= -1;
	std::cout << "(c *= 3) *= -1: " << c << std::endl;

	vect2 d;
	std::cout << "d++ = " << d++ << ", then " << d << std::endl;
	std::cout << "++d = " << ++d << std::endl;
	std::cout << "d-- = " << d-- << ", then " << d << std::endl;
	std::cout << "--d = " << --d << std::endl;
	++++d;
	std::cout << "++(++d) = " << d << std::endl;

	vect2 e;
	e[0] = 42;
	e[1] = -42;
	std::cout << "e = " << e << " e[0] = " << e[0] << " b[1] = " << b[1] << std::endl;
	vect2 f;
	f = e;
	f[0] = 0;
	std::cout << "copy is separate: e = " << e << " f = " << f << std::endl;
	vect2 &same_f = f;  // via a reference: clang warns on x = x
	f = same_f;
	std::cout << "self-assigned: " << f << std::endl;
	std::cout << "e == e: " << (e == e) << "  e != e: " << (e != e) << std::endl;
	std::cout << "e == f: " << (e == f) << "  e != f: " << (e != f) << std::endl;
	std::cout << "{0, 1} == {1, 0}: " << (vect2(0, 1) == vect2(1, 0)) << std::endl;
	return 0;
}
