#include "life.h"
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

static int	alive(const t_board *b, int x, int y)
{
	if (x < 0 || y < 0 || x >= b->width || y >= b->height)
		return (0);
	return (b->cells[y * b->width + x]);
}

static void	step(t_board *b)
{
	int		x;
	int		y;
	int		n;
	char	*tmp;

	y = -1;
	while (++y < b->height)
	{
		x = -1;
		while (++x < b->width)
		{
			n = alive(b, x - 1, y - 1) + alive(b, x, y - 1) + alive(b, x + 1, y - 1)
				+ alive(b, x - 1, y) + alive(b, x + 1, y)
				+ alive(b, x - 1, y + 1) + alive(b, x, y + 1) + alive(b, x + 1, y + 1);
			b->next[y * b->width + x] = (n == 3 || (n == 2 && alive(b, x, y)));
		}
	}
	tmp = b->cells;
	b->cells = b->next;
	b->next = tmp;
}

// the pen starts top-left, up; x lowers it (drawing where it stands) or lifts it
static void	draw(t_board *b)
{
	char	c;
	int		x;
	int		y;
	int		down;

	x = 0;
	y = 0;
	down = 0;
	while (read(0, &c, 1) == 1)
	{
		if (c == 'w' && y > 0)
			y--;
		else if (c == 's' && y < b->height - 1)
			y++;
		else if (c == 'a' && x > 0)
			x--;
		else if (c == 'd' && x < b->width - 1)
			x++;
		else if (c == 'x')
			down = !down;
		if (down)
			b->cells[y * b->width + x] = 1;
	}
}

int	main(int argc, char **argv)
{
	t_board	b;
	int		iterations;
	int		x;
	int		y;

	if (argc != 4)
		return (1);
	b.width = atoi(argv[1]);
	b.height = atoi(argv[2]);
	iterations = atoi(argv[3]);
	if (b.width <= 0 || b.height <= 0 || iterations < 0)
		return (1);
	b.cells = calloc(b.width * b.height, 1);
	b.next = calloc(b.width * b.height, 1);
	if (!b.cells || !b.next)
		return (free(b.cells), free(b.next), 1);
	draw(&b);
	while (iterations--)
		step(&b);
	y = -1;
	while (++y < b.height)
	{
		x = -1;
		while (++x < b.width)
			putchar(b.cells[y * b.width + x] ? 'O' : ' ');
		putchar('\n');
	}
	free(b.cells);
	free(b.next);
	return (0);
}
