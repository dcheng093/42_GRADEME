// turns ./picoshell cmd1 args "|" cmd2 args ... into the cmds array
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int	picoshell(char **cmds[]);

int	main(int argc, char **argv)
{
	int		cmds_size = 1;
	char	***cmds;
	int		ret;
	int		id = 0;

	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "|"))
			cmds_size++;
	cmds = calloc(cmds_size + 1, sizeof(char **));
	if (!cmds)
		return (1);
	cmds[id++] = argv + 1;
	for (int i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "|"))
		{
			cmds[id++] = argv + i + 1;
			argv[i] = NULL;
		}
	}
	ret = picoshell(cmds);
	if (ret)
		perror("picoshell");
	free(cmds);
	return (ret);
}
