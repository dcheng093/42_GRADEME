#pragma once

#include "searchable_bag.hpp"

// a set wraps a searchable bag it doesn't own, and only inserts what the bag
// doesn't have yet
class set
{
	searchable_bag *_bag;

public:
	set(searchable_bag &bag);
	set(const set &other);
	set &operator=(const set &other);
	~set();

	bool has(int value) const;
	void insert(int value);
	void insert(int *values, int count);
	void print() const;
	void clear();
	searchable_bag &get_bag();
	const searchable_bag &get_bag() const;
};
