#ifndef LIFE_H
# define LIFE_H

typedef struct s_board
{
	int		width;
	int		height;
	char	*cells;
	char	*next;
}	t_board;

#endif
