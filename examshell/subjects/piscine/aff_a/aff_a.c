#include <unistd.h>

int	main(int argc, char **argv)
{
	int	i;

	if (argc != 2)
		return (write(1, "a\n", 2), 0);
	i = 0;
	while (argv[1][i] && argv[1][i] != 'a')
		i++;
	if (argv[1][i] == 'a')
		write(1, "a", 1);
	write(1, "\n", 1);
	return (0);
}
