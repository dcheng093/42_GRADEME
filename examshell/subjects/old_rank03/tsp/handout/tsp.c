#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/types.h>

// distance between two cities
float	distance(float a[2], float b[2])
{
	return (sqrtf((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1])));
}

// the length of the shortest closed path going through every city
float	tsp(float (*array)[2], ssize_t size)
{
	float	best_distance;

	(void)array;
	(void)size;
	best_distance = 0;
	// your code here

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
