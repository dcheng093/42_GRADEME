#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

#define CHUNK 4096

// read all of stdin, then write it with every match of the pattern starred out
int	main(int argc, char **argv)
{
	char	*buf;
	char	*tmp;
	size_t	len;
	size_t	cap;
	ssize_t	n;
	size_t	plen;
	char	*hit;
	size_t	pos;

	if (argc != 2 || !argv[1][0])
		return (1);
	plen = strlen(argv[1]);
	len = 0;
	cap = CHUNK;
	buf = malloc(cap);
	if (!buf)
		return (perror("Error"), 1);
	while ((n = read(0, buf + len, cap - len)) > 0)
	{
		len += n;
		if (len == cap)
		{
			tmp = realloc(buf, cap * 2);
			if (!tmp)
				return (free(buf), perror("Error"), 1);
			buf = tmp;
			cap *= 2;
		}
	}
	if (n < 0)
		return (free(buf), perror("Error"), 1);
	pos = 0;
	while ((hit = memmem(buf + pos, len - pos, argv[1], plen)))
	{
		write(1, buf + pos, hit - (buf + pos));
		for (size_t i = 0; i < plen; i++)
			write(1, "*", 1);
		pos = (hit - buf) + plen;
	}
	write(1, buf + pos, len - pos);
	free(buf);
	return (0);
}
