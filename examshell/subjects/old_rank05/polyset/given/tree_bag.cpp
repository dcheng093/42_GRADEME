#include "tree_bag.hpp"

#include <iostream>
#include <cstddef>

tree_bag::tree_bag() : tree(NULL) {}

tree_bag::tree_bag(const tree_bag &src) : bag(), tree(copy_node(src.tree)) {}

tree_bag::~tree_bag()
{
	destroy_tree(tree);
}

tree_bag &tree_bag::operator=(const tree_bag &src)
{
	if (this != &src)
	{
		destroy_tree(tree);
		tree = copy_node(src.tree);
	}
	return *this;
}

tree_bag::node *tree_bag::extract_tree()
{
	node *taken = tree;
	tree = NULL;
	return taken;
}

void tree_bag::set_tree(node *new_tree)
{
	destroy_tree(tree);
	tree = new_tree;
}

// a binary search tree: smaller values to the left; a value already in
// the tree is not added again
void tree_bag::insert(int item)
{
	node **slot = &tree;
	while (*slot)
	{
		if (item < (*slot)->value)
			slot = &(*slot)->l;
		else if (item > (*slot)->value)
			slot = &(*slot)->r;
		else
			return;
	}
	*slot = new node;
	(*slot)->value = item;
	(*slot)->l = NULL;
	(*slot)->r = NULL;
}

void tree_bag::insert(int *items, int count)
{
	for (int i = 0; i < count; i++)
		insert(items[i]);
}

void tree_bag::print() const
{
	print_node(tree);
	std::cout << std::endl;
}

void tree_bag::clear()
{
	destroy_tree(tree);
	tree = NULL;
}

void tree_bag::destroy_tree(node *n)
{
	if (!n)
		return;
	destroy_tree(n->l);
	destroy_tree(n->r);
	delete n;
}

void tree_bag::print_node(node *n)
{
	if (!n)
		return;
	print_node(n->l);
	std::cout << n->value << " ";
	print_node(n->r);
}

tree_bag::node *tree_bag::copy_node(node *n)
{
	if (!n)
		return NULL;
	node *copy = new node;
	copy->value = n->value;
	copy->l = copy_node(n->l);
	copy->r = copy_node(n->r);
	return copy;
}
