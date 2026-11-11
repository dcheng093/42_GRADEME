#include <stdlib.h>
#include <unistd.h>

static int	contains(char *hay, char *needle, int len)
{
	for (int i = 0; hay[i]; i++)
	{
		int j = 0;
		while (j < len && hay[i + j] && hay[i + j] == needle[j])
			j++;
		if (j == len)
			return (1);
	}
	return (len == 0);
}

int	main(int argc, char **argv)
{
	int	len;
	int	n;

	if (argc < 2)
		return (write(1, "\n", 1), 0);
	n = 0;
	while (argv[1][n])
		n++;
	// the longest first; for one length, the first start in argv[1]
	for (len = n; len > 0; len--)
	{
		for (int start = 0; start + len <= n; start++)
		{
			int i = 2;
			while (i < argc && contains(argv[i], argv[1] + start, len))
				i++;
			if (i == argc)
			{
				write(1, argv[1] + start, len);
				write(1, "\n", 1);
				return (0);
			}
		}
	}
	write(1, "\n", 1);
	return (0);
}
