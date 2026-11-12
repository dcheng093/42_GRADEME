// ft_popen tests, one per argv[1]; prints what happened, never raw pointers or pids
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int	ft_popen(const char *file, char *const argv[], char type);

static int	count_fds(void)
{
	DIR				*dir = opendir("/proc/self/fd");
	struct dirent	*e;
	int				n = 0;

	if (!dir)
	{
		for (int fd = 0; fd < 1024; fd++)
			if (dup2(fd, fd) != -1)
				n++;
		return (n);
	}
	while ((e = readdir(dir)))
		if (e->d_name[0] != '.')
			n++;
	closedir(dir);
	return (n - 1);
}

static void	drain(int fd, const char *label)
{
	char	buf[4096];
	ssize_t	n;
	size_t	total = 0;

	printf("%s: \"", label);
	while ((n = read(fd, buf, sizeof(buf))) > 0)
	{
		total += n;
		for (ssize_t i = 0; i < n; i++)
			buf[i] == '\n' ? printf("\\n") : printf("%c", buf[i]);
	}
	printf("\" (%zu bytes)\n", total);
}

static void	reap(void)
{
	while (wait(NULL) > 0)
		;
}

int	main(int argc, char **argv)
{
	int	fd;
	int	before;

	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc != 2)
		return (1);
	switch (atoi(argv[1]))
	{
	case 0:
		fd = ft_popen("echo", (char *const []){"echo", "hello", "world", NULL}, 'r');
		drain(fd, "read from 'echo hello world'");
		close(fd);
		break ;
	case 1:
		printf("writing \"one\\ntwo\\n\" into 'cat':\n");
		fd = ft_popen("cat", (char *const []){"cat", NULL}, 'w');
		write(fd, "one\ntwo\n", 8);
		close(fd);
		reap();
		printf("(cat finished)\n");
		break ;
	case 2:
		fd = ft_popen("printf", (char *const []){"printf", "apple\\nbanana\\ncherry\\n", NULL}, 'r');
		dup2(fd, 0);
		close(fd);
		fd = ft_popen("grep", (char *const []){"grep", "an", NULL}, 'r');
		drain(fd, "'printf ... | grep an'");
		close(fd);
		break ;
	case 3:
		printf("type 'x': %d\n", ft_popen("ls", (char *const []){"ls", NULL}, 'x'));
		printf("type 0: %d\n", ft_popen("ls", (char *const []){"ls", NULL}, 0));
		printf("file NULL: %d\n", ft_popen(NULL, (char *const []){"ls", NULL}, 'r'));
		printf("argv NULL: %d\n", ft_popen("ls", NULL, 'r'));
		break ;
	case 4:
		fd = ft_popen("no_such_command_42", (char *const []){"no_such_command_42", NULL}, 'r');
		printf("a command that doesn't exist: %s\n", fd >= 0 ? "got a fd" : "-1");
		if (fd >= 0)
		{
			drain(fd, "its output");
			close(fd);
		}
		break ;
	case 5:
		before = count_fds();
		fd = ft_popen("echo", (char *const []){"echo", "x", NULL}, 'r');
		printf("new fds after ft_popen 'r': %d\n", count_fds() - before);
		close(fd);
		fd = ft_popen("cat", (char *const []){"cat", NULL}, 'w');
		printf("new fds after ft_popen 'w': %d\n", count_fds() - before);
		close(fd);
		reap();
		printf("leaked fds after closing both: %d\n", count_fds() - before);
		break ;
	case 6:
		// ls lists its own fds: 0 1 2 and the one it opens for the folder.
		// Anything more is a pipe end the child kept open.
		fd = ft_popen("ls", (char *const []){"ls", "/proc/self/fd", NULL}, 'r');
		drain(fd, "fds open inside the command ('r')");
		close(fd);
		reap();
		printf("fds open inside the command ('w'):\n");
		fd = ft_popen("ls", (char *const []){"ls", "/proc/self/fd", NULL}, 'w');
		close(fd);
		reap();
		break ;
	case 7:
		before = count_fds();
		for (int i = 0; i < 100; i++)
		{
			fd = ft_popen("true", (char *const []){"true", NULL}, i % 2 ? 'r' : 'w');
			if (fd < 0)
			{
				printf("call %d failed (fds exhausted?)\n", i);
				break ;
			}
			close(fd);
			reap();
		}
		printf("100 calls, leaked fds: %d\n", count_fds() - before);
		break ;
	default:
		return (1);
	}
	reap();
	return (0);
}
