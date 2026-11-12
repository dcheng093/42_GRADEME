#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/types.h>

// distance between two cities
float	distance(float a[2], float b[2])
{
	return (sqrtf((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1])));
}

// tries every order of the cities after the first one (the start doesn't matter
// on a closed path), cutting branches already longer than the best one
static void	search(float (*array)[2], ssize_t size, int *order, int *used, ssize_t depth,
			float length, float *best)
{
	if (length >= *best)
		return ;
	if (depth == size)
	{
		length += distance(array[order[size - 1]], array[order[0]]);
		if (length < *best)
			*best = length;
		return ;
	}
	for (ssize_t i = 1; i < size; i++)
	{
		if (used[i])
			continue ;
		used[i] = 1;
		order[depth] = (int)i;
		search(array, size, order, used, depth + 1,
			length + distance(array[order[depth - 1]], array[i]), best);
		used[i] = 0;
	}
}

// the length of the shortest closed path going through every city
float	tsp(float (*array)[2], ssize_t size)
{
	float	best_distance;
	int		order[64];
	int		used[64] = {0};

	if (size < 2 || size > 64)
		return (0);
	best_distance = INFINITY;
	order[0] = 0;
	used[0] = 1;
	search(array, size, order, used, 1, 0, &best_distance);
	return (best_distance);
}

// reads '%f, %f\n' lines until the end of the input
static ssize_t	read_cities(FILE *file, float (**array)[2])
{
	ssize_t	size;
	ssize_t	cap;
	float	x;
	float	y;
	float	(*bigger)[2];

	size = 0;
	cap = 16;
	*array = malloc(sizeof(float [2]) * cap);
	if (!*array)
		return (-1);
	while (fscanf(file, " %f , %f", &x, &y) == 2)
	{
		if (size == cap)
		{
			cap *= 2;
			bigger = realloc(*array, sizeof(float [2]) * cap);
			if (!bigger)
				return (-1);
			*array = bigger;
		}
		(*array)[size][0] = x;
		(*array)[size][1] = y;
		size++;
	}
	if (ferror(file))
		return (-1);
	return (size);
}

int	main(int argc, char **argv)
{
	FILE	*file;
	float	(*array)[2];
	ssize_t	size;

	file = stdin;
	if (argc > 1)
		file = fopen(argv[1], "r");
	if (!file)
	{
		fprintf(stderr, "Error opening %s\n", argv[1]);
		return (1);
	}
	array = NULL;
	size = read_cities(file, &array);
	if (size == -1)
	{
		fprintf(stderr, "Error reading the cities\n");
		free(array);
		return (1);
	}
	fprintf(stdout, "%.2f\n", tsp(array, size));
	free(array);
	if (argc > 1)
		fclose(file);
	return (0);
}
