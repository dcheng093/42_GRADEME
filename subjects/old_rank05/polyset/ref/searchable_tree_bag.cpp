#include "searchable_tree_bag.hpp"

searchable_tree_bag::searchable_tree_bag() : bag(), tree_bag(), searchable_bag() {}

searchable_tree_bag::searchable_tree_bag(const searchable_tree_bag &other)
	: bag(), tree_bag(other), searchable_bag(other) {}

searchable_tree_bag &searchable_tree_bag::operator=(const searchable_tree_bag &other)
{
	tree_bag::operator=(other);
	return *this;
}

searchable_tree_bag::~searchable_tree_bag() {}

bool searchable_tree_bag::has(int value) const
{
	const node *n = tree;
	while (n)
	{
		if (value == n->value)
			return true;
		n = value < n->value ? n->l : n->r;
	}
	return false;
}
