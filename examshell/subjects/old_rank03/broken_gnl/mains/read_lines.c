// reads a file (or stdin, or a bad fd) with get_next_line and shows every line
#include "get_next_line.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void	show(const char *line)
{
	for (; *line; line++)
	{
		if (*line == '\n')
			printf("\\n");
		else
			putchar(*line);
	}
}

int	main(int argc, char **argv)
{
	int		fd;
	int		n;
	char	*line;

	fd = 0;
	if (argc > 1 && strcmp(argv[1], "-1") == 0)
		fd = -1;
	else if (argc > 1)
		fd = open(argv[1], O_RDONLY);
	n = 0;
	while ((line = get_next_line(fd)))
	{
		printf("[%d] \"", ++n);
		show(line);
		printf("\"\n");
		free(line);
	}
	printf("NULL after %d line%s\n", n, n == 1 ? "" : "s");
	line = get_next_line(fd);
	printf("called again: %s\n", line ? "not NULL" : "NULL");
	free(line);
	if (fd > 0)
		close(fd);
	return (0);
}
