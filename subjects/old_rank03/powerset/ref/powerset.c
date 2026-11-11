#include <stdio.h>
#include <stdlib.h>

static void	search(int *set, int size, int i, int *picked, int count, long sum, long target)
{
	if (i == size)
	{
		if (sum != target)
			return ;
		for (int k = 0; k < count; k++)
			printf(k ? " %d" : "%d", picked[k]);
		printf("\n");
		return ;
	}
	picked[count] = set[i];
	search(set, size, i + 1, picked, count + 1, sum + set[i], target);
	search(set, size, i + 1, picked, count, sum, target);
}

int	main(int argc, char **argv)
{
	int	size;
	int	*set;
	int	*picked;

	if (argc < 2)
		return (1);
	size = argc - 2;
	set = malloc(sizeof(int) * (size + 1));
	picked = malloc(sizeof(int) * (size + 1));
	if (!set || !picked)
		return (free(set), free(picked), 1);
	for (int i = 0; i < size; i++)
		set[i] = atoi(argv[i + 2]);
	search(set, size, 0, picked, 0, 0, atoi(argv[1]));
	free(set);
	free(picked);
	return (0);
}
