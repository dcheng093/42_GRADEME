#include <stdio.h>

int	main(int argc, char **argv)
{
	int		counts[26] = {0};
	int		first;
	char	*s;
	int		c;

	if (argc == 2)
	{
		for (s = argv[1]; *s; s++)
			if ((*s | 32) >= 'a' && (*s | 32) <= 'z')
				counts[(*s | 32) - 'a']++;
		first = 1;
		for (s = argv[1]; *s; s++)
		{
			c = *s | 32;
			if (c >= 'a' && c <= 'z' && counts[c - 'a'])
			{
				printf(first ? "%d%c" : ", %d%c", counts[c - 'a'], c);
				counts[c - 'a'] = 0;
				first = 0;
			}
		}
	}
	printf("\n");
	return (0);
}
