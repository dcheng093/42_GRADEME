#include <stdio.h>
#include <stdlib.h>

// rows[c]: the line of the queen in column c
static int	safe(int *rows, int col, int row)
{
	for (int c = 0; c < col; c++)
	{
		if (rows[c] == row || abs(rows[c] - row) == col - c)
			return (0);
	}
	return (1);
}

static void	solve(int *rows, int col, int n)
{
	if (col == n)
	{
		for (int c = 0; c < n; c++)
			fprintf(stdout, c ? " %d" : "%d", rows[c]);
		fprintf(stdout, "\n");
		return ;
	}
	for (int row = 0; row < n; row++)
	{
		if (safe(rows, col, row))
		{
			rows[col] = row;
			solve(rows, col + 1, n);
		}
	}
}

int	main(int argc, char **argv)
{
	int	n;
	int	*rows;

	if (argc != 2)
		return (1);
	n = atoi(argv[1]);
	if (n <= 0)
		return (0);
	rows = calloc(n, sizeof(int));
	if (!rows)
		return (1);
	solve(rows, 0, n);
	free(rows);
	return (0);
}
