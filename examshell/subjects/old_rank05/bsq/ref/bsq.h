#ifndef BSQ_H
# define BSQ_H

# include <stdio.h>

typedef struct s_map
{
	int		rows;
	int		cols;
	char	empty;
	char	obstacle;
	char	full;
	char	**grid;
}	t_map;

int		read_map(FILE *file, t_map *map);
void	solve_map(t_map *map);
void	print_map(const t_map *map);
void	free_map(t_map *map);

#endif
