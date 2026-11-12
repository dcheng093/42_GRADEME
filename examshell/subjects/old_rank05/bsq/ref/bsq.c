#include "bsq.h"
#include <stdlib.h>
#include <string.h>

static int	is_printable(char c)
{
	return (c >= 32 && c <= 126);
}

// first line: "<rows> <empty> <obstacle> <full>\n"
static int	read_header(char *line, ssize_t len, t_map *map)
{
	ssize_t	i;
	long	rows;

	if (len < 8 || line[len - 1] != '\n')
		return (0);
	i = len - 1;
	map->full = line[i - 1];
	map->obstacle = line[i - 3];
	map->empty = line[i - 5];
	if (line[i - 2] != ' ' || line[i - 4] != ' ' || line[i - 6] != ' ')
		return (0);
	rows = 0;
	i = 0;
	while (i < len - 7)
	{
		if (line[i] < '0' || line[i] > '9' || rows > 100000000)
			return (0);
		rows = rows * 10 + (line[i] - '0');
		i++;
	}
	if (i == 0 || rows <= 0)
		return (0);
	if (!is_printable(map->empty) || !is_printable(map->obstacle) || !is_printable(map->full))
		return (0);
	if (map->empty == map->obstacle || map->empty == map->full || map->obstacle == map->full)
		return (0);
	map->rows = (int)rows;
	return (1);
}

int	read_map(FILE *file, t_map *map)
{
	char	*line;
	size_t	cap;
	ssize_t	len;
	int		r;
	int		c;

	line = NULL;
	cap = 0;
	map->grid = NULL;
	len = getline(&line, &cap, file);
	if (len <= 0 || !read_header(line, len, map))
		return (free(line), 0);
	map->grid = calloc(map->rows + 1, sizeof(char *));
	if (!map->grid)
		return (free(line), 0);
	map->cols = -1;
	r = 0;
	while (r < map->rows)
	{
		len = getline(&line, &cap, file);
		if (len <= 1 || line[len - 1] != '\n')
			return (free(line), 0);
		if (map->cols == -1)
			map->cols = (int)len - 1;
		if (len - 1 != map->cols)
			return (free(line), 0);
		c = 0;
		while (c < map->cols)
		{
			if (line[c] != map->empty && line[c] != map->obstacle)
				return (free(line), 0);
			c++;
		}
		map->grid[r] = malloc(map->cols + 1);
		if (!map->grid[r])
			return (free(line), 0);
		memcpy(map->grid[r], line, map->cols);
		map->grid[r][map->cols] = '\0';
		r++;
	}
	len = getline(&line, &cap, file);
	free(line);
	return (len <= 0);  // nothing may follow the last row
}

// size[r][c]: biggest square whose bottom-right corner is (r, c); the first
// strictly bigger one in reading order is the top-most, then left-most square
void	solve_map(t_map *map)
{
	int	*prev;
	int	*cur;
	int	best;
	int	best_r;
	int	best_c;
	int	r;
	int	c;
	int	*tmp;

	prev = calloc(map->cols + 1, sizeof(int));
	cur = calloc(map->cols + 1, sizeof(int));
	best = 0;
	best_r = 0;
	best_c = 0;
	r = 0;
	while (r < map->rows && prev && cur)
	{
		c = 0;
		while (c < map->cols)
		{
			if (map->grid[r][c] == map->obstacle)
				cur[c + 1] = 0;
			else
			{
				cur[c + 1] = prev[c];
				if (prev[c + 1] < cur[c + 1])
					cur[c + 1] = prev[c + 1];
				if (cur[c] < cur[c + 1])
					cur[c + 1] = cur[c];
				cur[c + 1] += 1;
				if (cur[c + 1] > best)
				{
					best = cur[c + 1];
					best_r = r;
					best_c = c;
				}
			}
			c++;
		}
		tmp = prev;
		prev = cur;
		cur = tmp;
		r++;
	}
	r = best_r - best + 1;
	while (best && r <= best_r)
	{
		c = best_c - best + 1;
		while (c <= best_c)
			map->grid[r][c++] = map->full;
		r++;
	}
	free(prev);
	free(cur);
}

void	print_map(const t_map *map)
{
	int	r;

	r = 0;
	while (r < map->rows)
	{
		fputs(map->grid[r], stdout);
		fputs("\n", stdout);
		r++;
	}
}

void	free_map(t_map *map)
{
	int	r;

	if (!map->grid)
		return ;
	r = 0;
	while (map->grid[r])
		free(map->grid[r++]);
	free(map->grid);
	map->grid = NULL;
}

static void	run(FILE *file)
{
	t_map	map;

	if (read_map(file, &map))
	{
		solve_map(&map);
		print_map(&map);
	}
	else
		fprintf(stderr, "map error\n");
	free_map(&map);
}

int	main(int argc, char **argv)
{
	FILE	*file;
	int		i;

	if (argc < 2)
	{
		run(stdin);
		return (0);
	}
	i = 1;
	while (i < argc)
	{
		file = fopen(argv[i], "r");
		if (!file)
			fprintf(stderr, "map error\n");
		else
		{
			run(file);
			fclose(file);
		}
		i++;
	}
	return (0);
}
