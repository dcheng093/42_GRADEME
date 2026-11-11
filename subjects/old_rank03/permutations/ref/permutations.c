#include <stdlib.h>
#include <unistd.h>

static int	ft_strlen(const char *s)
{
	int	n = 0;

	while (s[n])
		n++;
	return (n);
}

static void	sort(char *s, int n)
{
	for (int i = 1; i < n; i++)
	{
		char c = s[i];
		int j = i - 1;
		while (j >= 0 && s[j] > c)
		{
			s[j + 1] = s[j];
			j--;
		}
		s[j + 1] = c;
	}
}

// picks the letters in order, so the permutations come out alphabetically
static void	permute(const char *letters, int n, int *used, char *out, int depth)
{
	if (depth == n)
	{
		write(1, out, n);
		write(1, "\n", 1);
		return ;
	}
	for (int i = 0; i < n; i++)
	{
		if (used[i])
			continue ;
		used[i] = 1;
		out[depth] = letters[i];
		permute(letters, n, used, out, depth + 1);
		used[i] = 0;
	}
}

int	main(int argc, char **argv)
{
	int		n;
	char	*letters;
	char	*out;
	int		*used;

	if (argc != 2)
		return (1);
	n = ft_strlen(argv[1]);
	letters = malloc(n + 1);
	out = malloc(n + 1);
	used = calloc(n + 1, sizeof(int));
	if (!letters || !out || !used)
		return (free(letters), free(out), free(used), 1);
	for (int i = 0; i <= n; i++)
		letters[i] = argv[1][i];
	sort(letters, n);
	permute(letters, n, used, out, 0);
	free(letters);
	free(out);
	free(used);
	return (0);
}
