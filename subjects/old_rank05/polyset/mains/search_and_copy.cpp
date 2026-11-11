// has() on empty bags, duplicates, negatives, deep copies, sets over both bags
#include "searchable_array_bag.hpp"
#include "searchable_tree_bag.hpp"
#include "set.hpp"

#include <iostream>

int main()
{
	searchable_array_bag a;
	searchable_tree_bag t;
	std::cout << "empty: " << a.has(0) << t.has(0) << std::endl;

	int values[] = {5, -3, 5, 0, 12, -3, 7};
	a.insert(values, 7);
	t.insert(values, 7);
	std::cout << "array: ";
	a.print();
	std::cout << "tree:  ";
	t.print();
	int probes[] = {5, -3, 0, 12, 7, 6, -4, 13};
	for (int i = 0; i < 8; i++)
		std::cout << "has(" << probes[i] << "): " << a.has(probes[i]) << t.has(probes[i]) << std::endl;

	searchable_array_bag a2(a);
	searchable_tree_bag t2(t);
	a.clear();
	t.clear();
	std::cout << "after clearing the originals, copies have 12: " << a2.has(12) << t2.has(12)
		<< ", originals: " << a.has(12) << t.has(12) << std::endl;
	a = a2;
	t = t2;
	a2.clear();
	t2.clear();
	std::cout << "assigned back: " << a.has(-3) << t.has(-3) << a2.has(-3) << t2.has(-3) << std::endl;
	a = a;
	t = t;
	std::cout << "self-assigned: ";
	a.print();

	searchable_array_bag sa_bag;
	searchable_tree_bag st_bag;
	set sa(sa_bag);
	set st(st_bag);
	int more[] = {4, 4, 2, 9, 2, -1};
	sa.insert(more, 6);
	st.insert(more, 6);
	sa.insert(4);
	st.insert(9);
	std::cout << "set over array: ";
	sa.print();
	std::cout << "set over tree:  ";
	st.print();
	std::cout << "the array bag itself: ";
	sa.get_bag().print();
	std::cout << "set has 9, 3: " << sa.has(9) << sa.has(3) << st.has(9) << st.has(3) << std::endl;
	sa.clear();
	std::cout << "after clear: " << sa.has(4) << std::endl;
	sa.insert(1);
	sa.print();

	searchable_bag *poly[2];
	poly[0] = new searchable_array_bag(a);
	poly[1] = new searchable_tree_bag(t);
	for (int i = 0; i < 2; i++)
	{
		poly[i]->insert(100);
		std::cout << "through searchable_bag*: " << poly[i]->has(100) << poly[i]->has(101) << " ";
		poly[i]->print();
	}
	bag *as_bag = poly[0];
	delete as_bag;
	delete poly[1];
	return 0;
}
