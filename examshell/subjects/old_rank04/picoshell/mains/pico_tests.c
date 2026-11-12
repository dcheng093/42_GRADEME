// picoshell tests, one per argv[1]: output, fds left open, children left behind
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int	picoshell(char **cmds[]);

static int	count_fds(void)
{
	DIR				*dir = opendir("/proc/self/fd");
	struct dirent	*e;
	int				n = 0;

	if (!dir)
		return (-1);
	while ((e = readdir(dir)))
		if (e->d_name[0] != '.')
			n++;
	closedir(dir);
	return (n - 1);
}

static void	run(const char *label, char **cmds[], int show_ret)
{
	int	before = count_fds();
	int	ret;
	int	zombies = 0;

	printf("--- %s\n", label);
	ret = picoshell(cmds);
	if (show_ret)
		printf("--- returned %d\n", ret);
	printf("--- fds left open: %d\n", count_fds() - before);
	// any child still there, running or zombie, was not waited for
	for (pid_t r; (r = waitpid(-1, NULL, WNOHANG)) != -1; zombies++)
		if (r == 0)
		{
			usleep(100000);
			if (waitpid(-1, NULL, WNOHANG) == 0)
			{
				zombies++;
				break ;
			}
		}
	printf("--- children not waited for: %d\n", zombies);
}

int	main(int argc, char **argv)
{
	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc != 2)
		return (1);
	switch (atoi(argv[1]))
	{
	case 0:
		run("echo hello", (char **[]){(char *[]){"echo", "hello", NULL}, NULL}, 1);
		break ;
	case 1:
		run("echo test | cat", (char **[]){(char *[]){"echo", "test", NULL}, (char *[]){"cat", NULL}, NULL}, 1);
		break ;
	case 2:
		run("echo squalala | cat | sed s/a/b/g", (char **[]){(char *[]){"echo", "squalala", NULL},
			(char *[]){"cat", NULL}, (char *[]){"sed", "s/a/b/g", NULL}, NULL}, 1);
		break ;
	case 3:
		run("echo 'aaa bbb ccc' | sed | sed | sed", (char **[]){(char *[]){"echo", "aaa bbb ccc", NULL},
			(char *[]){"sed", "s/a/x/g", NULL}, (char *[]){"sed", "s/b/y/g", NULL},
			(char *[]){"sed", "s/c/z/g", NULL}, NULL}, 1);
		break ;
	case 4:
		run("printf 'b\\na\\nc\\n' | sort | head -n 2", (char **[]){(char *[]){"printf", "b\\na\\nc\\n", NULL},
			(char *[]){"sort", NULL}, (char *[]){"head", "-n", "2", NULL}, NULL}, 1);
		break ;
	case 5:
		// yes never stops by itself: it ends when head is done and nobody holds the pipe
		run("yes | head -n 3", (char **[]){(char *[]){"yes", NULL}, (char *[]){"head", "-n", "3", NULL}, NULL}, 0);
		break ;
	case 6:
	{
		char	**cmds[41];
		for (int i = 0; i < 40; i++)
			cmds[i] = i ? (char *[]){"cat", NULL} : (char *[]){"echo", "through 40 commands", NULL};
		cmds[40] = NULL;
		run("echo | cat | cat | ... (40 commands)", cmds, 1);
		break ;
	}
	case 7:
		run("no_such_command_42 | cat", (char **[]){(char *[]){"no_such_command_42", NULL},
			(char *[]){"cat", NULL}, NULL}, 0);
		break ;
	case 8:
		run("echo a | no_such_command_42 (stderr hidden)", (char **[]){(char *[]){"echo", "a", NULL},
			(char *[]){"no_such_command_42", NULL}, NULL}, 0);
		break ;
	default:
		return (1);
	}
	return (0);
}
