#include "array_bag.hpp"

#include <iostream>
#include <cstddef>

array_bag::array_bag() : data(NULL), size(0) {}

array_bag::array_bag(const array_bag &src) : bag(), data(NULL), size(0)
{
	*this = src;
}

array_bag &array_bag::operator=(const array_bag &src)
{
	if (this != &src)
	{
		delete[] data;
		data = NULL;
		size = src.size;
		if (size)
		{
			data = new int[size];
			for (int i = 0; i < size; i++)
				data[i] = src.data[i];
		}
	}
	return *this;
}

array_bag::~array_bag()
{
	delete[] data;
}

void array_bag::insert(int item)
{
	int *bigger = new int[size + 1];
	for (int i = 0; i < size; i++)
		bigger[i] = data[i];
	bigger[size] = item;
	delete[] data;
	data = bigger;
	size++;
}

void array_bag::insert(int *items, int count)
{
	for (int i = 0; i < count; i++)
		insert(items[i]);
}

void array_bag::print() const
{
	for (int i = 0; i < size; i++)
		std::cout << data[i] << " ";
	std::cout << std::endl;
}

void array_bag::clear()
{
	delete[] data;
	data = NULL;
	size = 0;
}
