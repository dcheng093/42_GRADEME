#include <stdio.h>
#include <string.h>

static int	g_count;
static char	g_seen[4096][64];

// how many '(' and ')' must go so that the string balances
static void	to_remove(const char *s, int *open, int *close)
{
	*open = 0;
	*close = 0;
	for (int i = 0; s[i]; i++)
	{
		if (s[i] == '(')
			(*open)++;
		else if (s[i] == ')')
		{
			if (*open)
				(*open)--;
			else
				(*close)++;
		}
	}
}

static int	balanced(const char *s)
{
	int	open;
	int	close;

	to_remove(s, &open, &close);
	return (open == 0 && close == 0);
}

static void	solve(char *s, int from, int open, int close)
{
	if (open == 0 && close == 0)
	{
		if (!balanced(s))
			return ;
		for (int i = 0; i < g_count; i++)
			if (strcmp(g_seen[i], s) == 0)
				return ;
		if (g_count < 4096)
			strcpy(g_seen[g_count++], s);
		puts(s);
		return ;
	}
	for (int i = from; s[i]; i++)
	{
		char c = s[i];
		if ((c == '(' && open) || (c == ')' && close))
		{
			s[i] = ' ';
			solve(s, i + 1, open - (c == '('), close - (c == ')'));
			s[i] = c;
		}
	}
}

int	main(int argc, char **argv)
{
	int		open;
	int		close;
	char	s[64];

	if (argc != 2 || strlen(argv[1]) >= sizeof(s))
		return (1);
	strcpy(s, argv[1]);
	to_remove(s, &open, &close);
	solve(s, 0, open, close);
	return (0);
}
